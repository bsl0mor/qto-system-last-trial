"""Sub-structure QTO calculations."""


class SubStructureCalculator:
    def __init__(self, pcc_thickness=0.1):
        self.pcc_thickness = pcc_thickness

    def calculate_foundation(self, foundations, excavation_depth=0.0):
        results = []
        total_area = 0.0
        total_volume = 0.0
        total_pcc_area = 0.0
        total_bitumen_area = 0.0
        for f in foundations:
            w, l, d, n = f['width'], f['length'], f['depth'], f['count']
            area = w * l * n
            volume = w * l * d * n
            pcc_area = (l + 0.2) * (w + 0.2) * n
            pcc_volume = pcc_area * self.pcc_thickness
            perimeter = 2 * (w + l)
            bitumen = (area + perimeter * d) * n
            results.append({'type': f.get('type', 'F'), 'area': area, 'volume': volume,
                            'pcc_area': pcc_area, 'pcc_volume': pcc_volume, 'bitumen': bitumen})
            total_area += area
            total_volume += volume
            total_pcc_area += pcc_area
            total_bitumen_area += bitumen
        return {
            'details': results,
            'total_area': total_area,
            'total_volume': total_volume,
            'total_pcc_area': total_pcc_area,
            'total_bitumen_area': total_bitumen_area
        }

    def calculate_neck_columns(self, neck_columns, gfl=0.0, excavation_depth=1.5, tb_depth=0.5, pcc_thickness=0.1):
        results = []
        total_volume = 0.0
        height = gfl + excavation_depth - tb_depth - pcc_thickness
        for nc in neck_columns:
            perimeter = nc.get('perimeter', 2 * (nc['width'] + nc['length']))
            count = nc.get('count', 1)
            nc_height = nc.get('height', height)
            volume = perimeter * nc_height * count
            results.append({'id': nc.get('id', 'NC'), 'volume': volume, 'height': nc_height, 'count': count})
            total_volume += volume
        return {'details': results, 'total_volume': total_volume}

    def calculate_tie_beams(self, tie_beams):
        results = []
        total_volume = 0.0
        total_pcc_area = 0.0
        total_bitumen = 0.0
        for tb in tie_beams:
            l, w, d = tb['length'], tb['width'], tb['depth']
            volume = l * w * d
            pcc = l * (w + 0.2) * self.pcc_thickness
            bitumen = l * d * 2
            results.append({'id': tb.get('id', 'TB'), 'volume': volume, 'pcc': pcc, 'bitumen': bitumen})
            total_volume += volume
            total_pcc_area += pcc
            total_bitumen += bitumen
        return {'details': results, 'total_volume': total_volume, 'total_pcc_area': total_pcc_area, 'total_bitumen': total_bitumen}

    def calculate_solid_block_work(self, solid_block_work, gfl=0.0, excavation_depth=1.5, tb_depth=0.5, pcc_thickness=0.1):
        results = []
        total_area = 0.0
        total_bitumen = 0.0
        height = gfl + excavation_depth - tb_depth - pcc_thickness
        for sbw in solid_block_work:
            area = sbw['length'] * height
            bitumen = area * 2
            results.append({'id': sbw.get('id', 'SBW'), 'area': area, 'bitumen': bitumen})
            total_area += area
            total_bitumen += bitumen
        return {'details': results, 'total_area': total_area, 'total_bitumen': total_bitumen}

    def calculate_slab_on_grade(self, slab_on_grade):
        area = slab_on_grade['area']
        thickness = slab_on_grade.get('thickness', 0.1)
        volume = area * thickness
        return {'area': area, 'volume': volume}

    def calculate_excavation(self, excavation):
        ll = excavation['longest_length']
        lw = excavation['longest_width']
        el = excavation['excavation_level']
        area = (2 + ll) * (2 + lw)
        volume = area * el
        return {'area': area, 'volume': volume, 'excavation_level': el}

    def calculate_back_filling(self, excavation_result, gfsl_level, all_items_volume):
        area = excavation_result['area']
        el = excavation_result['excavation_level']
        volume = (area * (el + abs(gfsl_level))) - all_items_volume
        return {'area': area, 'volume': max(volume, 0)}

    def calculate_anti_termite(self, total_pcc_area, slab_on_grade_area):
        area = (total_pcc_area + slab_on_grade_area) * 1.15
        return {'area': area}

    def calculate_polyethylene_sheet(self, total_pcc_area, slab_on_grade_area):
        area = total_pcc_area + slab_on_grade_area
        return {'area': area}

    def calculate_road_base(self, excavation_result, thickness=0.25):
        area = excavation_result['area']
        volume = area * thickness
        return {'area': area, 'volume': volume}
