# Firmware Power Manager Design

This design turns the hybrid power requirements in `FIRMWARE_NEXT_STEPS.md` into a small firmware architecture that can be integrated into `lora_myself_net` in stages. The first implementation should protect the supercap and block early LoRa TX before optimizing sensor latency.

## Goals

- Do not run high-draw sensors or LoRa TX from a flat supercap.
- Use `ADC_MONITOR` as the primary storage-voltage decision input.
- Keep all gated sensor rails off until the power manager explicitly allows them.
- Preserve the current synchronous sensor driver style for the first pass.
- Make later improvements, such as CO2 asynchronous conversion and STOP3 during wait windows, easy to add.

## Non-Goals For First Pass

- Do not redesign the LoRa packet format.
- Do not change gateway parsing.
- Do not enter STOP3 during the STCC4 conversion wait until RTC wake timing is verified.
- Do not rely on unconfirmed hybrid-PCB pins. Keep those mappings isolated in `lora_config.h`.

## New Configuration

Add these board-level macros to `lora_config.h` after the existing ADC and sensor enable definitions.

```c
/* Supercap thresholds. Bench-tune before release. */
#define CONFIG_VCAP_MIN_SENSORS_MV       2700U
#define CONFIG_VCAP_MIN_TX_MV            3000U
#define CONFIG_VCAP_CHARGE_TARGET_MV     3600U

/* Hybrid power status inputs: fill in after PCB pin review. */
#define CONFIG_PWR_STATUS_ENABLE         0
#define CONFIG_VBAT_OK_GPIOX             GPIOA
#define CONFIG_VBAT_OK_PIN               GPIO_PIN_0
#define CONFIG_BAT_GD_GPIOX              GPIOA
#define CONFIG_BAT_GD_PIN                GPIO_PIN_0
#define CONFIG_PRIM_STATUS_GPIOX         GPIOA
#define CONFIG_PRIM_STATUS_PIN           GPIO_PIN_0
#define CONFIG_PRIM_STATUS_SW_GPIOX      GPIOA
#define CONFIG_PRIM_STATUS_SW_PIN        GPIO_PIN_0

/* Hybrid gated loads: fill in after PCB pin review. */
#define CONFIG_RADAR_ENABLE              0
#define CONFIG_RADAR_EN_GPIOX            GPIOA
#define CONFIG_RADAR_EN_PIN              GPIO_PIN_0
#define CONFIG_RADAR_EN_ACTIVE_HIGH      1

#define CONFIG_CO2_EN_ACTIVE_HIGH        1
```

The placeholder status pins must not be used while `CONFIG_PWR_STATUS_ENABLE` is `0`. This lets the firmware compile before the hybrid pin map is finalized.

## New Module

Create:

- `components/lora_driver/include/power_manager.h`
- `components/lora_driver/src/power_manager.c`

The existing Makefile already includes `components/lora_driver/src/*.c`, so the new source file will be picked up automatically.

### Public Types

```c
typedef enum {
    POWER_STATE_COLD_START = 0,
    POWER_STATE_CHARGE_ONLY,
    POWER_STATE_READY,
    POWER_STATE_REPORT,
    POWER_STATE_TX_BLOCKED
} power_state_t;

typedef struct {
    power_state_t state;
    uint16_t vcap_mv;
    bool adc_valid;
    bool sensors_allowed;
    bool tx_allowed;
    bool vbat_ok;
    bool bat_gd;
    bool prim_status;
    bool prim_status_sw;
} power_status_t;
```

### Public API

```c
void power_manager_init(void);
power_status_t power_manager_sample(void);
power_status_t power_manager_get_status(void);
bool power_manager_can_run_sensors(void);
bool power_manager_can_tx(void);
const char *power_manager_state_name(power_state_t state);
```

`power_manager_sample()` should be the only function that reads `ADC_MONITOR` and advances the state machine. The simple `can_*` helpers return the last sampled decision.

## State Machine

```text
COLD_START
  - Initial state after boot.
  - Read ADC_MONITOR.
  - If ADC invalid or vcap < CONFIG_VCAP_CHARGE_TARGET_MV: CHARGE_ONLY.
  - If vcap >= CONFIG_VCAP_CHARGE_TARGET_MV: READY.

CHARGE_ONLY
  - All gated sensor rails off.
  - No LoRa TX.
  - Periodically sample ADC_MONITOR.
  - If vcap >= CONFIG_VCAP_CHARGE_TARGET_MV: READY.

READY
  - Low-draw sensor work may run if vcap >= CONFIG_VCAP_MIN_SENSORS_MV.
  - Report cycle may be attempted.
  - When report starts: REPORT.

REPORT
  - Sensors may run while vcap >= CONFIG_VCAP_MIN_SENSORS_MV.
  - Before TX, sample ADC_MONITOR again.
  - If vcap >= CONFIG_VCAP_MIN_TX_MV: allow TX and return READY.
  - Else: TX_BLOCKED.

TX_BLOCKED
  - Sensor rails off.
  - TX deferred until next wake or timer tick.
  - If vcap >= CONFIG_VCAP_MIN_TX_MV: READY.
  - Else remain TX_BLOCKED or CHARGE_ONLY depending on vcap.
```

