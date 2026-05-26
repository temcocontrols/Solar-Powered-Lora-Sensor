#!/usr/bin/env python3
<<<<<<< Updated upstream
"""Apply hybrid architecture + schematic BOM values to local BQ25505 TI spreadsheets."""
=======
"""Apply Rev2 schematic + energy-budget values to local BQ25505 TI spreadsheets."""
>>>>>>> Stashed changes

from __future__ import annotations

import shutil
from pathlib import Path

import openpyxl

from build_energy_budget_sheet import (
    BUDGET_PERIOD_S,
    HARVEST_EFF,
<<<<<<< Updated upstream
=======
    PANEL_AREA_CM2,
>>>>>>> Stashed changes
    PANEL_UW_CM2_REF,
    REF_LUX,
    V_MCU,
    build_model,
)

DOCS = Path(__file__).resolve().parent
TOOLS = DOCS / "tools"
SLUC484_SRC = TOOLS / "SLUC484" / "bq25505(70_Design_Help_V1_3.xlsx"
SLUC484_DST = TOOLS / "SLUC484" / "SolarSensor_BQ25505_Calculator.xlsx"
SLUC463_SRC = TOOLS / "SLUC463" / "bq25505SolarAppDesignExample_V1p3.xlsx"
SLUC463_DST = TOOLS / "SLUC463" / "SolarSensor_solar_load_study.xlsx"

VBIAS = 1.21

<<<<<<< Updated upstream
# Rev2 schematic ROV (4.2 V-class OVP — do not use with 3.8 V LIC)
REV2_ROV = {"rov1_m": 5.62, "rov2_m": 7.32}

# Hybrid 3.8 V OVP — 1% pair from SLUC484 lookup (0.28% error vs 3.8 V target)
HYBRID_ROV = {"rov1_m": 4.02, "rov2_m": 4.42}

