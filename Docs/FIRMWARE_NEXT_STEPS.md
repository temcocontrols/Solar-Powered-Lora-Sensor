# Firmware Next Steps — Mandatory Before Ship

**Task tracker (authoritative list):** [SolarSensorSchematicRev2_TODO.html](SolarSensorSchematicRev2_TODO.html) · spreadsheet tab **Firmware TODO** in [SolarSensorSchematicRev2_BOM.xlsx](SolarSensorSchematicRev2_BOM.xlsx)

**Hardware context:** [POWER_SYSTEM_ANALYSIS.md](POWER_SYSTEM_ANALYSIS.md)

Regenerate HTML + spreadsheet after editing tasks:

```bash
python Docs/firmware_todo.py
```

---

## The problem in one sentence

The schematic supports **automatic solar bring-up** (BQ_EN, VBAT_OK, 0.22 F supercap). The firmware **does not** — it boots, turns on sensors, and transmits LoRa while only **reporting** supercap voltage. That is not acceptable for this product.

---

## Gap summary

| Area | Design intent | Firmware today |
|------|---------------|----------------|
| Power bring-up | Charge-only boot, then sensors/TX | None — immediate sensor init + TX |
| BQ_EN / VBAT_OK | MCU-controlled harvester | Not defined in code |
| vcap | Gate TX and sensor rails | Telemetry only (payload bytes 10–11) |
| STCC4 | Single-shot + sleep (~510 ms) | Continuous mode + 5200 ms wait |
| Sensor timing | STCC4 first; fast sensors in parallel | Sequential reads |
| Filtering | Mean of last N reads | Not implemented |
| Sleep | STOP3 between reports | `NODE_STOP3_ENABLE 0` (debug) |

Close tasks **FW-001 through FW-020** in the TODO tracker before calling firmware Rev2-ready.

---

## Task list (FW-001 – FW-020)

### Pinout and power (do these first)

| Task | What | Why it matters |
|------|------|----------------|
| **FW-001** | Assign **BQ_EN** to an RA-08 GPIO in `lora_config.h` | Without this, the harvester is not under MCU control |
| **FW-002** | Assign **VBAT_OK** to an RA-08 GPIO | Optional but recommended for charge-ready detection |
| **FW-003** | Implement power manager state machine | COLD_START → CHARGE_ONLY → READY → REPORT → TX_BLOCKED |
| **FW-004** | Drive **BQ_EN** during charge-only boot | 0.22 F supercap must charge before heavy loads |
| **FW-005** | Define **VCAP_MIN_TX_mV**, **VCAP_MIN_SENSORS_mV**, **VCAP_CHARGE_TARGET_mV** on the bench | Thresholds must come from measurement, not guesses |
| **FW-006** | Block LoRa TX when vcap is too low | 52 ms @ ~60 mA will brown out a flat supercap |
| **FW-007** | Block sensor rails (PA5/6/7/12) until POWER_READY | STCC4 + SGP30 at boot load a discharged cap |
| **FW-008** | Remove/guard `node_send_sensor_report("startup")` | No TX before charge bring-up completes |
| **FW-009** | Re-enable STOP3 (`NODE_STOP3_ENABLE 1`) | Energy budget assumes ~1.3 µA sleep between reports |

### STCC4, sensors, and payload

| Task | What | Why it matters |
|------|------|----------------|
| **FW-010** | Rewrite `stcc4.c` to single-shot + sleep | Continuous mode + 5.2 s wait is wrong for this design |
| **FW-011** | Read SHT40, SGP30, BH1620 **during** CO₂ conversion | Saves time and matches energy budget |
| **FW-012** | STOP3 while waiting for CO₂ (~440 ms) | Do not busy-spin the MCU |
| **FW-013** | N-sample ring buffer (default N=5) | Smooth readings without extra sensor energy |
| **FW-014** | Send **filtered** values in 19-byte LoRa payload | Latest raw reading is not the spec |

### Flowcharts and documentation

| Task | What | Why it matters |
|------|------|----------------|
| **FW-015** | Add cold-boot branch to `power_optimization_flow.mmd` | Steady-state flowchart skips first power-on |
| **FW-016** | Regenerate flowchart PNGs and HTML | Diagrams must match shipped behavior |

### Verification and release

| Task | What | Why it matters |
|------|------|----------------|
| **FW-017** | OOB test: discharged 0.22 F supercap, indoor light, no user steps | Core product requirement |
| **FW-018** | Confirm BQ_EN raises vcap before first TX | Validates charge path |
| **FW-019** | Measure STOP3 sleep current vs energy budget | STOP3 is currently disabled |
| **FW-020** | `CONFIG_NODE_TX_SENSOR_BYPASS` must be 0 in release | Debug flag must not ship |

---

## Power state machine (FW-003)

```
COLD_START     MCU alive on small VSTOR cap; read vcap; read VBAT_OK if wired
CHARGE_ONLY    Assert BQ_EN; all sensor rails off; no LoRa TX; wake periodically to check vcap
READY          vcap >= VCAP_MIN_SENSORS_mV; allow sensor init
REPORT         Normal sensor + filter + TX cycle (see below)
TX_BLOCKED     vcap < VCAP_MIN_TX_mV; skip TX, stay low power until recovered
```

**Rules:**

1. First boot after factory reset requires **no customer action** — no “leave in sunlight” leaflet.
2. Do not enable STCC4, SGP30, or LoRa TX on an uncharacterized supercap.
3. Log state transitions on UART during bring-up.

Pin macros to add after schematic confirmation (FW-001, FW-002):

