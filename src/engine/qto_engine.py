"""
QTO Engine — orchestrates all calculators from a DrawingData input dict
and returns a complete BOQ with 50+ items.
"""

from __future__ import annotations

import json
import math
import os
from typing import Any

from src.engine.sub_structure import SubStructureCalculator
from src.engine.super_structure import SuperStructureCalculator
from src.engine.finishes import FinishesCalculator


# ---------------------------------------------------------------------------
# Config loader helpers
# ---------------------------------------------------------------------------

def _load_json(relative_path: str) -> dict:
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    full = os.path.join(base, relative_path)
    with open(full, encoding="utf-8") as fh:
        return json.load(fh)


def _load_averages() -> dict:
    return _load_json("config/averages.json")


def _load_rates() -> dict:
    return _load_json("config/rates.json")


# ---------------------------------------------------------------------------
# BOQ line item builder
# ---------------------------------------------------------------------------

def _item(
    item_no: str,
    description: str,
    unit: str,
    quantity: float,
    category: str,
    rate_key: str | None = None,
    rates: dict | None = None,
    confidence_note: str = "",
) -> dict:
    rates = rates or {}
    rate = 0.0
    if rate_key:
        for section in rates.values():
            if isinstance(section, dict) and rate_key in section:
                rate = section[rate_key]
                break
    amount = round(quantity * rate, 2)
    return {
        "item_no": item_no,
        "description": description,
        "unit": unit,
        "quantity": round(quantity, 3),
        "rate": rate,
        "amount": amount,
        "category": category,
        "confidence_note": confidence_note,
    }


# ---------------------------------------------------------------------------
# Main Engine
# ---------------------------------------------------------------------------

