"""Firmware TODO — single source for spreadsheet sheet, HTML page, and markdown cross-references."""

from __future__ import annotations

import html as html_mod
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

DOCS = Path(__file__).resolve().parent
XLSX_PATH = DOCS / "SolarSensorSchematicRev2_BOM.xlsx"
HTML_PATH = DOCS / "SolarSensorSchematicRev2_TODO.html"

# (id, priority, category, task, problem_today, required_action, files, status)
FIRMWARE_TODO: list[tuple[str, ...]] = [
    (
        "FW-001",
        "P0",
        "Pinout",
        "Assign ADC_MONITOR and status inputs on RAK3172",
        "Hybrid block diagram defines ADC_MONITOR, VBAT_OK, BAT_GD, PRIM_STATUS; not wired in legacy RA-08 firmware.",
        "Map each net to RAK3172 GPIO/ADC in lora_config.h. Confirm divider ratio for 100 F · 3.8 V supercap.",
        "lora_config.h · hybrid PCB",
        "Open",
    ),
    (
        "FW-002",
        "P0",
        "Pinout",
        "Assign GPIO_RADAR and GPIO_CO2 P-FET gates",
        "Radar and CO₂ use Si2301 P-FET gates; legacy firmware uses different RA-08 enables.",
        "Map GPIO_RADAR and GPIO_CO2 to RAK3172 outputs. Active level per hybrid schematic.",
        "lora_config.h · hybrid PCB",
        "Open",
    ),
    (
        "FW-003",
        "P0",
        "Power",
        "Implement the power manager state machine",
        "No bring-up logic: boot goes straight to sensors and LoRa.",
        "Add states: COLD_START → CHARGE_ONLY → READY → REPORT → TX_BLOCKED. One module, explicit transitions.",
        "power_manager.c · power_manager.h",
        "Open",
    ),
    (
        "FW-004",
        "P0",
        "Power",
        "Drive hybrid charge / path policy during boot",
        "Harvester uses internal OR logic; firmware must not load gated sensors on flat 100 F supercap.",
        "Implement charge-only boot: SHT41 only until ADC_MONITOR threshold; defer radar/CO₂ and LoRa TX.",
        "power_manager.c · lora_driver.c",
        "Open",
    ),
    (
        "FW-005",
        "P0",
        "Power",
        "Define supercap voltage thresholds on the bench",
        "No VCAP_MIN_* or charge target in code.",
        "Measure droop during LoRa TX and sensor bursts. Starting points from BQ25505_DESIGN_INPUTS.md: "
        "VCAP_MIN_SENSORS_mV=2700, VCAP_MIN_TX_mV=3000, VCAP_CHARGE_TARGET_mV=3600. Tune on bench.",
        "lora_config.h · adc_monitor.c",
        "Open",
    ),
    (
        "FW-006",
        "P0",
        "Power",
        "Block LoRa TX when supercap is too low",
        "Radio transmits even when vcap cannot support 52 ms @ ~60 mA.",
        "Skip or defer TX when vcap < VCAP_MIN_TX_mV. Retry on next wake when voltage recovers.",
        "lora_driver.c",
        "Open",
    ),
    (
        "FW-007",
        "P0",
        "Power",
        "Block sensor rails until POWER_READY",
        "PA5/6/7/12 enabled at boot; STCC4 and SGP30 load a flat supercap.",
        "Do not enable CO2_EN, HUM_EN, TVOC_EN, or BH1620_EN until vcap >= VCAP_MIN_SENSORS_mV.",
        "lora_driver.c · sensor drivers",
        "Open",
    ),
    (
        "FW-008",
        "P0",
        "Power",
        "Remove unconditional startup sensor report",
        "node_send_sensor_report(\"startup\") runs before charge bring-up completes.",
        "Guard first report behind charge target + boot path (FW-003). No LoRa TX during CHARGE_ONLY.",
        "lora_driver.c",
        "Open",
    ),
    (
        "FW-009",
        "P1",
        "Power",
        "Re-enable STOP3 between report cycles",
        "NODE_STOP3_ENABLE is 0 (debug). Sleep budget is wrong.",
        "Set NODE_STOP3_ENABLE to 1 after RTC wake path is verified.",
        "lora_driver.c",
        "Open",
    ),
    (
        "FW-010",
        "P0",
        "STCC4",
        "Replace continuous mode with single-shot + sleep",
        "stcc4.c uses START_CONTINUOUS and a 5200 ms first-sample wait.",
        "Use Sensirion commands: exit_sleep (0x3650), measure_single_shot (0x219D), read_measurement (0xEC05), enter_sleep_mode. Target ~510 ms per sample.",
        "stcc4.c · stcc4.h",
        "Open",
    ),
    (
        "FW-011",
        "P0",
        "Sensors",
        "Read fast sensors in parallel with CO₂ conversion",
        "Report path is sequential: SHT → vcap → STCC4 → SGP30 → BH1620.",
        "Start STCC4 single-shot first (~510 ms). During conversion, read SHT40 (~20 ms), SGP30 (~40 ms), BH1620 (~10 ms).",
        "lora_driver.c",
        "Open",
    ),
    (
        "FW-012",
        "P1",
        "Sensors",
        "Use STOP3 while waiting for CO₂ (~440 ms)",
        "Firmware likely busy-waits or blocks the MCU during conversion.",
        "Enter STOP3 after starting STCC4; wake on RTC/timer when conversion completes. Do not spin.",
        "lora_driver.c",
        "Open",
    ),
    (
        "FW-013",
        "P0",
        "Filter",
        "Implement N-sample ring buffer per channel",
        "No filtering; each report sends the latest raw reading.",
        "Ring buffer depth N (default 5). filtered = mean(buf[0..N-1]). No extra sensor reads for filtering.",
        "sensor_filter.c · lora_driver.c",
        "Open",
    ),
    (
        "FW-014",
        "P0",
        "Payload",
        "Send filtered values in the 19-byte LoRa packet",
        "Payload uses instantaneous readings.",
        "Bytes 0–13: filtered T, RH, TVOC, lux, vcap (raw mV OK), CO₂. See Sensors.html payload map.",
        "lora_driver.c",
        "Open",
    ),
    (
        "FW-015",
        "P1",
        "Flowchart",
        "Add cold-boot branch to power_optimization_flow.mmd",
        "Flowchart starts at RTC alarm; first power-on path is missing.",
        "Add: cold boot → vcap check → BQ_EN charge loop → STCC4 1000 ms boot → join steady-state report cycle.",
        "Docs/power_optimization_flow.mmd",
        "Open",
    ),
    (
        "FW-016",
        "P1",
        "Flowchart",
        "Regenerate flowchart PNGs and HTML after edits",
        "Diagrams may not match required firmware behavior.",
        "Run: python Docs/build_energy_budget_sheet.py. Optionally: mmdc on .mmd files in Docs/.",
        "Docs/build_energy_budget_sheet.py",
        "Open",
    ),
    (
        "FW-017",
        "P0",
        "Test",
        "Verify out-of-box boot from discharged 0.22 F supercap",
        "Product requirement: no customer pre-charge or install tricks.",
        "Ship-test condition: supercap at 0 V, indoor light. Unit must charge, join, and report without user steps.",
        "Bench test procedure",
        "Open",
    ),
    (
        "FW-018",
        "P0",
        "Test",
        "Verify BQ_EN raises vcap before first TX",
        "Charge path not validated.",
        "Log or scope vcap vs BQ_EN. First TX only after threshold met.",
        "Bench test procedure",
        "Open",
    ),
    (
        "FW-019",
        "P1",
        "Test",
        "Measure STOP3 sleep current vs energy budget",
        "STOP3 disabled; budget assumes ~1.3 µA sleep.",
        "Measure MCU sleep with all sensor rails off. Compare to Energy Budget sheet.",
        "Bench test procedure",
        "Open",
    ),
    (
        "FW-020",
        "P1",
        "Release",
        "Confirm CONFIG_NODE_TX_SENSOR_BYPASS is 0 in release builds",
        "Bypass flag exists for radio-only debug.",
        "Release build must use CONFIG_NODE_TX_SENSOR_BYPASS 0.",
        "lora_config.h",
        "Open",
    ),
]