```c
#define CONFIG_BQ_EN_ENABLE        1
#define CONFIG_BQ_EN_GPIOX         GPIOA   /* confirm from schematic */
#define CONFIG_BQ_EN_PIN           GPIO_PIN_x
#define CONFIG_BQ_EN_ACTIVE_HIGH   1

#define CONFIG_VBAT_OK_ENABLE      1
#define CONFIG_VBAT_OK_GPIOX       GPIOA   /* confirm from schematic */
#define CONFIG_VBAT_OK_PIN         GPIO_PIN_x
#define CONFIG_VBAT_OK_ACTIVE_HIGH 1
```

---

## Sensor report sequence — steady state (FW-010 – FW-014)

Reference: [SolarSensorSchematicRev2_Sensors.html](SolarSensorSchematicRev2_Sensors.html) · [power_optimization_flow.mmd](power_optimization_flow.mmd)

| Step | Action |
|------|--------|
| 1 | RTC alarm — wake from STOP3 (300 s interval) |
| 2 | Radio sleep — `node_radio_quiesce_before_sensor_read()` |
| 3 | STCC4: `exit_sleep` + `measure_single_shot` (~510 ms total) |
| 4 | **While CO₂ converts:** SHT40 ~20 ms, SGP30 ~40 ms, BH1620 ~10 ms |
| 5 | STOP3 until CO₂ ready (~440 ms) — no busy-wait |
| 6 | STCC4: `read_measurement` + `enter_sleep_mode` |
| 7 | Push raw T, RH, TVOC, lux, CO₂ into ring buffers |
| 8 | Compute filtered mean (N default 5) — [averaging_n_samples_flow.mmd](averaging_n_samples_flow.mmd) |
| 9 | Pack 19-byte payload with **filtered** values + vcap |
| 10 | LoRa TX (~52 ms) **only if** vcap >= VCAP_MIN_TX_mV |
| 11 | Disable all sensor rails; STOP3 until next interval |

### First boot branch (FW-008, FW-015)

| Step | Action |
|------|--------|
| B1 | Enter CHARGE_ONLY — no LoRa TX, sensor rails off |
| B2 | Assert BQ_EN; wait until vcap >= VCAP_CHARGE_TARGET_mV |
| B3 | STCC4 power-on wait 1000 ms |
| B4 | First CO₂: single-shot (not continuous) |
| B5 | Run one full report cycle; N-filter may use partial mean until buffer fills |
| B6 | First TX only if vcap allows |

---

## STCC4 commands (FW-010)

Replace continuous mode in `stcc4.c`:

| Command | Hex |
|---------|-----|
| exit_sleep | 0x3650 |
| measure_single_shot | 0x219D |
| read_measurement | 0xEC05 |
| enter_sleep_mode | 0x3650 |

Remove `STCC4_CMD_START_CONTINUOUS` and `STCC4_MEASURE_WAIT_MS 5200`.

---

## Payload map (FW-014)

| Bytes | Field | Source |
|-------|-------|--------|
| 0–1 | Temperature | SHT40, filtered |
| 2–3 | RH | SHT40, filtered |
| 4–5 | TVOC | SGP30, filtered (0 if absent) |
| 6–9 | Lux | BH1620, filtered |
| 10–11 | vcap | ADC PA8 (raw mV OK) |
| 12–13 | CO₂ ppm | STCC4, filtered |

---

## GPIO map (existing)

| Function | GPIO |
|----------|------|
| CO₂_EN (STCC4) | PA5 |
| HUM_EN (SHT40) | PA6 |
| TVOC_EN (SGP30) | PA7 |
| VCAP ADC | PA8 |
| BH1620 ADC | PA11 |
| BH1620 EN | PA12 |
| I²C SCL / SDA | PA14 / PA15 |
| **BQ_EN** | **TBD — FW-001** |
| **VBAT_OK** | **TBD — FW-002** |

---

## Flowchart maintenance (FW-015, FW-016)

**Source files:**

- `Docs/power_optimization_flow.mmd` — report cycle + boot branch
- `Docs/averaging_n_samples_flow.mmd` — N-sample filter

**Regenerate:**

```bash
python Docs/build_energy_budget_sheet.py
python Docs/firmware_todo.py
```

**Optional PNG export** (if `mmdc` installed):

```bash
cd Docs
mmdc -i power_optimization_flow.mmd -o power_optimization_flow.png -b transparent
mmdc -i averaging_n_samples_flow.mmd -o averaging_n_samples_flow.png -b transparent
```

**Cold-boot branch to add** (FW-015):

```mermaid
BOOT([Cold boot / reset]) --> PCHK{vcap >= charge target?}
PCHK -->|No| CHG[Assert BQ_EN · rails off · STOP3 poll vcap]
CHG --> PCHK
PCHK -->|Yes| CO2BOOT[STCC4 1000 ms boot · first single-shot]
CO2BOOT --> A([RTC alarm / report due])
```

---

## Files to touch

| File | Tasks |
|------|-------|
| `lora_config.h` | FW-001, FW-002, FW-005, FW-020 |
| `power_manager.c` / `.h` (new) | FW-003, FW-004 |
| `stcc4.c` | FW-010 |
| `lora_driver.c` | FW-006 – FW-009, FW-011 – FW-014 |
| `adc_monitor.c` | FW-005, FW-006 |
| `Docs/power_optimization_flow.mmd` | FW-015 |
| `Docs/firmware_todo.py` | Update task status when done |

---

## Ship gate

All **P0** tasks (FW-001 – FW-008, FW-010 – FW-011, FW-013 – FW-014, FW-017 – FW-018) must be **Closed** in the TODO tracker before firmware is Rev2-ready.