class QTOEngine:
    """
    Orchestrates sub-structure, super-structure and finishes calculators
    from a normalised DrawingData dictionary.
    """

    def __init__(self):
        self.sub_calc = SubStructureCalculator()
        self.sup_calc = SuperStructureCalculator()
        self.fin_calc = FinishesCalculator()
        self._averages = _load_averages()
        self._rates = _load_rates()

    # ------------------------------------------------------------------
    def run(self, data: dict) -> list[dict]:
        """
        Entry point.  `data` must conform to the DrawingData / sample_input schema.
        Returns a list of BOQ line-item dicts.
        """
        boq: list[dict] = []
        project_type = data.get("project_type", "G+1")
        plot_area = data.get("plot_area", 153.0)
        floor_height = data.get("floor_height", 3.0)

        # Project meta
        gfl = data.get("gfl", 0.30)          # Ground floor level (m above excavation datum)
        exc_depth = data.get("exc_depth", 1.50)
        tb_depth = data.get("tb_depth", 0.40)
        pcc_thickness = data.get("pcc_thickness", 0.10)
        gfsl_level = data.get("gfsl_level", 0.30)
        slab_thickness = data.get("slab_thickness", 0.20)

        # ------------------------------------------------------------------
        # SUB-STRUCTURE
        # ------------------------------------------------------------------
        boq.extend(self._calc_sub_structure(
            data, gfl, exc_depth, tb_depth, pcc_thickness, gfsl_level
        ))

        # ------------------------------------------------------------------
        # SUPER-STRUCTURE
        # ------------------------------------------------------------------
        boq.extend(self._calc_super_structure(
            data, floor_height, slab_thickness
        ))

        # ------------------------------------------------------------------
        # FINISHES
        # ------------------------------------------------------------------
        boq.extend(self._calc_finishes(
            data, floor_height, project_type, plot_area
        ))

        return boq

    # ==================================================================
    # SUB-STRUCTURE helpers
    # ==================================================================
    def _calc_sub_structure(
        self, data: dict, gfl: float, exc_depth: float,
        tb_depth: float, pcc_thickness: float, gfsl_level: float
    ) -> list[dict]:
        items: list[dict] = []
        r = self._rates

        footings = data.get("footings", [])
        neck_cols = data.get("neck_columns", [])
        tie_beams = data.get("tie_beams", [])
        solid_walls = data.get("solid_block_walls", [])
        gf_area = data.get("gf_area", data.get("plot_area", 153.0))
        longest_length = data.get("longest_length", 0.0)
        longest_width = data.get("longest_width", 0.0)
        has_road_base = data.get("has_road_base", False)

        # --- Foundation ---
        if footings:
            f_res = self.sub_calc.calculate_foundation(footings)
            items.append(_item("A.1", "Foundation — Concrete (Grade C30)", "m3",
                               f_res["volume_m3"], "Sub-Structure",
                               "foundation_concrete", r))
            items.append(_item("A.2", "Foundation — Plain Cement Concrete (PCC)", "m3",
                               f_res["pcc_volume_m3"], "Sub-Structure",
                               "foundation_pcc", r))
            items.append(_item("A.3", "Foundation — Bitumen Waterproofing", "m2",
                               f_res["bitumen_area_m2"], "Sub-Structure",
                               "foundation_bitumen", r))
            f_pcc_area = sum(
                (ff.get("length", 0) + 0.20) * (ff.get("width", 0) + 0.20) * ff.get("count", 1)
                for ff in footings
            )
        else:
            f_pcc_area = 0.0

        # --- Neck Columns ---
        if neck_cols:
            nc_res = self.sub_calc.calculate_neck_columns(
                neck_cols, gfl, exc_depth, tb_depth, pcc_thickness
            )
            items.append(_item("A.4", "Neck Columns — Concrete (Grade C30)", "m3",
                               nc_res["volume_m3"], "Sub-Structure",
                               "neck_column_concrete", r))
            items.append(_item("A.5", "Neck Columns — Formwork", "m2",
                               nc_res["volume_m3"] / max(0.20 * 0.30, 0.001),
                               "Sub-Structure", "neck_column_formwork", r))

        # --- Tie Beams ---
        if tie_beams:
            tb_res = self.sub_calc.calculate_tie_beams(tie_beams)
            items.append(_item("A.6", "Tie Beams — Concrete (Grade C30)", "m3",
                               tb_res["volume_m3"], "Sub-Structure",
                               "tie_beam_concrete", r))
            items.append(_item("A.7", "Tie Beams — Plain Cement Concrete (PCC)", "m3",
                               tb_res["pcc_volume_m3"], "Sub-Structure",
                               "tie_beam_pcc", r))
            items.append(_item("A.8", "Tie Beams — Bitumen Waterproofing", "m2",
                               tb_res["bitumen_area_m2"], "Sub-Structure",
                               "tie_beam_bitumen", r))
            tb_pcc_area = sum(
                b.get("length", 0) * (b.get("width", 0) + 0.20) * b.get("count", 1)
                for b in tie_beams
            )
        else:
            tb_pcc_area = 0.0

        # --- Solid Block Work ---
        if solid_walls:
            sbw_res = self.sub_calc.calculate_solid_block_work(
                solid_walls, gfl, exc_depth, tb_depth, pcc_thickness
            )
            items.append(_item("A.9", "Solid Block Work (Below Grade)", "m2",
                               sbw_res["area_m2"], "Sub-Structure",
                               "solid_block_work", r))
            items.append(_item("A.10", "Solid Block Work — Bitumen Waterproofing", "m2",
                               sbw_res["bitumen_area_m2"], "Sub-Structure",
                               "solid_block_bitumen", r))

        # --- Slab on Grade ---
        sog_res = self.sub_calc.calculate_slab_on_grade(gf_area)
        items.append(_item("A.11", "Slab on Grade — Concrete (Grade C30)", "m3",
                           sog_res["volume_m3"], "Sub-Structure",
                           "slab_on_grade_concrete", r))
        sog_area = sog_res["area_m2"]

        # --- Excavation ---
        # Determine longest dimensions from footprint or data
        if longest_length == 0.0 or longest_width == 0.0:
            side = math.sqrt(plot_area)
            longest_length = longest_length or side * 1.2
            longest_width = longest_width or side * 0.9

        exc_res = self.sub_calc.calculate_excavation(longest_length, longest_width, exc_depth)
        items.append(_item("A.12", "Excavation", "m3",
                           exc_res["volume_m3"], "Sub-Structure",
                           "excavation", r))
        exc_area = exc_res["area_m2"]

        # --- Back Filling ---
        # Collect all sub-structure volumes for deduction
        all_vols = sum(
            it["quantity"] for it in items
            if it["unit"] == "m3" and it["category"] == "Sub-Structure"
        )
        bf_res = self.sub_calc.calculate_back_filling(
            exc_area, exc_depth, gfsl_level, all_vols
        )
        items.append(_item("A.13", "Back Filling", "m3",
                           bf_res["net_volume_m3"], "Sub-Structure",
                           "back_filling", r))

        # --- Anti-Termite ---
        total_pcc_area = f_pcc_area + tb_pcc_area
        at_res = self.sub_calc.calculate_anti_termite(total_pcc_area, sog_area)
        items.append(_item("A.14", "Anti-Termite Treatment", "m2",
                           at_res["area_m2"], "Sub-Structure",
                           "anti_termite", r))

        # --- Polyethylene Sheet ---
        ps_res = self.sub_calc.calculate_polyethylene_sheet(total_pcc_area, sog_area)
        items.append(_item("A.15", "Polyethylene Sheet (1000 gauge)", "m2",
                           ps_res["area_m2"], "Sub-Structure",
                           "polyethylene_sheet", r))

        # --- Road Base (optional) ---
        if has_road_base:
            rb_res = self.sub_calc.calculate_road_base(exc_area)
            items.append(_item("A.16", "Road Base (25 cm compacted)", "m3",
                               rb_res["volume_m3"], "Sub-Structure",
                               "road_base", r))

        return items

    # ==================================================================
    # SUPER-STRUCTURE helpers
    # ==================================================================
    def _calc_super_structure(
        self, data: dict, floor_height: float, slab_thickness: float
    ) -> list[dict]:
        items: list[dict] = []
        r = self._rates

        slabs = data.get("slabs", [])
        beams = data.get("beams", [])
        columns = data.get("columns", [])
        total_floor_area = data.get("total_floor_area", data.get("plot_area", 153.0))

        # Wet area is derived from finishes data
        wet_rooms = [
            rm for rm in data.get("rooms", [])
            if rm.get("room_type", "").lower() in
            {"toilet", "bathroom", "kitchen", "pantry", "laundry"}
        ]
        wet_area = sum(rm.get("area", 0) for rm in wet_rooms)

        # --- Slabs ---
        if slabs:
            sl_res = self.sup_calc.calculate_slabs(slabs)
            items.append(_item("B.1", "Slabs — Concrete (Grade C30)", "m3",
                               sl_res["volume_m3"], "Super-Structure",
                               "slab_concrete", r))
        else:
            # Estimate from floor area
            est_vol = total_floor_area * slab_thickness
            items.append(_item("B.1", "Slabs — Concrete (Grade C30) [estimated]", "m3",
                               est_vol, "Super-Structure", "slab_concrete", r))

        # --- Beams ---
        if beams:
            bm_res = self.sup_calc.calculate_beams(beams, slab_thickness)
            items.append(_item("B.2", "Beams — Concrete (Grade C30)", "m3",
                               bm_res["volume_m3"], "Super-Structure",
                               "beam_concrete", r))

        # --- Columns ---
        if columns:
            col_res = self.sup_calc.calculate_columns(columns, floor_height)
            items.append(_item("B.3", "Columns — Concrete (Grade C30)", "m3",
                               col_res["volume_m3"], "Super-Structure",
                               "column_concrete", r))

        # --- Dry Area Flooring ---
        daf_res = self.sup_calc.calculate_dry_area_flooring(total_floor_area, wet_area)
        dry_area = daf_res["area_m2"]
        items.append(_item("B.4", "Dry Area Flooring", "m2",
                           dry_area, "Super-Structure", "dry_area_flooring", r))

        # --- Skirting ---
        dry_perimeter = data.get("dry_area_perimeter", 4 * (dry_area ** 0.5))
        door_widths = [
            op.get("width", 0) * op.get("count", 1)
            for op in data.get("openings", [])
            if op.get("opening_type", op.get("type", "")) == "door"
        ]
        sk_res = self.sup_calc.calculate_skirting(dry_perimeter, door_widths)
        items.append(_item("B.5", "Skirting", "RM",
                           sk_res["area_m"], "Super-Structure", "skirting", r))

        # --- Paint ---
        paint_res = self.sup_calc.calculate_paint(sk_res["area_m"], floor_height)
        items.append(_item("B.6", "Paint (Internal Walls)", "m2",
                           paint_res["area_m2"], "Super-Structure", "paint", r))

        # --- Dry Areas Ceiling ---
        dac_res = self.sup_calc.calculate_dry_areas_ceiling(dry_area)
        items.append(_item("B.7", "Dry Areas Ceiling", "m2",
                           dac_res["area_m2"], "Super-Structure",
                           "dry_areas_ceiling", r))

        return items

    # ==================================================================
    # FINISHES helpers
    # ==================================================================
    def _calc_finishes(
        self, data: dict, floor_height: float, project_type: str, plot_area: float
    ) -> list[dict]:
        items: list[dict] = []
        r = self._rates
        avg = self._averages
        fc = self.fin_calc

        rooms = data.get("rooms", [])
        openings = data.get("openings", [])

        # Categorise rooms
        def _area(types):
            return sum(
                rm.get("area", 0) for rm in rooms
                if rm.get("room_type", "").lower() in types
            )

        toilets = _area({"toilet"})
        bathrooms = _area({"bathroom"})
        kitchens = _area({"kitchen"})
        pantries = _area({"pantry"})
        laundry = _area({"laundry"})
        balcony_area = _area({"balcony"})

        # --- Wet Areas Flooring ---
        waf = fc.calculate_wet_areas_flooring(
            toilets, bathrooms, kitchens, pantries, laundry
        )
        wet_area_total = waf["area_m2"]
        items.append(_item("C.1", "Wet Areas Flooring (Ceramic / Porcelain)", "m2",
                           wet_area_total, "Finishes", "wet_areas_flooring", r))

        # --- Wall Tiles ---
        wet_perimeter = sum(
            rm.get("perimeter", 0) for rm in rooms
            if rm.get("room_type", "").lower() in
            {"toilet", "bathroom", "kitchen", "pantry", "laundry"}
        )
        wt = fc.calculate_wall_tiles(wet_perimeter, floor_height)
        items.append(_item("C.2", "Wall Tiles (Ceramic — Wet Areas)", "m2",
                           wt["area_m2"], "Finishes", "wall_tiles", r))

        # --- Wet Areas Ceiling ---
        wac = fc.calculate_wet_areas_ceiling(wet_area_total)
        items.append(_item("C.3", "Wet Areas Ceiling (Gypsum Board)", "m2",
                           wac["area_m2"], "Finishes", "wet_areas_ceiling", r))

        # --- Balcony Flooring ---
        bf = fc.calculate_balcony_flooring(balcony_area)
        items.append(_item("C.4", "Balcony Flooring", "m2",
                           bf["area_m2"], "Finishes", "balcony_flooring", r))

        # --- Marble Threshold ---
        door_widths = [
            op.get("width", 0.9)
            for op in openings
            if op.get("opening_type", op.get("type", "")) == "door"
            for _ in range(op.get("count", 1))
        ]
        mt = fc.calculate_marble_threshold(door_widths)
        items.append(_item("C.5", "Marble Threshold", "RM",
                           mt["length_rm"], "Finishes", "marble_threshold", r))

        # --- Openings ---
        op_res = fc.calculate_openings(openings)
        items.append(_item("C.6", "Doors (Supply & Install)", "m2",
                           op_res["total_door_area_m2"], "Finishes", "doors", r))
        items.append(_item("C.7", "Windows (Aluminium — Supply & Install)", "m2",
                           op_res["total_window_area_m2"], "Finishes", "windows", r))

        # Pre-compute wall areas for block / plaster items
        ext_walls = [w for w in data.get("walls", [])
                     if w.get("type", "external") == "external"]
        int_walls_20 = [w for w in data.get("walls", [])
                        if w.get("type", "") == "internal_20"]
        int_walls_10 = [w for w in data.get("walls", [])
                        if w.get("type", "") == "internal_10"]

        ext_perimeter = sum(w.get("length", 0) for w in ext_walls) or data.get("external_perimeter", 0.0)
        len_20 = sum(w.get("length", 0) for w in int_walls_20) or data.get("internal_wall_length_20cm", 0.0)
        len_10 = sum(w.get("length", 0) for w in int_walls_10) or data.get("internal_wall_length_10cm", 0.0)

        windows_area = op_res["total_window_area_m2"]
        doors_area = op_res["total_door_area_m2"]
        main_door_area = data.get("main_door_area", 4.0)  # default 2×2 m

        # --- Block 20 External ---
        b20e = fc.calculate_block_20_external(
            ext_perimeter, floor_height, windows_area, main_door_area
        )
        items.append(_item("C.8", "Block 20cm — External Walls", "m2",
                           b20e["net_area_m2"], "Finishes", "block_20_external", r))

        # --- Block 20 Internal ---
        b20i = fc.calculate_block_20_internal(len_20, floor_height, doors_area)
        items.append(_item("C.9", "Block 20cm — Internal Walls", "m2",
                           b20i["net_area_m2"], "Finishes", "block_20_internal", r))

        # --- Block 10 Internal ---
        b10i = fc.calculate_block_10_internal(len_10, floor_height, doors_area)
        items.append(_item("C.10", "Block 10cm — Internal Partition Walls", "m2",
                           b10i["net_area_m2"], "Finishes", "block_10_internal", r))

        # --- Internal Plaster ---
        int_wall_area = (len_20 + len_10) * floor_height
        ext_wall_area = ext_perimeter * floor_height
        ip = fc.calculate_internal_plaster(
            int_wall_area, ext_wall_area, doors_area, windows_area
        )
        items.append(_item("C.11", "Internal Plaster (Gypsum)", "m2",
                           ip["net_area_m2"], "Finishes", "internal_plaster", r))

        # --- External Villa Walls Finish ---
        evwf = fc.calculate_external_villa_walls_finish(ext_perimeter)
        items.append(_item("C.12", "External Villa Walls Finish", "m2",
                           evwf["area_m2"], "Finishes",
                           "external_villa_walls_finish", r))

        # --- Waterproofing ---
        first_floor_wet = sum(
            rm.get("area", 0) for rm in data.get("first_floor_rooms", [])
            if rm.get("room_type", "").lower() in
            {"toilet", "bathroom", "kitchen", "pantry", "laundry"}
        ) or wet_area_total * 0.5
        wp = fc.calculate_waterproofing(first_floor_wet, balcony_area)
        items.append(_item("C.13", "Waterproofing (1st Floor Wet Areas)", "m2",
                           wp["area_m2"], "Finishes", "waterproofing", r))

        # --- Combo Roof System ---
        roof_area = data.get("roof_area", data.get("plot_area", 153.0))
        crs = fc.calculate_combo_roof_system(roof_area)
        items.append(_item("C.14", "Combo Roof System", "m2",
                           crs["area_m2"], "Finishes", "combo_roof_system", r))

        # --- Thermal Block External ---
        tb_ext = fc.calculate_thermal_block_external(
            data.get("thermal_block_schedule_area"),
            plot_area, project_type, avg
        )
        items.append(_item("C.15", "Thermal Block (External Walls)", "m2",
                           tb_ext["area_m2"], "Finishes",
                           "thermal_block_external", r,
                           confidence_note=f"source={tb_ext['source']}"))

        # --- Interlock Paving ---
        il_pav = fc.calculate_interlock_paving(
            data.get("interlock_paving_area"),
            plot_area, project_type, avg
        )
        items.append(_item("C.16", "Interlock Paving", "m2",
                           il_pav["area_m2"], "Finishes",
                           "interlock_paving", r,
                           confidence_note=f"source={il_pav['source']}"))

        # --- False Ceiling ---
        fc_item = fc.calculate_false_ceiling(
            data.get("false_ceiling_area"),
            plot_area, project_type, avg
        )
        items.append(_item("C.17", "False Ceiling (Gypsum Board)", "m2",
                           fc_item["area_m2"], "Finishes",
                           "false_ceiling", r,
                           confidence_note=f"source={fc_item['source']}"))

        # --- Roof Waterproofing ---
        rw = fc.calculate_roof_waterproofing(
            data.get("roof_waterproofing_area"),
            plot_area, project_type, avg
        )
        items.append(_item("C.18", "Roof Waterproofing", "m2",
                           rw["area_m2"], "Finishes",
                           "roof_waterproofing", r,
                           confidence_note=f"source={rw['source']}"))

        return items
