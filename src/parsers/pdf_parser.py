"""
PDF Parser — uses Google Gemini Vision API to extract QTO data
from scanned or vector PDF architectural drawings.
Returns a DrawingData dict compatible with the QTO engine.

Cost-discipline defaults
------------------------
* Model   : gemini-2.0-flash  (~17× cheaper than gemini-2.5-pro, same vision quality)
* DPI     : 100  (vs 150 — reduces image tokens by ~44 % while remaining legible)
* max_pages: 3   (most architectural sets have the key plan on pages 1–3)
* format  : JPEG quality 85 (vs PNG — reduces image size ~55%, same Gemini legibility)

Override any of these via the constructor or the CLI (--gemini-model, --max-pages).
"""

from __future__ import annotations

import base64
import io
import json
import os
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Cost-discipline defaults
# ---------------------------------------------------------------------------

DEFAULT_MODEL: str = "gemini-2.0-flash"
DEFAULT_DPI: int = 100
DEFAULT_MAX_PAGES: int = 3
DEFAULT_JPEG_QUALITY: int = 85   # JPEG vs PNG saves ~55% image tokens


# ---------------------------------------------------------------------------
# Prompt sent to Gemini — v2: field names match QTO engine exactly
# ---------------------------------------------------------------------------

EXTRACTION_PROMPT = """
You are a professional Quantity Surveyor analysing an architectural drawing of a UAE residential villa.
Study the drawing VERY carefully — read ALL dimension strings, annotations, labels, scale bar, and room tags.
Return ONLY a single valid JSON object. No markdown, no code fences, no commentary — just the JSON.

All dimensions in METRES. All areas in SQUARE METRES.
If a value cannot be determined from the drawing, use null.

Required JSON structure:
{
  "walls": [
    {
      "type": "external | internal_20 | internal_10",
      "length": <float — measured length of this wall run in metres>,
      "thickness": <float — 0.25 for external, 0.20 for internal_20, 0.10 for internal_10>
    }
  ],
  "external_perimeter": <float — total external perimeter of building footprint in metres>,
  "internal_wall_length_20cm": <float — total linear metres of all 20 cm internal block walls>,
  "internal_wall_length_10cm": <float — total linear metres of all 10 cm partition walls>,
  "longest_length": <float — longest footprint dimension in metres>,
  "longest_width": <float — shortest footprint dimension in metres>,
  "columns": [
    {"length": <float>, "width": <float>, "qty": <int>}
  ],
  "beams": [
    {"length": <float>, "width": <float>, "depth": <float>, "count": <int>}
  ],
  "slabs": [
    {"area": <float m2>, "thickness": <float m>}
  ],
  "footings": [
    {"width": <float>, "length": <float>, "depth": <float>, "count": <int>}
  ],
  "neck_columns": [
    {"width": <float>, "length": <float>, "count": <int>}
  ],
  "tie_beams": [
    {"length": <float>, "width": <float>, "depth": <float>, "count": <int>}
  ],
  "openings": [
    {
      "opening_type": "door | window",
      "width": <float>,
      "height": <float>,
      "count": <int>
    }
  ],
  "rooms": [
    {
      "room_type": "toilet | bathroom | kitchen | pantry | laundry | bedroom | living | dining | balcony | other",
      "area": <float m2>,
      "perimeter": <float m>
    }
  ],
  "first_floor_rooms": [
    {
      "room_type": "toilet | bathroom | kitchen | pantry | laundry | bedroom | living | dining | balcony | other",
      "area": <float m2>,
      "perimeter": <float m>
    }
  ],
  "plot_area": <float m2 or null>,
  "gf_area": <float m2 — ground floor covered area, or null>,
  "roof_area": <float m2 — roof slab area, or null>,
  "total_floor_area": <float m2 — total built area across all floors, or null>,
  "dry_area_perimeter": <float — total perimeter of all non-wet rooms in metres, or null>,
  "floor_height": <float m — floor-to-floor height, typically 3.0>,
  "slab_thickness": <float m — structural slab thickness, typically 0.20>,
  "exc_depth": <float m — excavation depth below natural ground, typically 1.50>,
  "gfl": <float m — ground floor level above excavation datum, typically 0.30>,
  "tb_depth": <float m — tie beam depth, typically 0.40>,
  "project_type": "G | G+1 | G+2 | G+1 Service | null",
  "notes": "<any relevant observations>"
}

CRITICAL EXTRACTION RULES:
1. Read EVERY dimension string — pay attention to the scale bar and title block.
2. Wall types: external boundary walls → "external"; main internal structural walls (20 cm block) → "internal_20"; lightweight partitions (10 cm or dashed lines) → "internal_10".
3. Count ALL column and beam locations. List columns by cross-section size group.
4. Count ALL door and window openings. Use "opening_type": "door" or "opening_type": "window" — never use the key "type".
5. List EVERY room with its individual area and perimeter. Do not merge or omit rooms.
6. Identify which rooms are on the first (upper) floor and list them separately in "first_floor_rooms".
7. Provide "external_perimeter", "internal_wall_length_20cm", and "internal_wall_length_10cm" as top-level numbers.
""".strip()


