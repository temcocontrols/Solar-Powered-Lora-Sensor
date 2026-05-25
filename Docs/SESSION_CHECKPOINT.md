# Session checkpoint — 2026-05-24

Save point before Cursor restart. Pick up from here.

---

## Installed this session

| Tool | Version | Notes |
|------|---------|-------|
| Typst | 0.14.2 | `winget install Typst.Typst` |
| typstyle | 0.14.4 | Formatter — `typstyle file.typ` |
| tinymist | 0.14.18 | CLI + LSP — `tinymist preview file.typ` |
| Tinymist extension | 0.14.18 | `myriad-dreamin.tinymist` in Cursor |

Workspace config:
- `.vscode/extensions.json` — recommends Tinymist
- `.vscode/settings.json` — format-on-save for `.typ`, typstyle formatter, preview on type

After restart: **Ctrl+Shift+P → Developer: Reload Window**, then verify:

```powershell
typst --version
typstyle --version
tinymist --version
```

---

## Docs server

Local HTTP server (may need restart after reboot):

```powershell
python -m http.server 8877 --bind 127.0.0.1 --directory "D:\XDrive\Solar-Powered-Lora-Sensor\Docs"
```

| Page | URL |
|------|-----|
| BOM | http://127.0.0.1:8877/SolarSensorSchematicRev2_BOM.html |
| Block diagram | http://127.0.0.1:8877/SolarSensorSchematicRev2_BlockDiagram.html |
| Sensors | http://127.0.0.1:8877/SolarSensorSchematicRev2_Sensors.html |
| Energy budget | http://127.0.0.1:8877/SolarSensorSchematicRev2_EnergyBudget.html |
| **Firmware TODO** | http://127.0.0.1:8877/SolarSensorSchematicRev2_TODO.html |
| Spreadsheet | `Docs/SolarSensorSchematicRev2_BOM.xlsx` |

Regenerate docs:

```powershell
cd D:\XDrive\Solar-Powered-Lora-Sensor\Docs
python firmware_todo.py
python build_energy_budget_sheet.py
python build_bom.py
```

---

## Firmware backlog (authoritative)

**20 tasks: FW-001 – FW-020** (all Open)

| Source | Path |
|--------|------|
| Single source of truth | `Docs/firmware_todo.py` |
| HTML | `Docs/SolarSensorSchematicRev2_TODO.html` |
| Spreadsheet tab | **Firmware TODO** in xlsx |
| Markdown detail | `Docs/FIRMWARE_NEXT_STEPS.md` |
| Hardware context | `Docs/POWER_SYSTEM_ANALYSIS.md` |

**P0 ship blockers:** FW-001 – FW-008, FW-010 – FW-011, FW-013 – FW-014, FW-017 – FW-018

**Key gap:** Schematic has BQ_EN / VBAT_OK / 0.22 F supercap; firmware only reads vcap for telemetry — no power state machine, no TX gating, STCC4 still continuous mode, STOP3 disabled.

**GPIO TBD:** BQ_EN and VBAT_OK → RA-08 pin numbers not yet in `lora_config.h`.

Firmware tree: `projects/ASR6601CB-EVAL/examples/lora/lora_myself_net/`

---

## Incomplete from earlier message (do next)

User asked for UI fixes on grouped/tabbed TODO or spreadsheet view — **not finished**:

1. **Tab1:** Auto-hide expand arrow on first display (currently requires manual select)
2. **Tab2:** Indent child tables
3. **Tab3:** Hide expand control when row has no children

Likely targets: Excel **Firmware TODO** sheet grouping, or a future HTML accordion — search transcript / `firmware_todo.py` when resuming.

---

## Optional next steps

- [ ] Map BQ_EN / VBAT_OK GPIO from schematic → `lora_config.h`
- [ ] Implement power manager state machine in firmware
- [ ] Add cold-boot branch to `Docs/power_optimization_flow.mmd`
- [ ] Starter `Docs/report.typ` for PDF export of BOM / TODO via Typst
- [ ] Fix Tab1/Tab2/Tab3 UI items above

---

## Git status note

Untracked at session start included `Docs/SolarSensorSchematicRev2*.pdf/csv/html/xlsx`, workspace file. No commits made unless user requested later.
