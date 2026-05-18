"""
LLM-based prescription data extraction using Groq
Fixes: Pydantic v2 compatibility, direct JSON parsing instead of PydanticOutputParser
"""
import json
import re
from typing import Dict, Any, Optional, List
from src.config import get_llm_config
from src.utils.logger import get_logger

logger = get_logger(__name__)

# ── Extraction prompt ────────────────────────────────────────────────────────
EXTRACTION_PROMPT = """You are a medical data extraction expert. Extract prescription information from the OCR text below.

The OCR text may have errors (especially for handwritten prescriptions). Use your medical knowledge to correct obvious mistakes.

OCR TEXT:
{ocr_text}

Extract and return ONLY a valid JSON object with this exact structure (use null for missing fields):
{{
  "patient_name": "string or null",
  "patient_age": number or null,
  "patient_gender": "string or null",
  "doctor_name": "string or null",
  "doctor_specialty": "string or null",
  "clinic_name": "string or null",
  "prescription_date": "string or null",
  "diagnosis": "string or null",
  "medications": [
    {{
      "name": "medication name",
      "dosage": "e.g. 10mg",
      "frequency": "e.g. Once daily",
      "duration": "e.g. 30 days",
      "quantity": "e.g. 30 tablets",
      "instructions": "sig / special instructions"
    }}
  ],
  "notes": "any additional notes or null"
}}

Return ONLY the JSON object, no explanation, no markdown, no code blocks."""

# ── Low-confidence fallback prompt ───────────────────────────────────────────
LOW_CONF_PROMPT = """You are a medical AI assistant. The following text was extracted from a handwritten prescription using OCR. The quality is poor, so there may be many errors.

OCR TEXT (low quality):
{ocr_text}

Despite the noise, try to identify any medical information. Look for:
- Drug names (common ones: Lisinopril, Metformin, Atorvastatin, Amlodipine, Omeprazole, etc.)
- Dosages (numbers followed by mg, mcg, ml, units)
- Doctor names (Dr. prefix)
- Patient names
- Frequencies (daily, twice, BID, TID, QID)

Return ONLY a JSON object (same structure as before). If you cannot identify something, use null.
Make your best educated guess based on partial text matches."""