# ---------------------------------------------------------------------------
# Helper: convert PDF page to base64 JPEG (cost-optimised)
# ---------------------------------------------------------------------------

def _pdf_pages_to_base64(
    pdf_path: str,
    dpi: int = DEFAULT_DPI,
    max_pages: int = DEFAULT_MAX_PAGES,
    jpeg_quality: int = DEFAULT_JPEG_QUALITY,
) -> list[tuple[str, str]]:
    """Convert PDF pages to base64-encoded images.

    Returns list of (base64_string, mime_type) tuples.
    JPEG is used by default (~55 % fewer tokens vs PNG at same Gemini legibility).

    Parameters
    ----------
    pdf_path     : path to the PDF file
    dpi          : render resolution (lower = fewer image tokens = lower cost)
    max_pages    : maximum number of pages to process (0 = all)
    jpeg_quality : JPEG quality 1-95 (default 85 — good quality, small size)
    """
    try:
        from pdf2image import convert_from_path  # type: ignore
    except ImportError as exc:
        raise ImportError("pdf2image is required: pip install pdf2image") from exc

    images = convert_from_path(pdf_path, dpi=dpi)
    if max_pages and max_pages > 0:
        images = images[:max_pages]

    result = []
    for img in images:
        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="JPEG", quality=jpeg_quality, optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        result.append((b64, "image/jpeg"))
    return result


# ---------------------------------------------------------------------------
# Main parser class
# ---------------------------------------------------------------------------

