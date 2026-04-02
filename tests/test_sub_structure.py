"""
Unit tests for SubStructureCalculator — verifying every formula.
"""

import pytest
from src.engine.sub_structure import SubStructureCalculator


@pytest.fixture
def calc():
    return SubStructureCalculator()


# ---------------------------------------------------------------------------
# 1. Foundation
# ---------------------------------------------------------------------------

class TestFoundation:
    def test_single_footing_volume(self, calc):
        footings = [{"width": 1.0, "length": 2.0, "depth": 0.5, "count": 1}]
        res = calc.calculate_foundation(footings)
        assert res["volume_m3"] == pytest.approx(1.0 * 2.0 * 0.5, rel=1e-6)

    def test_multiple_footings_volume(self, calc):
        footings = [
            {"width": 1.0, "length": 1.0, "depth": 0.5, "count": 4},
            {"width": 1.5, "length": 1.5, "depth": 0.6, "count": 2},
        ]
        res = calc.calculate_foundation(footings)
        expected_vol = (1.0 * 1.0 * 0.5 * 4) + (1.5 * 1.5 * 0.6 * 2)
        assert res["volume_m3"] == pytest.approx(expected_vol, rel=1e-6)

    def test_pcc_formula(self, calc):
        # PCC = (L+0.20) × (W+0.20) × 0.10 × count
        footings = [{"width": 1.0, "length": 2.0, "depth": 0.5, "count": 1}]
        res = calc.calculate_foundation(footings)
        expected_pcc = (2.0 + 0.20) * (1.0 + 0.20) * 0.10
        assert res["pcc_volume_m3"] == pytest.approx(expected_pcc, rel=1e-6)

    def test_bitumen_formula(self, calc):
        # Bitumen = (area + perimeter × depth) × count
        w, l, d = 1.0, 2.0, 0.5
        footings = [{"width": w, "length": l, "depth": d, "count": 1}]
        res = calc.calculate_foundation(footings)
        area = w * l
        perimeter = 2 * (w + l)
        expected_bitumen = area + (perimeter * d)
        assert res["bitumen_area_m2"] == pytest.approx(expected_bitumen, rel=1e-6)

    def test_count_multiplier(self, calc):
        footings = [{"width": 1.0, "length": 1.0, "depth": 0.5, "count": 5}]
        res_x5 = calc.calculate_foundation(footings)
        footings_x1 = [{"width": 1.0, "length": 1.0, "depth": 0.5, "count": 1}]
        res_x1 = calc.calculate_foundation(footings_x1)
        assert res_x5["volume_m3"] == pytest.approx(res_x1["volume_m3"] * 5, rel=1e-6)

    def test_empty_footings(self, calc):
        res = calc.calculate_foundation([])
        assert res["volume_m3"] == 0.0
        assert res["pcc_volume_m3"] == 0.0
        assert res["bitumen_area_m2"] == 0.0


# ---------------------------------------------------------------------------
# 2. Neck Columns
# ---------------------------------------------------------------------------

class TestNeckColumns:
    def test_height_formula(self, calc):
        # height = GFL + exc_depth - tb_depth - pcc_thickness
        res = calc.calculate_neck_columns(
            [{"width": 0.3, "length": 0.3, "count": 1}],
            gfl=0.3, exc_depth=1.5, tb_depth=0.4, pcc_thickness=0.1
        )
        expected_height = 0.3 + 1.5 - 0.4 - 0.1
        assert res["height_m"] == pytest.approx(expected_height, rel=1e-6)

    def test_volume_formula(self, calc):
        # Volume = width × length × height × count  (concrete volume in m³)
        w, l, count = 0.3, 0.3, 4
        gfl, exc_depth, tb_depth, pcc = 0.3, 1.5, 0.4, 0.1
        res = calc.calculate_neck_columns(
            [{"width": w, "length": l, "count": count}],
            gfl, exc_depth, tb_depth, pcc
        )
        height = gfl + exc_depth - tb_depth - pcc
        expected_vol = w * l * height * count
        assert res["volume_m3"] == pytest.approx(expected_vol, rel=1e-6)

    def test_empty_columns(self, calc):
        res = calc.calculate_neck_columns([], 0.3, 1.5, 0.4, 0.1)
        assert res["volume_m3"] == 0.0


# ---------------------------------------------------------------------------
# 3. Tie Beams
# ---------------------------------------------------------------------------

class TestTieBeams:
    def test_volume(self, calc):
        beams = [{"length": 5.0, "width": 0.3, "depth": 0.5, "count": 2}]
        res = calc.calculate_tie_beams(beams)
        expected = 5.0 * 0.3 * 0.5 * 2
        assert res["volume_m3"] == pytest.approx(expected, rel=1e-6)

    def test_pcc_formula(self, calc):
        # PCC = length × (width + 0.20) × 0.10 × count
        beams = [{"length": 5.0, "width": 0.3, "depth": 0.5, "count": 1}]
        res = calc.calculate_tie_beams(beams)
        expected_pcc = 5.0 * (0.3 + 0.20) * 0.10
        assert res["pcc_volume_m3"] == pytest.approx(expected_pcc, rel=1e-6)

    def test_bitumen_formula(self, calc):
        # Bitumen = length × depth × 2 × count
        beams = [{"length": 5.0, "width": 0.3, "depth": 0.5, "count": 1}]
        res = calc.calculate_tie_beams(beams)
        expected_bitumen = 5.0 * 0.5 * 2
        assert res["bitumen_area_m2"] == pytest.approx(expected_bitumen, rel=1e-6)

    def test_multiple_beams(self, calc):
        beams = [
            {"length": 5.0, "width": 0.30, "depth": 0.50, "count": 4},
            {"length": 3.5, "width": 0.30, "depth": 0.50, "count": 6},
        ]
        res = calc.calculate_tie_beams(beams)
        expected_vol = (5.0 * 0.30 * 0.50 * 4) + (3.5 * 0.30 * 0.50 * 6)
        assert res["volume_m3"] == pytest.approx(expected_vol, rel=1e-6)


