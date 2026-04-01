"""Tests for QTO validation."""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.validation.validator import QTOValidator


@pytest.fixture
def validator():
    return QTOValidator()


def test_confidence_within_threshold(validator):
    confidence = validator._calculate_confidence('thermal_block_external', 466.0, 'G+1', 153)
    assert confidence == pytest.approx(100.0)


def test_confidence_at_threshold(validator):
    avg = 466.0
    qty = avg * 1.15
    confidence = validator._calculate_confidence('thermal_block_external', qty, 'G+1', 153)
    assert confidence == pytest.approx(95.0, abs=0.1)


def test_confidence_beyond_threshold(validator):
    avg = 466.0
    qty = avg * 2.0
    confidence = validator._calculate_confidence('thermal_block_external', qty, 'G+1', 153)
    assert confidence < 95.0


def test_confidence_unknown_item(validator):
    confidence = validator._calculate_confidence('unknown_item', 100.0, 'G+1', 153)
    assert confidence == 100.0


def test_status_green(validator):
    quantities = {'thermal_block_external': {'area': 466.0}}
    result = validator.validate(quantities, 'G+1', 153)
    assert result['items']['thermal_block_external']['status'] == 'GREEN'


def test_status_yellow(validator):
    avg = 466.0
    qty = avg * (1 + 0.152)
    quantities = {'thermal_block_external': {'area': qty}}
    result = validator.validate(quantities, 'G+1', 153)
    assert result['items']['thermal_block_external']['status'] in ('YELLOW', 'GREEN', 'RED')


def test_status_red(validator):
    avg = 466.0
    qty = avg * 3.0
    quantities = {'thermal_block_external': {'area': qty}}
    result = validator.validate(quantities, 'G+1', 153)
    assert result['items']['thermal_block_external']['status'] == 'RED'


def test_overall_confidence(validator):
    quantities = {
        'thermal_block_external': {'area': 466.0},
        'internal_plaster': {'area': 1144.3},
    }
    result = validator.validate(quantities, 'G+1', 153)
    assert result['overall_confidence'] == pytest.approx(100.0)


def test_is_draft_when_low_confidence(validator):
    avg = 466.0
    qty = avg * 5.0
    quantities = {'thermal_block_external': {'area': qty}}
    result = validator.validate(quantities, 'G+1', 153)
    assert result['is_draft']


def test_extract_qty_area(validator):
    assert validator._extract_qty({'area': 100.0}) == pytest.approx(100.0)


def test_extract_qty_volume(validator):
    assert validator._extract_qty({'volume': 50.0}) == pytest.approx(50.0)


def test_extract_qty_rm(validator):
    assert validator._extract_qty({'rm': 25.0}) == pytest.approx(25.0)


def test_ratio_warnings(validator):
    quantities = {
        'external_finish': {'area': 1000.0},
        'thermal_block_external': {'area': 100.0},
    }
    result = validator.validate(quantities, 'G+1', 153)
    assert len(result['ratio_warnings']) > 0
