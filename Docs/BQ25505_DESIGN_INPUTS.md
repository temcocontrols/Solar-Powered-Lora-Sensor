# BQ25505 design inputs — Solar Sensor hybrid

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
| ROV1 | **4.02 MΩ** | 5.62 MΩ | `C19` |
| ROV2 | **4.42 MΩ** | 7.32 MΩ | `C20` |
| ROK1 | **5.62 MΩ** | (same) | `I19` |
| ROK2 | **5.49 MΩ** | (same) | `I20` |
| ROK3 | **1.87 MΩ** | (same) | `I21` |
| L2 | **22 µH** | (same) | Schematic only |

**PCB action:** replace Rev2 ROV1/ROV2 (**5.62 / 7.32 MΩ**) with hybrid values above for **3.8 V** LIC OVP. ROK network unchanged.

### Storage — 100 F · 3.8 V LIC supercap

| Parameter | Value | Spreadsheet |
|-----------|-------|-------------|
| Capacitance | **100.0 F** | SLUC463 `B23` |
| Rated voltage | **3.8 V** | — |
| VBAT_OV target | **3.8 V** | SLUC484 `C9`, SLUC463 `E3` / `B22` |
| VBAT_OV (computed) | **3.811 V** | SLUC484 row 23 **`% diff`** |
| VBAT_OK | **2.392 V** | SLUC484 `I8`, SLUC463 `B21` |
| VBAT_OK_HYST | **2.795 V** | SLUC484 `I9` |

OVP vs target: **+0.28%** — OK (<1%).

### Firmware gating (above BQ25505 VBAT_OK)

| Threshold | Suggested | Basis |
|-----------|-----------|-------|
| `VCAP_MIN_SENSORS_mV` | **2700** | ~71% of 3.8 V — enable radar/CO₂ P-FETs |
| `VCAP_MIN_TX_mV` | **3000** | ~79% of 3.8 V — LoRa TX burst |
| `VCAP_CHARGE_TARGET_mV` | **3600** | ~95% of 3.8 V — full operating headroom |

Use **ADC_MONITOR** (10 kΩ / 10 kΩ divider) for fine gating; **VBAT_OK** is coarse hardware flag.

### Solar panel — 60×60 mm (36 cm²)

| Parameter | Value |
|-----------|-------|
| Area | **36.0 cm²** |
| Model | **8 µW/cm² @ 200 lux** (Amorton-class) |
| Break-even | **65 lux** @ 36 cm² |
| Margin @ 200 lux | **~2.3×** net harvest vs load |

### Boost — TPS61291 → 3.3 V SYSTEM_RAIL

SLUC463 efficiency **`D5` = 90%**. Run WEBENCH for inductor/caps.

### ADC sense (R10 / R11)

**10 kΩ / 10 kΩ** → 50% divider to **ADC_MONITOR**

---

## Energy budget load model (SLUC463)

Period **300 s** from `build_energy_budget_sheet.py` (Rev2 sensor set — update for RAK3172 + gated radar):

| Parameter | Value |
|-----------|-------|
| Average load | **16.46 µA** @ 3.3 V (**54.3 µW**) |
| Panel input required | **94 µW** (before BQ25505) |
| Harvester efficiency | **75%** |
| Report burst | **32.9 mA** × **0.15 s** every **300 s** |
| 100 F droop @ burst | **~0.049 V** (negligible) |

---

## Rev2 PCB legacy (reference)

| Parameter | Rev2 PCB | Hybrid |
|-----------|----------|--------|
| ROV1 / ROV2 | 5.62 / 7.32 MΩ | 4.02 / 4.42 MΩ |
| Supercap | 0.22 F · 5.5 V | 100.0 F · 3.8 V |
| VBAT_OV | ~4.18 V (from Rev2 ROV) | **3.81 V** |
| Panel | 16 cm² (40×40) | 36 cm² (60×60) |
| Boost | TPS613221A | TPS61291 |

---

## Tool split

| Block | Tool |
|-------|------|
| BQ25505 thresholds | **SLUC484** |
| Panel + daily energy | **SLUC463** |
| 3.3 V boost detail | **WEBENCH DC/DC** (TPS61291) |
