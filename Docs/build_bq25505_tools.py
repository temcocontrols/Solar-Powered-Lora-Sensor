#!/usr/bin/env python3
"""Apply hybrid architecture + schematic BOM values to local BQ25505 TI spreadsheets."""

from __future__ import annotations

import shutil
from pathlib import Path

import openpyxl

from build_energy_budget_sheet import (
    BUDGET_PERIOD_S,
    HARVEST_EFF,
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

# Rev2 schematic ROV (4.2 V-class OVP — do not use with 3.8 V LIC)
REV2_ROV = {"rov1_m": 5.62, "rov2_m": 7.32}

# Hybrid 3.8 V OVP — 1% pair from SLUC484 lookup (0.28% error vs 3.8 V target)
HYBRID_ROV = {"rov1_m": 4.02, "rov2_m": 4.42}

# Hybrid Power & Control — authoritative target (BlockDiagram.jpg)
DESIGN = {
    **HYBRID_ROV,
    "rok1_m": 5.62,
    "rok2_m": 5.49,
    "rok3_m": 1.87,
    "l2_uh": 22,
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
}


def threshold_voltages(rov1: float, rov2: float, rok1: float, rok2: float, rok3: float) -> dict[str, float]:
    return {
        "vbat_ov": VBIAS * (1 + rov2 / rov1) * 1.5,
        "vbat_ok": VBIAS * (1 + rok2 / rok1),
        "vbat_ok_hyst": VBIAS * ((rok1 + rok2 + rok3) / rok1),
    }


def panel_breakeven_lux(need_in_uw: float, area_cm2: float) -> float:
    return need_in_uw * REF_LUX / (area_cm2 * PANEL_UW_CM2_REF)


def fill_sluc484(d: dict) -> dict[str, float]:
    t = threshold_voltages(d["rov1_m"], d["rov2_m"], d["rok1_m"], d["rok2_m"], d["rok3_m"])

    shutil.copy2(SLUC484_SRC, SLUC484_DST)
    wb = openpyxl.load_workbook(SLUC484_DST)
    ws = wb["bq25505(70"]

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

    wb.save(SLUC484_DST)
    wb.close()
    return t


def fill_sluc463(d: dict, model: dict) -> float:
    t = threshold_voltages(d["rov1_m"], d["rov2_m"], d["rok1_m"], d["rok2_m"], d["rok3_m"])

    burst_s = 0.15
    burst_i_ma = min(model["total_c"] / burst_s, 60)

    shutil.copy2(SLUC463_SRC, SLUC463_DST)
    wb = openpyxl.load_workbook(SLUC463_DST)
    ws = wb["Computation"]

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
    ws["E10"] = 0
    ws["F11"] = 0
    ws["G11"] = BUDGET_PERIOD_S

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

Values applied to:

- **`Docs/tools/SLUC484/SolarSensor_BQ25505_Calculator.xlsx`**
- **`Docs/tools/SLUC463/SolarSensor_solar_load_study.xlsx`**

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

| Parameter | Value |
|-----------|-------|
| Average load | **{model['avg_uA']:.2f} µA** @ {V_MCU} V (**{model['avg_uW']:.1f} µW**) |
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

---

## Tool split

| Block | Tool |
|-------|------|
| BQ25505 thresholds | **SLUC484** |
| Panel + daily energy | **SLUC463** |
| 3.3 V boost detail | **WEBENCH DC/DC** ({d['boost_part']}) |
""",
        encoding="utf-8",
    )


def main() -> None:
    if not SLUC484_SRC.is_file():
        raise SystemExit(f"Missing TI original: {SLUC484_SRC}")
    if not SLUC463_SRC.is_file():
        raise SystemExit(f"Missing TI original: {SLUC463_SRC}")

    model = build_model()
    thresholds = fill_sluc484(DESIGN)
    breakeven = fill_sluc463(DESIGN, model)
    write_results_md(thresholds, model, breakeven)

    print(f"Updated {SLUC484_DST.relative_to(DOCS)}")
    print(f"Updated {SLUC463_DST.relative_to(DOCS)}")
    print(f"Updated BQ25505_DESIGN_INPUTS.md")
    print(f"Storage: {DESIGN['storage_cap_f']} F @ {DESIGN['storage_ov_v']} V OVP")
    print(f"Panel: {DESIGN['panel_mm']} mm ({DESIGN['panel_area_cm2']} cm²), break-even ~{breakeven:.0f} lux")
    print(
        f"Thresholds: VBAT_OV={thresholds['vbat_ov']:.3f} V (target {DESIGN['storage_ov_v']} V), "
        f"VBAT_OK={thresholds['vbat_ok']:.3f} V"
    )


if __name__ == "__main__":
    main()
