"""PDF parser using Google Gemini Vision API."""
import os
import json

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


def parse_pdf(file_path, api_key=None):
    """Parse a PDF drawing using Gemini Vision API to extract QTO dimensions."""
    key = api_key or os.environ.get('GEMINI_API_KEY')
    
    if not GEMINI_AVAILABLE:
        return _default_structure("google-generativeai not installed")
    
    if not key:
        return _default_structure("No Gemini API key provided")
    
    if not os.path.exists(file_path):
        return _default_structure(f"File not found: {file_path}")
    
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel('gemini-2.5-pro')
        
        with open(file_path, 'rb') as f:
            pdf_bytes = f.read()
        
        prompt = """Analyze this architectural/structural drawing and extract the following information in JSON format:
        {
          "project_name": "string",
          "project_type": "G+1 or G+2 etc",
          "plot_area": number (m2),
          "floor_height": number (m),
          "external_perimeter": number (m),
          "internal_20cm_wall_length": number (m),
          "internal_10cm_wall_length": number (m),
          "num_floors": number,
          "floor_area": number (m2 per floor),
          "wet_areas": [{"type": "toilet/bathroom/kitchen", "area": number, "perimeter": number}],
          "windows": [{"type": "string", "width": number, "height": number, "count": number}],
          "doors": [{"type": "string", "width": number, "height": number, "count": number}],
          "balcony_area": number or null
        }
        Only return valid JSON, no explanation."""
        
        response = model.generate_content([
            prompt,
            {"mime_type": "application/pdf", "data": pdf_bytes}
        ])
        
        text = response.text.strip()
        if text.startswith('```'):
            lines = text.split('\n')
            text = '\n'.join(lines[1:-1])
        
        extracted = json.loads(text)
        return _transform_gemini_output(extracted, file_path)
        
    except json.JSONDecodeError as e:
        return _default_structure(f"Failed to parse Gemini response as JSON: {e}")
    except Exception as e:
        return _default_structure(f"Gemini API error: {str(e)}")


def _transform_gemini_output(data, file_path):
    return {
        "project_name": data.get("project_name", os.path.basename(file_path)),
        "project_type": data.get("project_type", "G+1"),
        "plot_area": data.get("plot_area", 153),
        "gfl": 0.0,
        "gfsl": -0.3,
        "floor_height": data.get("floor_height", 3.0),
        "slab_thickness": 0.2,
        "pcc_thickness": 0.1,
        "walls": {
            "external_perimeter": data.get("external_perimeter", 46.0),
            "internal_20cm_length": data.get("internal_20cm_wall_length", 85.0),
            "internal_10cm_length": data.get("internal_10cm_wall_length", 30.0),
        },
        "rooms": {
            "wet_areas": data.get("wet_areas", []),
            "dry_areas": []
        },
        "openings": {
            "doors": data.get("doors", []),
            "windows": data.get("windows", [])
        },
        "balcony": {
            "exists": data.get("balcony_area") is not None,
            "area": data.get("balcony_area") or 0.0,
            "perimeter": 0.0
        },
        "_source": "pdf_gemini",
        "_note": "Extracted via Gemini Vision - please verify"
    }


def _default_structure(note=""):
    return {
        "project_name": "PDF Import",
        "project_type": "G+1",
        "plot_area": 153,
        "gfl": 0.0,
        "gfsl": -0.3,
        "floor_height": 3.0,
        "slab_thickness": 0.2,
        "pcc_thickness": 0.1,
        "_source": "pdf_default",
        "_note": note
    }
