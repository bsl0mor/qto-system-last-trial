"""Excel BOQ generator using openpyxl."""
import os
from openpyxl import Workbook
from openpyxl.styles import (
    PatternFill, Font, Alignment, Border, Side
)
from openpyxl.utils import get_column_letter


GREEN_FILL = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
YELLOW_FILL = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
RED_FILL = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
HEADER_FILL = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
SUBHEADER_FILL = PatternFill(start_color="2E75B6", end_color="2E75B6", fill_type="solid")
TOTAL_FILL = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")

HEADER_FONT = Font(name='Calibri', bold=True, color="FFFFFF", size=11)
SUBHEADER_FONT = Font(name='Calibri', bold=True, color="FFFFFF", size=10)
BOLD_FONT = Font(name='Calibri', bold=True, size=10)
NORMAL_FONT = Font(name='Calibri', size=10)

THIN_BORDER = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin')
)

CENTER_ALIGN = Alignment(horizontal='center', vertical='center', wrap_text=True)
LEFT_ALIGN = Alignment(horizontal='left', vertical='center', wrap_text=True)
RIGHT_ALIGN = Alignment(horizontal='right', vertical='center')


RATES = {
    "foundation_concrete": 850, "foundation_pcc": 350, "neck_column_concrete": 950,
    "tie_beam_concrete": 900, "solid_block_work": 120, "slab_on_grade": 320,
    "excavation": 45, "back_filling": 35, "anti_termite": 18, "polyethylene_sheet": 8,
    "road_base": 95, "slab_concrete": 900, "beam_concrete": 950, "column_concrete": 1000,
    "dry_area_flooring": 95, "skirting": 45, "paint": 22, "dry_areas_ceiling": 85,
    "wet_area_flooring": 115, "wall_tiles": 125, "wet_areas_ceiling": 90,
    "balcony_flooring": 110, "marble_threshold": 55, "block_20_external": 135,
    "block_20_internal": 120, "block_10_internal": 105, "internal_plaster": 38,
    "external_finish": 75, "waterproofing": 85, "combo_roof_system": 220,
    "thermal_block_external": 155, "interlock_paving": 68, "false_ceiling": 95,
    "roof_waterproofing": 95,
}

UNITS = {
    "excavation": "m3", "foundation": "m3", "neck_columns": "m3", "tie_beams": "m3",
    "solid_block_work": "m2", "slab_on_grade": "m3", "back_filling": "m3",
    "anti_termite": "m2", "polyethylene_sheet": "m2", "road_base": "m3",
    "slabs": "m3", "beams": "m3", "columns": "m3",
    "dry_area_flooring": "m2", "skirting": "m2", "paint": "m2", "dry_areas_ceiling": "m2",
    "wet_area_flooring": "m2", "wall_tiles": "m2", "wet_areas_ceiling": "m2",
    "balcony_flooring": "m2", "marble_threshold": "rm",
    "block_20_external": "m2", "block_20_internal": "m2", "block_10_internal": "m2",
    "internal_plaster": "m2", "external_finish": "m2", "waterproofing": "m2",
    "combo_roof_system": "m2", "thermal_block_external": "m2",
    "interlock_paving": "m2", "false_ceiling": "m2", "roof_waterproofing": "m2",
}

