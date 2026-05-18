"""
Personalized adherence intervention generation using LLM
"""
from typing import Dict, Any, List
from src.config import get_llm_config
from src.utils.logger import get_logger
from langchain_core.prompts import PromptTemplate

logger = get_logger(__name__)


class InterventionGenerator:
    """Generate personalized adherence interventions"""
    
    def __init__(self):
        """Initialize intervention generator"""
        self.llm_config = get_llm_config()
        logger.info("Intervention Generator initialized")
    
    def _get_llm(self):
        """Get LLM instance"""
        if self.llm_config["provider"] == "ollama":
            from langchain_community.llms import Ollama
            return Ollama(
                model=self.llm_config["model"],
                base_url=self.llm_config["base_url"],
                temperature=0.7
            )
        elif self.llm_config["provider"] == "openai":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                api_key=self.llm_config["api_key"],
                model=self.llm_config["model"],
                temperature=0.7
            )
        elif self.llm_config["provider"] == "groq":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                api_key=self.llm_config["api_key"],
                base_url="https://api.groq.com/openai/v1",
                model=self.llm_config["model"],
                temperature=0.7
            )
    
    def generate_interventions(
        self,
        patient_data: Dict[str, Any],
        prescription_data: Dict[str, Any],
        risk_assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate personalized adherence interventions
        
        Args:
            patient_data: Patient information
            prescription_data: Prescription details
            risk_assessment: Risk prediction results
        
        Returns:
            Personalized interventions
        """
        try:
            logger.info("Generating personalized interventions")
            
            # Generate different types of interventions
            reminders = self._generate_reminders(patient_data, prescription_data)
            educational_messages = self._generate_educational_content(
                prescription_data,
                risk_assessment
            )
            motivational_messages = self._generate_motivational_messages(
                patient_data,
                risk_assessment
            )
            behavioral_nudges = self._generate_behavioral_nudges(risk_assessment)
            
            result = {
                "status": "success",
                "reminders": reminders,
                "educational_messages": educational_messages,
                "motivational_messages": motivational_messages,
                "behavioral_nudges": behavioral_nudges,
                "intervention_plan": self._create_intervention_plan(
                    reminders,
                    educational_messages,
                    motivational_messages,
                    risk_assessment
                )
            }
            
            logger.info("Interventions generated successfully")
            
            return result
        
        except Exception as e:
            logger.error(f"Intervention generation failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _generate_reminders(
        self,
        patient_data: Dict[str, Any],
        prescription_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate medication reminders"""
        reminders = []
        medications = prescription_data.get("medications", [])
        
        for med in medications:
            frequency = med.get('frequency', 'once daily').lower()
            
            # Determine reminder times
            if 'once' in frequency or 'daily' in frequency:
                times = ['09:00']
            elif 'twice' in frequency or 'bid' in frequency:
                times = ['09:00', '21:00']
            elif 'three times' in frequency or 'tid' in frequency:
                times = ['08:00', '14:00', '20:00']
            elif 'four times' in frequency or 'qid' in frequency:
                times = ['08:00', '12:00', '16:00', '20:00']
            else:
                times = ['09:00']
            
            for time in times:
                reminders.append({
                    "medication": med.get('name', 'Unknown'),
                    "dosage": med.get('dosage', ''),
                    "time": time,
                    "instructions": med.get('instructions', 'Take as directed'),
                    "type": "medication_reminder"
                })
        
        return reminders
    
    def _generate_educational_content(
        self,
        prescription_data: Dict[str, Any],
        risk_assessment: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate educational messages using LLM"""
        try:
            medications = prescription_data.get("medications", [])
            if not medications:
                return []
            
            template = """Generate 3 brief, patient-friendly educational messages about medication adherence.

Medications: {medications}
Risk Factors: {risk_factors}

Create messages that:
1. Explain why taking medications as prescribed is important
2. Address specific risk factors
3. Provide practical tips
4. Use encouraging, non-judgmental language
5. Keep each message under 100 words

Format as numbered list (1., 2., 3.):"""

            med_names = [med.get('name', 'Unknown') for med in medications]
            risk_factors = [rf['factor'] for rf in risk_assessment.get('risk_factors', [])]
            
            prompt = PromptTemplate(
                template=template,
                input_variables=["medications", "risk_factors"]
            )
            
            llm = self._get_llm()
            chain = prompt | llm
            
            response = chain.invoke({
                "medications": ", ".join(med_names),
                "risk_factors": ", ".join(risk_factors) if risk_factors else "None identified"
            })
            
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            # Parse messages
            messages = []
            for line in content.split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    # Remove numbering
                    message_text = line.lstrip('0123456789.-) ')
                    if message_text:
                        messages.append({
                            "type": "educational",
                            "content": message_text,
                            "priority": "medium"
                        })
            
            return messages[:3]  # Return top 3
        
        except Exception as e:
            logger.error(f"Educational content generation failed: {e}")
            return [
                {
                    "type": "educational",
                    "content": "Taking your medications as prescribed helps manage your condition effectively.",
                    "priority": "medium"
                }
            ]
    
    def _generate_motivational_messages(
        self,
        patient_data: Dict[str, Any],
        risk_assessment: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate motivational messages"""
        messages = []
        
        risk_category = risk_assessment.get('risk_category', 'Moderate Risk')
        
        if risk_category == "High Risk":
            messages.extend([
                {
                    "type": "motivational",
                    "content": "Every dose you take is a step toward better health. You've got this!",
                    "tone": "encouraging"
                },
                {
                    "type": "motivational",
                    "content": "Managing your medications shows strength and self-care. Keep up the great work!",
                    "tone": "supportive"
                }
            ])
        elif risk_category == "Moderate Risk":
            messages.extend([
                {
                    "type": "motivational",
                    "content": "You're doing well with your medications. Consistency is key!",
                    "tone": "positive"
                },
                {
                    "type": "motivational",
                    "content": "Small daily actions lead to big health improvements. Stay on track!",
                    "tone": "encouraging"
                }
            ])
        else:
            messages.extend([
                {
                    "type": "motivational",
                    "content": "Excellent adherence! Your commitment to your health is inspiring.",
                    "tone": "congratulatory"
                }
            ])
        
        return messages
    
    def _generate_behavioral_nudges(
        self,
        risk_assessment: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate behavioral nudges based on risk factors"""
        nudges = []
        
        risk_factors = risk_assessment.get('risk_factors', [])
        
        for factor in risk_factors:
            if factor['factor'] == "Complex Regimen":
                nudges.append({
                    "type": "behavioral_nudge",
                    "strategy": "simplification",
                    "content": "Try linking medication times to daily routines (e.g., breakfast, bedtime)",
                    "action": "Set up pill organizer for the week"
                })
            
            elif factor['factor'] == "High Cost Burden":
                nudges.append({
                    "type": "behavioral_nudge",
                    "strategy": "financial_support",
                    "content": "Explore cost-saving options available to you",
                    "action": "Check patient assistance programs"
                })
            
            elif factor['factor'] == "Poor Past Adherence":
                nudges.append({
                    "type": "behavioral_nudge",
                    "strategy": "habit_formation",
                    "content": "Build a new habit: Start with one medication at a consistent time",
                    "action": "Set daily phone reminder"
                })
        
        # Add general nudges
        nudges.append({
            "type": "behavioral_nudge",
            "strategy": "social_proof",
            "content": "Patients who take medications consistently see better health outcomes",
            "action": "Track your adherence progress"
        })
        
        return nudges
    
    def _create_intervention_plan(
        self,
        reminders: List[Dict[str, Any]],
        educational: List[Dict[str, Any]],
        motivational: List[Dict[str, Any]],
        risk_assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create comprehensive intervention plan"""
        risk_category = risk_assessment.get('risk_category', 'Moderate Risk')
        
        if risk_category == "High Risk":
            intensity = "intensive"
            frequency = "daily"
        elif risk_category == "Moderate Risk":
            intensity = "moderate"
            frequency = "3x per week"
        else:
            intensity = "light"
            frequency = "weekly"
        
        plan = {
            "intensity": intensity,
            "frequency": frequency,
            "components": [
                {
                    "component": "Medication Reminders",
                    "frequency": "daily",
                    "count": len(reminders)
                },
                {
                    "component": "Educational Messages",
                    "frequency": frequency,
                    "count": len(educational)
                },
                {
                    "component": "Motivational Support",
                    "frequency": frequency,
                    "count": len(motivational)
                }
            ],
            "duration": "30 days",
            "review_schedule": "Weekly progress check-ins"
        }
        
        return plan


# Global generator instance
_intervention_generator = None

def get_intervention_generator() -> InterventionGenerator:
    """Get or create global intervention generator instance"""
    global _intervention_generator
    if _intervention_generator is None:
        _intervention_generator = InterventionGenerator()
    return _intervention_generator
