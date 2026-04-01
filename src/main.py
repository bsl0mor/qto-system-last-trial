"""Main CLI entry point for QTO Automation System."""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.engine.qto_engine import QTOEngine
from src.validation.validator import QTOValidator
from src.output.excel_generator import ExcelGenerator


def load_input(input_path, input_type=None):
    ext = os.path.splitext(input_path)[1].lower()
    
    if ext == '.json' or input_type == 'json':
        with open(input_path, 'r') as f:
            return json.load(f)
    elif ext == '.dxf' or input_type == 'dxf':
        from src.parsers.dxf_parser import parse_dxf
        return parse_dxf(input_path)
    elif ext == '.pdf' or input_type == 'pdf':
        from src.parsers.pdf_parser import parse_pdf
        api_key = os.environ.get('GEMINI_API_KEY')
        return parse_pdf(input_path, api_key=api_key)
    else:
        try:
            with open(input_path, 'r') as f:
                return json.load(f)
        except Exception:
            print(f"Error: Unsupported file type: {ext}", file=sys.stderr)
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='QTO Automation System - Generate Bill of Quantities',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/main.py --input samples/sample_input.json --type G+1 --output output_boq.xlsx
  python src/main.py --input drawings/plan.dxf --type G+2 --output project_boq.xlsx
  python src/main.py --input drawings/plan.pdf --output output_boq.xlsx
        """
    )
    parser.add_argument('--input', required=True, help='Input file (JSON, DXF, or PDF)')
    parser.add_argument('--type', dest='project_type', default=None,
                        help='Project type (G+1, G+2, etc.). Overrides input file value.')
    parser.add_argument('--output', default='output_boq.xlsx', help='Output Excel file path')
    parser.add_argument('--input-type', choices=['json', 'dxf', 'pdf'], default=None,
                        help='Force input file type')
    parser.add_argument('--verbose', action='store_true', help='Print detailed output')
    
    args = parser.parse_args()

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    input_path = args.input if os.path.isabs(args.input) else os.path.join(project_root, args.input)
    output_path = args.output if os.path.isabs(args.output) else os.path.join(project_root, args.output)

    if not os.path.exists(input_path):
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading input from: {input_path}")
    data = load_input(input_path, args.input_type)
    
    if args.project_type:
        data['project_type'] = args.project_type
    
    project_type = data.get('project_type', 'G+1')
    project_name = data.get('project_name', 'QTO Project')
    plot_area = data.get('plot_area', 153)
    
    print(f"Project: {project_name} | Type: {project_type} | Plot: {plot_area} m2")

    print("Running QTO calculations...")
    engine = QTOEngine()
    quantities = engine.calculate(data)
    
    print(f"Calculated {len(quantities)} line items")

    print("Validating quantities...")
    validator = QTOValidator()
    validated = validator.validate(quantities, project_type, plot_area)
    
    overall_confidence = validated['overall_confidence']
    is_draft = validated['is_draft']
    
    print(f"Overall Confidence: {overall_confidence:.1f}% | Status: {'DRAFT' if is_draft else 'FINAL'}")
    
    if validated.get('ratio_warnings'):
        for warning in validated['ratio_warnings']:
            print(f"  WARNING: {warning}")

    if args.verbose:
        print("\nItem Details:")
        for key, item in validated['items'].items():
            status_icon = "v" if item['status'] == 'GREEN' else ("~" if item['status'] == 'YELLOW' else "x")
            print(f"  {status_icon} {key}: {item['quantity']:.2f} | {item['confidence']:.1f}% [{item['status']}]")

    print(f"Generating Excel BOQ: {output_path}")
    generator = ExcelGenerator()
    generator.generate(quantities, validated, output_path, project_name, project_type)
    
    print(f"BOQ successfully generated: {output_path}")
    
    items = validated['items']
    green_count = sum(1 for i in items.values() if i['status'] == 'GREEN')
    yellow_count = sum(1 for i in items.values() if i['status'] == 'YELLOW')
    red_count = sum(1 for i in items.values() if i['status'] == 'RED')
    
    print(f"\nSummary: {green_count} GREEN | {yellow_count} YELLOW | {red_count} RED")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