TODO_HEADERS = [
    "Task",
    "Priority",
    "Category",
    "What to do",
    "Problem today",
    "Required action",
    "Files",
    "Status",
]

HEADER_FILL = PatternFill("solid", fgColor="1F3864")
TITLE_FILL = PatternFill("solid", fgColor="E8EEF7")
OPEN_FILL = PatternFill("solid", fgColor="FCE4D6")
THIN = Side(style="thin", color="D9D9D9")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def docs_nav(active: str = "") -> str:
    pages = [
        ("SolarSensorSchematicRev2_BOM.html", "Bill of Materials"),
        ("SolarSensorSchematicRev2_BlockDiagram.html", "Block Diagram"),
        ("SolarSensorSchematicRev2_Sensors.html", "Sensors"),
        ("SolarSensorSchematicRev2_EnergyBudget.html", "Energy Budget"),
        ("SolarSensorSchematicRev2_SolarCells.html", "Indoor Solar Cells"),
        ("SolarSensorSchematicRev2_TODO.html", "Firmware TODO"),
        ("SolarSensorSchematicRev2.pdf", "Schematic PDF"),
        ("SolarSensorSchematicRev2_BOM.xlsx", "Spreadsheet (.xlsx)"),
    ]
    lines = ["    <nav>"]
    for href, label in pages:
        cls = ' class="active"' if href == active else ""
        lines.append(f'      <a href="{href}"{cls}>{label}</a>')
    lines.append("    </nav>")
    return "\n".join(lines)


