"""Tests for sub-structure calculations."""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.engine.sub_structure import SubStructureCalculator


@pytest.fixture
def calc():
    return SubStructureCalculator(pcc_thickness=0.1)


def test_foundation_basic(calc):
    foundations = [{'type': 'F1', 'width': 1.5, 'length': 1.5, 'depth': 0.5, 'count': 8}]
    result = calc.calculate_foundation(foundations)
    assert result['total_area'] == pytest.approx(18.0)
    assert result['total_volume'] == pytest.approx(9.0)
    assert result['total_pcc_area'] == pytest.approx(8 * 1.7 * 1.7)


def test_foundation_multiple(calc):
    foundations = [
        {'type': 'F1', 'width': 1.5, 'length': 1.5, 'depth': 0.5, 'count': 8},
        {'type': 'F2', 'width': 2.0, 'length': 2.0, 'depth': 0.6, 'count': 4},
    ]
    result = calc.calculate_foundation(foundations)
    assert result['total_area'] == pytest.approx(18.0 + 16.0)
    assert result['total_volume'] == pytest.approx(9.0 + 9.6)
    assert len(result['details']) == 2


def test_neck_columns(calc):
    nc = [{'id': 'NC1', 'width': 0.3, 'length': 0.3, 'perimeter': 1.2, 'height': 1.3, 'count': 12}]
    result = calc.calculate_neck_columns(nc)
    assert result['total_volume'] == pytest.approx(1.2 * 1.3 * 12)


def test_tie_beams(calc):
    tbs = [
        {'id': 'TB1', 'length': 10.0, 'width': 0.3, 'depth': 0.5},
        {'id': 'TB2', 'length': 8.0, 'width': 0.3, 'depth': 0.5},
    ]
    result = calc.calculate_tie_beams(tbs)
    assert result['total_volume'] == pytest.approx(10.0 * 0.3 * 0.5 + 8.0 * 0.3 * 0.5)


def test_solid_block_work(calc):
    sbw = [{'id': 'SBW1', 'length': 46.0, 'height': 1.0}]
    result = calc.calculate_solid_block_work(sbw, gfl=0.0, excavation_depth=1.5, tb_depth=0.5, pcc_thickness=0.1)
    expected_height = 0.0 + 1.5 - 0.5 - 0.1
    assert result['total_area'] == pytest.approx(46.0 * expected_height)


def test_slab_on_grade(calc):
    sog = {'area': 110.0, 'thickness': 0.1}
    result = calc.calculate_slab_on_grade(sog)
    assert result['area'] == pytest.approx(110.0)
    assert result['volume'] == pytest.approx(11.0)


def test_excavation(calc):
    exc = {'longest_length': 14.0, 'longest_width': 11.0, 'excavation_level': 1.5}
    result = calc.calculate_excavation(exc)
    assert result['area'] == pytest.approx(16.0 * 13.0)
    assert result['volume'] == pytest.approx(16.0 * 13.0 * 1.5)


def test_back_filling(calc):
    exc_result = {'area': 208.0, 'volume': 312.0, 'excavation_level': 1.5}
    result = calc.calculate_back_filling(exc_result, gfsl_level=0.3, all_items_volume=50.0)
    expected = 208.0 * (1.5 + 0.3) - 50.0
    assert result['volume'] == pytest.approx(expected)


def test_anti_termite(calc):
    result = calc.calculate_anti_termite(total_pcc_area=50.0, slab_on_grade_area=110.0)
    assert result['area'] == pytest.approx(160.0 * 1.15)


def test_polyethylene_sheet(calc):
    result = calc.calculate_polyethylene_sheet(total_pcc_area=50.0, slab_on_grade_area=110.0)
    assert result['area'] == pytest.approx(160.0)


def test_road_base(calc):
    exc_result = {'area': 208.0, 'volume': 312.0, 'excavation_level': 1.5}
    result = calc.calculate_road_base(exc_result, thickness=0.25)
    assert result['volume'] == pytest.approx(208.0 * 0.25)
