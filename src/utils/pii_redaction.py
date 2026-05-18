"""
PII redaction and anonymization utilities
"""
import re
from typing import Dict, Any
from src.config import PII_FIELDS


def redact_pii(data: Dict[str, Any], fields_to_redact: list = None) -> Dict[str, Any]:
    """
    Redact PII fields from data dictionary
    
    Args:
        data: Dictionary containing potentially sensitive data
        fields_to_redact: List of field names to redact (uses default if None)
    
    Returns:
        Dictionary with PII fields redacted
    """
    if fields_to_redact is None:
        fields_to_redact = PII_FIELDS
    
    redacted_data = data.copy()
    
    for field in fields_to_redact:
        if field in redacted_data:
            redacted_data[field] = "[REDACTED]"
    
    return redacted_data


def mask_name(name: str) -> str:
    """
    Mask a name, keeping first letter
    Example: "John Doe" -> "J*** D**"
    """
    if not name:
        return "[REDACTED]"
    
    parts = name.split()
    masked_parts = []
    
    for part in parts:
        if len(part) > 0:
            masked = part[0] + "*" * (len(part) - 1)
            masked_parts.append(masked)
    
    return " ".join(masked_parts)


def mask_phone(phone: str) -> str:
    """
    Mask phone number, keeping last 4 digits
    Example: "555-123-4567" -> "***-***-4567"
    """
    if not phone:
        return "[REDACTED]"
    
    # Extract digits only
    digits = re.sub(r'\D', '', phone)
    
    if len(digits) >= 4:
        return f"***-***-{digits[-4:]}"
    else:
        return "***-***-****"


def mask_email(email: str) -> str:
    """
    Mask email address
    Example: "john.doe@example.com" -> "j***@example.com"
    """
    if not email or '@' not in email:
        return "[REDACTED]"
    
    local, domain = email.split('@', 1)
    
    if len(local) > 0:
        masked_local = local[0] + "***"
    else:
        masked_local = "***"
    
    return f"{masked_local}@{domain}"


def mask_ssn(ssn: str) -> str:
    """
    Mask SSN, keeping last 4 digits
    Example: "123-45-6789" -> "***-**-6789"
    """
    if not ssn:
        return "[REDACTED]"
    
    digits = re.sub(r'\D', '', ssn)
    
    if len(digits) >= 4:
        return f"***-**-{digits[-4:]}"
    else:
        return "***-**-****"


def anonymize_prescription_data(data: Dict[str, Any], mode: str = "full") -> Dict[str, Any]:
    """
    Anonymize prescription data for different use cases
    
    Args:
        data: Prescription data dictionary
        mode: "full" (complete redaction), "partial" (masked), "demo" (fake data)
    
    Returns:
        Anonymized data dictionary
    """
    anonymized = data.copy()
    
    if mode == "full":
        # Complete redaction
        anonymized = redact_pii(anonymized)
    
    elif mode == "partial":
        # Partial masking
        if "patient_name" in anonymized:
            anonymized["patient_name"] = mask_name(anonymized["patient_name"])
        if "patient_phone" in anonymized:
            anonymized["patient_phone"] = mask_phone(anonymized["patient_phone"])
        if "patient_email" in anonymized:
            anonymized["patient_email"] = mask_email(anonymized["patient_email"])
        if "ssn" in anonymized:
            anonymized["ssn"] = mask_ssn(anonymized["ssn"])
    
    elif mode == "demo":
        # Replace with demo data
        anonymized["patient_name"] = "Demo Patient"
        anonymized["patient_phone"] = "555-0100"
        anonymized["patient_email"] = "demo@example.com"
        if "ssn" in anonymized:
            anonymized["ssn"] = "***-**-0000"
    
    return anonymized


def detect_pii_in_text(text: str) -> Dict[str, list]:
    """
    Detect potential PII in text using regex patterns
    
    Returns:
        Dictionary with detected PII types and their positions
    """
    detected = {
        "emails": [],
        "phones": [],
        "ssns": [],
    }
    
    # Email pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    detected["emails"] = re.findall(email_pattern, text)
    
    # Phone pattern (US)
    phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
    detected["phones"] = re.findall(phone_pattern, text)
    
    # SSN pattern
    ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
    detected["ssns"] = re.findall(ssn_pattern, text)
    
    return detected
