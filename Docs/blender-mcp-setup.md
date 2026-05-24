# Blender MCP setup (Windows) — SolarSensor

Reference: [Blender MCP Server](https://www.blender.org/lab/mcp-server/) · [Video walkthrough](https://youtu.be/xBLGsYLwgks)

## 1. Install Blender 5.1+

Download from [blender.org](https://www.blender.org/download/). Add Blender to PATH optional; MCP uses the running GUI instance.

## 2. Install the MCP add-on in Blender

1. Open Blender → **Edit → Preferences → Get Extensions** (or drag-and-drop from the lab page).
2. Install **MCP** from Blender Lab (may require adding the Lab repo first, then installing the add-on twice per official instructions).
3. **Edit → Preferences → Add-ons** → search `MCP` → enable.
4. Start MCP server (**localhost:9876**). Enable **auto start** if available.

## 3. Install the MCP server package

The video uses `uvx blender-mcp`. On Windows without `uv`:

```powershell
pip install uv
uv tool install blender-mcp
```

Or run once via:

```powershell
pip install blender-mcp
python -m blender_mcp
```

(Exact module name may match the [blender_mcp release](https://projects.blender.org/lab/blender_mcp) — follow lab wiki if the package name differs.)

## 4. Connect Claude Desktop (optional)

**Settings → Connectors → Blender** (browse connectors), or edit developer config:

```json
{
  "mcpServers": {
    "blender": {
      "command": "uvx",
      "args": ["blender-mcp"]
    }
  }
}
```

[Claude Desktop quickstart](https://code.claude.com/docs/en/desktop-quickstart)

## 5. Connect Cursor

Add the same `blender` MCP server in Cursor MCP settings (command + args as above). Blender must be open with MCP server running before prompting.

## 6. Smoke test

In the MCP client:

> Delete the default cube in the current Blender file.

If the cube disappears, the loop works.

## 7. SolarSensor-specific tips

- **Reference images:** Import `Docs/T3E-Nano_*.png` and `Docs/image-removebg-preview.png` as background or texture references for scale and branding.
- **Datasheet numbers:** Paste specs from `Docs/SECONDGEN.pdf` or `Docs/pdf_extract.txt` into prompts (ranges, gateway protocols, “no battery”).
- **Iterations:** One-shot prompts often need refinement (animation timing, collection naming). Be explicit: units (mm), mount type (wall vs ceiling), which optional sensors (CO₂, TVOC, light).
- **Tutorial follow-up:** For complex organic shapes, the video found YouTube-transcript prompting weak; for **this** product, prefer **dimensioned box + LCD + solar panel** hard-surface modeling with explicit measurements.

## 8. Export

Ask the agent to render stills to `blender/renders/` or export GLB for web/T3000. Keep master `.blend` files under `blender/scenes/`.
