# BQ25505 design tools (local copies)

<<<<<<< Updated upstream
Texas Instruments does **not** support BQ25505 in WEBENCH. These spreadsheets are the official TI calculation tools, filled with **hybrid architecture** values.

Regenerate project copies:
=======
Texas Instruments does **not** support BQ25505 in WEBENCH. These are the official TI calculation spreadsheets, stored locally for the Solar Sensor hybrid architecture.

## Files

| File | TI doc | Purpose |
|------|--------|---------|
| `SLUC484/SolarSensor_BQ25505_Calculator.xlsx` | SLUC484 | **Start here** — Rev2 schematic divider values applied |
| `SLUC484/bq25505(70_Design_Help_V1_3.xlsx` | SLUC484 | Pristine TI original (v1.3) |
| `SLUC463/SolarSensor_solar_load_study.xlsx` | SLUC463 | Solar load study — energy budget applied to Rev2 schematic |
| `SLUC463/bq25505SolarAppDesignExample_V1p3.xlsx` | SLUC463 | Pristine TI solar example |

**Datasheet:** `Docs/datasheets/BQ25505.pdf`

**Architecture context:** `Docs/POWER_SYSTEM_ANALYSIS.md`, `Docs/BQ25505_DESIGN_INPUTS.md`

Project copies are regenerated from schematic/BOM data:
>>>>>>> Stashed changes

```powershell
cd Docs
python build_bq25505_tools.py
```

<<<<<<< Updated upstream
## Files

| File | Purpose |
|------|---------|
| **`SLUC484/SolarSensor_BQ25505_Calculator.xlsx`** | BQ25505 threshold / divider design (**start here**) |
| `SLUC484/bq25505(70_Design_Help_V1_3.xlsx` | Pristine TI original |
| **`SLUC463/SolarSensor_solar_load_study.xlsx`** | Solar load + panel sizing (energy budget applied) |
| `SLUC463/bq25505SolarAppDesignExample_V1p3.xlsx` | Pristine TI original |

See **`Docs/BQ25505_DESIGN_INPUTS.md`** for all applied values.

## Applied hybrid values

| Parameter | Value |
|-----------|-------|
| Supercap | **100 F · 3.8 V** |
| VBAT_OV target | **3.8 V** |
| Panel | **60×60 mm (36 cm²)** |
| Boost | **TPS61291 @ 90%** |
| BQ25505 dividers | ROV **4.02 / 4.42 MΩ**, ROK **5.62 / 5.49 / 1.87 MΩ** (Rev2 PCB: 5.62 / 7.32 ROV) |
| L2 | **22 µH** |

Open `.xlsx` files in **Excel** so formulas recalculate.

## WEBENCH (TPS61291 only)

[WEBENCH Power Designer](https://webench.ti.com/power-designer/) — 3.3 V boost from supercap, **not** BQ25505.

## Re-download from TI

- [SLUC484](https://www.ti.com/tool/download/SLUC484)
- [SLUC463](https://www.ti.com/tool/download/SLUC463)
=======
## How to use SLUC484 (threshold calculator)

1. Open **`SLUC484/SolarSensor_BQ25505_Calculator.xlsx`** in Excel (or LibreOffice — macros not required for divider math).
2. Sheet **`bq25505(70`** — yellow **User Input / Desired** cells drive computed resistor picks and typical voltages.
3. Compare **Selected** resistor values (rows 19–21) against Rev2 BOM:
   - ROV1 / ROK1: **5.62 MΩ**
   - ROK2: **5.49 MΩ**
   - ROV2: **7.32 MΩ**
   - ROK3: **1.87 MΩ**
4. Read computed **VBAT_OV**, **VBAT_OK**, **VBAT_OK_HYST** — map to firmware gating and to MCU inputs **VBAT_OK**, **BAT_GD**, **ADC_MONITOR**.
5. Adjust **I8 / I9** (VBAT_OK targets) until `% diff` in rows 23–24 is acceptable with 1% resistor stock.

Project pre-fill uses **3.8 V** storage OVP (100 F · 3.8 V supercap) instead of the spreadsheet default 4.2 V Li-ion example.

## How to use SLUC463 (solar sizing example)

1. Open **`SLUC463/bq25505SolarAppDesignExample_V1p3.xlsx`**.
2. Sheet **`Computation`** — enter active/sleep load modes, durations, and panel assumptions.
3. Adapt modes to RAK3172 + SHT41 always-on + gated radar/CO₂ (see Energy Budget sheet).
4. Sheet **`Block Diagram`** — reference topology only (TPS62736 in TI example ≠ our TPS61291).

## WEBENCH (TPS61291 only)

Use [WEBENCH Power Designer](https://webench.ti.com/power-designer/) for the **3.3 V boost** from supercap storage — not for BQ25505.

## Re-download from TI

- SLUC484: https://www.ti.com/tool/download/SLUC484
- SLUC463: https://www.ti.com/tool/download/SLUC463

Direct URLs (if TI page HTML is parsed):

- `https://dr-download.ti.com/design-tools-simulation/calculation-tool/MD-EgyVTlhPJz/01.00.00.00/sluc484.zip`
- `https://dr-download.ti.com/software-development/code-example-or-demo/MD-paJbHriwbH/01.00.00.0A/sluc463a.zip`
>>>>>>> Stashed changes