The state machine should be level-based, not delay-based. The firmware should not wait in a tight charge loop. It should sample, decide, sleep or idle, then retry on the next scheduled report wake.

## Rail Policy

First pass rail ownership stays inside each sensor driver, but entry into those drivers is blocked by the power manager.

| Load | Current owner | First-pass rule |
|------|---------------|-----------------|
| SHT40 / HUM_EN | `sht_sensor` / `sht40` | Read only if `sensors_allowed`, unless final hardware proves it is always-on and safe. |
| STCC4 CO2 | `stcc4.c` | Read only if `sensors_allowed`; driver must always power off on success or failure. |
| SGP30 TVOC | `sgp30.c` | Read only if `sensors_allowed`; update driver so init/read paths do not leave TVOC rail on. |
| BH1620 | `bh1620.c` | Read only if `sensors_allowed`; current read path already disables rail after sampling. |
| Radar | future driver | Read only if `sensors_allowed`; gate through `CONFIG_RADAR_EN_*`. |
| LoRa TX | `lora_driver.c` | TX only if `tx_allowed` immediately before `Radio.Send()`. |

Second pass can move common rail helpers into a `sensor_power.c` module if duplication grows.

## Integration In `lora_driver.c`

### Boot

After ADC init and before setting `node_report_due_immediately`, call:

```c
power_manager_init();
power_manager_sample();
```

Do not force a startup sensor report unconditionally. Instead, only request immediate report if:

```c
power_manager_can_run_sensors() && power_manager_can_tx()
```

Otherwise schedule the normal report timer and let the next wake re-check voltage.

### Report Entry

At the top of `node_send_sensor_report()`:

```c
power_status_t pwr = power_manager_sample();
if (!pwr.sensors_allowed) {
    printf("[PWR] %s skip sensors state=%s vcap=%umV\r\n", ...);
    node_schedule_next_report();
    return;
}
```

### Before TX

After sensor reads and packet packing, sample power again:

```c
pwr = power_manager_sample();
if (!pwr.tx_allowed) {
    printf("[PWR] %s defer TX state=%s vcap=%umV\r\n", ...);
    node_schedule_next_report();
    return;
}
```

Only call `Radio.Send()` after this check passes.

## First Implementation Order

1. Add threshold macros and placeholder hybrid pin macros in `lora_config.h`.
2. Add `power_manager.h/.c` with ADC-only decisions and status-input placeholders disabled by config.
3. Call the power manager during node boot.
4. Guard `node_send_sensor_report()` at entry and before TX.
5. Stop unconditional startup TX when voltage is below target.
6. Update `sgp30.c` so `TVOC_EN` is not left on after init/read failure.
7. Bench-test boot from discharged storage and tune thresholds.

This closes the highest-risk power tasks before touching packet filtering or async CO2 conversion.

## Second Implementation Order

1. Split STCC4 into start/wait/read APIs:

```c
bool stcc4_start_single_shot(void);
bool stcc4_read_single_shot(uint16_t *co2_ppm);
void stcc4_sleep_and_power_off(void);
```

2. Start STCC4 first, read fast sensors during its conversion window, then read CO2.
3. Add an N-sample ring buffer module for T/RH/vcap/CO2/TVOC/lux.
4. Use filtered values in the existing 19-byte payload.
5. Consider STOP3 during the remaining CO2 wait only after a TimerEvent wake is scheduled.

## Bench Checklist

- With storage at 0 V, firmware does not enable CO2, TVOC, BH1620, radar, or LoRa TX before threshold.
- First sensor report occurs only after `vcap >= CONFIG_VCAP_CHARGE_TARGET_MV`.
- Every TX checks `vcap >= CONFIG_VCAP_MIN_TX_MV` immediately before `Radio.Send()`.
- Failed sensor reads leave rails off.
- STOP3 wake still occurs on the report interval.
- Release build has `CONFIG_NODE_TX_SENSOR_BYPASS == 0`.
