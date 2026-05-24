# SolarSensor

Product visuals and technical drawings for the **Temco Controls indoor solar-powered environmental sensor node** (second-generation datasheet: `Docs/SECONDGEN.pdf`, model **AQ-Solar-LCD**).

## What this repo is for

- Automated **3D product renders** and **system diagrams** (gateway + wireless nodes)
- Assets for datasheets, T3000 floor plans, and marketing
- Repeatable generation via **Blender + MCP** (natural-language prompts that drive Blender Python)

Not related to the WECHAT messaging project.

## Source materials

| File | Role |
|------|------|
| `Docs/SECONDGEN.pdf` | Current product datasheet (Rev 1.0) |
| `Docs/SolarPoweredSensor.pdf` | Earlier / related product PDF |
| `Docs/AQ-N-3.pdf` | Additional product reference |
| `Docs/FIRSTGEN.docx`, `Docs/Project with dad...docx` | First-gen notes and draft copy |
| `Docs/T3E-Nano_*.png`, `Docs/image-removebg-preview.png` | Gateway / product cutouts for compositing |
| `Docs/T3000BacnetProgrammableControllerSeries-2.pdf` | Gateway (T3 Nano) documentation |

## Drawing automation (Blender MCP)

Inspired by [Blender Can Do AI Now](https://youtu.be/xBLGsYLwgks) — Claude (or another MCP client) talks to Blender through the official [Blender MCP server](https://www.blender.org/lab/mcp-server/).

**Requirements**

1. [Blender 5.1+](https://www.blender.org/download/)
2. [MCP add-on](https://www.blender.org/lab/mcp-server/) (drag-and-drop install in Blender; enable MCP server on `localhost:9876`)
3. MCP client: Claude Desktop, Cursor, or Llama.cpp — with `blender-mcp` server configured

See `Docs/blender-mcp-setup.md` for Windows setup and example prompts for this product.

**Security:** MCP runs LLM-generated Python inside Blender with no sandbox. Use a machine without sensitive data, or work on copies of `.blend` files.

## Suggested drawing backlog

1. **Hero product shot** — wall/ceiling-mounted node, LCD showing sample readings (23.5 °C, 48.2 %, 650 ppm, AQI)
2. **System block diagram** — solar nodes → sub-GHz → Temco gateway → BACnet/Modbus → BMS (match datasheet p.2)
3. **Cutaway / callouts** — indoor-tuned solar cell, supercapacitor, optional CO₂/TVOC modules
4. **Installation stills** — mount locations, light requirements, pairing flow
5. **T3000 floor-plan icons** — simple top-down sensor glyph for live overlays

## Repo layout (target)

```
SolarSensor/
  Docs/           # datasheets, setup, extracted text
  blender/        # .blend scenes, exported PNG/GLB
  prompts/        # reusable MCP prompt templates
  scripts/        # optional Python helpers (batch export, dimensions)
```

## Next step

Pick one item from the backlog, open Blender with the MCP add-on running, and use a prompt from `prompts/` (or ask in Cursor with Blender MCP connected).
