"""Integration tests for the full QTO pipeline."""
import pytest
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_INPUT = os.path.join(PROJECT_ROOT, 'samples', 'sample_input.json')
OUTPUT_XLSX = os.path.join(PROJECT_ROOT, 'output_boq_test.xlsx')


@pytest.fixture
def sample_data():
    with open(SAMPLE_INPUT, 'r') as f:
        return json.load(f)


@pytest.fixture(autouse=True)
def cleanup():
    yield
    if os.path.exists(OUTPUT_XLSX):
        os.remove(OUTPUT_XLSX)


def test_sample_input_exists():
    assert os.path.exists(SAMPLE_INPUT), f"Sample input not found: {SAMPLE_INPUT}"


def test_full_pipeline(sample_data):
    from src.engine.qto_engine import QTOEngine
    from src.validation.validator import QTOValidator
    from src.output.excel_generator import ExcelGenerator

    engine = QTOEngine()
    quantities = engine.calculate(sample_data)
    
    assert len(quantities) >= 25, f"Expected >= 25 items, got {len(quantities)}"


def test_engine_produces_required_keys(sample_data):
    from src.engine.qto_engine import QTOEngine
    engine = QTOEngine()
    quantities = engine.calculate(sample_data)
    
    required_keys = [
        'excavation', 'foundation', 'neck_columns', 'tie_beams', 'solid_block_work',
        'slab_on_grade', 'back_filling', 'anti_termite', 'polyethylene_sheet',
        'slabs', 'beams', 'columns', 'dry_area_flooring', 'skirting', 'paint',
        'wet_area_flooring', 'wall_tiles', 'wet_areas_ceiling', 'balcony_flooring',
        'marble_threshold', 'block_20_external', 'block_20_internal', 'block_10_internal',
        'internal_plaster', 'external_finish', 'waterproofing', 'combo_roof_system',
        'thermal_block_external', 'interlock_paving', 'false_ceiling', 'roof_waterproofing'
    ]
    for key in required_keys:
        assert key in quantities, f"Missing key: {key}"


def test_validation_results(sample_data):
    from src.engine.qto_engine import QTOEngine
    from src.validation.validator import QTOValidator
    
    engine = QTOEngine()
    quantities = engine.calculate(sample_data)
    
    validator = QTOValidator()
    validated = validator.validate(quantities, 'G+1', sample_data['plot_area'])
    
    assert 'items' in validated
    assert 'overall_confidence' in validated
    assert 'is_draft' in validated
    assert 0 <= validated['overall_confidence'] <= 100


def test_excel_generation(sample_data):
    from src.engine.qto_engine import QTOEngine
    from src.validation.validator import QTOValidator
    from src.output.excel_generator import ExcelGenerator
    
    engine = QTOEngine()
    quantities = engine.calculate(sample_data)
    
    validator = QTOValidator()
    validated = validator.validate(quantities, 'G+1', sample_data['plot_area'])
    
    generator = ExcelGenerator()
    result_path = generator.generate(
        quantities, validated, OUTPUT_XLSX,
        sample_data['project_name'], sample_data['project_type']
    )
    
    assert os.path.exists(OUTPUT_XLSX), f"Excel file not created: {OUTPUT_XLSX}"
    assert os.path.getsize(OUTPUT_XLSX) > 0


def test_excavation_calculation(sample_data):
    from src.engine.qto_engine import QTOEngine
    engine = QTOEngine()
    quantities = engine.calculate(sample_data)
    
    exc = quantities['excavation']
    expected_area = (2 + 14.0) * (2 + 11.0)
    assert exc['area'] == pytest.approx(expected_area)


def test_thermal_block_positive(sample_data):
    from src.engine.qto_engine import QTOEngine
    engine = QTOEngine()
    quantities = engine.calculate(sample_data)
    
    assert quantities['thermal_block_external']['area'] > 0


def test_all_quantities_positive(sample_data):
    from src.engine.qto_engine import QTOEngine
    from src.validation.validator import QTOValidator
    engine = QTOEngine()
    quantities = engine.calculate(sample_data)
    validator = QTOValidator()
    
    for key, val in quantities.items():
        qty = validator._extract_qty(val)
        assert qty >= 0, f"Negative quantity for {key}: {qty}"
