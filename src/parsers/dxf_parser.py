"""DXF file parser using ezdxf."""
import os

try:
    import ezdxf
    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False


def parse_dxf(file_path):
    """Parse a DXF file and extract structural dimensions."""
    if not EZDXF_AVAILABLE:
        return _default_structure("DXF parsing unavailable: ezdxf not installed")
    
    if not os.path.exists(file_path):
        return _default_structure(f"File not found: {file_path}")
    
    try:
        doc = ezdxf.readfile(file_path)
        msp = doc.modelspace()
        
        walls = _extract_walls(msp)
        columns = _extract_columns(msp)
        rooms = _extract_rooms(msp)
        
        return {
            "project_name": os.path.basename(file_path).replace('.dxf', ''),
            "project_type": "G+1",
            "plot_area": walls.get('plot_area', 153),
            "gfl": 0.0,
            "gfsl": -0.3,
            "floor_height": 3.0,
            "slab_thickness": 0.2,
            "pcc_thickness": 0.1,
            "walls": {
                "external_perimeter": walls.get('external_perimeter', 46.0),
                "internal_20cm_length": walls.get('internal_20cm', 85.0),
                "internal_10cm_length": walls.get('internal_10cm', 30.0),
            },
            "columns_extracted": columns,
            "rooms_extracted": rooms,
            "_source": "dxf",
            "_note": "Partial extraction - please verify dimensions"
        }
    except Exception as e:
        return _default_structure(f"DXF parse error: {str(e)}")


def _extract_walls(msp):
    result = {'external_perimeter': 0.0, 'internal_20cm': 0.0, 'internal_10cm': 0.0, 'plot_area': 0.0}
    polylines = []
    
    for entity in msp:
        if entity.dxftype() in ('LWPOLYLINE', 'POLYLINE'):
            try:
                if entity.dxftype() == 'LWPOLYLINE':
                    pts = list(entity.get_points())
                    if len(pts) >= 2:
                        length = sum(
                            ((pts[i+1][0]-pts[i][0])**2 + (pts[i+1][1]-pts[i][1])**2)**0.5
                            for i in range(len(pts)-1)
                        )
                        polylines.append({'length': length, 'layer': entity.dxf.layer})
            except Exception:
                continue
    
    if polylines:
        polylines.sort(key=lambda x: x['length'], reverse=True)
        if polylines:
            result['external_perimeter'] = polylines[0]['length']
        if len(polylines) > 1:
            result['internal_20cm'] = sum(p['length'] for p in polylines[1:3])
        result['plot_area'] = (result['external_perimeter'] / 4) ** 2 if result['external_perimeter'] > 0 else 153
    
    return result


def _extract_columns(msp):
    columns = []
    for entity in msp:
        if entity.dxftype() in ('INSERT', 'BLOCK'):
            try:
                columns.append({
                    'x': entity.dxf.insert[0],
                    'y': entity.dxf.insert[1],
                    'name': entity.dxf.name if hasattr(entity.dxf, 'name') else 'COL'
                })
            except Exception:
                continue
    return columns


def _extract_rooms(msp):
    rooms = []
    for entity in msp:
        if entity.dxftype() == 'TEXT' or entity.dxftype() == 'MTEXT':
            try:
                text = entity.dxf.text if entity.dxftype() == 'TEXT' else entity.text
                rooms.append({'label': text})
            except Exception:
                continue
    return rooms


def _default_structure(note=""):
    return {
        "project_name": "DXF Import",
        "project_type": "G+1",
        "plot_area": 153,
        "gfl": 0.0,
        "gfsl": -0.3,
        "floor_height": 3.0,
        "slab_thickness": 0.2,
        "pcc_thickness": 0.1,
        "_source": "dxf_default",
        "_note": note
    }
