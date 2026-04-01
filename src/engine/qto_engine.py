"""Main QTO Engine orchestrating all calculations."""
from .sub_structure import SubStructureCalculator
from .super_structure import SuperStructureCalculator
from .finishes import FinishesCalculator


class QTOEngine:
    def __init__(self):
        self.sub_calc = SubStructureCalculator()
        self.super_calc = SuperStructureCalculator()
        self.fin_calc = FinishesCalculator()

    def calculate(self, data):
        results = {}
        gfl = data.get('gfl', 0.0)
        gfsl = data.get('gfsl', -0.3)
        floor_height = data.get('floor_height', 3.0)
        slab_thickness = data.get('slab_thickness', 0.2)
        pcc_thickness = data.get('pcc_thickness', 0.1)
        num_floors = len(data.get('floors', []))

        # Sub-structure
        exc = self.sub_calc.calculate_excavation(data['excavation'])
        results['excavation'] = exc

        found = self.sub_calc.calculate_foundation(data.get('foundations', []))
        results['foundation'] = found

        nc = self.sub_calc.calculate_neck_columns(
            data.get('neck_columns', []), gfl,
            data['excavation']['excavation_level'],
            data.get('tie_beams', [{}])[0].get('depth', 0.5) if data.get('tie_beams') else 0.5,
            pcc_thickness)
        results['neck_columns'] = nc

        tb = self.sub_calc.calculate_tie_beams(data.get('tie_beams', []))
        results['tie_beams'] = tb

        sbw = self.sub_calc.calculate_solid_block_work(
            data.get('solid_block_work', []), gfl,
            data['excavation']['excavation_level'],
            data.get('tie_beams', [{}])[0].get('depth', 0.5) if data.get('tie_beams') else 0.5,
            pcc_thickness)
        results['solid_block_work'] = sbw

        sog = self.sub_calc.calculate_slab_on_grade(data.get('slab_on_grade', {'area': 0, 'thickness': 0.1}))
        results['slab_on_grade'] = sog

        total_pcc_area = found['total_pcc_area'] + tb['total_pcc_area']
        sub_items_volume = (found['total_volume'] + nc['total_volume'] + tb['total_volume'] + sog['volume'])

        bf = self.sub_calc.calculate_back_filling(exc, abs(gfsl), sub_items_volume)
        results['back_filling'] = bf

        at = self.sub_calc.calculate_anti_termite(total_pcc_area, sog['area'])
        results['anti_termite'] = at

        ps = self.sub_calc.calculate_polyethylene_sheet(total_pcc_area, sog['area'])
        results['polyethylene_sheet'] = ps

        # Sub-structure sub-items (PCC, Bitumen, Formwork)
        results['foundation_area'] = {'area': found['total_area']}
        results['foundation_pcc'] = {'area': found['total_pcc_area']}
        results['foundation_bitumen'] = {'area': found['total_bitumen_area']}
        results['tie_beam_pcc'] = {'area': tb['total_pcc_area']}
        results['tie_beam_bitumen'] = {'area': tb['total_bitumen']}
        results['solid_block_bitumen'] = {'area': sbw['total_bitumen']}
        results['neck_column_formwork'] = {'area': nc['total_volume']}

        if data.get('road_base', False):
            rb = self.sub_calc.calculate_road_base(exc)
            results['road_base'] = rb

        # Super-structure
        floors = data.get('floors', [])
        total_floor_area = sum(f.get('total_area', 0) for f in floors)

        slabs = self.super_calc.calculate_slabs(floors)
        results['slabs'] = slabs

        beams = self.super_calc.calculate_beams(floors, slab_thickness)
        results['beams'] = beams

        cols = self.super_calc.calculate_columns(floors)
        results['columns'] = cols

        wet_areas = data.get('rooms', {}).get('wet_areas', [])
        dry_areas = data.get('rooms', {}).get('dry_areas', [])
        doors = data.get('openings', {}).get('doors', [])
        windows = data.get('openings', {}).get('windows', [])

        wet_floor = self.fin_calc.calculate_wet_area_flooring(wet_areas)
        results['wet_area_flooring'] = wet_floor

        dry_floor = self.super_calc.calculate_dry_area_flooring(total_floor_area, wet_floor['area'])
        results['dry_area_flooring'] = dry_floor

        skirting = self.super_calc.calculate_skirting(dry_areas, doors)
        results['skirting'] = skirting

        paint = self.super_calc.calculate_paint(skirting['area'], floor_height)
        results['paint'] = paint

        dry_ceil = self.super_calc.calculate_dry_areas_ceiling(dry_floor['area'])
        results['dry_areas_ceiling'] = dry_ceil

        # Finishes
        wall_tiles = self.fin_calc.calculate_wall_tiles(wet_areas, floor_height)
        results['wall_tiles'] = wall_tiles

        wet_ceil = self.fin_calc.calculate_wet_areas_ceiling(wet_floor['area'])
        results['wet_areas_ceiling'] = wet_ceil

        balcony = data.get('balcony', {})
        bal_floor = self.fin_calc.calculate_balcony_flooring(balcony)
        results['balcony_flooring'] = bal_floor

        marble = self.fin_calc.calculate_marble_threshold(doors)
        results['marble_threshold'] = marble

        external_perimeter = data.get('walls', {}).get('external_perimeter', 0)
        internal_20 = data.get('walls', {}).get('internal_20cm_length', 0)
        internal_10 = data.get('walls', {}).get('internal_10cm_length', 0)

        main_doors = [d for d in doors if d.get('type') == 'main_door'] or doors[:1]

        b20_ext = self.fin_calc.calculate_block_20_external(
            external_perimeter, floor_height, windows,
            main_doors[0] if main_doors else {'width': 1.2, 'height': 2.4, 'count': 1})
        results['block_20_external'] = b20_ext

        b20_int = self.fin_calc.calculate_block_20_internal(internal_20, floor_height, doors)
        results['block_20_internal'] = b20_int

        b10_int = self.fin_calc.calculate_block_10_internal(internal_10, floor_height, doors)
        results['block_10_internal'] = b10_int

        int_plaster = self.fin_calc.calculate_internal_plaster(
            internal_20, internal_10, external_perimeter, floor_height, doors, windows, num_floors)
        results['internal_plaster'] = int_plaster

        ext_finish = self.fin_calc.calculate_external_finish(external_perimeter, floor_height, num_floors)
        results['external_finish'] = ext_finish

        first_floor_wet = wet_floor['area'] / max(num_floors, 1)
        wtp = self.fin_calc.calculate_waterproofing(first_floor_wet, bal_floor['area'])
        results['waterproofing'] = wtp

        combo_roof = self.fin_calc.calculate_combo_roof_system(data.get('roof_slab_area', 0))
        results['combo_roof_system'] = combo_roof

        thermal = self.fin_calc.calculate_thermal_block_external(external_perimeter, floor_height, num_floors)
        results['thermal_block_external'] = thermal

        plot_area = data.get('plot_area', 153)
        built_up = total_floor_area / max(num_floors, 1)
        interlock = self.fin_calc.calculate_interlock_paving(plot_area, built_up)
        results['interlock_paving'] = interlock

        false_ceil = self.fin_calc.calculate_false_ceiling(dry_floor['area'], wet_floor['area'])
        results['false_ceiling'] = false_ceil

        roof_wtp = self.fin_calc.calculate_roof_waterproofing(data.get('roof_slab_area', 0))
        results['roof_waterproofing'] = roof_wtp

        return results
