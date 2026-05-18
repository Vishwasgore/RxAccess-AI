"""
Prior Authorization form generation and management
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
import uuid
from src.config import get_llm_config
from src.utils.logger import get_logger
from langchain.prompts import PromptTemplate

logger = get_logger(__name__)


class PAGenerator:
    """Prior Authorization form generator"""
    
    def __init__(self):
        """Initialize PA generator"""
        self.llm_config = get_llm_config()
        logger.info("PA Generator initialized")
    
    def _get_llm(self):
        """Get LLM instance"""
        if self.llm_config["provider"] == "ollama":
            from langchain_community.llms import Ollama
            return Ollama(
                model=self.llm_config["model"],
                base_url=self.llm_config["base_url"],
                temperature=0.3  # Lower temperature for more consistent output
            )
        elif self.llm_config["provider"] == "openai":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                api_key=self.llm_config["api_key"],
                model=self.llm_config["model"],
                temperature=0.3
            )
        elif self.llm_config["provider"] == "groq":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                api_key=self.llm_config["api_key"],
                base_url="https://api.groq.com/openai/v1",
                model=self.llm_config["model"],
                temperature=0.3
            )
    
    def generate_pa_form(
        self,
        prescription_data: Dict[str, Any],
        patient_data: Dict[str, Any],
        insurance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate prior authorization form
        
        Args:
            prescription_data: Extracted prescription information
            patient_data: Patient demographics and history
            insurance_data: Insurance information
        
        Returns:
            PA form data dictionary
        """
        try:
            logger.info("Generating PA form")
            
            # Generate PA ID
            pa_id = f"PA-{uuid.uuid4().hex[:8].upper()}"
            
            # Extract medication information
            medications = prescription_data.get("medications", [])
            primary_medication = medications[0] if medications else {}
            
            # Generate clinical justification using LLM
            justification = self._generate_clinical_justification(
                prescription_data,
                patient_data
            )
            
            # Determine required documents
            required_docs = self._determine_required_documents(
                primary_medication,
                patient_data
            )
            
            # Create PA form
            pa_form = {
                "pa_id": pa_id,
                "status": "draft",
                "created_date": datetime.now().isoformat(),
                "submission_date": None,
                "decision_date": None,
                
                # Patient Information
                "patient": {
                    "name": patient_data.get("name", "Unknown"),
                    "dob": patient_data.get("dob", "Unknown"),
                    "member_id": insurance_data.get("member_id", "Unknown"),
                    "group_number": insurance_data.get("group_number", "Unknown")
                },
                
                # Provider Information
                "provider": {
                    "name": prescription_data.get("doctor_name", "Unknown"),
                    "npi": patient_data.get("provider_npi", "Unknown"),
                    "phone": patient_data.get("provider_phone", "Unknown"),
                    "fax": patient_data.get("provider_fax", "Unknown")
                },
                
                # Medication Information
                "medication": {
                    "name": primary_medication.get("name", "Unknown"),
                    "dosage": primary_medication.get("dosage", "Unknown"),
                    "frequency": primary_medication.get("frequency", "Unknown"),
                    "duration": primary_medication.get("duration", "Unknown"),
                    "quantity": primary_medication.get("quantity", "Unknown"),
                    "ndc_code": primary_medication.get("ndc_code", "Unknown")
                },
                
                # Clinical Information
                "clinical": {
                    "diagnosis": prescription_data.get("diagnosis", "Unknown"),
                    "icd10_code": patient_data.get("icd10_code", "Unknown"),
                    "justification": justification,
                    "previous_treatments": patient_data.get("previous_treatments", []),
                    "treatment_failures": patient_data.get("treatment_failures", [])
                },
                
                # Insurance Information
                "insurance": {
                    "payer_name": insurance_data.get("payer_name", "Unknown"),
                    "plan_type": insurance_data.get("plan_type", "Unknown"),
                    "member_id": insurance_data.get("member_id", "Unknown")
                },
                
                # Required Documents
                "required_documents": required_docs,
                
                # Checklist
                "checklist": self._generate_checklist(required_docs)
            }
            
            logger.info(f"PA form generated: {pa_id}")
            
            return {
                "status": "success",
                "pa_form": pa_form
            }
        
        except Exception as e:
            logger.error(f"Failed to generate PA form: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _generate_clinical_justification(
        self,
        prescription_data: Dict[str, Any],
        patient_data: Dict[str, Any]
    ) -> str:
        """Generate clinical justification using LLM"""
        try:
            template = """Generate a clinical justification for prior authorization based on the following information:

Diagnosis: {diagnosis}
Medication: {medication}
Patient Age: {age}
Previous Treatments: {previous_treatments}

Write a concise, professional clinical justification (2-3 paragraphs) that includes:
1. Medical necessity of the prescribed medication
2. Why this medication is appropriate for the patient's condition
3. Previous treatment attempts and outcomes (if any)
4. Expected clinical benefits

Clinical Justification:"""

            medications = prescription_data.get("medications", [])
            medication_name = medications[0].get("name", "Unknown") if medications else "Unknown"
            
            prompt = PromptTemplate(
                template=template,
                input_variables=["diagnosis", "medication", "age", "previous_treatments"]
            )
            
            llm = self._get_llm()
            chain = prompt | llm
            
            response = chain.invoke({
                "diagnosis": prescription_data.get("diagnosis", "Not specified"),
                "medication": medication_name,
                "age": patient_data.get("age", "Unknown"),
                "previous_treatments": ", ".join(patient_data.get("previous_treatments", ["None documented"]))
            })
            
            if hasattr(response, 'content'):
                return response.content.strip()
            else:
                return str(response).strip()
        
        except Exception as e:
            logger.error(f"Failed to generate justification: {e}")
            return "Clinical justification pending - please provide detailed medical necessity documentation."
    
    def _determine_required_documents(
        self,
        medication: Dict[str, Any],
        patient_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Determine required documents for PA"""
        required_docs = [
            {
                "name": "Prescription",
                "description": "Valid prescription from licensed provider",
                "required": True,
                "status": "pending"
            },
            {
                "name": "Clinical Notes",
                "description": "Recent clinical notes documenting diagnosis and treatment plan",
                "required": True,
                "status": "pending"
            },
            {
                "name": "Lab Results",
                "description": "Relevant laboratory test results",
                "required": False,
                "status": "pending"
            },
            {
                "name": "Treatment History",
                "description": "Documentation of previous treatment attempts",
                "required": True,
                "status": "pending"
            },
            {
                "name": "Insurance Card",
                "description": "Copy of current insurance card",
                "required": True,
                "status": "pending"
            }
        ]
        
        # Add specialty-specific documents
        if medication.get("name", "").lower() in ["humira", "enbrel", "remicade"]:
            required_docs.append({
                "name": "Imaging Results",
                "description": "X-rays or MRI results showing disease progression",
                "required": True,
                "status": "pending"
            })
        
        return required_docs
    
    def _generate_checklist(self, required_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate PA submission checklist"""
        checklist = [
            {
                "item": "Complete patient demographics",
                "completed": False,
                "required": True
            },
            {
                "item": "Provider information with NPI",
                "completed": False,
                "required": True
            },
            {
                "item": "Diagnosis with ICD-10 code",
                "completed": False,
                "required": True
            },
            {
                "item": "Medication details with NDC code",
                "completed": False,
                "required": True
            },
            {
                "item": "Clinical justification",
                "completed": False,
                "required": True
            }
        ]
        
        # Add document checklist items
        for doc in required_docs:
            if doc["required"]:
                checklist.append({
                    "item": f"Attach {doc['name']}",
                    "completed": False,
                    "required": True
                })
        
        return checklist
    
    def submit_pa(self, pa_form: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit PA form (simulation)
        
        Args:
            pa_form: PA form data
        
        Returns:
            Submission result
        """
        try:
            # Validate checklist
            checklist = pa_form.get("checklist", [])
            required_items = [item for item in checklist if item["required"]]
            completed_items = [item for item in required_items if item["completed"]]
            
            if len(completed_items) < len(required_items):
                return {
                    "status": "incomplete",
                    "message": f"Please complete all required items ({len(completed_items)}/{len(required_items)} completed)",
                    "missing_items": [item["item"] for item in required_items if not item["completed"]]
                }
            
            # Simulate submission
            pa_form["status"] = "submitted"
            pa_form["submission_date"] = datetime.now().isoformat()
            pa_form["expected_decision_date"] = (datetime.now() + timedelta(days=3)).isoformat()
            pa_form["tracking_number"] = f"TRK-{uuid.uuid4().hex[:12].upper()}"
            
            logger.info(f"PA submitted: {pa_form['pa_id']}")
            
            return {
                "status": "success",
                "message": "Prior authorization submitted successfully",
                "pa_id": pa_form["pa_id"],
                "tracking_number": pa_form["tracking_number"],
                "expected_decision_date": pa_form["expected_decision_date"]
            }
        
        except Exception as e:
            logger.error(f"PA submission failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }


# Global PA generator instance
_pa_generator = None

def get_pa_generator() -> PAGenerator:
    """Get or create global PA generator instance"""
    global _pa_generator
    if _pa_generator is None:
        _pa_generator = PAGenerator()
    return _pa_generator
