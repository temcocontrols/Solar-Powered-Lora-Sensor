#!/usr/bin/env python3
"""Regenerate block diagram HTML and mermaid source from hybrid design data."""

from __future__ import annotations

import html as html_mod
from pathlib import Path

from firmware_todo import docs_nav

DOCS = Path(__file__).resolve().parent
HTML_PATH = DOCS / "SolarSensorSchematicRev2_BlockDiagram.html"
MMD_PATH = DOCS / "schematic_block_diagram.mmd"
PNG_PATH = DOCS / "schematic_block_diagram.png"
DIAGRAM_IMAGE = "pics/BlockDiagram.jpg"

TITLE = "Solar Sensor — Hybrid Power & Control System"
SUBTITLE = "Block diagram (authoritative)"

NOTE = (
    "Functional view of the <strong>hybrid harvest + storage</strong> architecture: "
    "BQ25505 MPPT, LIC supercap path, ideal-diode OR, TPS61291 boost to 3.3 V, "
    "and RAK3172-controlled P-FET sensor gating. "
    "Legacy Rev2 PCB detail (RA-08, 0.22 F, TPS613221A) remains in "
    "<a href=\"SolarSensorSchematicRev2.pdf\">SolarSensorSchematicRev2.pdf</a> and the BOM until the next PCB spin."
)

SECTIONS = [
    (
        "Harvesting",
        ["Block", "Component", "Role", "Notes"],
        [
            ("Solar input", "60×60 mm panel", "Energy source", "Feeds BQ25505 VIN_DC"),
            ("Harvester", "BQ25505", "Cold start + MPPT charger", "VOC_SAMP, V_OV_SET, V_OK_SET, V_OK_HYST via divider network"),
            ("Path logic", "Ideal diode OR", "LIC vs primary routing", "Deadlock-proof charging via controlled LIC MOS switch"),
            ("Status", "VBAT_OK", "Storage OK flag", "Digital input to RAK3172"),
            ("Status", "BAT_GD", "Battery / path good", "Digital input to RAK3172"),
        ],
    ),
    (
        "Storage",
        ["Block", "Component", "Role", "Notes"],
        [
            ("LIC path", "100 F · 3.8 V supercap", "Main energy store", "LIC PATH from harvester; digital status outputs"),
            ("Monitor", "R10 / R11 divider", "ADC_MONITOR", "Supercap voltage sense into MCU ADC"),
            ("Hold-up", "C_STOR (boost input)", "Local bulk", "At boost input / system rail origin"),
        ],
    ),
    (
        "Power delivery",
        ["Block", "Component", "Role", "Notes"],
        [
            ("Boost", "TPS61291", "Step-up regulator", "Raises storage voltage to system rail"),
            ("Rail", "SYSTEM_RAIL 3.3 V", "MCU + always-on loads", "Powers RAK3172 and SHT41"),
        ],
    ),
    (
        "Sensing & control",
        ["Block", "Component", "Interface", "Notes"],
        [
            ("MCU / radio", "RAK3172 LoRa module", "LoRaWAN", "Monitors PRIM_STATUS_SW, BAT_GD, VBAT_OK, PRIM_STATUS, ADC_MONITOR"),
            ("Temp / RH", "SHT41", "I²C · always on", "On SYSTEM_RAIL 3.3 V — low standby"),
            ("Radar", "HLK-LD2410 mmWave", "GPIO_RADAR → P-FET", "Si2301 high-side gate; power-gated high-draw sensor"),
            ("CO₂", "CO₂ sensor", "GPIO_CO2 → P-FET", "Si2301 high-side gate; power-gated high-draw sensor"),
        ],
    ),
]

MCU_SIGNALS = [
    ("PRIM_STATUS_SW", "Input", "Primary-path switch status", "Hybrid path selection feedback"),
    ("BAT_GD", "Input", "Battery / storage good", "From BQ25505 power-path logic"),
    ("VBAT_OK", "Input", "OK threshold met", "Harvester OK output"),
    ("PRIM_STATUS", "Input", "Primary storage status", "Path / storage state"),
    ("ADC_MONITOR", "Input (ADC)", "Supercap voltage", "Via R10/R11 divider — firmware threshold gating"),
    ("GPIO_RADAR", "Output", "Radar P-FET gate", "Enable HLK-LD2410 rail (Si2301)"),
    ("GPIO_CO2", "Output", "CO₂ P-FET gate", "Enable CO₂ sensor rail (Si2301)"),
]

