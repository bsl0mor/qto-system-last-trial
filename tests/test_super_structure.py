"""
Unit tests for SuperStructureCalculator — verifying every formula.
"""

import pytest
from src.engine.super_structure import SuperStructureCalculator


@pytest.fixture
def calc():
    return SuperStructureCalculator()


# ---------------------------------------------------------------------------
# 1. Slabs
# ---------------------------------------------------------------------------

class TestSlabs:
    def test_single_slab_volume(self, calc):
        slabs = [{"area": 100.0, "thickness": 0.20}]
        res = calc.calculate_slabs(slabs)
        assert res["volume_m3"] == pytest.approx(20.0, rel=1e-6)

    def test_multiple_slabs_total_area(self, calc):
        slabs = [
            {"area": 80.0, "thickness": 0.20},
            {"area": 80.0, "thickness": 0.20},
        ]
        res = calc.calculate_slabs(slabs)
        assert res["area_m2"] == pytest.approx(160.0, rel=1e-6)

    def test_multiple_slabs_total_volume(self, calc):
        slabs = [
            {"area": 50.0, "thickness": 0.15},
            {"area": 70.0, "thickness": 0.20},
        ]
        res = calc.calculate_slabs(slabs)
        expected = 50.0 * 0.15 + 70.0 * 0.20
        assert res["volume_m3"] == pytest.approx(expected, rel=1e-6)

    def test_empty_slabs(self, calc):
        res = calc.calculate_slabs([])
        assert res["volume_m3"] == 0.0
        assert res["area_m2"] == 0.0


# ---------------------------------------------------------------------------
# 2. Beams
# ---------------------------------------------------------------------------

class TestBeams:
    def test_net_depth_deducts_slab(self, calc):
        # Volume = length × width × (depth - slab_thickness)
        beams = [{"length": 5.0, "width": 0.25, "depth": 0.60, "count": 1}]
        slab_t = 0.20
        res = calc.calculate_beams(beams, slab_t)
        expected = 5.0 * 0.25 * (0.60 - 0.20)
        assert res["volume_m3"] == pytest.approx(expected, rel=1e-6)

    def test_slab_thicker_than_beam_gives_zero(self, calc):
        beams = [{"length": 5.0, "width": 0.25, "depth": 0.20, "count": 1}]
        res = calc.calculate_beams(beams, slab_thickness=0.25)
        assert res["volume_m3"] == pytest.approx(0.0, abs=1e-9)

    def test_multiple_beams_count(self, calc):
        beams = [{"length": 4.0, "width": 0.25, "depth": 0.60, "count": 8}]
        res = calc.calculate_beams(beams, 0.20)
        expected = 4.0 * 0.25 * (0.60 - 0.20) * 8
        assert res["volume_m3"] == pytest.approx(expected, rel=1e-6)


# ---------------------------------------------------------------------------
# 3. Columns
# ---------------------------------------------------------------------------

class TestColumns:
    def test_volume_formula(self, calc):
        # Volume = length × width × floor_height × qty
        columns = [{"length": 0.30, "width": 0.30, "qty": 12}]
        res = calc.calculate_columns(columns, floor_height=3.0)
        expected = 0.30 * 0.30 * 3.0 * 12
        assert res["volume_m3"] == pytest.approx(expected, rel=1e-6)

    def test_multiple_column_types(self, calc):
        columns = [
            {"length": 0.30, "width": 0.30, "qty": 8},
            {"length": 0.40, "width": 0.40, "qty": 4},
        ]
        res = calc.calculate_columns(columns, floor_height=3.0)
        expected = (0.30 * 0.30 * 3.0 * 8) + (0.40 * 0.40 * 3.0 * 4)
        assert res["volume_m3"] == pytest.approx(expected, rel=1e-6)


# ---------------------------------------------------------------------------
# 4. Dry Area Flooring
# ---------------------------------------------------------------------------