def _style_cell(cell, *, bold=False, fill=None, align="left", color="000000"):
    cell.font = Font(bold=bold, color="FFFFFF" if fill == HEADER_FILL else color)
    if fill:
        cell.fill = fill
    cell.alignment = Alignment(horizontal=align, vertical="top", wrap_text=True)
    cell.border = BORDER


def write_todo_sheet(wb) -> None:
    if "Firmware TODO" in wb.sheetnames:
        del wb["Firmware TODO"]
    ws = wb.create_sheet("Firmware TODO")

    widths = {"A": 10, "B": 9, "C": 12, "D": 28, "E": 32, "F": 36, "G": 28, "H": 10}
    for col, w in widths.items():
        ws.column_dimensions[col].width = w

    r = 1
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=len(TODO_HEADERS))
    c = ws.cell(r, 1, "Solar Sensor Rev2 — Firmware TODO (mandatory before ship)")
    _style_cell(c, bold=True, fill=HEADER_FILL, align="center")
    c.font = Font(bold=True, color="FFFFFF", size=12)
    r += 1

    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=len(TODO_HEADERS))
    intro = ws.cell(
        r,
        1,
        "Hardware supports hybrid bring-up (BQ25505 OR paths, 100 F LIC supercap, P-FET sensor gates). "
        "Block diagram: pics/BlockDiagram.jpg · FIRMWARE_NEXT_STEPS.md · POWER_SYSTEM_ANALYSIS.md",
    )
    _style_cell(intro, fill=TITLE_FILL)
    r += 2

    for col, header in enumerate(TODO_HEADERS, start=1):
        hc = ws.cell(r, col, header)
        _style_cell(hc, bold=True, fill=HEADER_FILL, align="center")
    r += 1

    for row in FIRMWARE_TODO:
        for col, value in enumerate(row, start=1):
            cell = ws.cell(r, col, value)
            fill = OPEN_FILL if col == 8 and value == "Open" else None
            align = "center" if col in (1, 2, 8) else "left"
            _style_cell(cell, fill=fill, align=align)
        r += 1

    ws.freeze_panes = "A5"


TODO_CSS = """
    * { box-sizing: border-box; }
    body { margin: 0; font-family: Arial, sans-serif; background: #f5f5f5; color: #222; }
    .wrap { padding: 16px; max-width: 1600px; margin: 0 auto; }
    nav { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }
    nav a { padding: 8px 14px; background: #fff; border: 1px solid #d9d9d9; border-radius: 4px;
      color: #1f3864; text-decoration: none; font-size: 14px; font-weight: bold; }
    nav a.active { background: #1f3864; color: #fff; border-color: #1f3864; }
    nav a:hover:not(.active) { background: #eef2f8; }
    .note { background: #fff; border-left: 4px solid #cc0000; padding: 12px 14px; margin-bottom: 16px;
      font-size: 14px; line-height: 1.55; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
    .note strong { color: #1f3864; }
    table { width: 100%; border-collapse: collapse; background: #fff;
      box-shadow: 0 1px 4px rgba(0,0,0,0.12); margin-bottom: 16px; }
    th, td { border: 1px solid #d9d9d9; padding: 8px 10px; text-align: left; vertical-align: top; font-size: 13px; }
    thead { position: sticky; top: 0; z-index: 10; }
    tr.title th { background: #1f3864; color: #fff; font-size: 18px; font-weight: bold; text-align: center; padding: 14px 10px; }
    tr.header th { background: #1f3864; color: #fff; font-weight: bold; text-align: center; font-size: 12px; }
    tr.odd td { background: #fff; }
    tr.even td { background: #f2f2f2; }
    td.task-id, td.priority, td.status { text-align: center; white-space: nowrap; font-weight: bold; }
    td.priority { color: #cc0000; }
    td.status { color: #c55a11; }
    h2 { font-size: 16px; color: #1f3864; margin: 24px 0 8px; }
    .footnote { font-size: 12px; color: #555; line-height: 1.6; }
    code { background: #eef2f8; padding: 1px 4px; border-radius: 3px; font-size: 12px; }
"""


