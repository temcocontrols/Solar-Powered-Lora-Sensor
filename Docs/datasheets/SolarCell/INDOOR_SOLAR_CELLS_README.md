# Indoor solar cell datasheets (reference library)

Local copies of published datasheets for **indoor / low-light** PV modules comparable to the Dazheng perovskite cell under evaluation. **Dazheng has no public electrical PDF** — use these for benchmarking until vendor samples are characterised.

**Project context:** [INDOOR_SOLAR_PANEL_SPEC.md](../../INDOOR_SOLAR_PANEL_SPEC.md)

Test conditions vary by vendor — always check **lux**, **spectrum (5000 K LED vs fluorescent)**, and **temperature**.

---

## Files in this folder

| File | Vendor / part | Technology | Key specs @ 200 lux | Closest to 60×60 mm? |
|------|---------------|------------|---------------------|----------------------|
| [RICOH_EH_DSSC5284a_launch_spec.pdf](RICOH_EH_DSSC5284a_launch_spec.pdf) | RICOH **EH DSSC5284a** | Solid-state dye-sensitized | **276 µW** min, 52×84 mm, Voc 5.4 V | Scale to 36 cm² → ~227 µW |
| [RICOH_EH_DSSC_indoor_reference.pdf](RICOH_EH_DSSC_indoor_reference.pdf) | RICOH EH DSSC series | DSSC (tech overview) | 200 lux, 5000 K LED tables | Reference slides |
| [RICOH_EH_DSSC2020_launch_spec.pdf](RICOH_EH_DSSC2020_launch_spec.pdf) | RICOH EH DSSC (2020 launch) | DSSC | First-gen indoor modules | Historical |
| [Epishine_OneCell_indoor_datasheet.pdf](Epishine_OneCell_indoor_datasheet.pdf) | Epishine **OneCell** | Printed organic indoor | **Up to 8.4 µW/cm²** @ 200 lux | Custom sizes; 50×50 mm SKUs in multicell sheet |
| [Epishine_MultiCell_indoor_datasheet.pdf](Epishine_MultiCell_indoor_datasheet.pdf) | Epishine **MultiCell** | Printed organic indoor | **8.4 µW/cm²** typ @ 200 lux; 20–1000 lux SOC | **50×50 mm** modules listed |
| [Panasonic_Amorton_product_flyer.pdf](Panasonic_Amorton_product_flyer.pdf) | Panasonic **Amorton** | a-Si indoor | **7–9 µW/cm²** @ 200 lux; IoT / ESL | Custom; portfolio |
| [Panasonic_Amorton_brochure.pdf](Panasonic_Amorton_brochure.pdf) | Panasonic Amorton | a-Si indoor | 50–1000 lux range; many part numbers | Catalog |
| [Panasonic_AMG-1401C_indoor_datasheet.pdf](Panasonic_AMG-1401C_indoor_datasheet.pdf) | Panasonic **AMG-1401C** | a-Si indoor glass | **74.3 µW** @ 200 lux FL, 41.4×26.1 mm | Similar area to scaled 60×60 |
| [PowerFilm_LL200-2.4-37_indoor_drawing.pdf](PowerFilm_LL200-2.4-37_indoor_drawing.pdf) | PowerFilm **LL200-2.4-37** | a-Si flexible indoor | **68 µW** @ 200 lux, 54×36.5 mm | **Very close geometry** |

---

## Quick comparison @ 200 lux (≈36 cm² / 60×60 mm where noted)

| Source | Power @ 200 lux (est. 36 cm²) | µW/cm² | Voc note |
|--------|-------------------------------|--------|----------|
| Epishine (typ max) | **~302 µW** | 8.4 | ~0.5 V MPP (multi-cell) |
| Amorton flyer (typ) | **~288 µW** | 8.0 | ~0.63 V/cell |
| PowerFilm LL200 (scaled) | **~244 µW** from 68 µW @ 19.7 cm² | ~6.8 | 2.4 V avg Voc |
| Ricoh DSSC5284a (scaled) | **~227 µW** min | 6.3 | **5.4 V** — check BQ25505 Vin limit |
| Energy budget placeholder | **288 µW** in | 8.0 | Model only |

---

## Not available locally

| Vendor | Status |
|--------|--------|
| **Dazheng (大正) perovskite** | No public electrical PDF — request from vendor |
| **RICOH EH DSSC** full product catalog | Industry site merged; use launch PDFs above |

---

## Sources (download URLs)

- Ricoh: https://www.ricoh.com/-/Media/Ricoh/Sites/com/release/2021/pdf/0513_1.pdf
- Epishine: https://www.epishine.com/downloaddatasheet
- Panasonic Amorton: https://panasonic.net/electricworks/amorton/
- PowerFilm: https://www.powerfilmsolar.com/products/electronic-component-solar-panels/indoor-light-series/ll200-24-37
