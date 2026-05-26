# Indoor solar panel — project spec (public)

**Target vendor technology:** flexible **perovskite** indoor modules (Dazheng-class).  
**Company site:** [DaZheng Micro-Nano Technology](https://en.dazhengtop.com/)

**Related:** [Energy Budget](SolarSensorSchematicRev2_EnergyBudget.html) · [Indoor Solar Cells](SolarSensorSchematicRev2_SolarCells.html) · [BQ25505 design inputs](BQ25505_DESIGN_INPUTS.md)

---

## Project requirements

| Item | Detail |
|------|--------|
| **Use case** | Indoor environmental sensor; **LoRa** uplink (reference: Linemetrics solar LoRa T/RH sensor) |
| **Install environment** | Indoor only |
| **Illuminance range** | **200 – 1000 lux** |
| **Production panel** | **60 × 60 mm** (36 cm²) |
| **Lab panel** | **500 × 500 mm** (characterisation) |
| **Technology** | Flexible indoor **perovskite** (vendor under evaluation) |
| **Sample target** | 3 pcs × each size |

---

## Electrical targets (for vendor RFQ)

| Parameter | Value | Notes |
|-----------|-------|-------|
| Panel area | 60 × 60 mm | Production |
| Operating lux | 200 / 500 / 1000 | Office LED / fluorescent |
| Average load | ~55 µW @ 3.3 V | Energy budget (Rev2 sensor set) |
| Peak load | ~33 mA × 150 ms / 300 s | LoRa + sensor burst |
| Harvester | TI BQ25505 MPPT | Vin max **5.1 V** recommended |
| Storage | 100 F · 3.8 V LIC | Hybrid target |

### RFQ template (copy/adapt)

```
Application: Indoor LoRa environmental sensor (T/RH/CO₂ class).
Enclosure active area: 60×60 mm flexible module.
Illuminance: 200–1000 lux (LED/fluorescent office).
Load: ~55 µW average, ~33 mA × 150 ms burst every 300 s @ 3.3 V.
Harvester: TI BQ25505 MPPT (Vin max 5.1 V recommended operating).
Storage: 100 F / 3.8 V supercap.

Please quote 3× 60×60 mm samples and provide at 200 / 500 / 1000 lux (5000 K LED):
  Voc, Isc, Vmp, Imp, Pmax, and recommended MPPT fraction.
Also: thickness, min bend radius, lead attachment, MOQ/price.
```

---

## Dazheng — public catalog notes

Dazheng publishes **flexible perovskite (FPSC)** for IoT / weak-light use. **No public electrical PDF** with Voc/Isc or µW @ 200 lux was available as of project start — request a **custom 60×60 mm characterisation sheet** from the vendor.

| Module (public SKU) | Size (mm) | Electrical specs on web |
|---------------------|-----------|-------------------------|
| Dev module | 100 × 100 | None published |
| [350 × 350](https://en.dazhengtop.com/product_detail/20.html) | 350 × 350 | None published |
| [640 × 1040](https://en.dazhengtop.com/product_detail/8.html) | 640 × 1040 | None published |
| **Project target** | **60 × 60** | **Custom** |

Marketing claims: good weak-light / soft-light performance; ~23% lab cell efficiency (not indoor Pmax).

---

## Indoor benchmark — RICOH EH DSSC5284a @ 200 lux

Test: **200 lux**, **5000 K LED**, **25 °C**.

| Part | Size (mm) | Pmax (min) | Voc (typ) | Scaled to 36 cm² |
|------|-----------|------------|-----------|------------------|
| **EH DSSC5284a** | 52 × 84 | **276 µW** | **5.4 V** | **~227 µW** |

**BQ25505 note:** Ricoh Voc **5.4 V** may exceed recommended **5.1 V** input — verify MPP or add input protection. Custom perovskite may target lower Voc.

Full indoor cell library: [datasheets/SolarCell/INDOOR_SOLAR_CELLS_README.md](datasheets/SolarCell/INDOOR_SOLAR_CELLS_README.md)

---

## Next steps

1. Send RFQ template to vendor; obtain I–V data at 200 / 500 / 1000 lux.  
2. Characterise 60×60 mm samples on bench.  
3. Update `PANEL_UW_CM2_REF` in `build_energy_budget_sheet.py`.  
4. Compare to Ricoh / Epishine / Amorton benchmarks in **Indoor Solar Cells** sheet.  
5. Verify Voc vs BQ25505 before PCB spin.