# Hybrid Power & Control — authoritative target (BlockDiagram.jpg)
DESIGN = {
    **HYBRID_ROV,
=======
# Rev2 schematic BOM — BQ25505 divider network (U2)
SCHEMATIC = {
    "rov1_m": 5.62,
    "rov2_m": 7.32,
>>>>>>> Stashed changes
    "rok1_m": 5.62,
    "rok2_m": 5.49,
    "rok3_m": 1.87,
    "l2_uh": 22,
<<<<<<< Updated upstream
    # Storage — 100 F · 3.8 V LIC supercap
    "storage_cap_f": 100.0,
    "storage_cap_v_max": 3.8,
    "storage_ov_v": 3.8,
    # Solar — 60×60 mm panel
    "panel_area_cm2": 36.0,
    "panel_mm": "60×60",
    # Boost — TPS61291 hybrid rail (Rev2 PCB used TPS613221A @ ~85%)
    "boost_eff": 0.90,
    "boost_part": "TPS61291",
    # ADC sense — Rev2 BOM R10/R11
    "adc_r_top_k": 10.0,
    "adc_r_bot_k": 10.0,
}

# Rev2 PCB legacy (reference only in docs)
REV2_LEGACY = {
    **REV2_ROV,
    "storage_cap_f": 0.22,
    "storage_cap_v_max": 5.5,
    "storage_ov_v": 4.2,
    "panel_area_cm2": 16.0,
    "boost_eff": 0.85,
    "boost_part": "TPS613221A",
=======
    "storage_cap_f": 0.22,
    "storage_cap_v_max": 5.5,
    "storage_ov_v": 4.2,  # programmed OVP (~4.18 V from divider math)
    "panel_area_cm2": PANEL_AREA_CM2,  # 16 cm² — 40×40 mm in energy budget / Rev2
}

# Hybrid block-diagram target (100 F LIC) — documented alongside Rev2 PCB values
HYBRID = {
    "storage_cap_f": 100.0,
    "storage_cap_v_max": 3.8,
    "storage_ov_v": 3.8,
    "panel_area_cm2": 36.0,  # 60×60 mm
>>>>>>> Stashed changes
}


def threshold_voltages(rov1: float, rov2: float, rok1: float, rok2: float, rok3: float) -> dict[str, float]:
    return {
        "vbat_ov": VBIAS * (1 + rov2 / rov1) * 1.5,
        "vbat_ok": VBIAS * (1 + rok2 / rok1),
        "vbat_ok_hyst": VBIAS * ((rok1 + rok2 + rok3) / rok1),
    }


<<<<<<< Updated upstream
def panel_breakeven_lux(need_in_uw: float, area_cm2: float) -> float:
    return need_in_uw * REF_LUX / (area_cm2 * PANEL_UW_CM2_REF)


def fill_sluc484(d: dict) -> dict[str, float]:
    t = threshold_voltages(d["rov1_m"], d["rov2_m"], d["rok1_m"], d["rok2_m"], d["rok3_m"])
=======
def fill_sluc484() -> dict[str, float]:
    s = SCHEMATIC
    t = threshold_voltages(s["rov1_m"], s["rov2_m"], s["rok1_m"], s["rok2_m"], s["rok3_m"])
>>>>>>> Stashed changes

    shutil.copy2(SLUC484_SRC, SLUC484_DST)
    wb = openpyxl.load_workbook(SLUC484_DST)
    ws = wb["bq25505(70"]

<<<<<<< Updated upstream
    ws["C8"] = round(d["rov1_m"] + d["rov2_m"], 2)
    ws["C9"] = d["storage_ov_v"]
    ws["C19"] = d["rov1_m"]
    ws["C20"] = d["rov2_m"]

    ws["I7"] = round(d["rok1_m"] + d["rok2_m"] + d["rok3_m"], 2)
    ws["I8"] = round(t["vbat_ok"], 2)
    ws["I9"] = round(t["vbat_ok_hyst"], 2)
    ws["I19"] = d["rok1_m"]
    ws["I20"] = d["rok2_m"]
    ws["I21"] = d["rok3_m"]
=======
    # Overvoltage (storage charge limit)
    ws["C8"] = round(s["rov1_m"] + s["rov2_m"], 2)  # RSUM1 (MΩ)
    ws["C9"] = s["storage_ov_v"]  # desired VBAT_OV
    ws["C19"] = s["rov1_m"]
    ws["C20"] = s["rov2_m"]

    # VBAT_OK network
    ws["I7"] = round(s["rok1_m"] + s["rok2_m"] + s["rok3_m"], 2)
    ws["I8"] = round(t["vbat_ok"], 2)
    ws["I9"] = round(t["vbat_ok_hyst"], 2)
    ws["I19"] = s["rok1_m"]
    ws["I20"] = s["rok2_m"]
    ws["I21"] = s["rok3_m"]
>>>>>>> Stashed changes

    wb.save(SLUC484_DST)
    wb.close()
    return t


<<<<<<< Updated upstream
def fill_sluc463(d: dict, model: dict) -> float:
    t = threshold_voltages(d["rov1_m"], d["rov2_m"], d["rok1_m"], d["rok2_m"], d["rok3_m"])

    burst_s = 0.15
    burst_i_ma = min(model["total_c"] / burst_s, 60)
=======
def fill_sluc463(model: dict) -> None:
    s = SCHEMATIC
    t = threshold_voltages(s["rov1_m"], s["rov2_m"], s["rok1_m"], s["rok2_m"], s["rok3_m"])

    # Peak load during 150 ms report burst (TX + sensors), from energy budget total charge
    burst_s = 0.15
    burst_i_ma = model["total_c"] / burst_s  # mA if all charge occurs in burst window
    boost_eff = 0.85  # TPS613221A-class; Rev2 schematic U1
>>>>>>> Stashed changes

    shutil.copy2(SLUC463_SRC, SLUC463_DST)
    wb = openpyxl.load_workbook(SLUC463_DST)
    ws = wb["Computation"]

<<<<<<< Updated upstream
    ws["E3"] = d["storage_ov_v"]

    ws["B5"] = V_MCU
    ws["C5"] = round(burst_i_ma, 1)
    ws["D5"] = d["boost_eff"]
    ws["E6"] = 1.0
    ws["F7"] = burst_s
    ws["G7"] = BUDGET_PERIOD_S

    ws["B9"] = V_MCU
    ws["C9"] = 0
    ws["D9"] = d["boost_eff"]
=======
    ws["E3"] = s["storage_ov_v"]  # VSTOR nominal (BQ25505 storage rail)

    # Active Mode 1 — LoRa report + sensor burst @ 3.3 V
    ws["B5"] = V_MCU
    ws["C5"] = round(min(burst_i_ma, 60), 1)
    ws["D5"] = boost_eff
    ws["E6"] = 1.0  # BQ25505 activity during burst (mA from VSTOR)
    ws["F7"] = burst_s
    ws["G7"] = BUDGET_PERIOD_S

    # Clear unused TI example mode 2 (zero duration)
    ws["B9"] = V_MCU
    ws["C9"] = 0
    ws["D9"] = boost_eff
>>>>>>> Stashed changes
    ws["E10"] = 0
    ws["F11"] = 0
    ws["G11"] = BUDGET_PERIOD_S

<<<<<<< Updated upstream
    sleep_i_ma = max(model["avg_uA"] / 1000, 0.015)
    ws["E13"] = round(sleep_i_ma, 3)
    ws["E15"] = 0.000325

    ws["B21"] = round(t["vbat_ok"], 2)
    ws["B22"] = d["storage_ov_v"]
    ws["B23"] = d["storage_cap_f"]

    if ws["H15"].value in (None, 24):
        ws["H15"] = 24

    # Panel power density reference: 8 µW/cm² @ 200 lux (energy budget model)
    ws["E36"] = PANEL_UW_CM2_REF

    breakeven = panel_breakeven_lux(model["need_in_uw"], d["panel_area_cm2"])

    wb.save(SLUC463_DST)
    wb.close()
    return breakeven


def write_results_md(thresholds: dict, model: dict, breakeven_lux: float) -> None:
    d = DESIGN
    r = REV2_LEGACY
    ov_diff_pct = (thresholds["vbat_ov"] - d["storage_ov_v"]) / d["storage_ov_v"] * 100
    ov_ok = abs(ov_diff_pct) < 1.0
    path = DOCS / "BQ25505_DESIGN_INPUTS.md"
    path.write_text(
        f"""# BQ25505 design inputs — Solar Sensor hybrid
=======
    # Sleep — average idle current equivalent at VSTOR
    sleep_i_ma = model["avg_uA"] / 1000
    ws["E13"] = round(max(sleep_i_ma, 0.015), 3)
    ws["E15"] = 0.000325  # BQ25505 Iq (325 nA typ)

    # Supercap — Rev2 schematic C3: 0.22 F 5.5 V
    ws["B21"] = round(t["vbat_ok"], 2)
    ws["B22"] = s["storage_ov_v"]
    ws["B23"] = s["storage_cap_f"]

    # Panel / harvest assumptions (Rev2 energy budget model)
    if ws["H15"].value in (None, 24):
        ws["H15"] = 24

    wb.save(SLUC463_DST)
    wb.close()


def write_results_md(thresholds: dict, model: dict) -> None:
    s = SCHEMATIC
    h = HYBRID
    path = DOCS / "BQ25505_DESIGN_INPUTS.md"
    text = f"""# BQ25505 design inputs — Solar Sensor
>>>>>>> Stashed changes

Values applied to:

- **`Docs/tools/SLUC484/SolarSensor_BQ25505_Calculator.xlsx`**
- **`Docs/tools/SLUC463/SolarSensor_solar_load_study.xlsx`**

<<<<<<< Updated upstream
Regenerate: `python build_bq25505_tools.py`

Open in **Excel** so formulas recalculate.

---

## Hybrid architecture (authoritative)

Source: `Docs/pics/BlockDiagram.jpg`, `POWER_SYSTEM_ANALYSIS.md`

### BQ25505 — divider network (hybrid / next PCB spin)

| Ref | Hybrid value | Rev2 PCB | SLUC484 cell |
|-----|--------------|----------|--------------|
| ROV1 | **{d['rov1_m']} MΩ** | {r['rov1_m']} MΩ | `C19` |
| ROV2 | **{d['rov2_m']} MΩ** | {r['rov2_m']} MΩ | `C20` |
| ROK1 | **{d['rok1_m']} MΩ** | (same) | `I19` |
| ROK2 | **{d['rok2_m']} MΩ** | (same) | `I20` |
| ROK3 | **{d['rok3_m']} MΩ** | (same) | `I21` |
| L2 | **{d['l2_uh']} µH** | (same) | Schematic only |

**PCB action:** replace Rev2 ROV1/ROV2 (**{r['rov1_m']} / {r['rov2_m']} MΩ**) with hybrid values above for **3.8 V** LIC OVP. ROK network unchanged.

### Storage — 100 F · 3.8 V LIC supercap

| Parameter | Value | Spreadsheet |
|-----------|-------|-------------|
| Capacitance | **{d['storage_cap_f']} F** | SLUC463 `B23` |
| Rated voltage | **{d['storage_cap_v_max']} V** | — |
| VBAT_OV target | **{d['storage_ov_v']} V** | SLUC484 `C9`, SLUC463 `E3` / `B22` |
| VBAT_OV (computed) | **{thresholds['vbat_ov']:.3f} V** | SLUC484 row 23 **`% diff`** |
| VBAT_OK | **{thresholds['vbat_ok']:.3f} V** | SLUC484 `I8`, SLUC463 `B21` |
| VBAT_OK_HYST | **{thresholds['vbat_ok_hyst']:.3f} V** | SLUC484 `I9` |

OVP vs target: **{ov_diff_pct:+.2f}%** — {"OK (<1%)" if ov_ok else "review divider values"}.

### Firmware gating (above BQ25505 VBAT_OK)

| Threshold | Suggested | Basis |
|-----------|-----------|-------|
| `VCAP_MIN_SENSORS_mV` | **2700** | ~71% of 3.8 V — enable radar/CO₂ P-FETs |
| `VCAP_MIN_TX_mV` | **3000** | ~79% of 3.8 V — LoRa TX burst |
| `VCAP_CHARGE_TARGET_mV` | **3600** | ~95% of 3.8 V — full operating headroom |

Use **ADC_MONITOR** (10 kΩ / 10 kΩ divider) for fine gating; **VBAT_OK** is coarse hardware flag.

### Solar panel — {d['panel_mm']} mm ({d['panel_area_cm2']:.0f} cm²)

| Parameter | Value |
|-----------|-------|
| Area | **{d['panel_area_cm2']} cm²** |
| Model | **{PANEL_UW_CM2_REF} µW/cm² @ {REF_LUX} lux** (Amorton-class) |
| Break-even | **{breakeven_lux:.0f} lux** @ {d['panel_area_cm2']:.0f} cm² |
| Margin @ 200 lux | **~{d['panel_area_cm2'] * PANEL_UW_CM2_REF * 200 / REF_LUX * HARVEST_EFF / model['need_in_uw']:.1f}×** net harvest vs load |

### Boost — {d['boost_part']} → 3.3 V SYSTEM_RAIL

SLUC463 efficiency **`D5` = {d['boost_eff']:.0%}**. Run WEBENCH for inductor/caps.

### ADC sense (R10 / R11)

**{d['adc_r_top_k']:.0f} kΩ / {d['adc_r_bot_k']:.0f} kΩ** → 50% divider to **ADC_MONITOR**

---

## Energy budget load model (SLUC463)

Period **{BUDGET_PERIOD_S} s** from `build_energy_budget_sheet.py` (Rev2 sensor set — update for RAK3172 + gated radar):
=======
Regenerate with: `python build_bq25505_tools.py`

Open the `.xlsx` files in **Excel** so formulas recalculate.

---

## Rev2 schematic (SolarSensorSchematicRev2.pdf / BOM)

### BQ25505 U2 — divider network

| Ref | Schematic value | Calculator cell |
|-----|-----------------|-----------------|
| ROV1 | **{s['rov1_m']} MΩ** | SLUC484 `C19` |
| ROV2 | **{s['rov2_m']} MΩ** | SLUC484 `C20` |
| ROK1 | **{s['rok1_m']} MΩ** | SLUC484 `I19` |
| ROK2 | **{s['rok2_m']} MΩ** | SLUC484 `I20` |
| ROK3 | **{s['rok3_m']} MΩ** | SLUC484 `I21` |
| L2 | **{s['l2_uh']} µH** | Schematic only (not in SLUC484) |

### Storage (C3 on Rev2 PCB)

| Parameter | Schematic | SLUC484 / SLUC463 |
|-----------|-----------|-------------------|
| Capacitor | **{s['storage_cap_f']} F · {s['storage_cap_v_max']} V** | SLUC463 `B23` = {s['storage_cap_f']} F |
| VBAT_OV target | **{s['storage_ov_v']} V** | SLUC484 `C9`, SLUC463 `E3` / `B22` |
| VBAT_OK (computed from ROK network) | **{thresholds['vbat_ok']:.3f} V** | SLUC484 `I8`, SLUC463 `B21` |
| VBAT_OK_HYST (computed) | **{thresholds['vbat_ok_hyst']:.3f} V** | SLUC484 `I9` |
| VBAT_OV (computed from ROV network) | **{thresholds['vbat_ov']:.3f} V** | Compare SLUC484 row 23 `% diff` |

### ADC sense (R10 / R11)

Both **10 kΩ** on Rev2 BOM — equal divider (50%) from storage to **ADC_MONITOR**.

---

## Computed thresholds (from TI divider formulas)

| Output | Voltage |
|--------|---------|
| VBAT_OV (typ) | **{thresholds['vbat_ov']:.3f} V** |
| VBAT_OK (typ) | **{thresholds['vbat_ok']:.3f} V** |
| VBAT_OK_HYST (typ) | **{thresholds['vbat_ok_hyst']:.3f} V** |

---

## Energy budget → SLUC463 load model

From `build_energy_budget_sheet.py` ({BUDGET_PERIOD_S} s period):
>>>>>>> Stashed changes

| Parameter | Value |
|-----------|-------|
| Average load | **{model['avg_uA']:.2f} µA** @ {V_MCU} V (**{model['avg_uW']:.1f} µW**) |
<<<<<<< Updated upstream
| Panel input required | **{model['need_in_uw']:.0f} µW** (before BQ25505) |
| Harvester efficiency | **{HARVEST_EFF:.0%}** |
| Report burst | **{model['total_c'] / 0.15:.1f} mA** × **0.15 s** every **{BUDGET_PERIOD_S} s** |
| 100 F droop @ burst | **~{model['total_c'] / 0.15 * 0.15 / d['storage_cap_f']:.3f} V** (negligible) |

---

## Rev2 PCB legacy (reference)

| Parameter | Rev2 PCB | Hybrid |
|-----------|----------|--------|
| ROV1 / ROV2 | {r['rov1_m']} / {r['rov2_m']} MΩ | {d['rov1_m']} / {d['rov2_m']} MΩ |
| Supercap | {r['storage_cap_f']} F · {r['storage_cap_v_max']} V | {d['storage_cap_f']} F · {d['storage_cap_v_max']} V |
| VBAT_OV | ~4.18 V (from Rev2 ROV) | **{thresholds['vbat_ov']:.2f} V** |
| Panel | 16 cm² (40×40) | {d['panel_area_cm2']:.0f} cm² ({d['panel_mm']}) |
| Boost | {r['boost_part']} | {d['boost_part']} |
=======
| Panel input required | **{model['need_in_uw']:.0f} µW** (before BQ25505 losses) |
| Break-even illuminance | **{model['breakeven_lux']:.0f} lux** @ {s['panel_area_cm2']} cm² panel |
| Harvester efficiency assumed | **{HARVEST_EFF:.0%}** |
| Report burst model | **{model['total_c'] / 0.15:.1f} mA** peak × **0.15 s** every **{BUDGET_PERIOD_S} s** |

Solar panel on schematic: **user-selected via J1**; energy budget uses **{s['panel_area_cm2']} cm²** @ **{PANEL_UW_CM2_REF} µW/cm²** @ **{REF_LUX} lux** (Amorton-class).

---

## Hybrid block diagram (future PCB — not Rev2 C3)

| Parameter | Target |
|-----------|--------|
| Storage | **{h['storage_cap_f']} F · {h['storage_cap_v_max']} V** supercap |
| VBAT_OV | **{h['storage_ov_v']} V** — re-run calculator with `C9` = 3.8 V |
| Panel | **{h['panel_area_cm2']} cm²** (60×60 mm) |

Rev2 divider values are unchanged on hybrid; only storage OVP and panel area differ.
>>>>>>> Stashed changes

---

## Tool split

| Block | Tool |
|-------|------|
<<<<<<< Updated upstream
| BQ25505 thresholds | **SLUC484** |
| Panel + daily energy | **SLUC463** |
| 3.3 V boost detail | **WEBENCH DC/DC** ({d['boost_part']}) |
""",
        encoding="utf-8",
    )
=======
| BQ25505 thresholds | **SLUC484** (`SolarSensor_BQ25505_Calculator.xlsx`) |
| Panel + daily energy | **SLUC463** (`SolarSensor_solar_load_study.xlsx`) |
| 3.3 V boost | **WEBENCH DC/DC** (TPS613221A Rev2 / TPS61291 hybrid) |
"""
    path.write_text(text, encoding="utf-8")
>>>>>>> Stashed changes


def main() -> None:
    if not SLUC484_SRC.is_file():
        raise SystemExit(f"Missing TI original: {SLUC484_SRC}")
    if not SLUC463_SRC.is_file():
        raise SystemExit(f"Missing TI original: {SLUC463_SRC}")

    model = build_model()
<<<<<<< Updated upstream
    thresholds = fill_sluc484(DESIGN)
    breakeven = fill_sluc463(DESIGN, model)
    write_results_md(thresholds, model, breakeven)
=======
    thresholds = fill_sluc484()
    fill_sluc463(model)
    write_results_md(thresholds, model)
>>>>>>> Stashed changes

    print(f"Updated {SLUC484_DST.relative_to(DOCS)}")
    print(f"Updated {SLUC463_DST.relative_to(DOCS)}")
    print(f"Updated BQ25505_DESIGN_INPUTS.md")
<<<<<<< Updated upstream
    print(f"Storage: {DESIGN['storage_cap_f']} F @ {DESIGN['storage_ov_v']} V OVP")
    print(f"Panel: {DESIGN['panel_mm']} mm ({DESIGN['panel_area_cm2']} cm²), break-even ~{breakeven:.0f} lux")
    print(
        f"Thresholds: VBAT_OV={thresholds['vbat_ov']:.3f} V (target {DESIGN['storage_ov_v']} V), "
        f"VBAT_OK={thresholds['vbat_ok']:.3f} V"
=======
    print(
        f"Thresholds: VBAT_OV={thresholds['vbat_ov']:.3f} V, "
        f"VBAT_OK={thresholds['vbat_ok']:.3f} V, "
        f"VBAT_OK_HYST={thresholds['vbat_ok_hyst']:.3f} V"
>>>>>>> Stashed changes
    )


if __name__ == "__main__":
    main()
