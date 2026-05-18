"""
Insurance coverage and cost estimation
"""
from typing import Dict, Any, List
import random
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CoverageEstimator:
    """Estimate insurance coverage and costs"""
    
    def __init__(self):
        """Initialize coverage estimator"""
        # Mock drug pricing database
        self.drug_prices = {
            "lisinopril": {"brand": 120, "generic": 15},
            "metformin": {"brand": 180, "generic": 10},
            "atorvastatin": {"brand": 250, "generic": 20},
            "levothyroxine": {"brand": 90, "generic": 12},
            "amlodipine": {"brand": 140, "generic": 18},
            "omeprazole": {"brand": 160, "generic": 25},
            "losartan": {"brand": 130, "generic": 16},
            "gabapentin": {"brand": 200, "generic": 30},
            "sertraline": {"brand": 180, "generic": 22},
            "albuterol": {"brand": 60, "generic": 45},
        }
        
        logger.info("Coverage Estimator initialized")
    
    def estimate_coverage(
        self,
        prescription_data: Dict[str, Any],
        insurance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Estimate insurance coverage and out-of-pocket costs
        
        Args:
            prescription_data: Prescription information
            insurance_data: Insurance plan details
        
        Returns:
            Coverage estimation results
        """
        try:
            logger.info("Estimating coverage")
            
            medications = prescription_data.get("medications", [])
            plan_type = insurance_data.get("plan_type", "PPO")
            
            coverage_details = []
            total_retail = 0
            total_insurance_pays = 0
            total_copay = 0
            
            for med in medications:
                med_name = med.get("name", "").lower()
                
                # Get pricing
                retail_price = self._get_retail_price(med_name)
                
                # Determine coverage tier
                tier = self._determine_formulary_tier(med_name, insurance_data)
                
                # Calculate copay
                copay = self._calculate_copay(retail_price, tier, plan_type)
                
                # Calculate insurance payment
                insurance_pays = retail_price - copay
                
                total_retail += retail_price
                total_insurance_pays += insurance_pays
                total_copay += copay
                
                coverage_details.append({
                    "medication": med.get("name", "Unknown"),
                    "retail_price": round(retail_price, 2),
                    "formulary_tier": tier,
                    "copay": round(copay, 2),
                    "insurance_pays": round(insurance_pays, 2),
                    "coverage_percentage": round((insurance_pays / retail_price * 100), 1) if retail_price > 0 else 0,
                    "generic_available": self._has_generic(med_name)
                })
            
            result = {
                "status": "success",
                "plan_name": insurance_data.get("payer_name", "Unknown"),
                "plan_type": plan_type,
                "coverage_details": coverage_details,
                "summary": {
                    "total_retail_price": round(total_retail, 2),
                    "total_insurance_pays": round(total_insurance_pays, 2),
                    "total_copay": round(total_copay, 2),
                    "overall_coverage_percentage": round((total_insurance_pays / total_retail * 100), 1) if total_retail > 0 else 0
                },
                "deductible_info": {
                    "annual_deductible": insurance_data.get("deductible", 1500),
                    "deductible_met": insurance_data.get("deductible_met", 800),
                    "remaining": insurance_data.get("deductible", 1500) - insurance_data.get("deductible_met", 800)
                },
                "out_of_pocket_max": {
                    "annual_max": insurance_data.get("oop_max", 6000),
                    "current": insurance_data.get("oop_current", 1200),
                    "remaining": insurance_data.get("oop_max", 6000) - insurance_data.get("oop_current", 1200)
                }
            }
            
            logger.info(f"Coverage estimated: ${total_copay:.2f} copay")
            
            return result
        
        except Exception as e:
            logger.error(f"Coverage estimation failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _get_retail_price(self, med_name: str) -> float:
        """Get retail price for medication"""
        # Check if in database
        for drug_key in self.drug_prices:
            if drug_key in med_name:
                # Return generic price by default
                return self.drug_prices[drug_key]["generic"]
        
        # Default price for unknown medications
        return random.uniform(20, 150)
    
    def _determine_formulary_tier(self, med_name: str, insurance_data: Dict[str, Any]) -> str:
        """Determine formulary tier"""
        # Simplified tier assignment
        if self._has_generic(med_name):
            return "Tier 1 (Preferred Generic)"
        else:
            return random.choice([
                "Tier 2 (Generic)",
                "Tier 3 (Preferred Brand)",
                "Tier 4 (Non-Preferred Brand)"
            ])
    
    def _calculate_copay(self, retail_price: float, tier: str, plan_type: str) -> float:
        """Calculate copay based on tier and plan"""
        if "Tier 1" in tier:
            copay_rate = 0.10  # 10% copay
            min_copay = 5
            max_copay = 15
        elif "Tier 2" in tier:
            copay_rate = 0.20
            min_copay = 10
            max_copay = 30
        elif "Tier 3" in tier:
            copay_rate = 0.35
            min_copay = 30
            max_copay = 60
        else:  # Tier 4
            copay_rate = 0.50
            min_copay = 50
            max_copay = 150
        
        copay = retail_price * copay_rate
        copay = max(min_copay, min(copay, max_copay))
        
        return copay
    
    def _has_generic(self, med_name: str) -> bool:
        """Check if generic version exists"""
        for drug_key in self.drug_prices:
            if drug_key in med_name:
                return True
        return random.choice([True, False])
    
    def compare_options(
        self,
        prescription_data: Dict[str, Any],
        insurance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare insurance vs cash-pay options
        
        Args:
            prescription_data: Prescription information
            insurance_data: Insurance details
        
        Returns:
            Comparison results
        """
        try:
            # Get insurance coverage
            insurance_estimate = self.estimate_coverage(prescription_data, insurance_data)
            
            # Calculate cash-pay prices (usually with discount card)
            medications = prescription_data.get("medications", [])
            cash_pay_total = 0
            cash_pay_details = []
            
            for med in medications:
                med_name = med.get("name", "").lower()
                retail_price = self._get_retail_price(med_name)
                
                # Apply typical discount card savings (30-80%)
                discount_rate = random.uniform(0.3, 0.8)
                cash_price = retail_price * (1 - discount_rate)
                
                cash_pay_total += cash_price
                cash_pay_details.append({
                    "medication": med.get("name", "Unknown"),
                    "retail_price": round(retail_price, 2),
                    "cash_price": round(cash_price, 2),
                    "savings": round(retail_price - cash_price, 2)
                })
            
            insurance_total = insurance_estimate.get("summary", {}).get("total_copay", 0)
            
            # Determine recommendation
            if cash_pay_total < insurance_total:
                recommendation = "cash_pay"
                savings = insurance_total - cash_pay_total
                message = f"Cash-pay option saves ${savings:.2f} compared to insurance copay"
            else:
                recommendation = "insurance"
                savings = cash_pay_total - insurance_total
                message = f"Insurance option saves ${savings:.2f} compared to cash-pay"
            
            return {
                "status": "success",
                "insurance_option": {
                    "total_cost": round(insurance_total, 2),
                    "details": insurance_estimate.get("coverage_details", [])
                },
                "cash_pay_option": {
                    "total_cost": round(cash_pay_total, 2),
                    "details": cash_pay_details
                },
                "recommendation": recommendation,
                "savings": round(abs(savings), 2),
                "message": message
            }
        
        except Exception as e:
            logger.error(f"Option comparison failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }


# Global estimator instance
_coverage_estimator = None

def get_coverage_estimator() -> CoverageEstimator:
    """Get or create global coverage estimator instance"""
    global _coverage_estimator
    if _coverage_estimator is None:
        _coverage_estimator = CoverageEstimator()
    return _coverage_estimator
