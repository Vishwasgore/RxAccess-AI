"""
Vision-based prescription extractor using Groq's vision model.
Sends the image directly to the LLM — handles blurry, handwritten,
low-quality prescriptions far better than OCR alone.
"""
import base64
import json
import re
import io
from typing import Dict, Any, Optional
from PIL import Image
from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

VISION_PROMPT = """You are an expert medical data extraction AI. You are looking at a prescription image.

Extract ALL visible information from this prescription image, even if parts are blurry or handwritten.
Use your medical knowledge to intelligently interpret unclear text:
- Drug names that are partially visible (e.g. "Lisnprl" → Lisinopril)
- Abbreviated frequencies (QD=once daily, BID=twice daily, TID=3x daily, QID=4x daily, PRN=as needed)
- Common dosage patterns (mg, mcg, ml, units, tabs, caps)
- Doctor titles and clinic names

Return ONLY a valid JSON object with this exact structure (null for anything not visible):
{
  "patient_name": "full name or null",
  "patient_age": number or null,
  "patient_gender": "Male/Female/Other or null",
  "doctor_name": "Dr. Name or null",
  "doctor_specialty": "specialty or null",
  "clinic_name": "clinic/hospital name or null",
  "prescription_date": "date string or null",
  "diagnosis": "condition/diagnosis or null",
  "medications": [
    {
      "name": "full medication name",
      "dosage": "strength e.g. 10mg",
      "frequency": "how often e.g. Once daily",
      "duration": "how long e.g. 30 days",
      "quantity": "amount dispensed e.g. 30 tablets",
      "instructions": "special instructions e.g. Take with food"
    }
  ],
  "notes": "any other notes or null"
}

Be thorough. Even if the image is blurry, make your best medical interpretation.
Return ONLY the JSON, no explanation."""


class VisionExtractor:
    """Extract prescription data by sending image directly to Groq vision model"""

    def __init__(self):
        self.api_key = settings.groq_api_key
        self.model = "meta-llama/llama-4-scout-17b-16e-instruct"  # Groq vision model
        logger.info(f"Vision Extractor initialized: {self.model}")

    def _image_to_base64(self, image_bytes: bytes) -> tuple[str, str]:
        """Convert image bytes to base64 string and detect media type"""
        try:
            img = Image.open(io.BytesIO(image_bytes))

            # Convert to RGB if needed (handles RGBA, palette, etc.)
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')

            # Resize if too large (Groq has limits)
            w, h = img.size
            if max(w, h) > 2048:
                scale = 2048 / max(w, h)
                img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)

            # Save as JPEG for smaller size
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=90)
            img_bytes = buf.getvalue()

            b64 = base64.b64encode(img_bytes).decode('utf-8')
            return b64, "image/jpeg"

        except Exception as e:
            logger.error(f"Image conversion failed: {e}")
            raise

    def _parse_json(self, text: str) -> Optional[Dict]:
        """Robustly parse JSON from LLM response"""
        # Strip markdown
        text = re.sub(r'```(?:json)?', '', text).strip().rstrip('`')

        # Direct parse
        try:
            return json.loads(text)
        except Exception:
            pass

        # Find JSON block
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass

        # Fix common issues
        try:
            fixed = re.sub(r',\s*([}\]])', r'\1', text)
            return json.loads(fixed)
        except Exception:
            return None

    def _normalize(self, data: Dict) -> Dict:
        """Ensure all expected keys exist and medications list is clean"""
        defaults = {
            "patient_name": None, "patient_age": None, "patient_gender": None,
            "doctor_name": None, "doctor_specialty": None, "clinic_name": None,
            "prescription_date": None, "diagnosis": None,
            "medications": [], "notes": None
        }

        # Merge with defaults
        for k, v in defaults.items():
            if k not in data:
                data[k] = v

        # Normalize medications list
        if not isinstance(data.get("medications"), list):
            data["medications"] = []

        # Handle alternate key names LLM might use
        if not data["medications"]:
            for alt_key in ["prescriptions", "drugs", "rxs"]:
                if isinstance(data.get(alt_key), list):
                    for rx in data[alt_key]:
                        data["medications"].append({
                            "name": rx.get("drug_name") or rx.get("name") or rx.get("medication", "Unknown"),
                            "dosage": rx.get("dosage") or rx.get("strength"),
                            "frequency": rx.get("frequency") or rx.get("sig") or rx.get("directions"),
                            "duration": rx.get("duration"),
                            "quantity": str(rx.get("quantity", "")) or None,
                            "instructions": rx.get("instructions") or rx.get("notes")
                        })
                    break

        # Clean null strings
        for k, v in data.items():
            if v in ("null", "None", "N/A", "n/a", ""):
                data[k] = None

        return data

    def extract(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Send image directly to Groq vision model for extraction.

        Args:
            image_bytes: Raw image bytes (JPG, PNG, etc.)

        Returns:
            Dict with status and structured prescription data
        """
        try:
            logger.info("Starting vision-based extraction with Groq")

            # Convert image to base64
            b64_image, media_type = self._image_to_base64(image_bytes)

            # Call Groq vision API directly via requests (more reliable than LangChain for vision)
            import requests

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{media_type};base64,{b64_image}"
                                }
                            },
                            {
                                "type": "text",
                                "text": VISION_PROMPT
                            }
                        ]
                    }
                ],
                "max_tokens": 2048,
                "temperature": 0.1  # Low temperature for consistent extraction
            }

            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code != 200:
                logger.error(f"Groq API error: {response.status_code} — {response.text[:300]}")
                return {
                    "status": "error",
                    "data": None,
                    "error": f"Groq API returned {response.status_code}: {response.text[:200]}"
                }

            result = response.json()
            response_text = result["choices"][0]["message"]["content"]

            logger.info(f"Vision model response received ({len(response_text)} chars)")
            logger.debug(f"Raw response: {response_text[:500]}")

            # Parse JSON
            parsed = self._parse_json(response_text)

            if parsed:
                normalized = self._normalize(parsed)
                med_count = len(normalized.get("medications", []))
                logger.info(f"Vision extraction successful. Medications: {med_count}")
                return {
                    "status": "success",
                    "data": normalized,
                    "raw_response": response_text,
                    "method": "vision"
                }
            else:
                logger.warning("Could not parse JSON from vision response")
                return {
                    "status": "partial",
                    "data": self._normalize({}),
                    "raw_response": response_text,
                    "error": "JSON parsing failed",
                    "method": "vision"
                }

        except Exception as e:
            logger.error(f"Vision extraction failed: {e}")
            return {
                "status": "error",
                "data": None,
                "error": str(e),
                "method": "vision"
            }


# Global instance
_vision_extractor = None

def get_vision_extractor() -> VisionExtractor:
    global _vision_extractor
    if _vision_extractor is None:
        _vision_extractor = VisionExtractor()
    return _vision_extractor
