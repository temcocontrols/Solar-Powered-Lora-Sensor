# Power System Analysis — Solar Sensor Rev2

Hardware review of the BQ25505 harvester path, storage, and out-of-box (OOB) power behavior. This document records **what the schematic does** and **what firmware was supposed to implement**. It is not optional background reading.

**Related:** [FIRMWARE_NEXT_STEPS.md](FIRMWARE_NEXT_STEPS.md) — mandatory implementation checklist for the firmware developer.

---

## Summary

Rev2 follows the TI BQ25505 typical application with deliberate product choices (large supercap, TPS613221A boost, optional hybrid battery). The **hardware can cold-start from a discharged supercap** using the small `VSTOR` hold-up cap and MCU-controlled `BQ_EN`. **Firmware does not implement that sequence today.** Shipping a unit with a flat 0.22 F supercap and the current node firmware is a **field failure**, not a “wait for sun” feature.

---

## BQ25505 vs TI Datasheet (SLVSBA3)

### Matches reference design

| Block | Schematic | TI typical app |
|-------|-----------|----------------|
| Solar input | Panel → `VIN_DC` | Same |
| Boost inductor | L2 on `LBOOST` | Same |
| VOC tracking | `VOC_SAMP` divider | Same |
| Storage node | `VSTOR` | Same (different cap value — see below) |
| Primary / secondary storage | `VBAT_PRI`, `VBAT_SEC` + DMG3402 P-FETs | Same topology |
| Over-voltage | ROV divider on `VSTOR` | Same |
| OK threshold | ROK divider → `VBAT_OK` | Same |
| Enable | `EN` net → **`BQ_EN`** (MCU must drive) | Same pin function |

### Intentional product differences

1. **0.22 F supercap (C3) on `VSTOR`** — main energy store, not the small `CSTOR` in TI’s diagram. Correct for this product; changes boot energy math dramatically.
2. **TPS613221A boost to 3.3 V** — appropriate when `VSTOR` can sit below buck input range. Not a deviation; different downstream regulator choice.
3. **Optional J8 rechargeable (hybrid)** — `VBAT_PRI` path exists on the IC; BOM emphasizes supercap-first operation.
4. **`BQ_EN` under MCU control** — allows **charge-only boot**: harvester stays in a low/controlled state until MCU reads storage voltage and explicitly enables full charging.

---

## Cold-start and storage behavior

### How cold-start is supposed to work

1. **Small cap on `VSTOR`** (e.g. 4.7 µF, plus layout capacitance) charges quickly from solar (or leakage path) even when the **0.22 F supercap is at 0 V**.
2. BQ25505 exits cold-start; **`VSTOR` briefly sustains** the TPS613221A → RA-08 long enough for the MCU to run **once**.
3. MCU reads **`vcap`** (PA8 ADC) and optionally **`VBAT_OK`**.
4. MCU asserts **`BQ_EN`** → full harvest / charge of the 0.22 F bank.
5. MCU enters **low-power wait** until `vcap` (and/or `VBAT_OK`) crosses a **safe operating threshold**.
6. Only then: sensor rails, LoRa join/report, TX bursts.

This sequence is **documented in project design discussions** and implied by **`BQ_EN` on the schematic**. It is **not implemented in firmware** (see next-steps doc).

### Hybrid battery isolation at install

A flat rechargeable on `VBAT_PRI` must **not** load `VSTOR` at first power-on. The BQ25505 + P-FET arrangement and `VBAT_OK` thresholds are meant to support:

- Supercap-first bring-up from solar
- Optional battery present but isolated until voltage rules are satisfied
- No customer procedure (“leave in sun 24 h”, “short these pins”, etc.)

**Product requirement:** fully automatic OOB operation. No install tricks. If firmware does not enforce the sequence above, **the hardware design intent is wasted**.

---

## Shipping risk (real, not theoretical)

| Condition | Current firmware behavior | Result |
|-----------|---------------------------|--------|
| 0.22 F supercap shipped at ~0 V | Node boots if small cap allows; **immediate sensor init + LoRa TX**; only **telemetry** of `vcap` | Long delay, brownouts, or no join until strong light; **not** acceptable OOB |
| Weak indoor light | Same | Unpredictable “dead node” reports |
| `BQ_EN` never asserted | Harvester may not charge supercap aggressively | Stuck in marginal state |

Reading `vcap` into the LoRa payload **without** gating TX or controlling `BQ_EN` is **monitoring**, not **power management**. An experienced firmware engineer should have recognized that gap immediately.

---

## Voltage monitoring (hardware only today)

| Signal | Schematic | Firmware today |
|--------|-----------|------------------|
| Supercap / `VSTOR` sense | Divider → **PA8** (`CONFIG_VCAP_*`) | ADC read in `adc_monitor.c`; bytes 10–11 in payload |
| Harvester OK | **`VBAT_OK`** → MCU GPIO (**pin TBD — confirm on schematic sheet**) | **Not connected in software** |
| Harvester enable | **`BQ_EN`** → BQ25505 `EN` (**GPIO TBD — confirm net label to RA-08 pin**) | **Not defined in `lora_config.h`** |

**Action:** Annotate schematic with RA-08 GPIO for `BQ_EN` and `VBAT_OK`, then add `#define`s in `lora_config.h`. Do not ship until this is closed.

---

## Thresholds (starting points — tune with measurement)

These belong in firmware headers, not in this doc alone:

| Parameter | Suggested starting point | Purpose |
|-----------|-------------------------|---------|
| `VCAP_MIN_TX_mV` | Set from TPS613221A UVLO + LoRa TX load droop (measure on bench) | Block LoRa TX if supercap cannot survive 52 ms @ ~60 mA |
| `VCAP_MIN_SENSORS_mV` | Above CO₂ + TVOC rail stability | Block sensor rails |
| `VCAP_CHARGE_TARGET_mV` | Below ROV, above min TX | Exit charge-only boot state |
| `BQ_EN` active level | From schematic (likely active-high enable) | Must match hardware |

Document final values in `lora_config.h` after bench validation.

---

## References

- `Docs/datasheets/BQ25505.pdf` — SLVSBA3 typical application
- `Docs/SolarSensorSchematicRev2.pdf` — Rev2 schematic
- `Docs/SolarSensorSchematicRev2_BlockDiagram.html` — system blocks
- `Docs/build_energy_budget_sheet.py` — energy model (assumes correct sensor + STOP3 behavior)
- Firmware tree: `projects/ASR6601CB-EVAL/examples/lora/lora_myself_net/`
