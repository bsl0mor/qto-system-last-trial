"""Architectural finishes QTO calculations."""


class FinishesCalculator:
    def calculate_wet_area_flooring(self, wet_areas):
        area = sum(r['area'] for r in wet_areas)
        return {'area': area}

    def calculate_wall_tiles(self, wet_areas, floor_height):
        perimeter = sum(r['perimeter'] for r in wet_areas)
        area = perimeter * (floor_height - 0.5)
        return {'area': area}

    def calculate_wet_areas_ceiling(self, wet_area_flooring):
        return {'area': wet_area_flooring}

    def calculate_balcony_flooring(self, balcony):
        if balcony and balcony.get('exists', False):
            return {'area': balcony['area']}
        return {'area': 0.0}

    def calculate_marble_threshold(self, doors):
        total_width = sum(d['width'] * d.get('count', 1) for d in doors)
        return {'rm': total_width}

    def calculate_block_20_external(self, external_perimeter, floor_height, windows, main_door):
        wall_area = external_perimeter * floor_height
        windows_area = sum(w['width'] * w['height'] * w.get('count', 1) for w in windows)
        main_door_area = main_door['width'] * main_door['height'] * main_door.get('count', 1)
        area = wall_area - (windows_area + main_door_area)
        return {'area': max(area, 0)}

    def calculate_block_20_internal(self, internal_20cm_length, floor_height, doors):
        wall_area = internal_20cm_length * floor_height
        door_area = sum(d['width'] * d['height'] * d.get('count', 1) for d in doors)
        area = wall_area - 0.4 * door_area
        return {'area': max(area, 0)}

    def calculate_block_10_internal(self, internal_10cm_length, floor_height, doors):
        wall_area = internal_10cm_length * floor_height
        door_area = sum(d['width'] * d['height'] * d.get('count', 1) for d in doors)
        area = wall_area - 0.4 * door_area
        return {'area': max(area, 0)}

    def calculate_internal_plaster(self, internal_20cm_length, internal_10cm_length, external_perimeter, floor_height, doors, windows, num_floors=2):
        internal_walls_area = (internal_20cm_length + internal_10cm_length) * floor_height
        external_walls_area = external_perimeter * floor_height * num_floors
        doors_area = sum(d['width'] * d['height'] * d.get('count', 1) for d in doors)
        windows_area = sum(w['width'] * w['height'] * w.get('count', 1) for w in windows)
        area = (internal_walls_area * 2 + external_walls_area) - (doors_area * 2 + windows_area)
        return {'area': max(area, 0)}

    def calculate_external_finish(self, external_perimeter, floor_height, num_floors=2):
        total_height = num_floors * floor_height + 1.5
        area = external_perimeter * total_height
        return {'area': area}

    def calculate_waterproofing(self, first_floor_wet_areas, balcony_area=0.0):
        area = first_floor_wet_areas + balcony_area
        return {'area': area}

    def calculate_combo_roof_system(self, roof_slab_area):
        area = roof_slab_area * 1.2
        return {'area': area}

    def calculate_thermal_block_external(self, external_perimeter, floor_height, num_floors=2):
        area = external_perimeter * floor_height * num_floors
        return {'area': area}

    def calculate_interlock_paving(self, plot_area, built_up_area):
        area = plot_area - built_up_area
        return {'area': max(area, 0)}

    def calculate_false_ceiling(self, dry_area_flooring, wet_area_flooring):
        area = dry_area_flooring + wet_area_flooring
        return {'area': area}

    def calculate_roof_waterproofing(self, roof_slab_area):
        return {'area': roof_slab_area}
