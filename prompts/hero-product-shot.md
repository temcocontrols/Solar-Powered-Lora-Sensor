# Prompt: Hero product shot (AQ-Solar-LCD)

Use in Blender MCP after opening a new scene. Attach reference: `Docs/image-removebg-preview.png` if the client supports images.

---

Create a photorealistic product visualization of a wall-mounted indoor environmental sensor for a building-automation datasheet.

**Product**
- Compact rectangular enclosure, white/light gray plastic, subtle vent slots
- Top section: indoor-tuned solar panel (dark blue-black cell grid, not outdoor-scale panels)
- Front: small LCD showing **23.5 °C**, **48.2 % RH**, **650 ppm**, **AQI 95 — GOOD** (clean sans-serif UI)
- No visible battery compartment; design implies supercapacitor energy storage
- Optional small status LED near the LCD

**Scene**
- Mounted on a light office wall, soft indoor LED lighting (100–500 lux feel), no direct sunbeams
- Shallow depth of field, product sharp, background softly blurred
- Camera: 3/4 front angle, eye level, premium product-photo composition

**Output**
- Cycles or EEVEE render, 1920×1080, transparent or light gray background variant
- Name objects with prefix `GEO-`, lights `LGT-`, camera `CAM-hero`

Do not add text watermarks. Match professional BMS/hardware datasheet style.
