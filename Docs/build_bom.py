#!/usr/bin/env python3
"""Regenerate BOM CSV, HTML, and xlsx from shared row data."""

from __future__ import annotations

import csv
import html
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.styles import Font

from firmware_todo import docs_nav

DOCS = Path(__file__).resolve().parent
CSV_PATH = DOCS / "SolarSensorSchematicRev2_BOM.csv"
HTML_PATH = DOCS / "SolarSensorSchematicRev2_BOM.html"
XLSX_PATH = DOCS / "SolarSensorSchematicRev2_BOM.xlsx"

HEADERS = [
    "Item",
    "Reference Designators",
    "Qty",
    "Value",
    "Footprint",
    "Description",
    "Manufacturer",
    "MPN",
    "Notes",
    "Datasheet",
]

# Item number -> local PDF under Docs/datasheets/
DATASHEET_BY_ITEM = {
    1: "RA-08.pdf",
    2: "BQ25505.pdf",
    3: "TPS613221A.pdf",
    4: "SGM2019-1.8.pdf",
    5: "SHT40.pdf",
    6: "SGP30.pdf",
    7: "STCC4.pdf",
    8: "BH1620FVC.pdf",
    28: "SI2303CDS.pdf",
    29: "DMG3402L-7.pdf",
    30: "MMBT2222A.pdf",
}

