"""
Unit tests for FinishesCalculator — verifying every architectural finish formula.
"""

import pytest
from src.engine.finishes import FinishesCalculator


@pytest.fixture
def calc():
    return FinishesCalculator()


SAMPLE_AVERAGES = {
    "G+1": {
        "meta": {"avg_plot_area": 153, "project_count": 101, "avg_cost_aed": 641278},
        "items": {
            "thermal_block_external": {"value": 466.0, "unit": "m2"},
            "interlock_paving":       {"value": 358.4, "unit": "m2"},
            "false_ceiling":          {"value": 259.0, "unit": "m2"},
            "roof_waterproofing":     {"value": 121.8, "unit": "m2"},
        }
    }
}


# ---------------------------------------------------------------------------
# 1. Wet Areas Flooring
# ---------------------------------------------------------------------------

class TestWetAreasFlooring:
    def test_sum_of_all_types(self, calc):
        res = calc.calculate_wet_areas_flooring(
            toilets=4.0, bathrooms=5.0, kitchens=12.0, pantries=3.0, laundry=3.5
        )
        assert res["area_m2"] == pytest.approx(27.5, rel=1e-6)

    def test_defaults_are_zero(self, calc):
        res = calc.calculate_wet_areas_flooring()
        assert res["area_m2"] == pytest.approx(0.0, abs=1e-9)

    def test_breakdown_sums_to_total(self, calc):
        res = calc.calculate_wet_areas_flooring(2.0, 3.0, 4.0, 1.0, 1.5)
        total = sum(res["breakdown"].values())
        assert total == pytest.approx(res["area_m2"], rel=1e-6)


# ---------------------------------------------------------------------------
# 2. Wall Tiles
# ---------------------------------------------------------------------------

class TestWallTiles:
    def test_formula(self, calc):
        # area = perimeter × (floor_height - 0.50)
        res = calc.calculate_wall_tiles(40.0, 3.0)
        expected = 40.0 * (3.0 - 0.50)
        assert res["area_m2"] == pytest.approx(expected, rel=1e-6)

    def test_floor_height_less_than_50cm(self, calc):
        # tiled_height should not go below zero
        res = calc.calculate_wall_tiles(20.0, 0.40)
        assert res["area_m2"] == pytest.approx(0.0, abs=1e-9)


# ---------------------------------------------------------------------------
# 3. Wet Areas Ceiling
# ---------------------------------------------------------------------------

class TestWetAreasCeiling:
    def test_equals_flooring(self, calc):
        res = calc.calculate_wet_areas_ceiling(30.5)
        assert res["area_m2"] == pytest.approx(30.5, rel=1e-6)


# ---------------------------------------------------------------------------
# 4. Balcony Flooring
# ---------------------------------------------------------------------------

class TestBalconyFlooring:
    def test_returns_area(self, calc):
        res = calc.calculate_balcony_flooring(12.0)
        assert res["area_m2"] == pytest.approx(12.0, rel=1e-6)

    def test_default_is_zero(self, calc):
        res = calc.calculate_balcony_flooring()
        assert res["area_m2"] == pytest.approx(0.0, abs=1e-9)


# ---------------------------------------------------------------------------
# 5. Marble Threshold
# ---------------------------------------------------------------------------

class TestMarbleThreshold:
    def test_sum_of_door_widths(self, calc):
        res = calc.calculate_marble_threshold([0.9, 0.9, 2.0, 0.9])
        assert res["length_rm"] == pytest.approx(4.7, rel=1e-6)

    def test_no_doors(self, calc):
        res = calc.calculate_marble_threshold([])
        assert res["length_rm"] == pytest.approx(0.0, abs=1e-9)


# ---------------------------------------------------------------------------
# 6. Block 20 External
# ---------------------------------------------------------------------------

