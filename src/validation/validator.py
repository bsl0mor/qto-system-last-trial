"""QTO Validation layer with confidence scoring."""


class QTOValidator:
    AVERAGES = {
        "G+1": {
            "avg_plot_area": 153,
            "items": {
                "thermal_block_external": 466.0,
                "internal_plaster": 1144.3,
                "external_plaster": 718.8,
                "dry_area_flooring": 248.7,
                "wet_area_flooring": 317.1,
                "wall_tiles": 305.0,
                "roof_waterproofing": 121.8,
                "false_ceiling": 259.0,
                "interlock_paving": 358.4,
            },
            "ratios": {
                "external_plaster_to_thermal_block": 1.54
            }
        },
        "G+2": {
            "avg_plot_area": 3108,
            "items": {
                "thermal_block_external": 689.1,
                "internal_plaster": 1822.9,
                "dry_area_flooring": 287.9,
                "wet_area_flooring": 104.0,
                "false_ceiling": 301.4,
                "interlock_paving": 420.9,
            }
        }
    }
    DEVIATION_THRESHOLD = 0.15

    def _extract_qty(self, item_result):
        if isinstance(item_result, dict):
            for key in ('area', 'volume', 'rm', 'total_area', 'total_volume'):
                if key in item_result:
                    return item_result[key]
        return float(item_result) if item_result is not None else 0.0

    def _calculate_confidence(self, item_key, qty, project_type, plot_area):
        pt_data = self.AVERAGES.get(project_type)
        if not pt_data or item_key not in pt_data.get('items', {}):
            return 100.0
        avg_plot = pt_data['avg_plot_area']
        avg_qty = pt_data['items'][item_key]
        scaled_avg = avg_qty * (plot_area / avg_plot) if avg_plot > 0 else avg_qty
        if scaled_avg == 0:
            return 100.0
        deviation = abs(qty - scaled_avg) / scaled_avg
        if deviation <= self.DEVIATION_THRESHOLD:
            confidence = 100.0 - (deviation / self.DEVIATION_THRESHOLD) * 5.0
        else:
            excess = deviation - self.DEVIATION_THRESHOLD
            confidence = max(0.0, 95.0 - (excess / self.DEVIATION_THRESHOLD) * 95.0)
        return round(min(confidence, 100.0), 2)

    def validate(self, quantities, project_type, plot_area):
        results = {}
        for item_key, item_result in quantities.items():
            qty = self._extract_qty(item_result)
            confidence = self._calculate_confidence(item_key, qty, project_type, plot_area)
            status = 'GREEN' if confidence >= 95 else ('YELLOW' if confidence >= 90 else 'RED')
            results[item_key] = {
                'quantity': qty,
                'raw': item_result,
                'confidence': confidence,
                'status': status,
                'requires_review': confidence < 95
            }
        overall = self._overall_confidence(results)
        ratio_warnings = self._check_ratios(quantities, project_type)
        return {
            'items': results,
            'overall_confidence': overall,
            'is_draft': overall < 95,
            'ratio_warnings': ratio_warnings
        }

    def _overall_confidence(self, results):
        if not results:
            return 100.0
        scores = [r['confidence'] for r in results.values()]
        return round(sum(scores) / len(scores), 2)

    def _check_ratios(self, quantities, project_type):
        warnings = []
        pt_data = self.AVERAGES.get(project_type, {})
        ratios = pt_data.get('ratios', {})
        if 'external_plaster_to_thermal_block' in ratios:
            ep = self._extract_qty(quantities.get('external_finish', 0))
            tb = self._extract_qty(quantities.get('thermal_block_external', 0))
            if tb > 0:
                actual_ratio = ep / tb
                expected = ratios['external_plaster_to_thermal_block']
                if abs(actual_ratio - expected) / expected > 0.2:
                    warnings.append(
                        f"Ratio check: external_plaster/thermal_block = {actual_ratio:.2f}, expected ~{expected}"
                    )
        return warnings
