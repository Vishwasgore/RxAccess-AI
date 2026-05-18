"""
Disclaimer and legal notice utilities
"""
from src.config import MEDICAL_DISCLAIMER


def get_disclaimer() -> str:
    """Get the medical disclaimer text"""
    return MEDICAL_DISCLAIMER


def add_disclaimer_to_response(response: str) -> str:
    """Add disclaimer to any medical response"""
    disclaimer_footer = "\n\n---\n*This information is for educational purposes only. Consult healthcare professionals for medical advice.*"
    return response + disclaimer_footer


def get_pa_disclaimer() -> str:
    """Get prior authorization specific disclaimer"""
    return """
    **Prior Authorization Disclaimer:**
    - PA predictions are estimates based on general patterns
    - Actual approval depends on specific payer policies and clinical documentation
    - Always verify requirements with the specific insurance payer
    - This tool does not guarantee approval or denial
    """


def get_adherence_disclaimer() -> str:
    """Get adherence prediction disclaimer"""
    return """
    **Adherence Prediction Disclaimer:**
    - Risk scores are statistical predictions, not certainties
    - Individual circumstances may vary significantly
    - Use as one input among many for patient support decisions
    - Always consider patient-specific factors and preferences
    """


def get_affordability_disclaimer() -> str:
    """Get affordability estimation disclaimer"""
    return """
    **Affordability Disclaimer:**
    - Cost estimates are approximate and may not reflect actual prices
    - Insurance coverage varies by plan and individual circumstances
    - Patient assistance program availability changes frequently
    - Always verify costs and coverage with pharmacy and insurance provider
    """