class LLMExtractor:
    """LLM-based extractor — uses Groq for fast, reliable extraction"""

    def __init__(self):
        self.llm_config = get_llm_config()
        logger.info(f"LLM Extractor initialized: {self.llm_config['provider']} / {self.llm_config['model']}")

    def _get_llm(self):
        """Get LLM client"""
        cfg = self.llm_config
        if cfg["provider"] in ("groq", "openai"):
            from langchain_openai import ChatOpenAI
            base_url = "https://api.groq.com/openai/v1" if cfg["provider"] == "groq" else None
            kwargs = dict(
                api_key=cfg["api_key"],
                model=cfg["model"],
                temperature=cfg["temperature"],
                max_tokens=2048,
            )
            if base_url:
                kwargs["base_url"] = base_url
            return ChatOpenAI(**kwargs)
        elif cfg["provider"] == "ollama":
            from langchain_community.llms import Ollama
            return Ollama(model=cfg["model"], base_url=cfg["base_url"], temperature=cfg["temperature"])
        else:
            raise ValueError(f"Unsupported provider: {cfg['provider']}")

    def _parse_json_from_response(self, text: str) -> Optional[Dict]:
        """Robustly extract JSON from LLM response"""
        # Strip markdown code blocks if present
        text = re.sub(r'```(?:json)?', '', text).strip()

        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to find JSON object in the text
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        # Try to fix common JSON issues (trailing commas, single quotes)
        try:
            fixed = re.sub(r',\s*([}\]])', r'\1', text)   # remove trailing commas
            fixed = fixed.replace("'", '"')                 # single → double quotes
            return json.loads(fixed)
        except Exception:
            pass

        return None

    def extract_structured_data(self, ocr_text: str, confidence: float = 100.0) -> Dict[str, Any]:
        """
        Extract structured prescription data from OCR text.

        Args:
            ocr_text: Raw text from OCR
            confidence: OCR confidence score (0-100)

        Returns:
            Dict with status and structured data
        """
        if not ocr_text or not ocr_text.strip():
            return {"status": "error", "data": self._empty_prescription(), "error": "Empty OCR text"}

        try:
            llm = self._get_llm()

            # Use low-confidence prompt for poor OCR results
            if confidence < 40:
                logger.info(f"Low OCR confidence ({confidence:.1f}%) — using enhanced prompt")
                prompt = LOW_CONF_PROMPT.format(ocr_text=ocr_text[:3000])
            else:
                prompt = EXTRACTION_PROMPT.format(ocr_text=ocr_text[:3000])

            logger.info("Sending to LLM for extraction...")
            response = llm.invoke(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)

            logger.info(f"LLM response received ({len(response_text)} chars)")
            logger.debug(f"Raw LLM response: {response_text[:500]}")

            parsed = self._parse_json_from_response(response_text)

            if parsed:
                # Ensure medications is always a list
                if not isinstance(parsed.get("medications"), list):
                    parsed["medications"] = []

                # Normalize: LLM sometimes uses "prescriptions" instead of "medications"
                if not parsed["medications"] and isinstance(parsed.get("prescriptions"), list):
                    for rx in parsed["prescriptions"]:
                        parsed["medications"].append({
                            "name": rx.get("drug_name") or rx.get("name") or rx.get("medication", "Unknown"),
                            "dosage": rx.get("dosage"),
                            "frequency": rx.get("frequency") or rx.get("sig"),
                            "duration": rx.get("duration"),
                            "quantity": str(rx.get("quantity", "")) or None,
                            "instructions": rx.get("instructions") or rx.get("sig")
                        })

                # Clean up None strings
                for key, val in parsed.items():
                    if val == "null" or val == "None":
                        parsed[key] = None

                # Ensure all expected top-level keys exist
                defaults = self._empty_prescription()
                for k, v in defaults.items():
                    if k not in parsed:
                        parsed[k] = v

                logger.info(f"Extraction successful. Medications found: {len(parsed.get('medications', []))}")
                return {"status": "success", "data": parsed, "raw_response": response_text}
            else:
                logger.warning("Could not parse JSON from LLM response — using fallback")
                fallback = self._extract_fallback(ocr_text)
                return {"status": "partial", "data": fallback, "raw_response": response_text,
                        "error": "JSON parsing failed, used regex fallback"}

        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            fallback = self._extract_fallback(ocr_text)
            return {"status": "error", "data": fallback, "error": str(e)}

    def _extract_fallback(self, text: str) -> Dict[str, Any]:
        """Regex-based fallback extraction when LLM fails"""
        data = self._empty_prescription()
        data["notes"] = text[:300] if text else ""

        # Patient name
        for pattern in [r"Patient[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)", r"Name[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)"]:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                data["patient_name"] = m.group(1)
                break

        # Doctor name
        m = re.search(r"Dr\.?\s+([A-Z][a-z]+ [A-Z][a-z]+)", text, re.IGNORECASE)
        if m:
            data["doctor_name"] = "Dr. " + m.group(1)

        # Medications — look for common drug names + dosage patterns
        drug_pattern = r"([A-Z][a-z]{3,}(?:in|ol|am|ex|il|an)?)\s+(\d+\s*(?:mg|mcg|ml|units?))"
        for m in re.finditer(drug_pattern, text, re.IGNORECASE):
            data["medications"].append({
                "name": m.group(1),
                "dosage": m.group(2),
                "frequency": None,
                "duration": None,
                "quantity": None,
                "instructions": None
            })

        # Date
        m = re.search(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b", text)
        if m:
            data["prescription_date"] = m.group(1)

        return data

    def _empty_prescription(self) -> Dict[str, Any]:
        return {
            "patient_name": None, "patient_age": None, "patient_gender": None,
            "doctor_name": None, "doctor_specialty": None, "clinic_name": None,
            "prescription_date": None, "diagnosis": None,
            "medications": [], "notes": None
        }


# Global instance
llm_extractor = LLMExtractor()
