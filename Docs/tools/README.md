# BQ25505 design tools (local copies)

Texas Instruments does **not** support BQ25505 in WEBENCH. These spreadsheets are the official TI calculation tools, filled with **hybrid architecture** values.

Regenerate project copies:

```powershell
cd Docs
python build_bq25505_tools.py
```

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
