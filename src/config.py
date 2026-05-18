"""
Configuration management for RxAccess AI
Reads from: .env file → Streamlit secrets → environment variables
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Try to load from Streamlit secrets (when deployed on Streamlit Cloud)
def _get(key: str, default: str = "") -> str:
    """Read from Streamlit secrets first, then env vars"""
    try:
        import streamlit as st
        val = st.secrets.get(key)
        if val:
            return str(val)
    except Exception:
        pass
    return os.getenv(key, default)

# Project root directory
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
MODELS_DIR = ROOT_DIR / "models"
LOGS_DIR = ROOT_DIR / "logs"

for d in [DATA_DIR, MODELS_DIR, LOGS_DIR,
          DATA_DIR / "uploads", DATA_DIR / "knowledge_base",
          DATA_DIR / "synthetic"]:
    d.mkdir(exist_ok=True, parents=True)


class Settings:
    """Application settings — reads from Streamlit secrets or .env"""

    def __init__(self):
        self.llm_provider       = _get("LLM_PROVIDER", "groq")
        self.ollama_model       = _get("OLLAMA_MODEL", "llama3.2")
        self.ollama_base_url    = _get("OLLAMA_BASE_URL", "http://localhost:11434")
        self.groq_api_key       = _get("GROQ_API_KEY") or None
        self.openai_api_key     = _get("OPENAI_API_KEY") or None
        self.chroma_persist_dir = _get("CHROMA_PERSIST_DIR", str(DATA_DIR / "chroma_db"))
        self.embedding_model    = "sentence-transformers/all-MiniLM-L6-v2"
        self.tesseract_path     = _get("TESSERACT_PATH", "tesseract")
        self.tesseract_lang     = _get("TESSERACT_LANG", "eng")
        self.poppler_path       = _get("POPPLER_PATH") or None
        self.debug              = _get("DEBUG", "True").lower() == "true"
        self.log_level          = _get("LOG_LEVEL", "INFO")
        self.secret_key         = _get("SECRET_KEY", "rxaccess-secret-key")
        # Paths
        self.root_dir           = ROOT_DIR
        self.data_dir           = DATA_DIR
        self.models_dir         = MODELS_DIR
        self.logs_dir           = LOGS_DIR
        self.uploads_dir        = DATA_DIR / "uploads"
        self.knowledge_base_dir = DATA_DIR / "knowledge_base"
        self.synthetic_data_dir = DATA_DIR / "synthetic"


# Global settings instance
settings = Settings()


# LLM Configuration Helper
def get_llm_config():
    """Get LLM configuration based on provider"""
    if settings.llm_provider == "ollama":
        return {
            "provider": "ollama",
            "model": settings.ollama_model,
            "base_url": settings.ollama_base_url,
            "temperature": 0.7,
        }
    elif settings.llm_provider == "groq":
        return {
            "provider": "groq",
            "api_key": settings.groq_api_key,
            "model": "llama-3.1-8b-instant",
            "temperature": 0.7,
        }
    elif settings.llm_provider == "openai":
        return {
            "provider": "openai",
            "api_key": settings.openai_api_key,
            "model": "gpt-3.5-turbo",
            "temperature": 0.7,
        }
    else:
        raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")


# Disclaimer text
MEDICAL_DISCLAIMER = """
⚠️ **IMPORTANT MEDICAL DISCLAIMER**

This application is a prototype for demonstration purposes only and is NOT intended for actual medical use.

- This is not medical advice
- Always consult qualified healthcare professionals for medical decisions
- Do not rely on this system for diagnosis, treatment, or medication management
- Prescription information may contain errors
- Prior authorization predictions are estimates only
- Adherence recommendations are general guidance

By using this system, you acknowledge that it is for educational and demonstration purposes only.
"""

# PII Fields to redact
PII_FIELDS = [
    "patient_name",
    "patient_address",
    "patient_phone",
    "patient_email",
    "ssn",
    "medical_record_number",
    "insurance_id",
]
