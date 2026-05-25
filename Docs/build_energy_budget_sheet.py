"""Generate Energy Budget worksheet (xlsx) and HTML view from shared calculations."""
import html as html_mod
import openpyxl
import subprocess
from pathlib import Path
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from firmware_todo import docs_nav, update_workbook, write_todo_html

DOCS = Path(__file__).resolve().parent
XLSX_PATH = DOCS / "SolarSensorSchematicRev2_BOM.xlsx"
HTML_PATH = DOCS / "SolarSensorSchematicRev2_EnergyBudget.html"
FLOW_MMD_PATH = DOCS / "power_optimization_flow.mmd"
FLOW_PNG_PATH = DOCS / "power_optimization_flow.png"
AVG_MMD_PATH = DOCS / "averaging_n_samples_flow.mmd"
AVG_PNG_PATH = DOCS / "averaging_n_samples_flow.png"
FILTER_N_DEFAULT = 5
FILTER_N_TYPICAL = "3–5"

# --- Shared model constants ---
BUDGET_PERIOD_S = 300
LORA_INTERVAL_S = 300
V_MCU = 3.3
V_18 = 1.8
V_CO2 = 3.3
I_SLEEP_UA = 1.3
I_ACTIVE_MA = 4.0
T_ACTIVE_S = 0.10
HARVEST_EFF = 0.75
MARGIN = 1.30
PANEL_AREA_CM2 = 16
PANEL_UW_CM2_REF = 8
REF_LUX = 200

# Default per-sensor configuration: (name, ref, populated, sample_s, mode, i_ma, t_s, supply, notes)
# mode: pulsed | single-shot
SENSOR_CONFIG = [
    ("SHT40", "U5/U7", 1, 300, "pulsed", 0.8, 0.020, V_18, "HUM_EN switched"),
    ("SGP30", "U3", 0, 300, "pulsed", 48, 0.040, V_18, "TVOC optional — set Populated=1 if fitted"),
    ("BH1620 / GC2", "U8", 1, 300, "pulsed", 0.09, 0.010, V_MCU, "Light sensor"),
    ("STCC4 CO₂", "U6", 1, 300, "single-shot", 2.0, 0.505, V_CO2, "exit_sleep + measure_single_shot + sleep"),
]

TX_I, TX_T = 60, 0.052

FLOWCHART_MMD = Path(__file__).resolve().parent.joinpath("power_optimization_flow.mmd").read_text(encoding="utf-8")
AVG_FLOWCHART_MMD = Path(__file__).resolve().parent.joinpath("averaging_n_samples_flow.mmd").read_text(encoding="utf-8")

FLOW_STEPS = [
    ("1", "RTC alarm / report due", "—", "Wake from STOP3 on interval"),
    ("2", "Wake MCU + radio", "—", "RA-08 exits low-power mode"),
    ("3", "Start STCC4 first (slow)", "—", "exit_sleep 5 ms + measure_single_shot — 500 ms conversion begins"),
    ("4", "Parallel fast sensors", "—", "While CO₂ converts: SHT40 ~20 ms, SGP30 ~40 ms, BH1620 ~10 ms"),
    ("5", "Wait for CO₂ ready", "—", "STOP3 sleep ~440 ms remaining — not busy-wait"),
    ("6", "STCC4 read + sleep", "—", "read_measurement then enter_sleep_mode (~1 µA)"),
    ("7", "Push to N-sample buffers", "—", f"Ring buffer depth N (typically {FILTER_N_TYPICAL}) per channel"),
    ("8", "Compute filtered mean", "—", "avg = sum(last N reads) / N — no extra sensor reads"),
    ("9", "Pack + LoRa TX", "—", "19-byte payload with filtered values; 52 ms on-air"),
    ("10", "Disable rails + STOP3", "—", "Until next RTC interval"),
]

AVG_FLOW_STEPS = [
    ("1", "Raw reads complete", "—", "One sample per channel per report cycle"),
    ("2", "Write ring buffer", "—", f"buf[k] = raw; k = index mod N (N typically {FILTER_N_TYPICAL})"),
    ("3", "Advance index", "—", "sample_index++ wrap at N"),
    ("4", "Buffer full?", "—", f"If count < N use partial mean or wait (default N={FILTER_N_DEFAULT})"),
    ("5", "Compute mean", "—", "filtered = arithmetic mean of buf[0..N-1] per channel"),
    ("6", "Pack + TX", "—", "LoRa uplink uses filtered T · RH · TVOC · lux · CO₂"),
]

FLOW_LEGEND = [
    ("#4A86C7", "MCU low-power window (STOP3 / RTC wake)"),
    ("#6AA84F", "Sensor sleep or rail off"),
    ("#CC0000", "LoRa transmit burst"),
    ("#9FC5E8", f"N-read filter (mean of last N samples, typically {FILTER_N_TYPICAL})"),
]


def charge(i_ma, t_s):
    return i_ma * t_s


def energy_mj(charge_mas, v):
    return charge_mas * v


def fmt_charge(x):
    if x >= 1:
        return f"{x:.2f} mAs"
    if x >= 0.01:
        return f"{x:.3f} mAs"
    return f"{x:.4f} mAs"


