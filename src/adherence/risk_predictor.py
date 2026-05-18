"""
Medication adherence risk prediction using ML
"""
import numpy as np
import pandas as pd
from typing import Dict, Any
from pathlib import Path
import pickle
from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AdherenceRiskPredictor:
    """ML-based adherence risk predictor"""
    
    def __init__(self):
        """Initialize predictor"""
        self.model = None
        self.scaler = None
        self.feature_names = [
            'age',
            'num_medications',
            'doses_per_day',
            'regimen_complexity',
            'cost_burden',
            'has_side_effects',
            'chronic_condition',
            'previous_adherence_rate',
            'support_system_score'
        ]
        self.load_model()
        logger.info("Adherence Risk Predictor initialized")
    
    def load_model(self):
        """Load trained model and scaler"""
        try:
            model_path = settings.models_dir / "adherence_model.pkl"
            scaler_path = settings.models_dir / "scaler.pkl"
            
            if model_path.exists() and scaler_path.exists():
                with open(model_path, 'rb') as f:
                    self.model = pickle.load(f)
                with open(scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                logger.info("Loaded trained model and scaler")
            else:
                logger.warning("Model files not found. Using rule-based fallback.")
                self.model = None
                self.scaler = None
        
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.model = None
            self.scaler = None
    
    def predict_risk(
        self,
        patient_data: Dict[str, Any],
        prescription_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Predict adherence risk for a patient
        
        Args:
            patient_data: Patient information
            prescription_data: Prescription details
        
        Returns:
            Risk prediction with score and factors
        """
        try:
            logger.info("Predicting adherence risk")
            
            # Extract features
            features = self._extract_features(patient_data, prescription_data)
            
            # Predict using model or fallback
            if self.model is not None and self.scaler is not None:
                risk_score, risk_category = self._predict_with_model(features)
            else:
                risk_score, risk_category = self._predict_rule_based(features)
            
            # Identify risk factors
            risk_factors = self._identify_risk_factors(features)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(risk_factors, risk_category)
            
            result = {
                "status": "success",
                "risk_score": round(risk_score, 2),
                "risk_category": risk_category,
                "risk_factors": risk_factors,
                "recommendations": recommendations,
                "features": features
            }
            
            logger.info(f"Risk prediction: {risk_category} ({risk_score:.2f})")
            
            return result
        
        except Exception as e:
            logger.error(f"Risk prediction failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _extract_features(
        self,
        patient_data: Dict[str, Any],
        prescription_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Extract features for prediction"""
        medications = prescription_data.get("medications", [])
        
        # Calculate regimen complexity
        regimen_complexity = self._calculate_regimen_complexity(medications)
        
        # Extract features
        features = {
            'age': float(patient_data.get('age', 50)),
            'num_medications': float(len(medications)),
            'doses_per_day': self._calculate_doses_per_day(medications),
            'regimen_complexity': regimen_complexity,
            'cost_burden': float(patient_data.get('cost_burden', 3)),  # 1-5 scale
            'has_side_effects': float(patient_data.get('has_side_effects', 0)),  # 0 or 1
            'chronic_condition': float(patient_data.get('chronic_condition', 1)),  # 0 or 1
            'previous_adherence_rate': float(patient_data.get('previous_adherence_rate', 0.75)),  # 0-1
            'support_system_score': float(patient_data.get('support_system_score', 3))  # 1-5 scale
        }
        
        return features
    
    def _calculate_regimen_complexity(self, medications: list) -> float:
        """Calculate regimen complexity score (0-10)"""
        if not medications:
            return 0.0
        
        complexity = 0.0
        
        # More medications = higher complexity
        complexity += min(len(medications) * 1.5, 5.0)
        
        # Different frequencies = higher complexity
        frequencies = set()
        for med in medications:
            freq = (med.get('frequency') or '').lower()
            frequencies.add(freq)
        complexity += min(len(frequencies) * 0.5, 2.0)
        
        # Special instructions = higher complexity
        for med in medications:
            instructions = (med.get('instructions') or '').lower()
            if any(word in instructions for word in ['with food', 'before meals', 'at bedtime']):
                complexity += 0.5
        
        return min(complexity, 10.0)
    
    def _calculate_doses_per_day(self, medications: list) -> float:
        """Calculate total doses per day"""
        total_doses = 0.0
        
        for med in medications:
            frequency = (med.get('frequency') or '').lower()
            
            if 'once' in frequency or 'daily' in frequency:
                total_doses += 1
            elif 'twice' in frequency or 'bid' in frequency:
                total_doses += 2
            elif 'three times' in frequency or 'tid' in frequency:
                total_doses += 3
            elif 'four times' in frequency or 'qid' in frequency:
                total_doses += 4
            else:
                total_doses += 1  # Default
        
        return total_doses
    
    def _predict_with_model(self, features: Dict[str, float]) -> tuple:
        """Predict using trained ML model"""
        try:
            # Create feature vector
            feature_vector = np.array([[features[name] for name in self.feature_names]])
            
            # Scale features
            feature_vector_scaled = self.scaler.transform(feature_vector)
            
            # Predict probability
            risk_prob = self.model.predict_proba(feature_vector_scaled)[0][1]
            
            # Determine category
            if risk_prob >= 0.7:
                category = "High Risk"
            elif risk_prob >= 0.4:
                category = "Moderate Risk"
            else:
                category = "Low Risk"
            
            return risk_prob, category
        
        except Exception as e:
            logger.error(f"Model prediction failed: {e}")
            return self._predict_rule_based(features)
    
    def _predict_rule_based(self, features: Dict[str, float]) -> tuple:
        """Rule-based prediction fallback"""
        risk_score = 0.0
        
        # Age factor (elderly = higher risk)
        if features['age'] >= 65:
            risk_score += 0.15
        elif features['age'] <= 25:
            risk_score += 0.10
        
        # Medication count
        if features['num_medications'] >= 5:
            risk_score += 0.20
        elif features['num_medications'] >= 3:
            risk_score += 0.10
        
        # Regimen complexity
        risk_score += features['regimen_complexity'] * 0.03
        
        # Cost burden
        risk_score += features['cost_burden'] * 0.05
        
        # Side effects
        if features['has_side_effects']:
            risk_score += 0.15
        
        # Previous adherence
        risk_score += (1 - features['previous_adherence_rate']) * 0.25
        
        # Support system (inverse)
        risk_score += (5 - features['support_system_score']) * 0.03
        
        # Cap at 1.0
        risk_score = min(risk_score, 1.0)
        
        # Determine category
        if risk_score >= 0.6:
            category = "High Risk"
        elif risk_score >= 0.35:
            category = "Moderate Risk"
        else:
            category = "Low Risk"
        
        return risk_score, category
    
    def _identify_risk_factors(self, features: Dict[str, float]) -> list:
        """Identify specific risk factors"""
        risk_factors = []
        
        if features['age'] >= 65:
            risk_factors.append({
                "factor": "Advanced Age",
                "severity": "moderate",
                "description": "Elderly patients may face challenges with complex regimens"
            })
        
        if features['num_medications'] >= 5:
            risk_factors.append({
                "factor": "Polypharmacy",
                "severity": "high",
                "description": f"Taking {int(features['num_medications'])} medications increases complexity"
            })
        
        if features['regimen_complexity'] >= 7:
            risk_factors.append({
                "factor": "Complex Regimen",
                "severity": "high",
                "description": "Multiple medications with different schedules"
            })
        
        if features['cost_burden'] >= 4:
            risk_factors.append({
                "factor": "High Cost Burden",
                "severity": "high",
                "description": "Financial barriers may impact adherence"
            })
        
        if features['has_side_effects']:
            risk_factors.append({
                "factor": "Side Effects",
                "severity": "moderate",
                "description": "Experiencing medication side effects"
            })
        
        if features['previous_adherence_rate'] < 0.7:
            risk_factors.append({
                "factor": "Poor Past Adherence",
                "severity": "high",
                "description": f"Previous adherence rate: {features['previous_adherence_rate']*100:.0f}%"
            })
        
        if features['support_system_score'] <= 2:
            risk_factors.append({
                "factor": "Limited Support System",
                "severity": "moderate",
                "description": "Lack of family/caregiver support"
            })
        
        return risk_factors
    
    def _generate_recommendations(self, risk_factors: list, risk_category: str) -> list:
        """Generate adherence improvement recommendations"""
        recommendations = []
        
        if risk_category == "High Risk":
            recommendations.append("Consider intensive adherence support program")
            recommendations.append("Schedule frequent follow-up appointments")
        
        for factor in risk_factors:
            if factor["factor"] == "Polypharmacy":
                recommendations.append("Medication therapy management consultation recommended")
                recommendations.append("Consider medication synchronization program")
            
            elif factor["factor"] == "Complex Regimen":
                recommendations.append("Use pill organizer or medication management app")
                recommendations.append("Simplify regimen if possible (discuss with provider)")
            
            elif factor["factor"] == "High Cost Burden":
                recommendations.append("Explore patient assistance programs")
                recommendations.append("Consider generic alternatives")
            
            elif factor["factor"] == "Side Effects":
                recommendations.append("Discuss side effect management with provider")
                recommendations.append("Consider medication adjustment if appropriate")
            
            elif factor["factor"] == "Limited Support System":
                recommendations.append("Enroll in medication reminder service")
                recommendations.append("Consider community support resources")
        
        # General recommendations
        if not recommendations:
            recommendations.append("Continue current adherence practices")
            recommendations.append("Use medication reminders for consistency")
        
        return list(set(recommendations))  # Remove duplicates


# Global predictor instance
_risk_predictor = None

def get_risk_predictor() -> AdherenceRiskPredictor:
    """Get or create global risk predictor instance"""
    global _risk_predictor
    if _risk_predictor is None:
        _risk_predictor = AdherenceRiskPredictor()
    return _risk_predictor