ROWS = [
    (1, "MOD1", 1, "Ra-08", "Module", "LoRaWAN module ASR6601", "Ai-Thinker", "RA-08", "Main radio/MCU module"),
    (2, "U2", 1, "BQ25505", "QFN-24", "Energy harvester PMIC", "Texas Instruments", "BQ25505", "MPPT solar charger"),
    (3, "U1", 1, "TPS613221A", "SOT-23-5", "Boost converter 3.3V", "Texas Instruments", "TPS613221A", "Output for RA-08 VCC"),
    (4, "U4", 1, "SGM2019-1.8YN5G/TR", "SOT-23-5", "1.8V LDO regulator", "SG Micro", "SGM2019-1.8YN5G/TR", "Sensor 1.8V rail"),
    (5, "U5;U7", 2, "SHT40", "DFN-4", "Temperature/humidity sensor", "Sensirion", "SHT40-AD1B-R2", "Two footprints on schematic — populate one unless intentional"),
    (6, "U3", 1, "SGP30-2.5K", "DIL-6", "TVOC/eCO2 sensor", "Sensirion", "SGP30-2.5K", "Optional TVOC section"),
    (7, "U6", 1, "STCC4_CO2_SENSOR", "Custom", "CO2 sensor module", "Sensirion", "SCD41 or per STCC4 footprint", "Verify exact CO2 part against library/footprint"),
    (8, "U8", 1, "GC2", "Custom", "Light sensor", "—", "GC2", "Schematic lists GC2; firmware targets BH1620FVC"),
    (9, "L2", 1, "22uH 1A", "Inductor", "Boost inductor for BQ25505", "—", "22uH 1A min", "Harvesting boost"),
    (10, "L1", 1, "4.7uH", "Inductor", "Boost inductor for TPS613221A", "—", "4.7uH", "Step-up converter"),
    (11, "C3", 1, "0.22F 5.5V", "Horizontal supercap", "Supercapacitor storage", "—", "0.22F 5.5V", "Also J2/J9 for external cap"),
    (12, "C6", 1, "22uF 25V X5R", "0805", "Bulk cap RA-08 supply", "—", "22uF 25V 0805 X5R", ""),
    (13, "C7", 1, "10uF 25V", "—", "Bulk cap", "—", "10uF 25V", ""),
    (14, "C18", 1, "10uF 16V", "0603", "Decoupling", "—", "10uF 16V 0603", ""),
    (15, "C2;C5", 2, "4.7uF 50V", "0805", "Power decoupling", "—", "4.7uF 50V 0805", ""),
    (16, "C9;C17", 2, "1uF 50V", "0603", "Decoupling", "—", "1uF 50V 0603", ""),
    (17, "C8;C11;C12;C13;C14;C15;C16", 7, "0.1uF 50V", "0603", "Decoupling", "—", "0.1uF 50V 0603", ""),
    (18, "C1", 1, "0.01uF 50V", "0805", "HF decoupling", "—", "0.01uF 50V 0805", ""),
    (19, "C10", 1, "0.01uF 50V", "0603", "HF decoupling", "—", "0.01uF 50V 0603", ""),
    (20, "C4", 1, "10nF", "0805", "Filter/decoupling", "—", "10nF 0805", ""),
    (21, "R1;R2;R3;R4;R5;R6;R7;R10;R11;R12;R13;R14;R15;R16;R18;R19;R21;R22;R24;R25", 20, "10K", "0603", "Resistor", "—", "10K 0603", ""),
    (22, "R8;R9", 2, "2K", "0603", "Resistor", "—", "2K 0603", ""),
    (23, "R17;R20;R23;R26", 4, "5.1K", "0603", "I2C pull-up / bias", "—", "5.1K 0603", ""),
    (24, "ROV1;ROK1", 2, "5.62M", "0805", "BQ25505 divider resistor", "—", "5.62M 0805", "Rev2 OVP network; hybrid 3.8V LIC: ROV1=4.02M — see BQ25505_DESIGN_INPUTS.md"),
    (25, "ROK2", 1, "5.49M", "0805", "BQ25505 divider resistor", "—", "5.49M 0805", ""),
    (26, "ROV2", 1, "7.32M", "0805", "BQ25505 OV resistor", "—", "7.32M 0805", "Rev2 OVP network; hybrid 3.8V LIC: ROV2=4.42M"),
    (27, "ROK3", 1, "1.87M", "0805", "BQ25505 OK resistor", "—", "1.87M 0805", ""),
    (28, "Q1;Q2;Q3;Q4;Q7;Q8;Q10;Q12;Q14;Q16", 10, "SI2303CDS", "SOT-23", "N-channel MOSFET", "Vishay/SI", "SI2303CDS", "Sensor/load switches"),
    (29, "Q5;Q6", 2, "DMG3402L-7", "SOT-23", "P-channel MOSFET", "Diodes Inc", "DMG3402L-7", "Power path switching"),
    (30, "Q11;Q13;Q15;Q17", 4, "MMBT2222A", "SOT-23", "NPN transistor", "—", "MMBT2222A", "Low-side / enable drivers"),
    (31, "J1", 1, "Header 2-pin 2.54mm XH 180", "Solar connector", "Solar panel input", "—", "2.54mm XH 180", "Solar mounting hole nearby"),
    (32, "J2;J9", 2, "Header 2-pin 2.54mm XH 180", "Connector", "Big capacitor connection", "—", "2.54mm XH 180", ""),
    (33, "J8", 1, "Header 2-pin 2.54mm XH 180", "Connector", "Rechargeable battery", "—", "2.54mm XH 180", ""),
    (34, "J3;J5", 2, "Header 2-pin 2.54mm 180", "Connector", "FW load strap headers", "—", "2.54mm 180", "Short during firmware programming"),
    (35, "J4;J7", 2, "Header 4-pin 2.54mm 180", "Connector", "Debug/firmware UART", "—", "2.54mm 180", "J4 noted as firmware connector"),
    (36, "—", 1, "Solar panel", "External", "Photovoltaic source", "—", "User-selected", "Connect via J1; size for load/region"),
    (37, "—", 1, "Rechargeable battery", "External", "NiMH/Li-ion etc", "—", "User-selected", "Connect via J8; optional if supercap only"),
    (38, "—", 1, "Antenna", "External", "LoRa antenna 868/915 MHz", "—", "User-selected", "Connect to MOD1 ANT"),
    (39, "—", 1, "PCB", "A2", "Printed circuit board", "—", "SolarSensor Rev2", "Feb 2026 core design"),
]


def datasheet_path(item: int) -> str:
    name = DATASHEET_BY_ITEM.get(item)
    if not name:
        return ""
    path = DOCS / "datasheets" / name
    return f"datasheets/{name}" if path.is_file() else ""


def build_table_rows() -> list[list[str]]:
    rows = []
    for row in ROWS:
        item = row[0]
        ds = datasheet_path(item)
        rows.append([str(v) for v in row] + [ds])
    return rows


def write_csv(rows: list[list[str]]) -> None:
    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Solar Sensor Schematic Rev2 - Bill of Materials"] + [""] * (len(HEADERS) - 1))
        writer.writerow(HEADERS)
        writer.writerows(rows)


