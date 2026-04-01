"""Tests for finishes calculations."""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.engine.finishes import FinishesCalculator


@pytest.fixture
def calc():
    return FinishesCalculator()


WET_AREAS = [
    {"type": "toilet", "area": 3.5, "perimeter": 7.5},
    {"type": "toilet", "area": 3.5, "perimeter": 7.5},
    {"type": "bathroom", "area": 6.0, "perimeter": 10.0},
    {"type": "bathroom", "area": 6.0, "perimeter": 10.0},
    {"type": "kitchen", "area": 12.0, "perimeter": 14.0},
    {"type": "laundry", "area": 4.0, "perimeter": 8.0},
]

DOORS = [
    {"type": "main_door", "width": 1.2, "height": 2.4, "count": 1},
    {"type": "bedroom_door", "width": 0.9, "height": 2.1, "count": 6},
    {"type": "bathroom_door", "width": 0.8, "height": 2.1, "count": 4},
]

WINDOWS = [
    {"type": "bedroom_window", "width": 1.5, "height": 1.2, "count": 6},
    {"type": "living_window", "width": 2.0, "height": 1.5, "count": 3},
    {"type": "kitchen_window", "width": 1.2, "height": 1.0, "count": 2},
]


def test_wet_area_flooring(calc):
    result = calc.calculate_wet_area_flooring(WET_AREAS)
    assert result['area'] == pytest.approx(3.5 + 3.5 + 6.0 + 6.0 + 12.0 + 4.0)


def test_wall_tiles(calc):
    result = calc.calculate_wall_tiles(WET_AREAS, floor_height=3.0)
    total_perimeter = 7.5 + 7.5 + 10.0 + 10.0 + 14.0 + 8.0
    assert result['area'] == pytest.approx(total_perimeter * (3.0 - 0.5))


def test_wet_areas_ceiling(calc):
    result = calc.calculate_wet_areas_ceiling(35.0)
    assert result['area'] == pytest.approx(35.0)


def test_balcony_flooring_exists(calc):
    balcony = {"exists": True, "area": 12.0, "perimeter": 14.0}
    result = calc.calculate_balcony_flooring(balcony)
    assert result['area'] == pytest.approx(12.0)


def test_balcony_flooring_no_balcony(calc):
    result = calc.calculate_balcony_flooring({"exists": False, "area": 0.0})
    assert result['area'] == 0.0


def test_marble_threshold(calc):
    result = calc.calculate_marble_threshold(DOORS)
    expected = 1.2 * 1 + 0.9 * 6 + 0.8 * 4
    assert result['rm'] == pytest.approx(expected)


def test_block_20_external(calc):
    main_door = {"type": "main_door", "width": 1.2, "height": 2.4, "count": 1}
    result = calc.calculate_block_20_external(46.0, 3.0, WINDOWS, main_door)
    wall_area = 46.0 * 3.0
    win_area = 1.5 * 1.2 * 6 + 2.0 * 1.5 * 3 + 1.2 * 1.0 * 2
    door_area = 1.2 * 2.4 * 1
    assert result['area'] == pytest.approx(wall_area - win_area - door_area)


def test_block_20_internal(calc):
    result = calc.calculate_block_20_internal(85.0, 3.0, DOORS)
    wall_area = 85.0 * 3.0
    door_area = 1.2*2.4*1 + 0.9*2.1*6 + 0.8*2.1*4
    assert result['area'] == pytest.approx(wall_area - 0.4 * door_area)


def test_block_10_internal(calc):
    result = calc.calculate_block_10_internal(30.0, 3.0, DOORS)
    wall_area = 30.0 * 3.0
    door_area = 1.2*2.4*1 + 0.9*2.1*6 + 0.8*2.1*4
    assert result['area'] == pytest.approx(wall_area - 0.4 * door_area)


def test_internal_plaster(calc):
    result = calc.calculate_internal_plaster(85.0, 30.0, 46.0, 3.0, DOORS, WINDOWS, num_floors=2)
    assert result['area'] > 0


def test_external_finish(calc):
    result = calc.calculate_external_finish(46.0, 3.0, num_floors=2)
    assert result['area'] == pytest.approx(46.0 * (2 * 3.0 + 1.5))


def test_waterproofing(calc):
    result = calc.calculate_waterproofing(17.5, balcony_area=12.0)
    assert result['area'] == pytest.approx(29.5)


def test_combo_roof_system(calc):
    result = calc.calculate_combo_roof_system(110.0)
    assert result['area'] == pytest.approx(132.0)


def test_thermal_block_external(calc):
    result = calc.calculate_thermal_block_external(46.0, 3.0, num_floors=2)
    assert result['area'] == pytest.approx(46.0 * 3.0 * 2)


def test_interlock_paving(calc):
    result = calc.calculate_interlock_paving(plot_area=153.0, built_up_area=110.0)
    assert result['area'] == pytest.approx(43.0)


def test_false_ceiling(calc):
    result = calc.calculate_false_ceiling(dry_area_flooring=185.0, wet_area_flooring=35.0)
    assert result['area'] == pytest.approx(220.0)


def test_roof_waterproofing(calc):
    result = calc.calculate_roof_waterproofing(110.0)
    assert result['area'] == pytest.approx(110.0)