DESCRIPTIONS = {
    "excavation": "Bulk Excavation",
    "foundation": "Foundation Concrete (M25)",
    "neck_columns": "Neck Column Concrete",
    "tie_beams": "Tie Beam Concrete",
    "solid_block_work": "Solid Block Work (Substructure)",
    "slab_on_grade": "Slab on Grade Concrete",
    "back_filling": "Back Filling & Compaction",
    "anti_termite": "Anti-Termite Treatment",
    "polyethylene_sheet": "Polyethylene Sheet (DPM)",
    "road_base": "Road Base (Sub-base)",
    "slabs": "Slab Concrete (M25)",
    "beams": "Beam Concrete (M25)",
    "columns": "Column Concrete (M25)",
    "dry_area_flooring": "Dry Area Flooring (Ceramic/Porcelain)",
    "skirting": "Skirting",
    "paint": "Interior Paint (2 coats)",
    "dry_areas_ceiling": "Dry Areas Ceiling Paint",
    "wet_area_flooring": "Wet Area Flooring (Anti-slip Tiles)",
    "wall_tiles": "Wall Tiles (Wet Areas)",
    "wet_areas_ceiling": "Wet Areas Ceiling (Moisture Resistant)",
    "balcony_flooring": "Balcony Flooring",
    "marble_threshold": "Marble Threshold",
    "block_20_external": "20cm Block Work (External)",
    "block_20_internal": "20cm Block Work (Internal)",
    "block_10_internal": "10cm Block Work (Internal Partitions)",
    "internal_plaster": "Internal Plaster",
    "external_finish": "External Plaster & Finish",
    "waterproofing": "Waterproofing (Wet Areas + Balcony)",
    "combo_roof_system": "Combo Roof System (Insulation + Waterproofing)",
    "thermal_block_external": "Thermal Block (External Walls)",
    "interlock_paving": "Interlock Paving (External)",
    "false_ceiling": "False Ceiling (Gypsum Board)",
    "roof_waterproofing": "Roof Waterproofing",
}

SUB_STRUCTURE_ITEMS = [
    "excavation", "foundation", "neck_columns", "tie_beams",
    "solid_block_work", "slab_on_grade", "back_filling",
    "anti_termite", "polyethylene_sheet", "road_base"
]

SUPER_STRUCTURE_ITEMS = [
    "slabs", "beams", "columns",
    "dry_area_flooring", "skirting", "paint", "dry_areas_ceiling"
]

FINISHES_ITEMS = [
    "wet_area_flooring", "wall_tiles", "wet_areas_ceiling",
    "balcony_flooring", "marble_threshold",
    "block_20_external", "block_20_internal", "block_10_internal",
    "internal_plaster", "external_finish", "waterproofing",
    "combo_roof_system", "thermal_block_external",
    "interlock_paving", "false_ceiling", "roof_waterproofing"
]


def _get_status_fill(status):
    if status == 'GREEN':
        return GREEN_FILL
    elif status == 'YELLOW':
        return YELLOW_FILL
    return RED_FILL


def _extract_qty(item_result, key):
    if isinstance(item_result, dict):
        for k in ('volume', 'area', 'rm', 'total_volume', 'total_area'):
            if k in item_result:
                return item_result[k]
    try:
        return float(item_result)
    except (TypeError, ValueError):
        return 0.0


def _get_rate(key):
    rate_key_map = {
        "foundation": "foundation_concrete",
        "neck_columns": "neck_column_concrete",
        "tie_beams": "tie_beam_concrete",
        "slabs": "slab_concrete",
        "beams": "beam_concrete",
        "columns": "column_concrete",
    }
    rate_key = rate_key_map.get(key, key)
    return RATES.get(rate_key, 0)


def _apply_header_row(ws, row, titles, fills=None, fonts=None):
    for col, title in enumerate(titles, 1):
        cell = ws.cell(row=row, column=col, value=title)
        cell.font = fonts[col-1] if fonts else HEADER_FONT
        cell.fill = fills[col-1] if fills else HEADER_FILL
        cell.alignment = CENTER_ALIGN
        cell.border = THIN_BORDER


def _set_column_widths(ws, widths):
    for col, width in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(col)].width = width


