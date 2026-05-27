# Firmware Next Steps — Hybrid Power & Control

**Task tracker:** [SolarSensorSchematicRev2_TODO.html](SolarSensorSchematicRev2_TODO.html) · spreadsheet tab **Firmware TODO**

**Architecture:** [Block Diagram](SolarSensorSchematicRev2_BlockDiagram.html) · [POWER_SYSTEM_ANALYSIS.md](POWER_SYSTEM_ANALYSIS.md) · [FIRMWARE_POWER_MANAGER_DESIGN.md](FIRMWARE_POWER_MANAGER_DESIGN.md)

Regenerate docs: `python Docs/build_block_diagram.py` · `python Docs/firmware_todo.py`

---

## Architecture (from block diagram)

| Block | Hardware |
|-------|----------|
| Harvest | BQ25505 · 60×60 mm panel · ideal-diode OR · LIC MOS switch |
| Storage | 100 F · 3.8 V supercap · ADC_MONITOR (R10/R11) |
| Rail | TPS61291 → SYSTEM_RAIL 3.3 V |
| MCU | RAK3172 LoRa module |
| Always-on sensor | SHT41 on 3.3 V |
| Gated sensors | HLK-LD2410 radar, CO₂ — Si2301 P-FET via GPIO_RADAR / GPIO_CO2 |

Legacy **RA-08 / Rev2** firmware in `lora_myself_net` does **not** implement this architecture.

---

## MCU signal map (assign pins in `lora_config.h`)

| Signal | Dir | Use |
|--------|-----|-----|
| ADC_MONITOR | In (ADC) | Supercap voltage — TX and P-FET gating |
| VBAT_OK | In | BQ25505 OK |
| BAT_GD | In | Path / battery good |
| PRIM_STATUS | In | Primary storage status |
| PRIM_STATUS_SW | In | Primary-path switch status |
| GPIO_RADAR | Out | Radar P-FET (Si2301) |
| GPIO_CO2 | Out | CO₂ P-FET (Si2301) |

---

## Power state machine (required)

```
COLD_START     → BQ25505 cold-start; read ADC_MONITOR + status inputs
CHARGE_ONLY    → Sensor P-FETs off; no LoRa TX; wait for storage threshold
READY          → vcap OK for low-draw sensors (SHT41)
REPORT         → SHT41 + gated radar/CO₂ sequence; LoRa if allowed
TX_BLOCKED     → Defer TX until ADC_MONITOR recovers
```

---

## Sensor sequence (target)

1. Wake from low power (RTC / interrupt).
2. Read **ADC_MONITOR** — abort high-draw work if low.
3. Read **SHT41** (always powered).
4. Assert **GPIO_RADAR** → sample radar → deassert.
5. Assert **GPIO_CO2** → single-shot CO₂ (not continuous) → deassert.
6. Apply N-sample filter if configured.
7. LoRa TX only if storage voltage allows burst current.
8. Sleep until next interval.

---

## Task list

See **FW-001 – FW-020** in [SolarSensorSchematicRev2_TODO.html](SolarSensorSchematicRev2_TODO.html). Update task wording to RAK3172 / hybrid signals as pins are confirmed on the new PCB.

---

## Ship gate

All **P0** tasks closed; block diagram signal map implemented in firmware; OOB boot from discharged 100 F supercap verified in reasonable indoor light.
