"""Tests for super-structure calculations."""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.engine.super_structure import SuperStructureCalculator


@pytest.fixture
def calc():
    return SuperStructureCalculator()


SAMPLE_FLOORS = [
    {
        "level": "Ground Floor",
        "total_area": 110.0,
        "slabs": [{"area": 110.0, "thickness": 0.2}],
        "beams": [
            {"length": 10.0, "width": 0.3, "depth": 0.6, "count": 4},
            {"length": 8.0, "width": 0.3, "depth": 0.6, "count": 3}
        ],
        "columns": [{"width": 0.3, "length": 0.3, "floor_height": 3.0, "qty": 12}]
    },
    {
        "level": "First Floor",
        "total_area": 110.0,
        "slabs": [{"area": 110.0, "thickness": 0.2}],
        "beams": [
            {"length": 10.0, "width": 0.3, "depth": 0.6, "count": 4},
            {"length": 8.0, "width": 0.3, "depth": 0.6, "count": 3}
        ],
        "columns": [{"width": 0.3, "length": 0.3, "floor_height": 3.0, "qty": 12}]
    }
]


def test_slabs(calc):
    result = calc.calculate_slabs(SAMPLE_FLOORS)
    assert result['total_area'] == pytest.approx(220.0)
    assert result['total_volume'] == pytest.approx(220.0 * 0.2)


def test_beams(calc):
    result = calc.calculate_beams(SAMPLE_FLOORS, slab_thickness=0.2)
    eff = 0.6 - 0.2
    expected = 2 * (10.0 * 0.3 * eff * 4 + 8.0 * 0.3 * eff * 3)
    assert result['total_volume'] == pytest.approx(expected)


def test_columns(calc):
    result = calc.calculate_columns(SAMPLE_FLOORS)
    expected = 2 * (0.3 * 0.3 * 3.0 * 12)
    assert result['total_volume'] == pytest.approx(expected)


def test_dry_area_flooring(calc):
    result = calc.calculate_dry_area_flooring(total_floor_area=220.0, wet_area_flooring=35.0)
    assert result['area'] == pytest.approx(185.0)


def test_dry_area_flooring_no_negative(calc):
    result = calc.calculate_dry_area_flooring(total_floor_area=30.0, wet_area_flooring=40.0)
    assert result['area'] == 0.0


def test_skirting(calc):
    dry_areas = [{"area": 15.0, "perimeter": 16.0}, {"area": 25.0, "perimeter": 20.0}]
    doors = [{"type": "bedroom_door", "width": 0.9, "count": 2}]
    result = calc.calculate_skirting(dry_areas, doors)
    expected = (16.0 + 20.0) - 0.4 * (0.9 * 2)
    assert result['area'] == pytest.approx(expected)


def test_paint(calc):
    result = calc.calculate_paint(skirting_area=100.0, floor_height=3.0)
    assert result['area'] == pytest.approx(300.0)


def test_dry_areas_ceiling(calc):
    result = calc.calculate_dry_areas_ceiling(dry_area_flooring=185.0)
    assert result['area'] == pytest.approx(185.0)