def _write_boq_sheet(ws, title, items, validated, sheet_number):
    ws.sheet_view.showGridLines = False
    
    ws.merge_cells('A1:G1')
    title_cell = ws['A1']
    title_cell.value = title
    title_cell.font = Font(name='Calibri', bold=True, size=14, color="FFFFFF")
    title_cell.fill = HEADER_FILL
    title_cell.alignment = CENTER_ALIGN
    ws.row_dimensions[1].height = 30

    headers = ['Item No.', 'Description', 'Unit', 'Quantity', 'Rate (AED)', 'Amount (AED)', 'Confidence %']
    _apply_header_row(ws, 2, headers)
    ws.row_dimensions[2].height = 20

    _set_column_widths(ws, [10, 45, 10, 12, 14, 16, 14])

    row = 3
    item_no = 1
    sheet_total = 0.0
    items_data = validated.get('items', {})

    for key in items:
        val_data = items_data.get(key, {})
        qty = val_data.get('quantity', _extract_qty(None, key))
        confidence = val_data.get('confidence', 100.0)
        status = val_data.get('status', 'GREEN')
        rate = _get_rate(key)
        amount = qty * rate
        sheet_total += amount

        fill = _get_status_fill(status)

        row_data = [
            f"{sheet_number}.{item_no}",
            DESCRIPTIONS.get(key, key.replace('_', ' ').title()),
            UNITS.get(key, 'm2'),
            round(qty, 2),
            rate,
            round(amount, 2),
            f"{confidence:.1f}%"
        ]

        for col, val in enumerate(row_data, 1):
            cell = ws.cell(row=row, column=col, value=val)
            cell.font = NORMAL_FONT
            cell.border = THIN_BORDER
            if col == 7:
                cell.fill = fill
                cell.alignment = CENTER_ALIGN
            elif col in (4, 5, 6):
                cell.alignment = RIGHT_ALIGN
            else:
                cell.alignment = LEFT_ALIGN if col == 2 else CENTER_ALIGN

        ws.row_dimensions[row].height = 18
        row += 1
        item_no += 1

    ws.cell(row=row, column=1, value="").border = THIN_BORDER
    ws.merge_cells(f'B{row}:E{row}')
    total_label = ws.cell(row=row, column=2, value=f"Total {title}")
    total_label.font = BOLD_FONT
    total_label.fill = TOTAL_FILL
    total_label.alignment = RIGHT_ALIGN
    total_label.border = THIN_BORDER
    for c in range(3, 6):
        ws.cell(row=row, column=c).fill = TOTAL_FILL
        ws.cell(row=row, column=c).border = THIN_BORDER

    total_val = ws.cell(row=row, column=6, value=round(sheet_total, 2))
    total_val.font = BOLD_FONT
    total_val.fill = TOTAL_FILL
    total_val.alignment = RIGHT_ALIGN
    total_val.border = THIN_BORDER
    ws.cell(row=row, column=7).fill = TOTAL_FILL
    ws.cell(row=row, column=7).border = THIN_BORDER
    ws.row_dimensions[row].height = 20

    return sheet_total