# ---------------------------------------------------------------------------
# 4. Solid Block Work
# ---------------------------------------------------------------------------

class TestSolidBlockWork:
    def test_area_formula(self, calc):
        # height = GFL + exc_depth - tb_depth - pcc_thickness
        # area = wall_length × height
        walls = [{"wall_length": 50.0, "count": 1}]
        res = calc.calculate_solid_block_work(walls, 0.3, 1.5, 0.4, 0.1)
        height = 0.3 + 1.5 - 0.4 - 0.1
        expected = 50.0 * height
        assert res["area_m2"] == pytest.approx(expected, rel=1e-6)

    def test_bitumen_is_double_area(self, calc):
        walls = [{"wall_length": 30.0, "count": 1}]
        res = calc.calculate_solid_block_work(walls, 0.3, 1.5, 0.4, 0.1)
        assert res["bitumen_area_m2"] == pytest.approx(res["area_m2"] * 2.0, rel=1e-6)


# ---------------------------------------------------------------------------
# 5. Slab on Grade
# ---------------------------------------------------------------------------

class TestSlabOnGrade:
    def test_volume(self, calc):
        res = calc.calculate_slab_on_grade(100.0, 0.10)
        assert res["volume_m3"] == pytest.approx(10.0, rel=1e-6)

    def test_default_thickness(self, calc):
        res = calc.calculate_slab_on_grade(100.0)
        assert res["thickness_m"] == 0.10

    def test_area_preserved(self, calc):
        res = calc.calculate_slab_on_grade(75.5)
        assert res["area_m2"] == pytest.approx(75.5, rel=1e-6)


# ---------------------------------------------------------------------------
# 6. Excavation
# ---------------------------------------------------------------------------

class TestExcavation:
    def test_area_formula(self, calc):
        # Area = (2 + L) × (2 + W)
        res = calc.calculate_excavation(10.0, 8.0, 1.5)
        expected_area = (2.0 + 10.0) * (2.0 + 8.0)
        assert res["area_m2"] == pytest.approx(expected_area, rel=1e-6)

    def test_volume_formula(self, calc):
        # Volume = area × exc_level
        res = calc.calculate_excavation(10.0, 8.0, 1.5)
        expected_area = (2.0 + 10.0) * (2.0 + 8.0)
        expected_vol = expected_area * 1.5
        assert res["volume_m3"] == pytest.approx(expected_vol, rel=1e-6)


# ---------------------------------------------------------------------------
# 7. Back Filling
# ---------------------------------------------------------------------------

class TestBackFilling:
    def test_net_volume(self, calc):
        # net = (exc_area × (exc_level + gfsl_level)) - all_items_volume
        res = calc.calculate_back_filling(
            exc_area=120.0, exc_level=1.5, gfsl_level=0.3, all_items_volume=20.0
        )
        gross = 120.0 * (1.5 + 0.3)
        expected_net = gross - 20.0
        assert res["net_volume_m3"] == pytest.approx(expected_net, rel=1e-6)

    def test_never_negative(self, calc):
        res = calc.calculate_back_filling(
            exc_area=10.0, exc_level=1.0, gfsl_level=0.1, all_items_volume=999.0
        )
        assert res["net_volume_m3"] >= 0.0


# ---------------------------------------------------------------------------
# 8. Anti-Termite
# ---------------------------------------------------------------------------

class TestAntiTermite:
    def test_formula(self, calc):
        res = calc.calculate_anti_termite(100.0, 50.0)
        expected = (100.0 + 50.0) * 1.15
        assert res["area_m2"] == pytest.approx(expected, rel=1e-6)


# ---------------------------------------------------------------------------
# 9. Polyethylene Sheet
# ---------------------------------------------------------------------------

class TestPolyethyleneSheet:
    def test_formula(self, calc):
        res = calc.calculate_polyethylene_sheet(100.0, 50.0)
        assert res["area_m2"] == pytest.approx(150.0, rel=1e-6)


# ---------------------------------------------------------------------------
# 10. Road Base
# ---------------------------------------------------------------------------

class TestRoadBase:
    def test_volume(self, calc):
        res = calc.calculate_road_base(120.0, 0.25)
        assert res["volume_m3"] == pytest.approx(120.0 * 0.25, rel=1e-6)

    def test_default_thickness(self, calc):
        res = calc.calculate_road_base(100.0)
        assert res["thickness_m"] == 0.25
