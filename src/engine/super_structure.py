"""Super-structure QTO calculations."""


class SuperStructureCalculator:
    def calculate_slabs(self, floors):
        total_volume = 0.0
        total_area = 0.0
        for floor in floors:
            for slab in floor.get('slabs', []):
                vol = slab['area'] * slab['thickness']
                total_volume += vol
                total_area += slab['area']
        return {'total_area': total_area, 'total_volume': total_volume}

    def calculate_beams(self, floors, slab_thickness=0.2):
        total_volume = 0.0
        for floor in floors:
            for beam in floor.get('beams', []):
                effective_depth = beam['depth'] - slab_thickness
                vol = beam['length'] * beam['width'] * effective_depth * beam.get('count', 1)
                total_volume += vol
        return {'total_volume': total_volume}

    def calculate_columns(self, floors):
        total_volume = 0.0
        for floor in floors:
            for col in floor.get('columns', []):
                vol = col['width'] * col['length'] * col['floor_height'] * col['qty']
                total_volume += vol
        return {'total_volume': total_volume}

    def calculate_dry_area_flooring(self, total_floor_area, wet_area_flooring):
        area = total_floor_area - wet_area_flooring
        return {'area': max(area, 0)}

    def calculate_skirting(self, dry_areas, doors):
        perimeter = sum(d.get('perimeter', 0) for d in dry_areas)
        door_width_sum = sum(door['width'] * door.get('count', 1) for door in doors)
        area = perimeter - 0.4 * door_width_sum
        return {'area': max(area, 0)}

    def calculate_paint(self, skirting_area, floor_height):
        area = skirting_area * floor_height
        return {'area': area}

    def calculate_dry_areas_ceiling(self, dry_area_flooring):
        return {'area': dry_area_flooring}