def _write_summary_sheet(ws, project_name, project_type, totals, validated, overall_confidence, is_draft):
    ws.sheet_view.showGridLines = False
    
    ws.merge_cells('A1:F1')
    title_cell = ws['A1']
    title_cell.value = "BILL OF QUANTITIES - SUMMARY"
    title_cell.font = Font(name='Calibri', bold=True, size=16, color="FFFFFF")
    title_cell.fill = HEADER_FILL
    title_cell.alignment = CENTER_ALIGN
    ws.row_dimensions[1].height = 35

    info_rows = [
        ("Project Name:", project_name),
        ("Project Type:", project_type),
        ("Overall Confidence:", f"{overall_confidence:.1f}%"),
        ("Status:", "** DRAFT - REQUIRES REVIEW **" if is_draft else "FINAL"),
    ]
    for i, (label, value) in enumerate(info_rows, 2):
        ws.cell(row=i, column=1, value=label).font = BOLD_FONT
        cell = ws.cell(row=i, column=2, value=value)
        if label == "Status:":
            cell.font = Font(name='Calibri', bold=True, size=11,
                           color="FF0000" if is_draft else "008000")
        else:
            cell.font = NORMAL_FONT
        ws.row_dimensions[i].height = 18

    row = 7
    ws.merge_cells(f'A{row}:F{row}')
    sub_title = ws.cell(row=row, column=1, value="COST SUMMARY")
    sub_title.font = SUBHEADER_FONT
    sub_title.fill = SUBHEADER_FILL
    sub_title.alignment = CENTER_ALIGN
    ws.row_dimensions[row].height = 22
    row += 1

    headers = ['Section', 'Description', 'Amount (AED)', 'Confidence %']
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=row, column=col, value=h)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = CENTER_ALIGN
        cell.border = THIN_BORDER
    ws.row_dimensions[row].height = 20
    row += 1

    sections = [
        ("1", "Sub-Structure", totals.get('sub_structure', 0)),
        ("2", "Super-Structure", totals.get('super_structure', 0)),
        ("3", "Architectural Finishes", totals.get('finishes', 0)),
    ]

    grand_total = 0.0
    for sec_no, desc, amount in sections:
        grand_total += amount
        ws.cell(row=row, column=1, value=sec_no).border = THIN_BORDER
        ws.cell(row=row, column=1).alignment = CENTER_ALIGN
        ws.cell(row=row, column=2, value=desc).border = THIN_BORDER
        ws.cell(row=row, column=2).alignment = LEFT_ALIGN
        amt_cell = ws.cell(row=row, column=3, value=round(amount, 2))
        amt_cell.border = THIN_BORDER
        amt_cell.alignment = RIGHT_ALIGN
        conf_cell = ws.cell(row=row, column=4, value=f"{overall_confidence:.1f}%")
        conf_cell.border = THIN_BORDER
        conf_cell.alignment = CENTER_ALIGN
        ws.row_dimensions[row].height = 18
        row += 1

    ws.cell(row=row, column=1, value="").border = THIN_BORDER
    gt_label = ws.cell(row=row, column=2, value="GRAND TOTAL")
    gt_label.font = BOLD_FONT
    gt_label.fill = TOTAL_FILL
    gt_label.border = THIN_BORDER
    gt_label.alignment = RIGHT_ALIGN
    gt_val = ws.cell(row=row, column=3, value=round(grand_total, 2))
    gt_val.font = BOLD_FONT
    gt_val.fill = TOTAL_FILL
    gt_val.border = THIN_BORDER
    gt_val.alignment = RIGHT_ALIGN
    ws.cell(row=row, column=4).fill = TOTAL_FILL
    ws.cell(row=row, column=4).border = THIN_BORDER
    ws.row_dimensions[row].height = 22

    _set_column_widths(ws, [12, 40, 18, 16, 10, 10])

    row += 2
    ws.cell(row=row, column=1, value="CONFIDENCE LEGEND").font = BOLD_FONT
    row += 1
    legend = [
        ("GREEN (>=95%)", GREEN_FILL, "Within acceptable range"),
        ("YELLOW (90-95%)", YELLOW_FILL, "Minor deviation - review recommended"),
        ("RED (<90%)", RED_FILL, "Significant deviation - review required"),
    ]
    for label, fill, desc in legend:
        cell = ws.cell(row=row, column=1, value=label)
        cell.fill = fill
        cell.border = THIN_BORDER
        cell.font = NORMAL_FONT
        ws.cell(row=row, column=2, value=desc).font = NORMAL_FONT
        ws.row_dimensions[row].height = 16
        row += 1


class ExcelGenerator:
    def generate(self, quantities, validated, output_path, project_name="QTO Project", project_type="G+1"):
        """Generate a professional BOQ Excel file."""
        wb = Workbook()
        
        ws_sub = wb.active
        ws_sub.title = "Sub-Structure"
        sub_total = _write_boq_sheet(ws_sub, "SUB-STRUCTURE", SUB_STRUCTURE_ITEMS, validated, 1)

        ws_super = wb.create_sheet("Super-Structure")
        super_total = _write_boq_sheet(ws_super, "SUPER-STRUCTURE", SUPER_STRUCTURE_ITEMS, validated, 2)

        ws_fin = wb.create_sheet("Finishes")
        fin_total = _write_boq_sheet(ws_fin, "ARCHITECTURAL FINISHES", FINISHES_ITEMS, validated, 3)

        ws_sum = wb.create_sheet("Summary")
        overall_confidence = validated.get('overall_confidence', 100.0)
        is_draft = validated.get('is_draft', False)
        _write_summary_sheet(
            ws_sum, project_name, project_type,
            {'sub_structure': sub_total, 'super_structure': super_total, 'finishes': fin_total},
            validated, overall_confidence, is_draft
        )

        wb.move_sheet("Summary", offset=-3)

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        wb.save(output_path)
        return output_path