class PDFParser:
    """
    Parse architectural PDF drawings via Gemini Vision and return DrawingData.

    Parameters
    ----------
    pdf_path     : path to the PDF file
    api_key      : Gemini API key
    model        : Gemini model name (default: gemini-2.0-flash)
    dpi          : render DPI for page images (default: 100)
    max_pages    : cap on number of pages sent to the API (default: 3; 0 = all)
    jpeg_quality : JPEG compression quality (default: 85; use 95 for max accuracy)
    """

    def __init__(
        self,
        pdf_path: str,
        api_key: str,
        model: str = DEFAULT_MODEL,
        dpi: int = DEFAULT_DPI,
        max_pages: int = DEFAULT_MAX_PAGES,
        jpeg_quality: int = DEFAULT_JPEG_QUALITY,
    ):
        self.pdf_path = pdf_path
        self.api_key = api_key
        self.model = model
        self.dpi = dpi
        self.max_pages = max_pages
        self.jpeg_quality = jpeg_quality

    # ------------------------------------------------------------------
    def parse(self) -> dict:
        """Send PDF pages to Gemini and aggregate extracted data."""
        try:
            import google.generativeai as genai  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "google-generativeai is required: pip install google-generativeai"
            ) from exc

        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.model)

        pages = _pdf_pages_to_base64(
            self.pdf_path, dpi=self.dpi,
            max_pages=self.max_pages, jpeg_quality=self.jpeg_quality,
        )
        if not pages:
            print("[PDFParser] Warning: no pages were extracted from the PDF.")
            return self._merge_pages([])

        print(
            f"[PDFParser] Processing {len(pages)} page(s) with model '{self.model}' "
            f"at {self.dpi} DPI (JPEG q{self.jpeg_quality})."
        )
        all_page_data: list[dict] = []

        for i, (page_b64, mime_type) in enumerate(pages):
            try:
                image_part = {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": page_b64,
                    }
                }
                response = model.generate_content([EXTRACTION_PROMPT, image_part])
                raw_text = response.text.strip()
                # Strip potential markdown code fences
                if raw_text.startswith("```"):
                    raw_text = raw_text.split("```")[1]
                    if raw_text.startswith("json"):
                        raw_text = raw_text[4:]
                page_data = json.loads(raw_text)
                all_page_data.append(page_data)
            except Exception as exc:  # noqa: BLE001
                print(f"[PDFParser] Warning: page {i + 1} extraction failed: {exc}")

        return self._merge_pages(all_page_data)

    # ------------------------------------------------------------------
    @staticmethod
    def _merge_pages(pages: list[dict]) -> dict:
        """Merge per-page extraction results into a single DrawingData dict."""
        merged: dict[str, Any] = {
            "source": "pdf",
            "walls": [],
            "columns": [],
            "beams": [],
            "openings": [],
            "rooms": [],
            "first_floor_rooms": [],
            "slabs": [],
            "foundations": [],
            "footings": [],
            "neck_columns": [],
            "tie_beams": [],
            "plot_area": None,
            "gf_area": None,
            "roof_area": None,
            "floor_height": None,
            "slab_thickness": None,
            "exc_depth": None,
            "gfl": None,
            "tb_depth": None,
            "project_type": None,
            "external_perimeter": None,
            "internal_wall_length_20cm": None,
            "internal_wall_length_10cm": None,
            "longest_length": None,
            "longest_width": None,
            "dry_area_perimeter": None,
            "total_floor_area": None,
            "notes": [],
            "bounding_box": {},
            "total_wall_length": 0.0,
        }

        list_keys = [
            "walls", "columns", "beams", "openings", "rooms", "first_floor_rooms",
            "slabs", "foundations", "footings", "neck_columns", "tie_beams",
        ]
        scalar_keys = [
            "plot_area", "gf_area", "roof_area", "floor_height", "slab_thickness",
            "exc_depth", "gfl", "tb_depth", "project_type", "external_perimeter",
            "internal_wall_length_20cm", "internal_wall_length_10cm",
            "longest_length", "longest_width", "dry_area_perimeter", "total_floor_area",
        ]

        for page in pages:
            for key in list_keys:
                if isinstance(page.get(key), list):
                    merged[key].extend(page[key])
            for key in scalar_keys:
                if page.get(key) is not None and merged[key] is None:
                    merged[key] = page[key]
            if page.get("notes"):
                merged["notes"].append(page["notes"])

        # Derived totals
        merged["total_wall_length"] = sum(
            w.get("length", 0) for w in merged["walls"]
        )
        # Derive internal wall lengths from the walls list if not provided top-level
        if merged["internal_wall_length_20cm"] is None:
            merged["internal_wall_length_20cm"] = sum(
                w.get("length", 0) for w in merged["walls"]
                if w.get("type", "") == "internal_20"
            )
        if merged["internal_wall_length_10cm"] is None:
            merged["internal_wall_length_10cm"] = sum(
                w.get("length", 0) for w in merged["walls"]
                if w.get("type", "") == "internal_10"
            )
        if merged["external_perimeter"] is None:
            merged["external_perimeter"] = sum(
                w.get("length", 0) for w in merged["walls"]
                if w.get("type", "") == "external"
            )
        merged["total_floor_area"] = merged["total_floor_area"] or sum(
            r.get("area", 0) for r in merged["rooms"]
        )
        return merged


# ---------------------------------------------------------------------------
# Public convenience function
# ---------------------------------------------------------------------------

def parse_pdf(
    pdf_path: str,
    api_key: str | None = None,
    model: str = DEFAULT_MODEL,
    dpi: int = DEFAULT_DPI,
    max_pages: int = DEFAULT_MAX_PAGES,
    jpeg_quality: int = DEFAULT_JPEG_QUALITY,
) -> dict:
    """
    Parse a PDF architectural drawing.

    Parameters
    ----------
    pdf_path     : path to the PDF file
    api_key      : Gemini API key; falls back to GEMINI_API_KEY env var
    model        : Gemini model (default: gemini-2.0-flash — cheap + vision-capable)
    dpi          : render resolution (default: 100 — lower cost, still legible)
    max_pages    : maximum pages to process (default: 3; 0 = all pages)
    jpeg_quality : JPEG quality 1-95 (default: 85 — ~55% token saving vs PNG)
    """
    key = api_key or os.environ.get("GEMINI_API_KEY", "")
    if not key:
        raise ValueError(
            "A Gemini API key is required. Pass --api-key or set GEMINI_API_KEY."
        )
    parser = PDFParser(pdf_path, key, model=model, dpi=dpi,
                       max_pages=max_pages, jpeg_quality=jpeg_quality)
    return parser.parse()
