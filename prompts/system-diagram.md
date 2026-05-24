# Prompt: System overview diagram

Matches SECONDGEN datasheet “System Overview — Wiring & Connectivity”.

---

Create a clean **technical diagram** (not photorealistic) in Blender using simple meshes and labeled empties:

**Left cluster — Wireless sensor nodes (4 icons)**
- Temp/RH node (solar powered label)
- CO₂ node (optional, asterisk)
- TVOC node (optional, asterisk)
- Ambient light node
Each: small box + solar panel icon + wireless antenna symbol

**Center — Temco Gateway**
- Box labeled “TEMCO GATEWAY (T3 Nano)”
- Icons/labels: Ethernet, Wi-Fi, BACnet, Modbus

**Right — Building**
- “BMS / BACnet / Modbus / T3000” block

**Connections**
- Dashed arrows: sub-GHz “Long-range wireless” from all nodes to gateway
- Solid arrows: gateway to building network (Ethernet/Wi-Fi) and to BMS

**Style**
- Orthographic camera, flat colors (Temco-style blue/gray palette), white background
- Use text objects for labels; keep readable at 1920×1080 export
- Organize in collections: `NODES`, `GATEWAY`, `BMS`, `ANNOTATIONS`

Export PNG to `blender/renders/system-overview.png`.