def fmt_energy_mj(x):
    if x >= 1:
        return f"{x:.1f} mJ"
    return f"{x:.2f} mJ"


def fmt_uw(x):
    return f"{x:.0f} µW"


def fmt_uA(x):
    return f"{x:.1f} µA"


def fmt_mw(x):
    return f"{x:.2f} mW"


def co2_strategy(charge_mas, interval):
    i_uA = charge_mas / interval * 1000
    p_mw = i_uA * V_CO2 / 1000
    e_mj = energy_mj(charge_mas, V_CO2)
    return i_uA, p_mw, e_mj


def panel_harvest(lux):
    p_in = PANEL_AREA_CM2 * PANEL_UW_CM2_REF * lux / REF_LUX
    return p_in, p_in * HARVEST_EFF


def sensor_period_charge(populated, sample_s, i_ma, t_s, period):
    if not populated:
        return 0.0, 0
    events = max(1, int(-(-period // sample_s)))  # ceil division
    per_event = i_ma * t_s
    return per_event * events, events


def build_model(period=BUDGET_PERIOD_S, sensors=None, lora_interval=LORA_INTERVAL_S, lora_enabled=1):
    sensors = sensors or SENSOR_CONFIG
    tx_c = charge(TX_I, TX_T)
    lora_events = max(1, int(-(-period // lora_interval))) if lora_enabled else 0
    lora_period_c = tx_c * lora_events if lora_enabled else 0
    mcu_act_c = charge(I_ACTIVE_MA, T_ACTIVE_S) * (1 if lora_enabled else 0)
    mcu_sleep_c = (I_SLEEP_UA / 1000) * period

    sensor_rows = []
    total_c = lora_period_c + mcu_act_c + mcu_sleep_c
    for name, ref, pop, sample_s, mode, i_ma, t_s, supply, note in sensors:
        period_c, events = sensor_period_charge(pop, sample_s, i_ma, t_s, period)
        per_event_c = i_ma * t_s
        sensor_rows.append({
            "name": name, "ref": ref, "populated": pop, "sample_s": sample_s, "mode": mode,
            "i_ma": i_ma, "t_s": t_s,
            "supply": supply, "note": note, "per_event_c": per_event_c,
            "events": events, "period_c": period_c, "period_e": energy_mj(period_c, supply),
            "avg_uA": period_c / period * 1000, "avg_uW": period_c / period * 1000 * supply,
        })
        total_c += period_c

    avg_uA = total_c / period * 1000
    need_net_uw = avg_uA * V_MCU * MARGIN
    need_in_uw = need_net_uw / HARVEST_EFF
    breakeven_lux = need_in_uw * REF_LUX / (PANEL_AREA_CM2 * PANEL_UW_CM2_REF)

    co2_ss_c = charge(2.0, 0.505)

    return {
        "period": period,
        "lora_interval": lora_interval,
        "filter_n": FILTER_N_DEFAULT,
        "sensor_rows": sensor_rows,
        "system_rows": [
            ("LoRa TX", lora_enabled, lora_period_c, energy_mj(lora_period_c, V_MCU),
             lora_period_c / period * 1000, lora_period_c / period * 1000 * V_MCU,
             f"{lora_events}× per {period} s" if lora_enabled else "Disabled"),
            ("MCU active", 1, mcu_act_c, energy_mj(mcu_act_c, V_MCU),
             mcu_act_c / period * 1000, mcu_act_c / period * 1000 * V_MCU, "Per report burst"),
            ("MCU sleep", 1, mcu_sleep_c, energy_mj(mcu_sleep_c, V_MCU),
             mcu_sleep_c / period * 1000, mcu_sleep_c / period * 1000 * V_MCU, "STOP3 over budget period"),
        ],
        "total_c": total_c,
        "total_e": energy_mj(total_c, V_MCU),
        "avg_uA": avg_uA,
        "avg_uW": avg_uA * V_MCU,
        "need_net_uw": need_net_uw,
        "need_in_uw": need_in_uw,
        "breakeven_lux": breakeven_lux,
        "tx_c": tx_c,
        "tx_e": energy_mj(tx_c, V_MCU),
        "co2_options": [
            ("Single-shot + sleep", co2_ss_c, *co2_strategy(co2_ss_c, period), "Recommended — ASC retained in sleep"),
            ("Hard power-off CO2_EN", 1.5, *co2_strategy(1.5, period), "Resets ASC; ~1 s boot + sample"),
        ],
    }


# --- XLSX (formulas) ---
HEADER_FILL = PatternFill("solid", fgColor="1F3864")
TITLE_FILL = PatternFill("solid", fgColor="E8EEF7")
THIN = Side(style="thin", color="D9D9D9")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def style_cell(cell, bold=False, fill=None, align="left", num_fmt=None):
    cell.font = Font(bold=bold, color="FFFFFF" if fill == HEADER_FILL else "000000")
    if fill:
        cell.fill = fill
    cell.alignment = Alignment(horizontal=align, vertical="top", wrap_text=True)
    cell.border = BORDER
    if num_fmt:
        cell.number_format = num_fmt


def ensure_mermaid_png(mmd_path, png_path, mmd_text):
    mmd_path.write_text(mmd_text, encoding="utf-8")
    if png_path.exists() and png_path.stat().st_mtime >= mmd_path.stat().st_mtime:
        return png_path
    try:
        subprocess.run(
            [
                "npx", "--yes", "@mermaid-js/mermaid-cli",
                "-i", str(mmd_path), "-o", str(png_path),
                "-b", "transparent", "-w", "1400",
            ],
            check=True,
            timeout=180,
            capture_output=True,
        )
    except (subprocess.SubprocessError, OSError):
        pass
    return png_path if png_path.exists() else None


def _embed_flow_image(ws, row, png_path, width=920):
    if not png_path:
        return row + 10
    img = XLImage(str(png_path))
    scale = width / img.width
    img.width = int(img.width * scale)
    img.height = int(img.height * scale)
    ws.add_image(img, f"A{row}")
    return row + int(img.height / 15) + 2


def write_flowchart_sheet(wb):
    if "Power Optimization" in wb.sheetnames:
        del wb["Power Optimization"]
    ws = wb.create_sheet("Power Optimization")

    for col, w in {"A": 6, "B": 34, "C": 18, "D": 48}.items():
        ws.column_dimensions[col].width = w

    r = 1
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=4)
    c = ws.cell(r, 1, "Solar Sensor Rev2 — Power Optimization")
    style_cell(c, bold=True, fill=HEADER_FILL, align="center")
    c.font = Font(bold=True, color="FFFFFF", size=12)
    r += 2

    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=4)
    note = ws.cell(
        r, 1,
        f"Parallel warm-up: start STCC4 first, read fast sensors during conversion, STOP3 while waiting. "
        f"Filter = mean of last N reads per channel (N typically {FILTER_N_TYPICAL}, default {FILTER_N_DEFAULT}). "
        f"No extra sensor energy for filtering.",
    )
    style_cell(note, fill=TITLE_FILL)
    r += 2

    title_row(ws, r, "Report cycle — parallel sensor warm-up", cols=4)
    r += 1
    flow_png = ensure_mermaid_png(FLOW_MMD_PATH, FLOW_PNG_PATH, FLOWCHART_MMD)
    r = _embed_flow_image(ws, r, flow_png)

    title_row(ws, r, f"N-read filter — mean of last N samples (typically {FILTER_N_TYPICAL})", cols=4)
    r += 1
    avg_png = ensure_mermaid_png(AVG_MMD_PATH, AVG_PNG_PATH, AVG_FLOWCHART_MMD)
    r = _embed_flow_image(ws, r, avg_png)

    title_row(ws, r, "Legend", cols=4)
    r += 1
    for color, label in FLOW_LEGEND:
        swatch = ws.cell(r, 1)
        swatch.fill = PatternFill("solid", fgColor=color[1:])
        style_cell(swatch)
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=4)
        style_cell(ws.cell(r, 2, label))
        r += 1
    r += 1

    title_row(ws, r, "Report cycle steps", cols=4)
    r += 1
    header_row(ws, r, ["Step", "Action", "Branch", "Notes"])
    r += 1
    for step in FLOW_STEPS:
        for col, val in enumerate(step, 1):
            style_cell(ws.cell(r, col, val))
        r += 1
    r += 1

    title_row(ws, r, "N-read filter steps", cols=4)
    r += 1
    header_row(ws, r, ["Step", "Action", "Branch", "Notes"])
    r += 1
    for step in AVG_FLOW_STEPS:
        for col, val in enumerate(step, 1):
            style_cell(ws.cell(r, col, val))
        r += 1


def title_row(ws, row, text, cols=8):
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=cols)
    c = ws.cell(row=row, column=1, value=text)
    style_cell(c, bold=True, fill=HEADER_FILL, align="center")
    c.font = Font(bold=True, color="FFFFFF", size=12)


def header_row(ws, row, headers):
    for col, h in enumerate(headers, 1):
        c = ws.cell(row=row, column=col, value=h)
        style_cell(c, bold=True, fill=HEADER_FILL, align="center")
        c.font = Font(bold=True, color="FFFFFF")


def write_xlsx():
    wb = openpyxl.load_workbook(XLSX_PATH)
    if "Energy Budget" in wb.sheetnames:
        del wb["Energy Budget"]
    ws = wb.create_sheet("Energy Budget")

    def _title(row, text, cols=15):
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=cols)
        c = ws.cell(row=row, column=1, value=text)
        style_cell(c, bold=True, fill=HEADER_FILL, align="center")
        c.font = Font(bold=True, color="FFFFFF", size=12)

    def _header(row, headers):
        for col, h in enumerate(headers, 1):
            c = ws.cell(row=row, column=col, value=h)
            style_cell(c, bold=True, fill=HEADER_FILL, align="center")
            c.font = Font(bold=True, color="FFFFFF")

    widths = {
        "A": 18, "B": 8, "C": 11, "D": 14, "E": 12, "F": 12, "G": 12, "H": 12,
        "I": 8, "J": 14, "K": 14, "L": 14, "M": 12, "N": 12, "O": 34,
    }
    for col, w in widths.items():
        ws.column_dimensions[col].width = w

    def B(row):
        return f"$B${row}"

    r = 1
    _title(r, "Solar Sensor Rev2 — Energy Budget")
    r = 3
    _title(r, "Global Assumptions", cols=4)
    r += 1
    _header(r, ["Parameter", "Value", "Unit", "Notes"])
    r += 1
    assumptions = [
        ("Budget period", BUDGET_PERIOD_S, "s", "Analysis window for averages and solar sizing"),
        ("LoRa report interval", LORA_INTERVAL_S, "s", "TX cadence; may differ from sensor sample rates"),
        ("Filter depth N", FILTER_N_DEFAULT, "reads", f"Mean of last N samples per channel (typical {FILTER_N_TYPICAL})"),
        ("Supply voltage MCU/radio", V_MCU, "V", "RA-08 module"),
        ("Sensor 1.8 V rail", V_18, "V", "SHT40, SGP30"),
        ("STCC4 supply", V_CO2, "V", "CO₂ sensor rail"),
        ("MCU sleep current", I_SLEEP_UA, "µA", "STOP3 between activity"),
        ("MCU active current", I_ACTIVE_MA, "mA", "During sensor read + TX prep"),
        ("MCU active time", T_ACTIVE_S, "s", "Per LoRa report burst"),
        ("Harvester efficiency", HARVEST_EFF, "", "BQ25505 end-to-end"),
        ("Design margin", MARGIN, "", "Aging, soiling, tolerance"),
        ("Panel area", PANEL_AREA_CM2, "cm²", "40 mm × 40 mm"),
        ("Panel power density @ ref", PANEL_UW_CM2_REF, "µW/cm²", "Amorton-class @ ref lux"),
        ("Reference illuminance", REF_LUX, "lux", "Indoor a-Si reference point"),
    ]
    assump_start = r
    for label, val, unit, note in assumptions:
        ws.cell(r, 1, label)
        ws.cell(r, 2, val)
        ws.cell(r, 3, unit)
        ws.cell(r, 4, note)
        for c in range(1, 5):
            style_cell(ws.cell(r, c))
        r += 1

    R_BUDGET = assump_start
    R_LORA_INT = assump_start + 1
    R_FILTER_N = assump_start + 2
    R_VMCU = assump_start + 3
    R_V18 = assump_start + 4
    R_VCO2 = assump_start + 5
    R_ISLEEP = assump_start + 6
    R_IACTIVE = assump_start + 7
    R_TACTIVE = assump_start + 8
    R_HARVEST = assump_start + 9
    R_MARGIN = assump_start + 10
    R_AREA = assump_start + 11
    R_PDENS = assump_start + 12
    R_REF_LUX = assump_start + 13

    r += 1
    _title(r, "Sensor Configuration — edit Populated, sample interval, and mode per channel")
    r += 1
    _header(r, [
        "Sensor", "Ref", "Populated", "Sample interval (s)", "Mode", "I active (mA)",
        "t active (s)", "Supply (V)", "Charge / event (mAs)",
        "Samples / period", "Charge / period (mAs)", "Energy / period (mJ)",
        "Avg I (µA)", "Avg power (µW)", "Notes",
    ])
    r += 1
    sensor_start = r
    for name, ref, pop, sample_s, mode, i_ma, t_s, supply, note in SENSOR_CONFIG:
        ws.cell(r, 1, name)
        ws.cell(r, 2, ref)
        ws.cell(r, 3, pop)
        ws.cell(r, 4, sample_s)
        ws.cell(r, 5, mode)
        ws.cell(r, 6, i_ma)
        ws.cell(r, 7, t_s)
        ws.cell(r, 8, supply)
        ws.cell(r, 9, f'=IF($C{r}=0,0,$F{r}*$G{r})')
        ws.cell(r, 10, f'=IF($C{r}=0,0,ROUNDUP({B(R_BUDGET)}/$D{r},0))')
        ws.cell(r, 11, f'=IF($C{r}=0,0,$I{r}*$J{r})')
        ws.cell(r, 12, f"=$K{r}*$H{r}")
        ws.cell(r, 13, f"=$K{r}/{B(R_BUDGET)}*1000")
        ws.cell(r, 14, f"=$M{r}*$H{r}")
        ws.cell(r, 15, note)
        for c in range(1, 16):
            style_cell(ws.cell(r, c), num_fmt="0.000" if c in (6, 7, 9, 11, 12, 13, 14) else "0" if c in (3, 4, 10) else None)
        r += 1
    sensor_end = r - 1

    r += 1
    _title(r, "LoRa Transmit (19-byte sensor report, opcode 0x21)", cols=4)
    r += 1
    _header(r, ["Parameter", "Value", "Unit", "Notes"])
    r += 1
    lora_start = r
    for param, val, unit, note in [
        ("Payload size", 19, "bytes", "sizeof(pkt) in lora_driver.c"),
        ("Time on air", TX_T, "s", "RadioTimeOnAir() SF7/125kHz"),
        ("TX current (est.)", TX_I, "mA", "ASR6601 @ 3.3 V"),
        ("LoRa enabled", 1, "0/1", "Set 0 to model receive-only / no uplink"),
    ]:
        ws.cell(r, 1, param)
        ws.cell(r, 2, val)
        ws.cell(r, 3, unit)
        ws.cell(r, 4, note)
        for c in range(1, 5):
            style_cell(ws.cell(r, c))
        r += 1
    tx_t_row = lora_start + 1
    tx_i_row = lora_start + 2
    lora_en_row = lora_start + 3
    ws.cell(r, 1, "TX charge / packet")
    ws.cell(r, 2, f"=B{tx_i_row}*B{tx_t_row}")
    ws.cell(r, 3, "mAs")
    for c in range(1, 4):
        style_cell(ws.cell(r, c), num_fmt="0.000" if c == 2 else None)
    tx_pkt_row = r
    r += 1
    ws.cell(r, 1, "TX packets / budget period")
    ws.cell(r, 2, f'=IF(B{lora_en_row}=0,0,ROUNDUP({B(R_BUDGET)}/{B(R_LORA_INT)},0))')
    ws.cell(r, 3, "count")
    for c in range(1, 4):
        style_cell(ws.cell(r, c), num_fmt="0" if c == 2 else None)
    tx_count_row = r
    r += 1
    ws.cell(r, 1, "LoRa charge / period")
    ws.cell(r, 2, f"=B{tx_pkt_row}*B{tx_count_row}")
    ws.cell(r, 3, "mAs")
    for c in range(1, 4):
        style_cell(ws.cell(r, c), bold=True, fill=TITLE_FILL, num_fmt="0.000" if c == 2 else None)
    lora_period_row = r
    r += 2

    _title(r, "System Elements", cols=6)
    r += 1
    _header(r, ["Element", "Enabled", "Charge / period (mAs)", "Energy / period (mJ)", "Avg I (µA)", "Avg power (µW)", "Notes"])
    r += 1
    sys_start = r
    ws.cell(r, 1, "LoRa TX")
    ws.cell(r, 2, f"=B{lora_en_row}")
    ws.cell(r, 3, f"=B{lora_period_row}")
    ws.cell(r, 4, f"=C{r}*{B(R_VMCU)}")
    ws.cell(r, 5, f"=C{r}/{B(R_BUDGET)}*1000")
    ws.cell(r, 6, f"=E{r}*{B(R_VMCU)}")
    ws.cell(r, 7, "Uplink radio @ 3.3 V")
    lora_sys_row = r
    for c in range(1, 8):
        style_cell(ws.cell(r, c), num_fmt="0.000" if c in (3, 4, 5, 6) else None)
    r += 1
    ws.cell(r, 1, "MCU active")
    ws.cell(r, 2, f"=B{lora_en_row}")
    ws.cell(r, 3, f"=IF(B{lora_en_row}=0,0,{B(R_IACTIVE)}*{B(R_TACTIVE)}*B{tx_count_row})")
    ws.cell(r, 4, f"=C{r}*{B(R_VMCU)}")
    ws.cell(r, 5, f"=C{r}/{B(R_BUDGET)}*1000")
    ws.cell(r, 6, f"=E{r}*{B(R_VMCU)}")
    ws.cell(r, 7, "Scales with LoRa report count")
    mcu_act_sys_row = r
    for c in range(1, 8):
        style_cell(ws.cell(r, c), num_fmt="0.000" if c in (3, 4, 5, 6) else None)
    r += 1
    ws.cell(r, 1, "MCU sleep")
    ws.cell(r, 2, 1)
    ws.cell(r, 3, f"={B(R_ISLEEP)}/1000*{B(R_BUDGET)}")
    ws.cell(r, 4, f"=C{r}*{B(R_VMCU)}")
    ws.cell(r, 5, f"=C{r}/{B(R_BUDGET)}*1000")
    ws.cell(r, 6, f"=E{r}*{B(R_VMCU)}")
    ws.cell(r, 7, "STOP3 over full budget period")
    mcu_sleep_sys_row = r
    for c in range(1, 8):
        style_cell(ws.cell(r, c), num_fmt="0.000" if c in (3, 4, 5, 6) else None)
    sys_end = r
    r += 2

    _title(r, "Budget Summary", cols=6)
    r += 1
    _header(r, ["Contributor", "Populated", "Charge / period (mAs)", "Energy / period (mJ)", "Avg I (µA)", "Avg power (µW)", "Notes"])
    r += 1
    summary_sensor_start = r
    for row in range(sensor_start, sensor_end + 1):
        ws.cell(r, 1, f"=A{row}")
        ws.cell(r, 2, f"=C{row}")
        ws.cell(r, 3, f"=K{row}")
        ws.cell(r, 4, f"=L{row}")
        ws.cell(r, 5, f"=M{row}")
        ws.cell(r, 6, f"=N{row}")
        ws.cell(r, 7, f"=O{row}")
        for c in range(1, 8):
            style_cell(ws.cell(r, c), num_fmt="0.000" if c in (3, 4, 5, 6) else None)
        r += 1
    summary_sensor_end = r - 1
    sys_rows = []
    for label, src_row in [
        ("LoRa TX", lora_sys_row),
        ("MCU active", mcu_act_sys_row),
        ("MCU sleep", mcu_sleep_sys_row),
    ]:
        ws.cell(r, 1, label)
        ws.cell(r, 2, f"=B{src_row}")
        ws.cell(r, 3, f"=C{src_row}")
        ws.cell(r, 4, f"=D{src_row}")
        ws.cell(r, 5, f"=E{src_row}")
        ws.cell(r, 6, f"=F{src_row}")
        ws.cell(r, 7, f"=G{src_row}")
        sys_rows.append(r)
        for c in range(1, 8):
            style_cell(ws.cell(r, c), num_fmt="0.000" if c in (3, 4, 5, 6) else None)
        r += 1
    sum_row = r
    ws.cell(r, 1, "TOTAL")
    ws.cell(r, 2, "")
    ws.cell(r, 3, f"=SUM(C{summary_sensor_start}:C{r-1})")
    ws.cell(r, 4, f"=SUM(D{summary_sensor_start}:D{r-1})")
    ws.cell(r, 5, f"=SUM(E{summary_sensor_start}:E{r-1})")
    ws.cell(r, 6, f"=SUM(F{summary_sensor_start}:F{r-1})")
    ws.cell(r, 7, "Sum of populated sensors + system elements")
    for c in range(1, 8):
        style_cell(ws.cell(r, c), bold=True, fill=TITLE_FILL, num_fmt="0.000" if c in (3, 4, 5, 6) else None)
    total_row = r
    r += 2

    _title(r, "STCC4 CO₂ Options", cols=4)
    r += 1
    _header(r, ["Option", "Typical I", "Charge / sample", "Notes"])
    r += 1
    for mode, i, ch, use in [
        ("single-shot + sleep", "2.0 mA × 0.505 s", "1.01 mAs", "Recommended — set STCC4 Mode=single-shot"),
        ("pulsed", "I × t per sample", "scales with sample interval", "SHT40, SGP30, BH1620"),
        ("hard power-off", "~1 s boot + sample", "1.5 mAs", "Resets ASC; use CO2_EN switch"),
    ]:
        ws.cell(r, 1, mode)
        ws.cell(r, 2, i)
        ws.cell(r, 3, ch)
        ws.cell(r, 4, use)
        for c in range(1, 5):
            style_cell(ws.cell(r, c))
        r += 1
    r += 1

    _title(r, "Indoor Solar — 40×40 mm Panel", cols=4)
    r += 1
    _header(r, ["Parameter", "Value", "Unit", "Notes"])
    r += 1
    ws.cell(r, 1, "Required net power (+ margin)")
    ws.cell(r, 2, f"=F{total_row}*{B(R_MARGIN)}")
    ws.cell(r, 3, "µW")
    need_net_row = r
    for c in range(1, 4):
        style_cell(ws.cell(r, c), num_fmt="0.0" if c == 2 else None)
    r += 1
    ws.cell(r, 1, "Required panel input")
    ws.cell(r, 2, f"=B{need_net_row}/{B(R_HARVEST)}")
    ws.cell(r, 3, "µW")
    need_in_row = r
    for c in range(1, 4):
        style_cell(ws.cell(r, c), num_fmt="0.0" if c == 2 else None)
    r += 1
    ws.cell(r, 1, "Break-even illuminance")
    ws.cell(r, 2, f"=B{need_in_row}*{B(R_REF_LUX)}/({B(R_AREA)}*{B(R_PDENS)})")
    ws.cell(r, 3, "lux")
    breakeven_row = r
    for c in range(1, 4):
        style_cell(ws.cell(r, c), bold=True, fill=TITLE_FILL, num_fmt="0" if c == 2 else None)
    r += 1
    ws.cell(r, 1, "Comfortable illuminance (~2×)")
    ws.cell(r, 2, f"=B{breakeven_row}*2")
    ws.cell(r, 3, "lux")
    for c in range(1, 4):
        style_cell(ws.cell(r, c), num_fmt="0" if c == 2 else None)
    r += 2

    _title(r, "Panel Output vs Illuminance", cols=4)
    r += 1
    _header(r, ["Illuminance (lux)", "Panel output (µW)", "Harvested (µW)", "Budget status"])
    r += 1
    for lux in [100, 150, 200, 250, 300, 400, 500]:
        ws.cell(r, 1, lux)
        ws.cell(r, 2, f"={B(R_AREA)}*{B(R_PDENS)}*A{r}/{B(R_REF_LUX)}")
        ws.cell(r, 3, f"=B{r}*{B(R_HARVEST)}")
        ws.cell(r, 4, f'=IF(C{r}>=B{need_net_row},"OK","DEFICIT")')
        for c in range(1, 5):
            style_cell(ws.cell(r, c), num_fmt="0" if c == 1 else "0.0" if c in (2, 3) else None)
        r += 1

    write_flowchart_sheet(wb)
    wb.save(XLSX_PATH)



CSS = """
    * { box-sizing: border-box; }
    body { margin: 0; font-family: Arial, sans-serif; background: #f5f5f5; color: #222; }
    .wrap { padding: 16px; max-width: 1400px; margin: 0 auto; }
    nav { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }
    nav a { padding: 8px 14px; background: #fff; border: 1px solid #d9d9d9; border-radius: 4px;
      color: #1f3864; text-decoration: none; font-size: 14px; font-weight: bold; }
    nav a.active { background: #1f3864; color: #fff; border-color: #1f3864; }
    nav a:hover:not(.active) { background: #eef2f8; }
    .note { background: #fff; border-left: 4px solid #1f3864; padding: 12px 14px; margin-bottom: 16px;
      font-size: 14px; line-height: 1.5; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
    .legacy { background: #fff8e6; border-left: 4px solid #e69138; padding: 10px 14px; margin-bottom: 16px;
      font-size: 13px; line-height: 1.5; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
    table { width: 100%; border-collapse: collapse; background: #fff;
      box-shadow: 0 1px 4px rgba(0,0,0,0.12); margin-bottom: 16px; }
    th, td { border: 1px solid #d9d9d9; padding: 8px 10px; text-align: left; vertical-align: top; font-size: 14px; }
    thead { position: sticky; top: 0; z-index: 10; }
    tr.title th { background: #1f3864; color: #fff; font-size: 18px; font-weight: bold; text-align: center; padding: 14px 10px; }
    tr.header th { background: #1f3864; color: #fff; font-weight: bold; text-align: center; }
    tr.odd td { background: #fff; }
    tr.even td { background: #f2f2f2; }
    tr.summary td { background: #e8eef7; font-weight: bold; }
    td.num { text-align: right; white-space: nowrap; }
    h2 { font-size: 16px; color: #1f3864; margin: 24px 0 12px; }
    .footnote { font-size: 12px; color: #555; line-height: 1.6; }
"""


def table_html(title, headers, rows, summary_rows=None, colspan=None):
    cols = colspan or len(headers)
    out = [f'<table><thead><tr class="title"><th colspan="{cols}">{html_mod.escape(title)}</th></tr>']
    out.append("<tr class=\"header\">" + "".join(f"<th>{html_mod.escape(h)}</th>" for h in headers) + "</tr></thead><tbody>")
    for i, row in enumerate(rows):
        cls = "odd" if i % 2 == 0 else "even"
        cells = "".join(f'<td class="{("num" if j else "")}">{c}</td>' for j, c in enumerate(row))
        out.append(f'<tr class="{cls}">{cells}</tr>')
    if summary_rows:
        for row in summary_rows:
            cells = "".join(f'<td class="{("num" if j else "")}">{c}</td>' for j, c in enumerate(row))
            out.append(f'<tr class="summary">{cells}</tr>')
    out.append("</tbody></table>")
    return "\n".join(out)


def write_html():
    m = build_model(BUDGET_PERIOD_S)
    m10 = build_model(10, sensors=[
        (n, r, p, 10 if p else s, md, i, t, v, nt)
        for n, r, p, s, md, i, t, v, nt in SENSOR_CONFIG
    ])

    assumptions = [
        ("Budget period", f"{BUDGET_PERIOD_S} s", "Analysis window for averages"),
        ("LoRa report interval", f"{LORA_INTERVAL_S} s", "TX cadence (independent of sensor rates)"),
        ("Filter depth N", f"{FILTER_N_DEFAULT} reads (typical {FILTER_N_TYPICAL})", "Mean of last N samples — no extra sensor reads"),
        ("Supply voltage MCU/radio", f"{V_MCU} V", "RA-08 module"),
        ("Sensor 1.8 V rail", f"{V_18} V", "SHT40, SGP30"),
        ("STCC4 supply", f"{V_CO2} V", "CO₂ sensor rail"),
        ("MCU sleep current", f"{I_SLEEP_UA} µA", "STOP3 between activity"),
        ("MCU active", f"{I_ACTIVE_MA} mA × {T_ACTIVE_S} s", "Per LoRa report burst"),
        ("Harvester efficiency", str(HARVEST_EFF), "BQ25505 end-to-end"),
        ("Design margin", str(MARGIN), "Aging / soiling"),
        ("Panel", f"{PANEL_AREA_CM2} cm² (40×40 mm)", f"{PANEL_UW_CM2_REF} µW/cm² @ {REF_LUX} lux"),
    ]

    sensor_cfg_rows = []
    for s in m["sensor_rows"]:
        sensor_cfg_rows.append([
            s["name"],
            "Yes" if s["populated"] else "No",
            f"{s['sample_s']} s",
            s["mode"],
            f"{s['i_ma']} mA" if s["i_ma"] < 10 else f"{s['i_ma']:.2f} mA",
            fmt_charge(s["per_event_c"]),
            str(s["events"]),
            fmt_charge(s["period_c"]),
            fmt_energy_mj(s["period_e"]),
            fmt_uA(s["avg_uA"]),
            fmt_uw(s["avg_uW"]),
            s["note"],
        ])

    summary_rows = []
    for s in m["sensor_rows"]:
        if s["populated"]:
            summary_rows.append([
                s["name"], fmt_charge(s["period_c"]), fmt_energy_mj(s["period_e"]),
                fmt_uA(s["avg_uA"]), fmt_uw(s["avg_uW"]), s["note"],
            ])
    for name, pop, c, e, i_uA, p_uW, note in m["system_rows"]:
        summary_rows.append([name, fmt_charge(c), fmt_energy_mj(e), fmt_uA(i_uA), fmt_uw(p_uW), note])
    summary_total = [
        ["TOTAL", fmt_charge(m["total_c"]), fmt_energy_mj(m["total_e"]),
         fmt_uA(m["avg_uA"]), fmt_uw(m["avg_uW"]), "Edit spreadsheet for live what-if"],
    ]

    co2_rows = []
    for name, ch, i_uA, p_mw, e_mj, note in m["co2_options"]:
        co2_rows.append([name, fmt_charge(ch), fmt_uA(i_uA), fmt_mw(p_mw), fmt_energy_mj(e_mj), note])

    co2_10_rows = []
    for name, ch, i_uA, p_mw, e_mj, note in m10["co2_options"]:
        co2_10_rows.append([name, fmt_charge(ch), fmt_uA(i_uA), fmt_mw(p_mw), fmt_energy_mj(e_mj), note])

    lux_rows = []
    for lux in [100, 150, 200, 250, 300, 400, 500]:
        pin, ph = panel_harvest(lux)
        status = "OK" if ph >= m["need_net_uw"] else "DEFICIT"
        lux_rows.append([f"{lux} lux", fmt_uw(pin), fmt_uw(ph), status])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Solar Sensor Schematic Rev2 - Energy Budget</title>
  <style>{CSS}</style>
</head>
<body>
  <div class="wrap">
    {docs_nav("SolarSensorSchematicRev2_EnergyBudget.html")}
    <div class="legacy"><strong>Rev2 RA-08 energy model.</strong> Hybrid architecture (100 F · TPS61291 · RAK3172):
    <a href="SolarSensorSchematicRev2_BlockDiagram.html">block diagram</a>.</div>
    <div class="note">
      Per-sensor sample rates and populate flags are editable in the
      <a href="SolarSensorSchematicRev2_BOM.xlsx">Energy Budget sheet</a>.
      Set <strong>Populated=0</strong> to exclude unfit sensors (e.g. SGP30).
      Default budget period: <strong>{BUDGET_PERIOD_S} s</strong>.
    </div>

    {table_html("Assumptions", ["Parameter", "Value", "Notes"], assumptions)}

    {table_html("Sensor Configuration (per channel)", [
        "Sensor", "Populated", "Sample interval", "Mode", "I active",
        "Charge / event", "Samples / period", "Charge / period", "Energy / period",
        "Avg I", "Avg power", "Notes",
    ], sensor_cfg_rows)}

    {table_html("LoRa Transmit — 19-byte packet", ["Parameter", "Value", "Notes"], [
        ["Payload", "19 bytes", "sizeof(pkt) in lora_driver.c"],
        ["Time on air", "52 ms", "SF7 · 125 kHz"],
        ["TX charge / packet", f"{fmt_charge(m['tx_c'])} · {fmt_energy_mj(m['tx_e'])}", "60 mA × 52 ms"],
    ])}

    <h2>Budget Summary @ {BUDGET_PERIOD_S} s</h2>
    {table_html("All contributors", [
        "Contributor", "Charge / period", "Energy / period", "Avg I", "Avg power", "Notes",
    ], summary_rows, summary_total)}

    {table_html(f"STCC4 CO₂ Options @ {BUDGET_PERIOD_S} s", [
        "Option", "CO₂ charge", "Avg CO₂ I", "Avg power", "Energy", "Notes",
    ], co2_rows)}

    {table_html("STCC4 CO₂ @ 10 s sample (reference)", [
        "Option", "CO₂ charge", "Avg CO₂ I", "Avg power", "Energy", "Notes",
    ], co2_10_rows)}

    <h2>Indoor Solar — 40×40 mm Panel</h2>
    {table_html("Solar Sizing Summary", ["Parameter", "Value", "Notes"], [
        ["Required net power (+ margin)", fmt_uw(m["need_net_uw"]), "From budget summary total"],
        ["Required panel input", fmt_uw(m["need_in_uw"]), "Before BQ25505 losses"],
        ["Break-even illuminance", f"{m['breakeven_lux']:.0f} lux", "Amorton-class panel"],
        ["Comfortable illuminance", f"{m['breakeven_lux'] * 2:.0f} lux", "~2× break-even"],
    ])}

    {table_html("Panel Output vs Illuminance", ["Illuminance", "Panel output", "Harvested (75%)", f"vs budget ({fmt_uw(m['need_net_uw'])})"], lux_rows)}

    <p class="footnote">
      Filtering uses the arithmetic mean of the last N raw readings per channel (N typically {FILTER_N_TYPICAL}, default {FILTER_N_DEFAULT}).
      N is a firmware constant — no extra sensor reads or energy. See Power Optimization sheet for flowcharts.
      Regenerate with <code>python Docs/build_energy_budget_sheet.py</code>.
    </p>
  </div>
</body>
</html>"""

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)


if __name__ == "__main__":
    write_xlsx()
    write_html()
    update_workbook()
    write_todo_html()
    print(f"Updated {XLSX_PATH}")
    print(f"Wrote {HTML_PATH}")
