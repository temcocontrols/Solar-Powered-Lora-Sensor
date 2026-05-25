"""Indoor solar cell comparison — shared data for Energy Budget xlsx/HTML."""

from __future__ import annotations

from dataclasses import dataclass

TARGET_PANEL_AREA_CM2 = 36.0  # 60 × 60 mm
COMPARE_LUX = (200, 500, 1000)
REF_LUX_FOR_DENSITY = 200


@dataclass(frozen=True)
class SolarCell:
    vendor: str
    part: str
    technology: str
    size_note: str
    voc_note: str
    datasheet: str
    notes: str
    uw_cm2_at_200: float | None = None
    power_uw_at_200: float | None = None
    native_area_cm2: float | None = None

    def panel_in_uw(self, lux: int, area_cm2: float = TARGET_PANEL_AREA_CM2) -> float | None:
        if self.power_uw_at_200 is not None and self.native_area_cm2:
            base = self.power_uw_at_200 * (area_cm2 / self.native_area_cm2)
        elif self.uw_cm2_at_200 is not None:
            base = self.uw_cm2_at_200 * area_cm2
        else:
            return None
        return base * lux / REF_LUX_FOR_DENSITY

    def uw_cm2(self, lux: int = REF_LUX_FOR_DENSITY) -> float | None:
        p = self.panel_in_uw(lux)
        if p is None:
            return None
        return p / TARGET_PANEL_AREA_CM2


SOLAR_CELLS: list[SolarCell] = [
    SolarCell(
        vendor="Dazheng (target)",
        part="Flexible perovskite 60×60",
        technology="Perovskite flexible",
        size_note="60×60 mm (custom)",
        voc_note="TBD — request from vendor",
        datasheet="INDOOR_SOLAR_PANEL_SPEC.md",
        notes="Vendor under evaluation; no public electrical PDF",
    ),
    SolarCell(
        vendor="Epishine",
        part="MultiCell (typ max)",
        technology="Printed organic indoor",
        size_note="50×50 mm catalog; 60×60 custom",
        uw_cm2_at_200=8.4,
        voc_note="~0.5 V MPP/cell",
        datasheet="datasheets/SolarCell/Epishine_MultiCell_indoor_datasheet.pdf",
        notes="20–1000 lux SOC; 5000 K LED test conditions",
    ),
    SolarCell(
        vendor="Panasonic",
        part="Amorton (flyer typ)",
        technology="a-Si indoor",
        size_note="Custom sizes",
        uw_cm2_at_200=8.0,
        voc_note="~0.63 V/cell",
        datasheet="datasheets/SolarCell/Panasonic_Amorton_product_flyer.pdf",
        notes="7–9 µW/cm² @ 200 lux (fluorescent)",
    ),
    SolarCell(
        vendor="Panasonic",
        part="AMG-1401C",
        technology="a-Si indoor glass",
        size_note="41.4×26.1 mm",
        power_uw_at_200=74.3,
        native_area_cm2=41.4 * 26.1 / 100,
        voc_note="2.7 V Voc @ 200 lux FL",
        datasheet="datasheets/SolarCell/Panasonic_AMG-1401C_indoor_datasheet.pdf",
        notes="White fluorescent @ 200 lux",
    ),
    SolarCell(
        vendor="PowerFilm",
        part="LL200-2.4-37",
        technology="a-Si flexible indoor",
        size_note="54×36.5 mm",
        power_uw_at_200=68.0,
        native_area_cm2=54.0 * 36.5 / 100,
        voc_note="~2.4 V Voc avg @ 200 lux",
        datasheet="datasheets/SolarCell/PowerFilm_LL200-2.4-37_indoor_drawing.pdf",
        notes="Closest catalog geometry to 60×60 mm",
    ),
    SolarCell(
        vendor="RICOH",
        part="EH DSSC5284a",
        technology="Solid-state DSSC",
        size_note="52×84 mm",
        power_uw_at_200=276.0,
        native_area_cm2=52.0 * 84.0 / 100,
        voc_note="5.4 V Voc — check BQ25505 Vin",
        datasheet="datasheets/SolarCell/RICOH_EH_DSSC5284a_launch_spec.pdf",
        notes="200 lux, 5000 K LED; min Pmax rating",
    ),
]


def model_placeholder_cell(model_uw_cm2_ref: float) -> SolarCell:
    return SolarCell(
        vendor="Model",
        part="Energy budget placeholder",
        technology="Amorton-class coeff",
        size_note=f"{TARGET_PANEL_AREA_CM2:.0f} cm²",
        uw_cm2_at_200=model_uw_cm2_ref,
        voc_note="—",
        datasheet="build_energy_budget_sheet.py",
        notes="Replace when Dazheng sample is characterised",
    )


def all_cells(model_uw_cm2_ref: float = 8.0) -> list[SolarCell]:
    return [*SOLAR_CELLS, model_placeholder_cell(model_uw_cm2_ref)]


def build_catalog_rows(
    area_cm2: float = TARGET_PANEL_AREA_CM2,
    model_uw_cm2_ref: float = 8.0,
) -> list[list[str]]:
    rows = []
    for c in all_cells(model_uw_cm2_ref):
        p200 = c.panel_in_uw(200, area_cm2)
        dens = c.uw_cm2(200)
        rows.append([
            c.vendor,
            c.part,
            c.technology,
            c.size_note,
            f"{dens:.1f}" if dens is not None else "—",
            f"{p200:.0f} µW" if p200 is not None else "TBD",
            c.voc_note,
            c.datasheet,
            c.notes,
        ])
    return rows


def build_lux_matrix_rows(
    need_net_uw: float,
    harvest_eff: float,
    lux_levels: tuple[int, ...] = COMPARE_LUX,
    area_cm2: float = TARGET_PANEL_AREA_CM2,
    model_uw_cm2_ref: float = 8.0,
) -> list[list[str]]:
    rows = []
    for c in all_cells(model_uw_cm2_ref):
        for lux in lux_levels:
            pin = c.panel_in_uw(lux, area_cm2)
            if pin is None:
                rows.append([c.vendor, c.part, str(lux), "—", "—", "—", "—"])
                continue
            ph = pin * harvest_eff
            ratio = ph / need_net_uw if need_net_uw else 0
            status = "OK" if ph >= need_net_uw else "DEFICIT"
            rows.append([
                c.vendor,
                c.part,
                str(lux),
                f"{pin:.0f}",
                f"{ph:.0f}",
                f"{ratio:.1f}×",
                status,
            ])
    return rows


def build_summary_at_lux(
    lux: int,
    need_net_uw: float,
    harvest_eff: float,
    area_cm2: float = TARGET_PANEL_AREA_CM2,
    model_uw_cm2_ref: float = 8.0,
) -> list[list[str]]:
    rows = []
    for c in all_cells(model_uw_cm2_ref):
        pin = c.panel_in_uw(lux, area_cm2)
        if pin is None:
            rows.append([c.vendor, c.part, "TBD", "—", "—"])
            continue
        ph = pin * harvest_eff
        ratio = ph / need_net_uw if need_net_uw else 0
        rows.append([c.vendor, c.part, f"{pin:.0f} µW", f"{ph:.0f} µW", f"{ratio:.1f}×"])
    return rows
