"""
PDF Parser — uses Google Gemini 2.5 Pro Vision API to extract QTO data
from scanned or vector PDF architectural drawings.
Returns a DrawingData dict compatible with the QTO engine.
"""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Prompt sent to Gemini
# ---------------------------------------------------------------------------

EXTRACTION_PROMPT = """
You are a professional Quantity Surveyor analysing an architectural drawing.
Extract ALL of the following information from this drawing image and return it
as a single valid JSON object — no markdown, no commentary, ONLY the JSON.

Required JSON structure:
{
  "walls": [
    {"length": <float metres>, "thickness": <float metres>, "type": "external|internal"}
  ],
  "columns": [
    {"width": <float>, "length": <float>, "qty": <int>}
  ],
  "beams": [
    {"length": <float>, "width": <float>, "depth": <float>}
  ],
  "openings": [
    {"type": "door|window", "width": <float>, "height": <float>, "count": <int>}
  ],
  "rooms": [
    {"room_type": "toilet|bathroom|kitchen|pantry|laundry|bedroom|living|balcony|other",
     "area": <float m2>, "perimeter": <float m>}
  ],
  "slabs": [
    {"area": <float m2>, "thickness": <float m>}
  ],
  "foundations": [
    {"width": <float>, "length": <float>, "depth": <float>, "count": <int>}
  ],
  "plot_area": <float m2 or null>,
  "floor_height": <float m or null>,
  "project_type": "G|G+1|G+2|G+1 Service or null",
  "notes": "<any relevant observations>"
}

If a value cannot be determined from the drawing, use null.
All dimensions must be in METRES and areas in SQUARE METRES.
""".strip()


# ---------------------------------------------------------------------------
# Helper: convert PDF page to base64 PNG
# ---------------------------------------------------------------------------

def _pdf_pages_to_base64(pdf_path: str) -> list[str]:
    """Convert each page of a PDF to a base64-encoded PNG string."""
    try:
        from pdf2image import convert_from_path  # type: ignore
    except ImportError as exc:
        raise ImportError("pdf2image is required: pip install pdf2image") from exc

    images = convert_from_path(pdf_path, dpi=150)
    result = []
    for img in images:
        import io
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        result.append(base64.b64encode(buf.getvalue()).decode("utf-8"))
    return result


# ---------------------------------------------------------------------------
# Main parser class
# ---------------------------------------------------------------------------

class PDFParser:
    """
    Parse architectural PDF drawings via Gemini Vision and return DrawingData.
    """

    def __init__(self, pdf_path: str, api_key: str):
        self.pdf_path = pdf_path
        self.api_key = api_key

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
        model = genai.GenerativeModel("gemini-2.5-pro")

        pages_b64 = _pdf_pages_to_base64(self.pdf_path)
        all_page_data: list[dict] = []

        for i, page_b64 in enumerate(pages_b64):
            try:
                import google.generativeai.types as genai_types
                image_part = {
                    "inline_data": {
                        "mime_type": "image/png",
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
                # Log and continue; partial data is better than nothing
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
            "slabs": [],
            "foundations": [],
            "plot_area": None,
            "floor_height": None,
            "project_type": None,
            "notes": [],
            "bounding_box": {},
            "total_wall_length": 0.0,
            "total_floor_area": 0.0,
        }

        list_keys = ["walls", "columns", "beams", "openings", "rooms", "slabs", "foundations"]

        for page in pages:
            for key in list_keys:
                if isinstance(page.get(key), list):
                    merged[key].extend(page[key])
            if page.get("plot_area") and merged["plot_area"] is None:
                merged["plot_area"] = page["plot_area"]
            if page.get("floor_height") and merged["floor_height"] is None:
                merged["floor_height"] = page["floor_height"]
            if page.get("project_type") and merged["project_type"] is None:
                merged["project_type"] = page["project_type"]
            if page.get("notes"):
                merged["notes"].append(page["notes"])

        merged["total_wall_length"] = sum(
            w.get("length", 0) for w in merged["walls"]
        )
        merged["total_floor_area"] = sum(
            r.get("area", 0) for r in merged["rooms"]
        )
        return merged


# ---------------------------------------------------------------------------
# Public convenience function
# ---------------------------------------------------------------------------

def parse_pdf(pdf_path: str, api_key: str | None = None) -> dict:
    """
    Parse a PDF architectural drawing.

    Parameters
    ----------
    pdf_path : str
        Path to the PDF file.
    api_key : str, optional
        Gemini API key. Falls back to the GEMINI_API_KEY environment variable.
    """
    key = api_key or os.environ.get("GEMINI_API_KEY", "")
    if not key:
        raise ValueError(
            "A Gemini API key is required. Pass --api-key or set GEMINI_API_KEY."
        )
    parser = PDFParser(pdf_path, key)
    return parser.parse()
