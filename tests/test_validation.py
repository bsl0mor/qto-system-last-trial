"""
Unit tests for the QTO Validation layer.
"""

import json
import os
import pytest
from unittest.mock import patch, mock_open

from src.validation.validator import QTOValidator, ValidationResult, ValidationReport


# ---------------------------------------------------------------------------
# Fixtures — use real config files from the repo
# ---------------------------------------------------------------------------

@pytest.fixture
def validator():
    return QTOValidator()


# ---------------------------------------------------------------------------
# validate_item
# ---------------------------------------------------------------------------

class TestValidateItem:
    def test_item_within_tolerance_is_green(self, validator):
        # G+1 avg thermal_block_external = 359.7 m² @ avg_plot 587 m²
        # Exact match at avg plot → 0% deviation, n=42 → n_cap=100% → confidence=100%
        result = validator.validate_item(
            item_name="Thermal Block (External Walls)",
            calculated_qty=359.7,
            unit="m2",
            project_type="G+1",
            plot_area=587.0,
        )
        assert result.flag == "GREEN"
        assert result.confidence == pytest.approx(100.0, abs=0.1)
        assert not result.requires_manual_review

    def test_item_far_outside_tolerance_is_red(self, validator):
        # Massive deviation should produce RED
        result = validator.validate_item(
            item_name="Thermal Block (External Walls)",
            calculated_qty=1400.0,   # ~4× the avg at 587 m² plot
            unit="m2",
            project_type="G+1",
            plot_area=587.0,
        )
        assert result.flag == "RED"
        assert result.requires_manual_review

    def test_item_without_reference_data_gets_neutral_confidence(self, validator):
        # "Doors (Supply & Install)" has no key in averages.json
        result = validator.validate_item(
            item_name="Doors (Supply & Install)",
            calculated_qty=20.0,
            unit="m2",
            project_type="G+1",
            plot_area=153.0,
        )
        assert result.confidence == 100.0
        assert result.average_qty is None
        assert result.scaled_average is None

    def test_confidence_decreases_with_deviation(self, validator):
        # Close: exact average at avg plot → high confidence
        res_close = validator.validate_item(
            "Thermal Block (External Walls)", 359.7, "m2", "G+1", 587.0
        )
        # Far: 4× average → low confidence
        res_far = validator.validate_item(
            "Thermal Block (External Walls)", 1440.0, "m2", "G+1", 587.0
        )
        assert res_close.confidence > res_far.confidence

    def test_scaled_average_proportional_to_plot_area(self, validator):
        # Double the plot area → double the expected quantity
        res_normal = validator.validate_item(
            "Thermal Block (External Walls)", 359.7, "m2", "G+1", 587.0
        )
        res_double = validator.validate_item(
            "Thermal Block (External Walls)", 359.7, "m2", "G+1", 1174.0
        )
        assert res_double.scaled_average == pytest.approx(
            res_normal.scaled_average * 2, rel=0.01
        )


# ---------------------------------------------------------------------------
# validate_ratios
# ---------------------------------------------------------------------------

class TestValidateRatios:
    def test_thermal_block_to_block20_internal_ratio_g1(self, validator):
        # G+1 expected ratio: thermal_block_external / block_20_internal = 1.149
        # Provide both items at the exact expected ratio → GREEN
        tb_qty = 359.7
        b20_qty = round(tb_qty / 1.149, 1)
        boq = [
            {"description": "Thermal Block (External Walls)", "quantity": tb_qty, "unit": "m2"},
            {"description": "Block 20cm — Internal Walls",    "quantity": b20_qty, "unit": "m2"},
        ]
        results = validator.validate_ratios(boq, "G+1")
        assert len(results) >= 1
        target = next(
            r for r in results
            if r.ratio_name == "thermal_block_external_to_block_20_internal"
        )
        assert target.flag in ("GREEN", "YELLOW")

    def test_zero_denominator_gives_red(self, validator):
        boq = [
            {"description": "Thermal Block (External Walls)", "quantity": 359.7, "unit": "m2"},
            # block_20_internal missing → denominator zero for that ratio
        ]
        results = validator.validate_ratios(boq, "G+1")
        if results:
            red_results = [r for r in results if r.flag == "RED"]
            assert len(red_results) >= 1

    def test_no_ratio_checks_for_unknown_type(self, validator):
        boq = [{"description": "Thermal Block (External Walls)", "quantity": 359.7, "unit": "m2"}]
        results = validator.validate_ratios(boq, "G+3")   # undefined type → no ratio checks
        assert results == []


# ---------------------------------------------------------------------------
# validate_all
# ---------------------------------------------------------------------------

class TestValidateAll:
    def test_returns_validation_report(self, validator):
        boq = [
            {"description": "Thermal Block (External Walls)", "quantity": 359.7, "unit": "m2"},
            {"description": "Internal Plaster (Gypsum)",      "quantity": 1141.8, "unit": "m2"},
            {"description": "Dry Area Flooring",              "quantity": 196.1,  "unit": "m2"},
        ]
        report = validator.validate_all(boq, "G+1", 587.0)
        assert isinstance(report, ValidationReport)
        assert len(report.item_results) == 3
        assert report.project_type == "G+1"
        assert report.plot_area == 587.0

    def test_overall_confidence_is_weighted_average(self, validator):
        # Items at exact averages, avg plot area → 0 % deviation, n≥10 → confidence=100%
        boq = [
            {"description": "Thermal Block (External Walls)", "quantity": 359.7, "unit": "m2"},
            {"description": "Dry Area Flooring",              "quantity": 196.1, "unit": "m2"},
        ]
        report = validator.validate_all(boq, "G+1", 587.0)
        assert report.overall_confidence >= 95.0

    def test_draft_flag_when_confidence_below_threshold(self, validator):
        # Wildly wrong quantities → low confidence → DRAFT
        boq = [
            {"description": "Thermal Block (External Walls)", "quantity": 9999.0, "unit": "m2"},
            {"description": "Dry Area Flooring",              "quantity": 9999.0, "unit": "m2"},
        ]
        report = validator.validate_all(boq, "G+1", 587.0)
        assert report.is_draft is True

    def test_final_flag_when_confidence_high(self, validator):
        # Exact averages → confidence ~100% → is_draft False
        boq = [
            {"description": "Thermal Block (External Walls)", "quantity": 359.7, "unit": "m2"},
        ]
        report = validator.validate_all(boq, "G+1", 587.0)
        assert report.is_draft is False

    def test_summary_string_is_not_empty(self, validator):
        boq = [{"description": "Dry Area Flooring", "quantity": 100.0, "unit": "m2"}]
        report = validator.validate_all(boq, "G+1", 153.0)
        assert report.summary != ""

    def test_manual_review_count_in_summary(self, validator):
        boq = [
            {"description": "Thermal Block (External Walls)", "quantity": 9999.0, "unit": "m2"},
        ]
        report = validator.validate_all(boq, "G+1", 587.0)
        manual_review_items = [r for r in report.item_results if r.requires_manual_review]
        assert len(manual_review_items) >= 1
        assert "manual review" in report.summary.lower()