class TestBlock20External:
    def test_net_area(self, calc):
        # net = (ext_perimeter × floor_height) - (windows + main_door)
        res = calc.calculate_block_20_external(
            external_villa_length=50.0,
            floor_height=3.0,
            windows_area=20.0,
            main_door_area=4.0,
        )
        expected_gross = 50.0 * 3.0
        expected_net = expected_gross - (20.0 + 4.0)
        assert res["gross_area_m2"] == pytest.approx(expected_gross, rel=1e-6)
        assert res["net_area_m2"] == pytest.approx(expected_net, rel=1e-6)

    def test_deductions_larger_than_gross_gives_zero(self, calc):
        res = calc.calculate_block_20_external(5.0, 2.0, 50.0, 10.0)
        assert res["net_area_m2"] >= 0.0


# ---------------------------------------------------------------------------
# 7. Block 20 Internal
# ---------------------------------------------------------------------------

class TestBlock20Internal:
    def test_net_area_formula(self, calc):
        # net = (length × floor_height) - 40% door areas
        res = calc.calculate_block_20_internal(40.0, 3.0, 20.0)
        expected_gross = 40.0 * 3.0
        expected_net = expected_gross - (20.0 * 0.40)
        assert res["net_area_m2"] == pytest.approx(expected_net, rel=1e-6)


# ---------------------------------------------------------------------------
# 8. Block 10 Internal
# ---------------------------------------------------------------------------

class TestBlock10Internal:
    def test_net_area_formula(self, calc):
        res = calc.calculate_block_10_internal(20.0, 3.0, 10.0)
        expected_gross = 20.0 * 3.0
        expected_net = expected_gross - (10.0 * 0.40)
        assert res["net_area_m2"] == pytest.approx(expected_net, rel=1e-6)


# ---------------------------------------------------------------------------
# 9. Internal Plaster
# ---------------------------------------------------------------------------

class TestInternalPlaster:
    def test_full_formula(self, calc):
        # net = ((int_walls × 2) + ext_walls) - (doors × 2 + windows)
        res = calc.calculate_internal_plaster(
            internal_walls_area=300.0,
            external_walls_area=150.0,
            doors_area=20.0,
            windows_area=15.0,
        )
        expected_gross = (300.0 * 2) + 150.0
        expected_net = expected_gross - (20.0 * 2 + 15.0)
        assert res["gross_area_m2"] == pytest.approx(expected_gross, rel=1e-6)
        assert res["net_area_m2"] == pytest.approx(expected_net, rel=1e-6)


# ---------------------------------------------------------------------------
# 10. External Villa Walls Finish
# ---------------------------------------------------------------------------

class TestExternalVillaWallsFinish:
    def test_default_two_floors_plus_1_5m(self, calc):
        # total_height = 2 × floor_height + 1.5 m
        res = calc.calculate_external_villa_walls_finish(50.0, floor_count=2, floor_height=3.0)
        total_h = 2 * 3.0 + 1.5
        expected = 50.0 * total_h
        assert res["area_m2"] == pytest.approx(expected, rel=1e-6)


# ---------------------------------------------------------------------------
# 11. Waterproofing
# ---------------------------------------------------------------------------

class TestWaterproofing:
    def test_wet_only(self, calc):
        res = calc.calculate_waterproofing(first_floor_wet_area=20.0)
        assert res["area_m2"] == pytest.approx(20.0, rel=1e-6)

    def test_no_balcony(self, calc):
        res = calc.calculate_waterproofing(15.0)
        assert res["area_m2"] == pytest.approx(15.0, rel=1e-6)

    def test_balcony_waterproofing_separate(self, calc):
        res = calc.calculate_balcony_waterproofing(balcony_area=10.0)
        assert res["area_m2"] == pytest.approx(10.0, rel=1e-6)

    def test_balcony_waterproofing_default_zero(self, calc):
        res = calc.calculate_balcony_waterproofing()
        assert res["area_m2"] == pytest.approx(0.0, abs=1e-9)


