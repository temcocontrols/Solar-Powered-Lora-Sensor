# SolarSensor local workspace notes

Product visuals and technical drawings for the **Temco Controls indoor solar-powered environmental sensor node** (second-generation datasheet: `Docs/SECONDGEN.pdf`, model **AQ-Solar-LCD**).

## What this folder is for (local work)

- Automated **3D product renders** and **system diagrams** (gateway + wireless nodes)
- Assets for datasheets, T3000 floor plans, and marketing
- Repeatable generation via **Blender + MCP** (natural-language prompts that drive Blender Python)

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

See `Docs/blender-mcp-setup.md` and `prompts/` for setup and example prompts.