class TestDryAreaFlooring:
    def test_dry_equals_total_minus_wet(self, calc):
        res = calc.calculate_dry_area_flooring(153.0, 30.0)
        assert res["area_m2"] == pytest.approx(123.0, rel=1e-6)

    def test_result_never_negative(self, calc):
        res = calc.calculate_dry_area_flooring(50.0, 100.0)
        assert res["area_m2"] >= 0.0

    def test_zero_wet_equals_total(self, calc):
        res = calc.calculate_dry_area_flooring(200.0, 0.0)
        assert res["area_m2"] == pytest.approx(200.0, rel=1e-6)


# ---------------------------------------------------------------------------
# 5. Skirting
# ---------------------------------------------------------------------------

class TestSkirting:
    def test_deducts_40_percent_of_doors(self, calc):
        # Skirting = perimeter - 40% of sum(door widths)
        door_widths = [0.9, 0.9, 0.9, 2.0]
        perimeter = 100.0
        res = calc.calculate_skirting(perimeter, door_widths)
        deduction = sum(door_widths) * 0.40
        expected = perimeter - deduction
        assert res["area_m"] == pytest.approx(expected, rel=1e-6)

    def test_no_doors_equals_perimeter(self, calc):
        res = calc.calculate_skirting(80.0, [])
        assert res["area_m"] == pytest.approx(80.0, rel=1e-6)

    def test_result_never_negative(self, calc):
        res = calc.calculate_skirting(5.0, [100.0])
        assert res["area_m"] >= 0.0


# ---------------------------------------------------------------------------
# 6. Paint
# ---------------------------------------------------------------------------

class TestPaint:
    def test_area_formula(self, calc):
        # Paint = skirting_length × floor_height
        res = calc.calculate_paint(80.0, 3.0)
        assert res["area_m2"] == pytest.approx(240.0, rel=1e-6)

    def test_zero_skirting(self, calc):
        res = calc.calculate_paint(0.0, 3.0)
        assert res["area_m2"] == pytest.approx(0.0, abs=1e-9)


# ---------------------------------------------------------------------------
# 8. Parapet Block Work
# ---------------------------------------------------------------------------

class TestParapetBlock:
    def test_area_formula(self, calc):
        # Area = perimeter × height
        res = calc.calculate_parapet_block(perimeter=82.0, height=1.0)
        assert res["area_m2"] == pytest.approx(82.0, rel=1e-6)

    def test_custom_height(self, calc):
        res = calc.calculate_parapet_block(perimeter=60.0, height=1.2)
        assert res["area_m2"] == pytest.approx(60.0 * 1.2, rel=1e-6)

    def test_default_height_is_1m(self, calc):
        res = calc.calculate_parapet_block(perimeter=50.0)
        assert res["area_m2"] == pytest.approx(50.0, rel=1e-6)

    def test_zero_perimeter(self, calc):
        res = calc.calculate_parapet_block(perimeter=0.0)
        assert res["area_m2"] == pytest.approx(0.0, abs=1e-9)


# ---------------------------------------------------------------------------
# 9. Parapet Concrete Capping
# ---------------------------------------------------------------------------

class TestParapetConcrete:
    def test_volume_formula(self, calc):
        # Volume = perimeter × thickness × capping_height
        res = calc.calculate_parapet_concrete(
            perimeter=82.0, thickness=0.15, capping_height=0.20
        )
        expected = 82.0 * 0.15 * 0.20
        assert res["volume_m3"] == pytest.approx(expected, rel=1e-6)

    def test_default_dimensions(self, calc):
        # defaults: thickness=0.20, capping_height=0.20
        res = calc.calculate_parapet_concrete(perimeter=82.0)
        expected = 82.0 * 0.20 * 0.20
        assert res["volume_m3"] == pytest.approx(expected, rel=1e-6)

    def test_zero_perimeter(self, calc):
        res = calc.calculate_parapet_concrete(perimeter=0.0)
        assert res["volume_m3"] == pytest.approx(0.0, abs=1e-9)