def write_todo_html() -> None:
    body_rows = []
    for i, row in enumerate(FIRMWARE_TODO):
        cls = "odd" if i % 2 == 0 else "even"
        task_id, pri, cat, task, problem, action, files, status = row
        body_rows.append(
            f'        <tr class="{cls}">'
            f'<td class="task-id">{html_mod.escape(task_id)}</td>'
            f"<td class=\"priority\">{html_mod.escape(pri)}</td>"
            f"<td>{html_mod.escape(cat)}</td>"
            f"<td><strong>{html_mod.escape(task)}</strong></td>"
            f"<td>{html_mod.escape(problem)}</td>"
            f"<td>{html_mod.escape(action)}</td>"
            f"<td>{html_mod.escape(files)}</td>"
            f'<td class="status">{html_mod.escape(status)}</td>'
            f"</tr>"
        )

    headers_html = "".join(f"<th>{html_mod.escape(h)}</th>" for h in TODO_HEADERS)
    open_count = sum(1 for r in FIRMWARE_TODO if r[-1] == "Open")

    content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Solar Sensor Schematic Rev2 - Firmware TODO</title>
  <style>{TODO_CSS}</style>
</head>
<body>
  <div class="wrap">
    {docs_nav("SolarSensorSchematicRev2_TODO.html")}
    <div class="note">
      <strong>{open_count} open tasks.</strong>
      The hybrid block diagram (100 F supercap, TPS61291, RAK3172, P-FET sensor gates) defines the target architecture.
      Legacy RA-08 Rev2 firmware does not implement it. Close every P0 task before ship.
      Markdown detail: <a href="FIRMWARE_NEXT_STEPS.md">FIRMWARE_NEXT_STEPS.md</a> ·
      <a href="POWER_SYSTEM_ANALYSIS.md">POWER_SYSTEM_ANALYSIS.md</a> ·
      spreadsheet tab <strong>Firmware TODO</strong>.
    </div>

    <table>
      <thead>
        <tr class="title"><th colspan="{len(TODO_HEADERS)}">Firmware TODO — mandatory before ship</th></tr>
        <tr class="header">{headers_html}</tr>
      </thead>
      <tbody>
{chr(10).join(body_rows)}
      </tbody>
    </table>

    <h2>Sensor report sequence (target — tasks FW-010 through FW-014)</h2>
    <p class="footnote">
      1. RTC wake from STOP3 → 2. Radio sleep → 3. STCC4 single-shot start (~510 ms) →
      4. SHT40 + SGP30 + BH1620 in parallel → 5. STOP3 until CO₂ ready →
      6. STCC4 read + sleep → 7. Push to N-sample buffers → 8. Compute mean →
      9. Pack filtered 19-byte payload → 10. LoRa TX if vcap OK → 11. Rails off → STOP3.
      Flowcharts: <a href="power_optimization_flow.mmd">power_optimization_flow.mmd</a>,
      <a href="averaging_n_samples_flow.mmd">averaging_n_samples_flow.mmd</a>,
      <a href="SolarSensorSchematicRev2_Sensors.html">Sensors.html</a>.
    </p>

    <p class="footnote">
      Regenerate this page and the spreadsheet tab:
      <code>python Docs/firmware_todo.py</code> or
      <code>python Docs/build_energy_budget_sheet.py</code>.
    </p>
  </div>
</body>
</html>"""
    HTML_PATH.write_text(content, encoding="utf-8")

def update_workbook() -> None:
    wb = load_workbook(XLSX_PATH)
    write_todo_sheet(wb)
    wb.save(XLSX_PATH)


def main() -> None:
    update_workbook()
    write_todo_html()
    open_count = sum(1 for r in FIRMWARE_TODO if r[-1] == "Open")
    print(f"Wrote Firmware TODO sheet in {XLSX_PATH.name} ({len(FIRMWARE_TODO)} tasks, {open_count} open)")
    print(f"Wrote {HTML_PATH.name}")


if __name__ == "__main__":
    main()
