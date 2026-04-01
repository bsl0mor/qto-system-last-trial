# QTO Automation System

A complete Quantity Takeoff (QTO) automation system for construction projects, generating professional Bill of Quantities (BOQ) Excel reports.

## Features

- **Multi-format input**: JSON data, DXF drawings, PDF drawings (via Gemini AI)
- **Complete QTO calculations**: Sub-structure, Super-structure, Architectural finishes
- **Confidence scoring**: Validates quantities against historical project averages
- **Professional Excel output**: Color-coded 4-sheet BOQ with confidence indicators
- **Project types**: G+1, G+2 villas (UAE construction standards)

## Project Structure

```
qto-system/
├── config/          # Configuration files (rates, averages, thresholds)
├── samples/         # Sample input files
├── src/
│   ├── parsers/     # DXF and PDF input parsers
│   ├── engine/      # QTO calculation engine
│   ├── validation/  # Confidence scoring and validation
│   └── output/      # Excel BOQ generator
├── tests/           # Unit and integration tests
└── requirements.txt
```

## Quick Start

### Install dependencies
```bash
pip install -r requirements.txt
```

### Run with sample data
```bash
python src/main.py --input samples/sample_input.json --type G+1 --output output_boq.xlsx
```

### Run tests
```bash
python -m pytest tests/ -v
```

## Input Formats

### JSON
Structured project data with foundations, floors, rooms, openings, etc.

### DXF
AutoCAD drawings - extracts walls, columns, and room labels automatically.

### PDF (requires Gemini API key)
Architectural PDF drawings analyzed by Google Gemini Vision AI.
```bash
export GEMINI_API_KEY=your_api_key
python src/main.py --input drawing.pdf --output output_boq.xlsx
```

## Output

The system generates a 4-sheet Excel workbook:
1. **Summary** - Project overview and grand total
2. **Sub-Structure** - Excavation, foundations, tie beams, etc.
3. **Super-Structure** - Slabs, beams, columns, flooring
4. **Finishes** - Tiles, plaster, block work, waterproofing

### Confidence Color Coding
- 🟢 **GREEN** (≥95%): Within acceptable range
- 🟡 **YELLOW** (90-95%): Minor deviation - review recommended
- 🔴 **RED** (<90%): Significant deviation - review required

## Configuration

- `config/rates.json` - Unit rates in AED
- `config/averages.json` - Historical project averages for validation
- `config/thresholds.json` - Confidence thresholds
- `config/formulas.json` - Formula documentation
