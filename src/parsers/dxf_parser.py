"""
DXF Parser — extracts geometric data from DXF files using ezdxf.
Returns a DrawingData dict compatible with the QTO engine.
"""

from __future__ import annotations

import math
from typing import Any

try:
    import ezdxf
    from ezdxf.math import Vec3
    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False


# ---------------------------------------------------------------------------
# Default dimension constants for opening extraction
# ---------------------------------------------------------------------------

DEFAULT_DOOR_HEIGHT: float = 2.10   # metres
DEFAULT_WINDOW_HEIGHT: float = 1.50  # metres

# ---------------------------------------------------------------------------
# Helper geometry utilities
# ---------------------------------------------------------------------------

def _polyline_length(points: list[tuple[float, float]]) -> float:
    """Return total arc-length of an open polyline."""
    total = 0.0
    for i in range(len(points) - 1):
        dx = points[i + 1][0] - points[i][0]
        dy = points[i + 1][1] - points[i][1]
        total += math.hypot(dx, dy)
    return total


def _closed_polyline_perimeter(points: list[tuple[float, float]]) -> float:
    """Return perimeter of a closed polyline (adds closing segment)."""
    if not points:
        return 0.0
    pts = list(points) + [points[0]]
    return _polyline_length(pts)


def _polygon_area(points: list[tuple[float, float]]) -> float:
    """Shoelace formula for polygon area."""
    n = len(points)
    if n < 3:
        return 0.0
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += points[i][0] * points[j][1]
        area -= points[j][0] * points[i][1]
    return abs(area) / 2.0


def _entity_to_points(entity: Any) -> list[tuple[float, float]]:
    """Convert a DXF LWPOLYLINE or POLYLINE entity to a list of (x, y) tuples."""
    dxftype = entity.dxftype()
    if dxftype == "LWPOLYLINE":
        return [(pt[0], pt[1]) for pt in entity.get_points()]
    if dxftype == "POLYLINE":
        return [(v.dxf.location.x, v.dxf.location.y) for v in entity.vertices]
    if dxftype == "LINE":
        s = entity.dxf.start
        e = entity.dxf.end
        return [(s.x, s.y), (e.x, e.y)]
    return []


def _bounding_box(all_points: list[tuple[float, float]]) -> dict:
    if not all_points:
        return {"min_x": 0, "max_x": 0, "min_y": 0, "max_y": 0, "width": 0, "height": 0}
    xs = [p[0] for p in all_points]
    ys = [p[1] for p in all_points]
    return {
        "min_x": min(xs),
        "max_x": max(xs),
        "min_y": min(ys),
        "max_y": max(ys),
        "width": max(xs) - min(xs),
        "height": max(ys) - min(ys),
    }


# ---------------------------------------------------------------------------
# Layer-name conventions
# ---------------------------------------------------------------------------

LAYER_WALLS = {"walls", "wall", "parti", "partition"}
LAYER_COLUMNS = {"columns", "column", "col", "cols"}
LAYER_BEAMS = {"beams", "beam"}
LAYER_OPENINGS = {"openings", "opening", "doors", "door", "windows", "window"}
LAYER_ROOMS = {"rooms", "room", "space", "spaces", "floor", "area"}
LAYER_SLABS = {"slabs", "slab"}
LAYER_FOUNDATION = {"foundation", "footing", "footings"}


def _layer_matches(layer_name: str, layer_set: set[str]) -> bool:
    ln = layer_name.lower().strip()
    return any(tok in ln for tok in layer_set)


# ---------------------------------------------------------------------------
# Main parser class
# ---------------------------------------------------------------------------

