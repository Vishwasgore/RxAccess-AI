"""
Patient assistance program finder
"""
from typing import Dict, Any, List
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AssistanceFinder:
    """Find patient assistance programs"""
    
    def __init__(self):
        """Initialize assistance finder"""
        # Mock assistance programs database
        self.programs = [
            {
                "name": "RxAssist Patient Assistance Program",
                "type": "manufacturer",
                "eligibility": "Income < 200% FPL",
                "coverage": "Free or low-cost medications",
                "website": "https://www.rxassist.org",
                "phone": "1-800-RX-ASSIST"
            },
            {
                "name": "NeedyMeds",
                "type": "nonprofit",
                "eligibility": "Varies by program",
                "coverage": "Discount cards and assistance",
                "website": "https://www.needymeds.org",
                "phone": "1-800-503-6897"
            },
            {
                "name": "Partnership for Prescription Assistance",
                "type": "coalition",
                "eligibility": "Uninsured or underinsured",
                "coverage": "Free or reduced-cost medications",
                "website": "https://www.pparx.org",
                "phone": "1-888-477-2669"
            },
            {
                "name": "GoodRx",
                "type": "discount_card",
                "eligibility": "No restrictions",
                "coverage": "Discount coupons (10-80% off)",
                "website": "https://www.goodrx.com",
                "phone": "1-855-268-2822"
            },
            {
                "name": "SingleCare",
                "type": "discount_card",
                "eligibility": "No restrictions",
                "coverage": "Prescription discounts",
                "website": "https://www.singlecare.com",
                "phone": "1-844-234-3057"
            },
            {
                "name": "Medicare Extra Help",
                "type": "government",
                "eligibility": "Medicare beneficiaries with limited income",
                "coverage": "Help with Part D costs",
                "website": "https://www.ssa.gov/medicare/prescriptionhelp",
                "phone": "1-800-772-1213"
            },
            {
                "name": "State Pharmaceutical Assistance Programs",
                "type": "state",
                "eligibility": "Varies by state",
                "coverage": "State-specific assistance",
                "website": "Varies by state",
                "phone": "Contact state health department"
            }
        ]
        
        logger.info("Assistance Finder initialized")
    
    def find_programs(
        self,
        patient_data: Dict[str, Any],
        prescription_data: Dict[str, Any],
        cost_burden: float = None
    ) -> Dict[str, Any]:
        """
        Find relevant patient assistance programs
        
        Args:
            patient_data: Patient information
            prescription_data: Prescription details
            cost_burden: Estimated cost burden (optional)
        
        Returns:
            List of relevant assistance programs
        """
        try:
            logger.info("Finding assistance programs")
            
            age = patient_data.get("age", 50)
            income_level = patient_data.get("income_level", "moderate")  # low, moderate, high
            insurance_status = patient_data.get("insurance_status", "insured")  # insured, uninsured, underinsured
            
            # Filter programs based on eligibility
            eligible_programs = []
            
            for program in self.programs:
                eligibility_score = self._check_eligibility(
                    program,
                    age,
                    income_level,
                    insurance_status
                )
                
                if eligibility_score > 0:
                    program_copy = program.copy()
                    program_copy["eligibility_score"] = eligibility_score
                    program_copy["match_reason"] = self._get_match_reason(
                        program,
                        age,
                        income_level,
                        insurance_status
                    )
                    eligible_programs.append(program_copy)
            
            # Sort by eligibility score
            eligible_programs.sort(key=lambda x: x["eligibility_score"], reverse=True)
            
            # Generate application guidance
            application_steps = self._generate_application_steps(eligible_programs)
            
            result = {
                "status": "success",
                "programs_found": len(eligible_programs),
                "programs": eligible_programs,
                "application_steps": application_steps,
                "estimated_savings": self._estimate_savings(eligible_programs, cost_burden)
            }
            
            logger.info(f"Found {len(eligible_programs)} eligible programs")
            
            return result
        
        except Exception as e:
            logger.error(f"Program search failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _check_eligibility(
        self,
        program: Dict[str, Any],
        age: int,
        income_level: str,
        insurance_status: str
    ) -> float:
        """Check eligibility and return score (0-1)"""
        score = 0.0
        
        program_type = program["type"]
        
        # Discount cards - everyone eligible
        if program_type == "discount_card":
            score = 0.8
        
        # Manufacturer programs - income-based
        elif program_type == "manufacturer":
            if income_level == "low":
                score = 1.0
            elif income_level == "moderate":
                score = 0.7
            else:
                score = 0.3
        
        # Nonprofit programs
        elif program_type == "nonprofit":
            if insurance_status in ["uninsured", "underinsured"]:
                score = 0.9
            else:
                score = 0.6
        
        # Government programs
        elif program_type == "government":
            if age >= 65:
                score = 0.95
            elif income_level == "low":
                score = 0.8
            else:
                score = 0.4
        
        # State programs
        elif program_type == "state":
            if income_level == "low":
                score = 0.85
            else:
                score = 0.5
        
        # Coalition programs
        elif program_type == "coalition":
            if insurance_status == "uninsured":
                score = 1.0
            elif insurance_status == "underinsured":
                score = 0.8
            else:
                score = 0.5
        
        return score
    
    def _get_match_reason(
        self,
        program: Dict[str, Any],
        age: int,
        income_level: str,
        insurance_status: str
    ) -> str:
        """Get reason for program match"""
        program_type = program["type"]
        
        if program_type == "discount_card":
            return "Available to all patients, no eligibility requirements"
        elif program_type == "government" and age >= 65:
            return "Medicare beneficiary - eligible for Extra Help program"
        elif income_level == "low":
            return "Income-based eligibility - likely to qualify"
        elif insurance_status == "uninsured":
            return "Uninsured patients are priority for this program"
        elif insurance_status == "underinsured":
            return "Designed for patients with inadequate insurance coverage"
        else:
            return "May be eligible based on specific circumstances"
    
    def _generate_application_steps(self, programs: List[Dict[str, Any]]) -> List[str]:
        """Generate application guidance"""
        if not programs:
            return ["No eligible programs found. Consider generic alternatives or discount cards."]
        
        steps = [
            "Gather required documents: proof of income, insurance cards, prescription",
            f"Start with highest-match program: {programs[0]['name']}",
            f"Visit {programs[0]['website']} or call {programs[0]['phone']}",
            "Complete application with provider's assistance if needed",
            "Follow up within 2-3 weeks if no response",
            "Apply to multiple programs to maximize chances of approval"
        ]
        
        return steps
    
    def _estimate_savings(self, programs: List[Dict[str, Any]], cost_burden: float = None) -> Dict[str, Any]:
        """Estimate potential savings"""
        if not programs:
            return {
                "min_savings": 0,
                "max_savings": 0,
                "average_savings": 0
            }
        
        # Estimate based on program types
        if cost_burden is None:
            cost_burden = 100  # Default monthly cost
        
        # Discount cards typically save 10-80%
        # Manufacturer programs can provide free medications
        # Government programs vary widely
        
        top_program = programs[0]
        
        if top_program["type"] == "manufacturer":
            min_savings = cost_burden * 0.5
            max_savings = cost_burden * 1.0  # Free
        elif top_program["type"] == "discount_card":
            min_savings = cost_burden * 0.1
            max_savings = cost_burden * 0.8
        elif top_program["type"] == "government":
            min_savings = cost_burden * 0.3
            max_savings = cost_burden * 0.9
        else:
            min_savings = cost_burden * 0.2
            max_savings = cost_burden * 0.7
        
        return {
            "min_savings": round(min_savings, 2),
            "max_savings": round(max_savings, 2),
            "average_savings": round((min_savings + max_savings) / 2, 2),
            "timeframe": "per month"
        }
    
    def get_generic_alternatives(
        self,
        prescription_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Find generic alternatives for brand medications"""
        try:
            medications = prescription_data.get("medications", [])
            alternatives = []
            
            # Mock generic alternatives
            generic_map = {
                "lipitor": "atorvastatin",
                "zocor": "simvastatin",
                "norvasc": "amlodipine",
                "prinivil": "lisinopril",
                "glucophage": "metformin",
                "synthroid": "levothyroxine",
                "prilosec": "omeprazole",
                "zoloft": "sertraline",
                "prozac": "fluoxetine",
                "cozaar": "losartan"
            }
            
            for med in medications:
                med_name = med.get("name", "").lower()
                
                # Check if brand name has generic
                generic_name = None
                for brand, generic in generic_map.items():
                    if brand in med_name:
                        generic_name = generic
                        break
                
                if generic_name:
                    alternatives.append({
                        "brand_name": med.get("name"),
                        "generic_name": generic_name.title(),
                        "potential_savings": "60-90%",
                        "bioequivalent": True,
                        "recommendation": "Discuss with provider"
                    })
            
            return {
                "status": "success",
                "alternatives_found": len(alternatives),
                "alternatives": alternatives
            }
        
        except Exception as e:
            logger.error(f"Generic search failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }


# Global finder instance
_assistance_finder = None

def get_assistance_finder() -> AssistanceFinder:
    """Get or create global assistance finder instance"""
    global _assistance_finder
    if _assistance_finder is None:
        _assistance_finder = AssistanceFinder()
    return _assistance_finder