def write_html(rows: list[list[str]]) -> None:
    body_rows = []
    for i, row in enumerate(rows):
        cls = "odd" if i % 2 == 0 else "even"
        cells = "".join(f"<td>{html.escape(c)}</td>" for c in row[:-1])
        ds = row[-1]
        if ds:
            href = html.escape(ds, quote=True)
            label = html.escape(Path(ds).name)
            ds_cell = f'<td><a href="{href}" target="_blank" rel="noopener">{label}</a></td>'
        else:
            ds_cell = "<td></td>"
        body_rows.append(f'        <tr class="{cls}">{cells}{ds_cell}</tr>')

    content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Solar Sensor Schematic Rev2 - Bill of Materials</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: Arial, sans-serif; background: #f5f5f5; color: #222; }}
    .wrap {{ padding: 16px; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: #fff;
      box-shadow: 0 1px 4px rgba(0, 0, 0, 0.12);
    }}
    th, td {{
      border: 1px solid #d9d9d9;
      padding: 8px 10px;
      text-align: left;
      vertical-align: top;
      font-size: 14px;
    }}
    thead {{
      position: sticky;
      top: 0;
      z-index: 10;
    }}
    tr.title th {{
      background: #1f3864;
      color: #fff;
      font-size: 18px;
      font-weight: bold;
      text-align: center;
      padding: 14px 10px;
    }}
    tr.header th {{
      background: #1f3864;
      color: #fff;
      font-weight: bold;
      text-align: center;
    }}
    tr.odd td {{ background: #fff; }}
    tr.even td {{ background: #f2f2f2; }}
    td:first-child, th:first-child {{ text-align: center; white-space: nowrap; }}
    td:last-child, th:last-child {{ text-align: center; white-space: nowrap; }}
    td a {{ color: #1f3864; font-weight: bold; text-decoration: none; }}
    td a:hover {{ text-decoration: underline; }}
    nav {{
      display: flex;
      gap: 8px;
      margin-bottom: 16px;
      flex-wrap: wrap;
    }}
    nav a {{
      padding: 8px 14px;
      background: #fff;
      border: 1px solid #d9d9d9;
      border-radius: 4px;
      color: #1f3864;
      text-decoration: none;
      font-size: 14px;
      font-weight: bold;
    }}
    nav a.active {{
      background: #1f3864;
      color: #fff;
      border-color: #1f3864;
    }}
    nav a:hover:not(.active) {{ background: #eef2f8; }}
    .legacy {{ background: #fff8e6; border-left: 4px solid #e69138; padding: 10px 14px; margin-bottom: 16px;
      font-size: 13px; line-height: 1.5; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }}
  </style>
</head>
<body>
  <div class="wrap">
    {docs_nav("SolarSensorSchematicRev2_BOM.html")}
    <div class="legacy"><strong>Rev2 PCB BOM.</strong> System architecture reference:
    <a href="SolarSensorSchematicRev2_BlockDiagram.html">Hybrid block diagram</a> (RAK3172 · 100 F · TPS61291).</div>
    <table>
      <thead>
        <tr class="title"><th colspan="{len(HEADERS)}">Solar Sensor Schematic Rev2 - Bill of Materials</th></tr>
        <tr class="header">{"".join(f"<th>{html.escape(h)}</th>" for h in HEADERS)}</tr>
      </thead>
      <tbody>
{chr(10).join(body_rows)}
      </tbody>
    </table>
  </div>
</body>
</html>
"""
    content = content.replace('<motion class="wrap">', '<motion class="wrap">'.replace("motion", "motion"))
    content = content.replace('<motion class="wrap">', '<motion class="wrap">')
    # fix typo
    content = content.replace('<motion class="wrap">', '<div class="wrap">')
    HTML_PATH.write_text(content, encoding="utf-8")


def write_xlsx(rows: list[list[str]]) -> None:
    wb = load_workbook(XLSX_PATH)
    ws = wb["BOM"]
    link_font = Font(color="0563C1", underline="single")

    # Clear old BOM body (keep title row 1 if present)
    if ws.max_row >= 2:
        ws.delete_rows(2, ws.max_row - 1)

    ws.append(HEADERS)
    for row in rows:
        ds = row[-1]
        values = row[:-1]
        ws.append(values)
        if ds:
            cell = ws.cell(row=ws.max_row, column=len(HEADERS))
            cell.value = Path(ds).name
            cell.hyperlink = ds
            cell.font = link_font

    wb.save(XLSX_PATH)


def main() -> None:
    rows = build_table_rows()
    missing = [item for item, name in DATASHEET_BY_ITEM.items() if not (DOCS / "datasheets" / name).is_file()]
    if missing:
        raise SystemExit(f"Missing datasheet PDFs for items: {missing}")
    write_csv(rows)
    write_html(rows)
    write_xlsx(rows)
    linked = sum(1 for r in rows if r[-1])
    print(f"Wrote {CSV_PATH.name}, {HTML_PATH.name}, BOM sheet in {XLSX_PATH.name} ({linked} datasheet links)")


if __name__ == "__main__":
    main()
