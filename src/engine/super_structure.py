"""
Super-Structure Calculator — implements the exact formulas for above-grade structural elements.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# ---------------------------------------------------------------------------
# Data classes for input
# ---------------------------------------------------------------------------

@dataclass
class Slab:
    area: float         # m²
    thickness: float    # m


@dataclass
class Beam:
    length: float       # m
    width: float        # m
    depth: float        # m (overall depth including slab soffit to top)
    count: int = 1


@dataclass
class Column:
    length: float       # m (cross-section)
    width: float        # m (cross-section)
    qty: int = 1


# ---------------------------------------------------------------------------
# Calculator
# ---------------------------------------------------------------------------

class SuperStructureCalculator:
    """
    Calculates all super-structure QTO items according to the specified formulas.
    """

    # ------------------------------------------------------------------
    # 1. Slabs
    # ------------------------------------------------------------------
    def calculate_slabs(self, slabs: list[dict | Slab]) -> dict:
        """
        Volume = area × thickness  (per slab)
        """
        total_area = 0.0
        total_volume = 0.0

        for s in slabs:
            a = s["area"] if isinstance(s, dict) else s.area
            t = s["thickness"] if isinstance(s, dict) else s.thickness
            total_area += a
            total_volume += a * t

        return {
            "area_m2": round(total_area, 3),
            "volume_m3": round(total_volume, 3),
        }

    # ------------------------------------------------------------------
    # 2. Beams
    # ------------------------------------------------------------------
    def calculate_beams(
        self, beams: list[dict | Beam], slab_thickness: float
    ) -> dict:
        """
        Volume = length × width × (depth - slab_thickness)  per beam
        The portion embedded in the slab is excluded to avoid double-counting.
        """
        total_volume = 0.0

        for b in beams:
            l = b["length"] if isinstance(b, dict) else b.length
            w = b["width"] if isinstance(b, dict) else b.width
            d = b["depth"] if isinstance(b, dict) else b.depth
            n = b.get("count", 1) if isinstance(b, dict) else b.count

            net_depth = max(d - slab_thickness, 0.0)
            total_volume += l * w * net_depth * n

        return {"volume_m3": round(total_volume, 3)}

    # ------------------------------------------------------------------
    # 3. Columns
    # ------------------------------------------------------------------
    def calculate_columns(
        self, columns: list[dict | Column], floor_height: float
    ) -> dict:
        """
        Volume = length × width × floor_height × qty  (per column type)
        """
        total_volume = 0.0

        for c in columns:
            l = c["length"] if isinstance(c, dict) else c.length
            w = c["width"] if isinstance(c, dict) else c.width
            qty = c.get("qty", 1) if isinstance(c, dict) else c.qty
            total_volume += l * w * floor_height * qty

        return {"volume_m3": round(total_volume, 3)}

    # ------------------------------------------------------------------
    # 4. Dry Area Flooring
    # ------------------------------------------------------------------
    def calculate_dry_area_flooring(
        self, total_floor_area: float, wet_area: float
    ) -> dict:
        """
        Dry Area Flooring = total_floor_area - wet_area
        """
        dry = max(total_floor_area - wet_area, 0.0)
        return {"area_m2": round(dry, 3)}

    # ------------------------------------------------------------------
    # 5. Skirting
    # ------------------------------------------------------------------
    def calculate_skirting(
        self, dry_area_perimeter: float, door_widths: list[float]
    ) -> dict:
        """
        Skirting = perimeter_of_dry_areas - (40% of sum of door widths)
        """
        door_deduction = sum(door_widths) * 0.40
        skirting = max(dry_area_perimeter - door_deduction, 0.0)
        return {
            "perimeter_m": round(dry_area_perimeter, 3),
            "door_deduction_m": round(door_deduction, 3),
            "area_m": round(skirting, 3),  # skirting is linear metres (RM)
        }

    # ------------------------------------------------------------------
    # 6. Paint
    # ------------------------------------------------------------------
    def calculate_paint(
        self, skirting_length: float, floor_height: float
    ) -> dict:
        """
        Paint area = skirting_length × floor_height
        """
        area = skirting_length * floor_height
        return {"area_m2": round(area, 3)}

    # ------------------------------------------------------------------
    # 7. Dry Areas Ceiling
    # ------------------------------------------------------------------
    def calculate_dry_areas_ceiling(self, dry_area_flooring: float) -> dict:
        """
        Dry Areas Ceiling = Dry Areas Flooring  (1:1 relationship)
        """
        return {"area_m2": round(dry_area_flooring, 3)}