class DXFParser:
    """Parse a DXF file and return a structured DrawingData dictionary."""

    def __init__(self, filepath: str):
        if not EZDXF_AVAILABLE:
            raise ImportError("ezdxf is not installed. Run: pip install ezdxf")
        self.filepath = filepath
        self.doc = None
        self.msp = None

    # ------------------------------------------------------------------
    def parse(self) -> dict:
        """Parse the DXF file and return DrawingData."""
        self.doc = ezdxf.readfile(self.filepath)
        self.msp = self.doc.modelspace()

        walls = self._extract_walls()
        columns = self._extract_columns()
        beams = self._extract_beams()
        openings = self._extract_openings()
        rooms = self._extract_rooms()
        slabs = self._extract_slabs()
        foundations = self._extract_foundations()

        all_points: list[tuple[float, float]] = []
        for w in walls:
            all_points.extend(w.get("points", []))
        bbox = _bounding_box(all_points)

        return {
            "source": "dxf",
            "filepath": self.filepath,
            "walls": walls,
            "columns": columns,
            "beams": beams,
            "openings": openings,
            "rooms": rooms,
            "slabs": slabs,
            "foundations": foundations,
            "bounding_box": bbox,
            "total_wall_length": sum(w.get("length", 0) for w in walls),
            "total_floor_area": sum(r.get("area", 0) for r in rooms),
        }

    # ------------------------------------------------------------------
    def _extract_walls(self) -> list[dict]:
        walls = []
        for entity in self.msp:
            if not _layer_matches(entity.dxf.layer, LAYER_WALLS):
                continue
            pts = _entity_to_points(entity)
            if not pts:
                continue
            length = _polyline_length(pts)
            # Try to determine thickness from the LWPOLYLINE width attribute
            thickness = getattr(entity.dxf, "const_width", 0.0) or 0.20
            walls.append({
                "layer": entity.dxf.layer,
                "points": pts,
                "length": length,
                "thickness": thickness,
            })
        return walls

    def _extract_columns(self) -> list[dict]:
        columns = []
        for entity in self.msp:
            if not _layer_matches(entity.dxf.layer, LAYER_COLUMNS):
                continue
            pts = _entity_to_points(entity)
            if len(pts) < 2:
                continue
            bbox = _bounding_box(pts)
            columns.append({
                "layer": entity.dxf.layer,
                "points": pts,
                "width": bbox["width"],
                "length": bbox["height"],
                "qty": 1,
            })
        return columns

    def _extract_beams(self) -> list[dict]:
        beams = []
        for entity in self.msp:
            if not _layer_matches(entity.dxf.layer, LAYER_BEAMS):
                continue
            pts = _entity_to_points(entity)
            if not pts:
                continue
            length = _polyline_length(pts)
            beams.append({
                "layer": entity.dxf.layer,
                "points": pts,
                "length": length,
                "width": 0.30,
                "depth": 0.60,
            })
        return beams

    def _extract_openings(self) -> list[dict]:
        openings = []
        for entity in self.msp:
            if not _layer_matches(entity.dxf.layer, LAYER_OPENINGS):
                continue
            layer_lower = entity.dxf.layer.lower()
            opening_type = "window" if "win" in layer_lower else "door"
            pts = _entity_to_points(entity)
            if not pts:
                continue
            bbox = _bounding_box(pts)
            openings.append({
                "layer": entity.dxf.layer,
                "type": opening_type,
                "width": max(bbox["width"], bbox["height"]),
                "height": DEFAULT_DOOR_HEIGHT if opening_type == "door" else DEFAULT_WINDOW_HEIGHT,
                "count": 1,
            })
        return openings

    def _extract_rooms(self) -> list[dict]:
        rooms = []
        for entity in self.msp:
            if not _layer_matches(entity.dxf.layer, LAYER_ROOMS):
                continue
            pts = _entity_to_points(entity)
            if len(pts) < 3:
                continue
            area = _polygon_area(pts)
            perimeter = _closed_polyline_perimeter(pts)
            rooms.append({
                "layer": entity.dxf.layer,
                "points": pts,
                "area": area,
                "perimeter": perimeter,
                "room_type": "general",
            })
        return rooms

    def _extract_slabs(self) -> list[dict]:
        slabs = []
        for entity in self.msp:
            if not _layer_matches(entity.dxf.layer, LAYER_SLABS):
                continue
            pts = _entity_to_points(entity)
            if len(pts) < 3:
                continue
            area = _polygon_area(pts)
            slabs.append({
                "layer": entity.dxf.layer,
                "area": area,
                "thickness": 0.20,
            })
        return slabs

    def _extract_foundations(self) -> list[dict]:
        foundations = []
        for entity in self.msp:
            if not _layer_matches(entity.dxf.layer, LAYER_FOUNDATION):
                continue
            pts = _entity_to_points(entity)
            if len(pts) < 2:
                continue
            bbox = _bounding_box(pts)
            foundations.append({
                "layer": entity.dxf.layer,
                "width": bbox["width"],
                "length": bbox["height"],
                "depth": 0.50,
                "count": 1,
            })
        return foundations


# ---------------------------------------------------------------------------
# Public convenience function
# ---------------------------------------------------------------------------

def parse_dxf(filepath: str) -> dict:
    """Parse a DXF file and return a DrawingData dict."""
    parser = DXFParser(filepath)
    return parser.parse()