# ---------------------------------------------------------------------------
# 12. Combo Roof System
# ---------------------------------------------------------------------------

class TestComboRoofSystem:
    def test_multiplier_1_2(self, calc):
        res = calc.calculate_combo_roof_system(100.0)
        assert res["area_m2"] == pytest.approx(120.0, rel=1e-6)


# ---------------------------------------------------------------------------
# 13. Openings
# ---------------------------------------------------------------------------

class TestOpenings:
    def test_single_door(self, calc):
        openings = [{"opening_type": "door", "width": 0.9, "height": 2.1, "count": 1}]
        res = calc.calculate_openings(openings)
        assert res["total_door_area_m2"] == pytest.approx(0.9 * 2.1, rel=1e-6)
        assert res["total_window_area_m2"] == pytest.approx(0.0, abs=1e-9)

    def test_multiple_openings(self, calc):
        openings = [
            {"opening_type": "door",   "width": 2.0, "height": 2.4, "count": 1},
            {"opening_type": "door",   "width": 0.9, "height": 2.1, "count": 8},
            {"opening_type": "window", "width": 1.8, "height": 1.5, "count": 6},
        ]
        res = calc.calculate_openings(openings)
        expected_doors = (2.0 * 2.4 * 1) + (0.9 * 2.1 * 8)
        expected_windows = 1.8 * 1.5 * 6
        assert res["total_door_area_m2"] == pytest.approx(expected_doors, rel=1e-6)
        assert res["total_window_area_m2"] == pytest.approx(expected_windows, rel=1e-6)
        assert res["total_area_m2"] == pytest.approx(
            expected_doors + expected_windows, rel=1e-6
        )

    def test_count_multiplied(self, calc):
        openings = [{"opening_type": "window", "width": 1.2, "height": 1.2, "count": 4}]
        res = calc.calculate_openings(openings)
        assert res["total_window_area_m2"] == pytest.approx(1.2 * 1.2 * 4, rel=1e-6)


# ---------------------------------------------------------------------------
# 14-17. Average-data items (schedule provided)
# ---------------------------------------------------------------------------

class TestAverageDataItems:
    def test_thermal_block_uses_schedule_when_provided(self, calc):
        res = calc.calculate_thermal_block_external(schedule_area=466.0)
        assert res["area_m2"] == pytest.approx(466.0, rel=1e-6)
        assert res["source"] == "schedule"

    def test_thermal_block_scales_from_averages(self, calc):
        res = calc.calculate_thermal_block_external(
            schedule_area=None,
            plot_area=306.0,   # double the avg plot (153 m²)
            project_type="G+1",
            averages=SAMPLE_AVERAGES,
        )
        # Should be approximately 466 × (306/153) = 932
        assert res["area_m2"] == pytest.approx(466.0 * 2, rel=0.01)
        assert res["source"] == "scaled_average"

    def test_combo_roof_1_2_multiplier(self, calc):
        res = calc.calculate_combo_roof_system(150.0)
        assert res["area_m2"] == pytest.approx(180.0, rel=1e-6)

    def test_roof_waterproofing_uses_schedule(self, calc):
        res = calc.calculate_roof_waterproofing(schedule_area=121.8)
        assert res["area_m2"] == pytest.approx(121.8, rel=1e-6)
        assert res["source"] == "schedule"

    def test_false_ceiling_scales_from_averages(self, calc):
        res = calc.calculate_false_ceiling(
            schedule_area=None,
            plot_area=153.0,
            project_type="G+1",
            averages=SAMPLE_AVERAGES,
        )
        # Same plot → same average
        assert res["area_m2"] == pytest.approx(259.0, rel=0.01)

    def test_interlock_paving_no_data_returns_zero(self, calc):
        res = calc.calculate_interlock_paving(schedule_area=None, plot_area=None)
        assert res["area_m2"] == pytest.approx(0.0, abs=1e-9)
        assert res["source"] == "unavailable"
