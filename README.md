# Solar-Powered LoRa Sensor

Solar-powered LoRa sensor nodes with hybrid energy harvesting (BQ25505), supercap storage, and gated sensor loads.

## Documentation

Open locally:

```powershell
python -m http.server 8877 --bind 127.0.0.1 --directory Docs
```

| Page | Description |
|------|-------------|
| [Block Diagram](Docs/SolarSensorSchematicRev2_BlockDiagram.html) | **Hybrid power & control** (authoritative architecture) |
| [Firmware TODO](Docs/SolarSensorSchematicRev2_TODO.html) | Numbered firmware backlog FW-001–FW-020 |
| [BOM](Docs/SolarSensorSchematicRev2_BOM.html) | Rev2 PCB bill of materials |
| [Sensors](Docs/SolarSensorSchematicRev2_Sensors.html) | Rev2 sensor timing & flowcharts |
| [Energy Budget](Docs/SolarSensorSchematicRev2_EnergyBudget.html) | Rev2 power budget worksheet |

Regenerate:

```powershell
python Docs/build_block_diagram.py
python Docs/build_bom.py
python Docs/build_energy_budget_sheet.py
python Docs/firmware_todo.py
```

Markdown: `Docs/POWER_SYSTEM_ANALYSIS.md`, `Docs/FIRMWARE_NEXT_STEPS.md`

---

## Legacy firmware (RA-08 / Rev2 PCB)

This project demonstrates solar-powered RA-08 sensor nodes using either SHT3x or SHT40 sensors.  
Each node samples temperature and humidity, then reports the data to an RA-08 gateway over LoRa.

The gateway supports AT commands over UART for management functions such as node discovery.

## Key Features

- Compile-time selectable sensor: **SHT3x** or **SHT40**
- Node auto-join using **JOIN / ASSIGN**
- Persistent node address storage in flash
- Gateway AT command for discovery:
  - `AT+FIND=<addr>[,<duration_secs>]`
- Node identification support:
  - nodes blink to identify themselves
  - nodes send ACK for both start and finish of identification
- Periodic sensor reporting
- Sensor read failure handling:
  - node sends `0/0` if sensor reading fails

## Hardware

### Node
- RA-08 (ASR6601)
- SHT3x or SHT40 sensor
- Solar panel
- Power management circuit
- Battery or supercapacitor recommended

### Gateway
- RA-08 development board
- UART connection to host device (PC or MCU)

## Quick Start

### Build Environment
Recommended build environment:

- **WSL**
- **Ubuntu**

```bash
cd /mnt/d/work/Ai-Thinker-LoRaWAN-Ra-08
source build/envsetup.sh
make -j32 projects/ASR6601CB-EVAL/examples/lora/lora_myself_net
```

Select SHT40 at compile time:

```bash
make CFLAGS+=" -DSHT_SENSOR_TYPE=40"
```

Flash firmware using `TremoProgrammer_v0.8.exe` as described in the project README.

## Protocol / Commands

### AT Command (to gateway UART)

```text
AT+FIND=<addr>[,<duration_secs>]\r\n
# Example:
AT+FIND=1,5
```

### LoRa FIND Packet (gateway -> node)

```text
A0 F9 <addr> <duration> <cs> A1
```

- `cs = (F9 + addr + duration) & 0xFF`

### FIND ACK (node -> gateway)

```text
A0 FA <addr> <status> <cs> A1
```

- `status: 0x01 = started, 0x02 = finished`
- `cs = (FA + addr + status) & 0xFF`

## Solar Deployment Notes

- Estimate peak transmit current and size battery/supercap to cover LoRa TX bursts.
- Use low-power sleep modes and sensible reporting intervals to maximize uptime.
- Include undervoltage protection and a charging controller for reliable operation.
- Consider energy budgeting (duty cycle, transmit power, reporting interval) and use RTC wake when possible.