DESIGN_NOTES = [
    "BQ25505 uses internal logic for autonomous power-path management and deadlock prevention.",
    "P-FET (Si2301) power gates are used for high-draw sensors; SHT41 stays on the 3.3 V rail.",
    "Firmware must read ADC_MONITOR and status inputs before enabling radar / CO₂ or LoRa TX.",
    "No customer pre-charge or install procedure — cold-start + charge-wait is a firmware requirement.",
]

MERMAID = """flowchart TB
    subgraph HARVEST["Harvesting"]
        SOLAR["Solar panel<br/>60×60 mm"]
        BQ["BQ25505<br/>Cold start · MPPT"]
        OR["Ideal diode OR<br/>LIC / Primary paths"]
    end

    subgraph STORE["Storage"]
        SCAP["100 F · 3.8 V supercap<br/>LIC PATH"]
        DIV["R10/R11 divider<br/>ADC_MONITOR"]
    end

    subgraph DELIV["Power delivery"]
        BOOST["TPS61291 boost"]
        RAIL["SYSTEM_RAIL 3.3 V<br/>C_STOR"]
    end

    subgraph CTRL["Sensing & control"]
        MCU["RAK3172 LoRa MCU"]
        SHT["SHT41<br/>always on"]
        RAD["HLK-LD2410 radar<br/>P-FET gated"]
        CO2["CO₂ sensor<br/>P-FET gated"]
    end

    SOLAR --> BQ
    BQ --> OR
    OR --> SCAP
    SCAP --> BOOST
    BOOST --> RAIL
    RAIL --> MCU
    RAIL --> SHT
    MCU -->|"GPIO_RADAR"| RAD
    MCU -->|"GPIO_CO2"| CO2
    DIV --> MCU
    BQ -->|"VBAT_OK · BAT_GD"| MCU

    style MCU fill:#1f3864,color:#fff
    style BQ fill:#d9ead3,color:#000
    style SCAP fill:#cfe2f3,color:#000
    style BOOST fill:#fff2cc,color:#000
    style SHT fill:#d9d2e9,color:#000
"""

CSS = """
    * { box-sizing: border-box; }
    body { margin: 0; font-family: Arial, sans-serif; background: #f5f5f5; color: #222; }
    .wrap { padding: 16px; max-width: 1400px; margin: 0 auto; }
    nav { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }
    nav a { padding: 8px 14px; background: #fff; border: 1px solid #d9d9d9; border-radius: 4px;
      color: #1f3864; text-decoration: none; font-size: 14px; font-weight: bold; }
    nav a.active { background: #1f3864; color: #fff; border-color: #1f3864; }
    nav a:hover:not(.active) { background: #eef2f8; }
    .note { background: #fff; border-left: 4px solid #1f3864; padding: 12px 14px; margin-bottom: 16px;
      font-size: 14px; line-height: 1.55; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
    .legacy { background: #fff8e6; border-left: 4px solid #e69138; padding: 10px 14px; margin-bottom: 16px;
      font-size: 13px; line-height: 1.5; }
    h2 { font-size: 16px; color: #1f3864; margin: 24px 0 12px; }
    .diagram-panel { background: #fff; border: 1px solid #d9d9d9; box-shadow: 0 1px 4px rgba(0,0,0,0.12);
      padding: 16px; margin-bottom: 16px; overflow-x: auto; text-align: center; }
    .diagram-panel img { max-width: 100%; height: auto; border: 1px solid #eee; }
    .diagram-caption { font-size: 13px; color: #555; margin-top: 10px; text-align: left; }
    table { width: 100%; border-collapse: collapse; background: #fff;
      box-shadow: 0 1px 4px rgba(0,0,0,0.12); margin-bottom: 16px; }
    th, td { border: 1px solid #d9d9d9; padding: 8px 10px; text-align: left; vertical-align: top; font-size: 14px; }
    tr.title th { background: #1f3864; color: #fff; font-size: 18px; font-weight: bold; text-align: center; padding: 14px 10px; }
    tr.header th { background: #1f3864; color: #fff; font-weight: bold; text-align: center; }
    tr.odd td { background: #fff; }
    tr.even td { background: #f2f2f2; }
  td.center { text-align: center; }
    ul.notes { font-size: 14px; line-height: 1.6; background: #fff; padding: 12px 12px 12px 28px;
      border: 1px solid #d9d9d9; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
    .footnote { font-size: 12px; color: #555; line-height: 1.6; }
"""


