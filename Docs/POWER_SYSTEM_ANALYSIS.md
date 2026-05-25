# Power System Analysis — Hybrid Power & Control

Hardware review of the **Solar Sensor Hybrid Power & Control System** (see `Docs/pics/BlockDiagram.jpg` and [Block Diagram HTML](SolarSensorSchematicRev2_BlockDiagram.html)).

**Related:** [FIRMWARE_NEXT_STEPS.md](FIRMWARE_NEXT_STEPS.md)

> **Note:** BOM, Sensors, and Energy Budget sheets still describe the **Rev2 RA-08 PCB** (0.22 F, TPS613221A). This document follows the **hybrid block diagram**, which is the architecture target.

---

## Summary

The hybrid design uses **BQ25505** for cold-start and MPPT harvesting, **ideal-diode OR logic** for LIC vs primary paths, a **100 F · 3.8 V supercap** on the LIC path, **TPS61291** boost to **SYSTEM_RAIL 3.3 V**, and **RAK3172** with **P-FET (Si2301) gating** for high-draw sensors (radar, CO₂). **SHT41** remains always-on on 3.3 V.

Firmware must treat **ADC_MONITOR**, **VBAT_OK**, **BAT_GD**, and **PRIM_STATUS** as first-class inputs — not optional telemetry.

---

## Block-by-block

### Harvesting

| Element | Role |
|---------|------|
| 60×60 mm solar panel | Input to BQ25505 |
| BQ25505 | Cold start, MPPT charger, internal path management |
| VOC_SAMP / V_OV_SET / V_OK_SET / V_OK_HYST | Threshold programming via divider network |
| Ideal diode OR + LIC MOS switch | Deadlock-proof routing between LIC and primary paths |
| VBAT_OK, BAT_GD | Status to MCU |

### Storage

| Element | Role |
|---------|------|
| 100 F · 3.8 V supercap | Main LIC-path energy store |
| R10 / R11 divider → ADC_MONITOR | MCU supercap voltage sense |
| Digital status outputs | Storage / path state feedback |

### Power delivery

| Element | Role |
|---------|------|
| TPS61291 | Boost to regulated system rail |
| SYSTEM_RAIL 3.3 V + C_STOR | MCU, SHT41, boost input hold-up |

### Sensing & control

| Element | Role | Power |
|---------|------|-------|
| RAK3172 | LoRa MCU | SYSTEM_RAIL |
| SHT41 | Temperature / RH | Always on |
| HLK-LD2410 radar | mmWave presence | GPIO_RADAR → Si2301 P-FET |
| CO₂ sensor | Air quality | GPIO_CO2 → Si2301 P-FET |

---

## Cold-start and OOB behavior

1. BQ25505 **cold-starts** from solar; small hold-up caps allow brief MCU power.
2. MCU reads **ADC_MONITOR** and status lines (**VBAT_OK**, **BAT_GD**, **PRIM_STATUS**, **PRIM_STATUS_SW**).
3. **Do not** enable GPIO_RADAR / GPIO_CO2 or LoRa TX until storage voltage supports high-draw loads.
4. BQ25505 internal logic manages path deadlock; firmware must not fight the harvester with premature sensor loads.

**Product requirement:** no customer pre-charge or install tricks.

---

## Firmware monitoring vs management

| Signal | Purpose |
|--------|---------|
| ADC_MONITOR | Supercap voltage — **gate** TX and P-FET enables |
| VBAT_OK | Harvester OK threshold |
| BAT_GD | Storage / battery path good |
| PRIM_STATUS / PRIM_STATUS_SW | Hybrid path state |
| GPIO_RADAR / GPIO_CO2 | **Outputs** — radar and CO₂ rail enables |

Reporting storage voltage in LoRa without gating is **telemetry only**, not power management.

---

## BQ25505 thresholds (hybrid — SLUC484)

Rev2 PCB ROV dividers target **~4.18 V OVP** (Li-ion class). **100 F · 3.8 V LIC** requires new ROV values on the next PCB spin:

| Network | Rev2 PCB | Hybrid (recommended) | Computed voltage |
|---------|----------|----------------------|------------------|
| ROV1 / ROV2 | 5.62 / 7.32 MΩ | **4.02 / 4.42 MΩ** | **VBAT_OV ≈ 3.81 V** |
| ROK1 / ROK2 / ROK3 | 5.62 / 5.49 / 1.87 MΩ | (unchanged) | **VBAT_OK ≈ 2.39 V**, **HYST ≈ 2.80 V** |

Suggested firmware ADC thresholds (via **ADC_MONITOR**, 10 kΩ / 10 kΩ divider):

| Constant | mV | Purpose |
|----------|-----|---------|
| `VCAP_MIN_SENSORS_mV` | 2700 | Enable radar / CO₂ P-FETs |
| `VCAP_MIN_TX_mV` | 3000 | LoRa TX |
| `VCAP_CHARGE_TARGET_mV` | 3600 | Full operating headroom |

Detail: [BQ25505_DESIGN_INPUTS.md](BQ25505_DESIGN_INPUTS.md)

---

## References

- `Docs/pics/BlockDiagram.jpg` — authoritative diagram
- `Docs/schematic_block_diagram.mmd` — simplified flow
- `Docs/datasheets/BQ25505.pdf`
- `Docs/BQ25505_DESIGN_INPUTS.md` — calculator inputs, ROV fix, firmware thresholds
- `Docs/tools/SLUC484/SolarSensor_BQ25505_Calculator.xlsx` — TI threshold design (hybrid values)
- `Docs/tools/SLUC463/SolarSensor_solar_load_study.xlsx` — solar load / panel sizing
- `Docs/tools/README.md` — local tool index
- `Docs/SolarSensorSchematicRev2.pdf` — Rev2 PCB (legacy detail)
