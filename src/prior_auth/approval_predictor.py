"""
Prior Authorization approval likelihood prediction
"""
from typing import Dict, Any
import random
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ApprovalPredictor:
    """Predict PA approval likelihood"""
    
    def __init__(self):
        """Initialize approval predictor"""
        logger.info("Approval Predictor initialized")
    
    def predict_approval(
        self,
        pa_form: Dict[str, Any],
        patient_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Predict approval likelihood for PA
        
        Args:
            pa_form: PA form data
            patient_data: Patient information
        
        Returns:
            Prediction results with likelihood score and factors
        """
        try:
            logger.info(f"Predicting approval for PA: {pa_form.get('pa_id', 'Unknown')}")
            
            # Calculate score based on multiple factors
            score = 0.0
            factors = []
            
            # Factor 1: Documentation completeness (30%)
            doc_score = self._score_documentation(pa_form)
            score += doc_score * 0.3
            factors.append({
                "factor": "Documentation Completeness",
                "score": doc_score,
                "weight": 0.3,
                "impact": "positive" if doc_score > 0.7 else "negative",
                "details": f"{doc_score*100:.0f}% of required documents provided"
            })
            
            # Factor 2: Clinical justification strength (25%)
            clinical_score = self._score_clinical_justification(pa_form)
            score += clinical_score * 0.25
            factors.append({
                "factor": "Clinical Justification",
                "score": clinical_score,
                "weight": 0.25,
                "impact": "positive" if clinical_score > 0.7 else "neutral",
                "details": "Strong medical necessity documented" if clinical_score > 0.7 else "Additional justification may be needed"
            })
            
            # Factor 3: Previous treatment attempts (20%)
            treatment_score = self._score_treatment_history(patient_data)
            score += treatment_score * 0.2
            factors.append({
                "factor": "Treatment History",
                "score": treatment_score,
                "weight": 0.2,
                "impact": "positive" if treatment_score > 0.5 else "negative",
                "details": f"{len(patient_data.get('previous_treatments', []))} previous treatments documented"
            })
            
            # Factor 4: Medication tier/formulary status (15%)
            formulary_score = self._score_formulary_status(pa_form)
            score += formulary_score * 0.15
            factors.append({
                "factor": "Formulary Status",
                "score": formulary_score,
                "weight": 0.15,
                "impact": "neutral",
                "details": "Medication requires PA per plan formulary"
            })
            
            # Factor 5: Provider credentials (10%)
            provider_score = self._score_provider(pa_form)
            score += provider_score * 0.1
            factors.append({
                "factor": "Provider Credentials",
                "score": provider_score,
                "weight": 0.1,
                "impact": "positive",
                "details": "Licensed provider with valid NPI"
            })
            
            # Determine likelihood category
            if score >= 0.8:
                likelihood = "Very High"
                recommendation = "Strong approval likelihood. Submit with confidence."
            elif score >= 0.65:
                likelihood = "High"
                recommendation = "Good approval likelihood. Ensure all documents are complete."
            elif score >= 0.5:
                likelihood = "Moderate"
                recommendation = "Moderate approval likelihood. Consider strengthening clinical justification."
            elif score >= 0.35:
                likelihood = "Low"
                recommendation = "Low approval likelihood. Additional documentation strongly recommended."
            else:
                likelihood = "Very Low"
                recommendation = "Very low approval likelihood. Consult with provider for alternative options."
            
            # Identify missing elements
            missing_elements = self._identify_missing_elements(pa_form, patient_data)
            
            # Generate improvement suggestions
            suggestions = self._generate_suggestions(factors, missing_elements)
            
            result = {
                "status": "success",
                "pa_id": pa_form.get("pa_id", "Unknown"),
                "approval_score": round(score, 2),
                "likelihood": likelihood,
                "recommendation": recommendation,
                "factors": factors,
                "missing_elements": missing_elements,
                "suggestions": suggestions,
                "estimated_decision_time": "3-5 business days"
            }
            
            logger.info(f"Approval prediction: {likelihood} ({score:.2f})")
            
            return result
        
        except Exception as e:
            logger.error(f"Approval prediction failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _score_documentation(self, pa_form: Dict[str, Any]) -> float:
        """Score documentation completeness"""
        required_docs = pa_form.get("required_documents", [])
        if not required_docs:
            return 0.5
        
        required_count = sum(1 for doc in required_docs if doc.get("required", False))
        completed_count = sum(1 for doc in required_docs if doc.get("required", False) and doc.get("status") == "completed")
        
        if required_count == 0:
            return 0.5
        
        return completed_count / required_count
    
    def _score_clinical_justification(self, pa_form: Dict[str, Any]) -> float:
        """Score clinical justification strength"""
        justification = pa_form.get("clinical", {}).get("justification", "")
        
        if not justification or len(justification) < 50:
            return 0.3
        elif len(justification) < 200:
            return 0.6
        else:
            return 0.85
    
    def _score_treatment_history(self, patient_data: Dict[str, Any]) -> float:
        """Score treatment history"""
        previous_treatments = patient_data.get("previous_treatments", [])
        treatment_failures = patient_data.get("treatment_failures", [])
        
        if len(previous_treatments) >= 2:
            return 0.9
        elif len(previous_treatments) == 1:
            return 0.7
        elif len(treatment_failures) > 0:
            return 0.5
        else:
            return 0.3
    
    def _score_formulary_status(self, pa_form: Dict[str, Any]) -> float:
        """Score formulary status"""
        # Simplified scoring - in production, check actual formulary
        return 0.6
    
    def _score_provider(self, pa_form: Dict[str, Any]) -> float:
        """Score provider credentials"""
        provider = pa_form.get("provider", {})
        npi = provider.get("npi", "Unknown")
        
        if npi and npi != "Unknown":
            return 0.9
        else:
            return 0.5
    
    def _identify_missing_elements(
        self,
        pa_form: Dict[str, Any],
        patient_data: Dict[str, Any]
    ) -> list:
        """Identify missing or weak elements"""
        missing = []
        
        # Check required documents
        required_docs = pa_form.get("required_documents", [])
        for doc in required_docs:
            if doc.get("required") and doc.get("status") != "completed":
                missing.append(f"Missing: {doc['name']}")
        
        # Check clinical justification
        justification = pa_form.get("clinical", {}).get("justification", "")
        if len(justification) < 100:
            missing.append("Clinical justification needs more detail")
        
        # Check treatment history
        if len(patient_data.get("previous_treatments", [])) == 0:
            missing.append("No previous treatment history documented")
        
        # Check ICD-10 code
        if pa_form.get("clinical", {}).get("icd10_code") == "Unknown":
            missing.append("ICD-10 diagnosis code not provided")
        
        return missing
    
    def _generate_suggestions(self, factors: list, missing_elements: list) -> list:
        """Generate improvement suggestions"""
        suggestions = []
        
        # Suggestions based on low-scoring factors
        for factor in factors:
            if factor["score"] < 0.6:
                if factor["factor"] == "Documentation Completeness":
                    suggestions.append("Complete all required documentation before submission")
                elif factor["factor"] == "Clinical Justification":
                    suggestions.append("Strengthen clinical justification with specific medical necessity details")
                elif factor["factor"] == "Treatment History":
                    suggestions.append("Document previous treatment attempts and outcomes")
        
        # Suggestions based on missing elements
        if missing_elements:
            suggestions.append(f"Address {len(missing_elements)} missing elements to improve approval chances")
        
        # General suggestions
        if not suggestions:
            suggestions.append("PA appears well-prepared. Review one final time before submission.")
        
        return suggestions


# Global predictor instance
_approval_predictor = None

def get_approval_predictor() -> ApprovalPredictor:
    """Get or create global approval predictor instance"""
    global _approval_predictor
    if _approval_predictor is None:
        _approval_predictor = ApprovalPredictor()
    return _approval_predictor