def table_html(section_title: str, headers: list[str], rows: list[tuple[str, ...]]) -> str:
    out = [
        f'<table><thead><tr class="title"><th colspan="{len(headers)}">{html_mod.escape(section_title)}</th></tr>',
        '<tr class="header">' + "".join(f"<th>{html_mod.escape(h)}</th>" for h in headers) + "</tr></thead><tbody>",
    ]
    for i, row in enumerate(rows):
        cls = "odd" if i % 2 == 0 else "even"
        cells = "".join(f"<td>{html_mod.escape(c)}</td>" for c in row)
        out.append(f'<tr class="{cls}">{cells}</tr>')
    out.append("</tbody></table>")
    return "\n".join(out)


def write_mmd() -> None:
    MMD_PATH.write_text(MERMAID.strip() + "\n", encoding="utf-8")


def write_html() -> None:
    section_tables = "\n".join(table_html(title, headers, rows) for title, headers, rows in SECTIONS)

    mcu_rows = []
    for i, row in enumerate(MCU_SIGNALS):
        cls = "odd" if i % 2 == 0 else "even"
        mcu_rows.append(
            f'<tr class="{cls}"><td>{html_mod.escape(row[0])}</td><td class="center">'
            f'{html_mod.escape(row[1])}</td><td>{html_mod.escape(row[2])}</td><td>{html_mod.escape(row[3])}</td></tr>'
        )

    notes_li = "".join(f"<li>{html_mod.escape(n)}</li>" for n in DESIGN_NOTES)

    content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html_mod.escape(TITLE)}</title>
  <style>{CSS}</style>
</head>
<body>
  <div class="wrap">
    {docs_nav("SolarSensorSchematicRev2_BlockDiagram.html")}
    <div class="note">{NOTE}</div>
    <div class="legacy">
      <strong>Rev2 PCB docs (BOM, Sensors, Energy Budget)</strong> still describe the earlier RA-08 / 0.22 F / TPS613221A board.
      Use this page as the system architecture reference until those sheets are regenerated for the hybrid spin.
    </div>

    <h2>{html_mod.escape(SUBTITLE)}</h2>
    <div class="diagram-panel">
      <img src="{html_mod.escape(DIAGRAM_IMAGE)}" alt="{html_mod.escape(TITLE)}" width="1200">
      <p class="diagram-caption">Source image: <code>{html_mod.escape(DIAGRAM_IMAGE)}</code>.
        Simplified flow: <code>schematic_block_diagram.mmd</code>.</p>
    </div>

    {section_tables}

    <h2>RAK3172 signal map</h2>
    <table>
      <thead>
        <tr class="title"><th colspan="4">MCU interfaces (from block diagram)</th></tr>
        <tr class="header"><th>Signal</th><th>Direction</th><th>Function</th><th>Notes</th></tr>
      </thead>
      <tbody>
        {"".join(mcu_rows)}
      </tbody>
    </table>

    <h2>Design notes</h2>
    <ul class="notes">{notes_li}</ul>

    <p class="footnote">
      Regenerate: <code>python Docs/build_block_diagram.py</code>.
      Power analysis: <a href="POWER_SYSTEM_ANALYSIS.md">POWER_SYSTEM_ANALYSIS.md</a>.
      Firmware backlog: <a href="SolarSensorSchematicRev2_TODO.html">Firmware TODO</a>.
    </p>
  </motion>
</body>
</html>"""
    content = content.replace("<motion ", "<motion ").replace("<motion ", "<motion ")
    content = content.replace("<motion class=", "<div class=").replace("</motion>", "</motion>")
    content = content.replace("</motion>", "</motion>")
    content = content.replace("</motion>", "</div>")
    HTML_PATH.write_text(content, encoding="utf-8")


def main() -> None:
    write_mmd()
    write_html()
    print(f"Wrote {HTML_PATH.name}, {MMD_PATH.name}")
    if not (DOCS / DIAGRAM_IMAGE).is_file():
        print(f"WARNING: missing {DIAGRAM_IMAGE}")


if __name__ == "__main__":
    main()
