# QTO System — Quantity Take-Off Automation

A complete QTO automation system for villa construction projects (G, G+1, G+2, G+1 Service).
Calculates 50+ BOQ line items from DXF/PDF drawings or structured JSON input, validates
results against historical project averages, and exports a colour-coded Excel BOQ.

---

## Features

- **Sub-Structure** (10 items): Foundation, Neck Columns, Tie Beams, Solid Block Work,
  Slab on Grade, Excavation, Back Filling, Anti-Termite, Polyethylene Sheet, Road Base
- **Super-Structure** (7 items): Slabs, Beams, Columns, Dry Area Flooring, Skirting, Paint, Ceiling
- **Architectural Finishes** (18+ items): Wet Areas, Wall Tiles, Block Work, Plaster,
  Waterproofing, Thermal Block, Interlock Paving, False Ceiling, Openings, and more
- **Validation engine** — compares every item against 101+ G+1 / 46 G+2 historical project averages,
  scales by plot area ratio, flags deviations > ±15% RED, produces per-item confidence scores
- **Excel output** — colour-coded BOQ (GREEN ≥ 95%, YELLOW 90–95%, RED < 90%) with Summary sheet
- **Input formats** — DXF (via ezdxf), PDF (via Gemini 2.5 Pro Vision), or structured JSON
- **CLI** with `--sample` flag for demo without any drawing files

---

## Quick Start

```bash
pip install -r requirements.txt

# Run with built-in sample data (G+1 villa, 153 m² plot)
python src/main.py --sample --type G+1 --output boq.xlsx

# Run from a JSON input file
python src/main.py --input samples/sample_input.json --type G+1 --output boq.xlsx

# Run from a DXF file
python src/main.py --input drawing.dxf --type G+1 --output boq.xlsx --plot-area 153

# Run from a PDF file (requires Gemini API key)
python src/main.py --input plan.pdf --type G+1 --output boq.xlsx --api-key YOUR_KEY
```

---

## Project Structure

```
qto-system-last-trial/
├── requirements.txt
├── config/
│   ├── averages.json        # Historical averages (G+1: 101 projects, G+2: 46 projects)
│   ├── formulas.json        # Formula descriptions per item
│   ├── rates.json           # Default AED unit rates
│   └── thresholds.json      # Confidence thresholds and ratio checks
├── src/
│   ├── main.py              # CLI entry point
│   ├── parsers/
│   │   ├── dxf_parser.py    # ezdxf-based DXF/DWG parser
│   │   └── pdf_parser.py    # Gemini Vision PDF parser
│   ├── engine/
│   │   ├── qto_engine.py    # Orchestrator — runs all calculators
│   │   ├── sub_structure.py # 10 sub-structure item formulas
│   │   ├── super_structure.py # 7 super-structure item formulas
│   │   └── finishes.py      # 18 architectural finish formulas
│   ├── validation/
│   │   └── validator.py     # Average comparison, confidence scoring
│   └── output/
│       └── excel_generator.py # Professional colour-coded Excel BOQ
├── tests/                   # 114 unit + integration tests (all passing)
└── samples/
    └── sample_input.json    # Realistic G+1 villa sample data
```

---

## Running Tests

```bash
pip install ezdxf openpyxl pytest
python -m pytest tests/ -v
```

All 114 tests pass.

---

## Validation Rules

| Rule | Detail |
|------|--------|
| Range check | Deviation > ±15% from scaled average → RED |
| Confidence | 0–100%, linear decay; < 95% → REQUIRES MANUAL REVIEW |
| Ratio check | e.g. External Plaster ≈ 1.54× Thermal Block (G+1) |
| Overall BOQ | Weighted avg confidence < 95% → entire output marked **DRAFT** |

---

## Average Data Built-In

- **G+1**: 101 projects, avg plot 153 m², avg cost 641,278 AED
- **G+2**: 46 projects, avg plot 3,108 m², avg cost 927,255 AED
- **G**: 5 projects, avg cost 180,928 AED
- **G+1 Service**: 7 projects, avg cost 2,019,933 AED
