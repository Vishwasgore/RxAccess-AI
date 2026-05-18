"""
System initialization script
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.utils.logger import get_logger
import json

logger = get_logger(__name__)


def create_directories():
    """Create necessary directories"""
    directories = [
        settings.data_dir,
        settings.uploads_dir,
        settings.knowledge_base_dir,
        settings.synthetic_data_dir,
        settings.models_dir,
        settings.logs_dir,
        settings.data_dir / "chroma_db",
        settings.synthetic_data_dir / "prescriptions",
        Path("evaluation/results")
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {directory}")


def create_knowledge_base():
    """Create sample knowledge base files"""
    logger.info("Creating knowledge base files")
    
    # Drug information
    drug_info = [
        {
            "name": "Lisinopril",
            "generic_name": "Lisinopril",
            "class": "ACE Inhibitor",
            "uses": "Treatment of hypertension (high blood pressure) and heart failure",
            "dosage": "Typical dose: 10-40mg once daily",
            "side_effects": "Dizziness, headache, persistent dry cough, fatigue",
            "precautions": "Monitor kidney function and potassium levels. Avoid in pregnancy.",
            "interactions": "NSAIDs, potassium supplements, lithium"
        },
        {
            "name": "Metformin",
            "generic_name": "Metformin",
            "class": "Biguanide",
            "uses": "Treatment of type 2 diabetes mellitus",
            "dosage": "500-2000mg daily in divided doses with meals",
            "side_effects": "Nausea, diarrhea, stomach upset, metallic taste",
            "precautions": "Monitor kidney function. Risk of lactic acidosis. Hold before contrast procedures.",
            "interactions": "Alcohol, contrast dye, certain antibiotics"
        },
        {
            "name": "Atorvastatin",
            "generic_name": "Atorvastatin",
            "class": "Statin",
            "uses": "Lower cholesterol and reduce cardiovascular risk",
            "dosage": "10-80mg once daily",
            "side_effects": "Muscle pain, liver enzyme elevation, headache",
            "precautions": "Monitor liver function. Report unexplained muscle pain immediately.",
            "interactions": "Grapefruit juice, certain antibiotics, antifungals"
        }
    ]
    
    drug_info_file = settings.knowledge_base_dir / "drug_info.json"
    with open(drug_info_file, 'w') as f:
        json.dump(drug_info, f, indent=2)
    logger.info(f"Created {drug_info_file}")
    
    # Drug interactions
    interactions = [
        {
            "drug1": "Lisinopril",
            "drug2": "Ibuprofen",
            "severity": "Moderate",
            "description": "NSAIDs may reduce the antihypertensive effect of ACE inhibitors and increase risk of kidney problems",
            "recommendation": "Monitor blood pressure and kidney function. Consider alternative pain reliever like acetaminophen."
        },
        {
            "drug1": "Metformin",
            "drug2": "Alcohol",
            "severity": "Moderate",
            "description": "Alcohol increases risk of lactic acidosis with metformin",
            "recommendation": "Limit alcohol consumption. Avoid excessive drinking."
        }
    ]
    
    interactions_file = settings.knowledge_base_dir / "interactions.json"
    with open(interactions_file, 'w') as f:
        json.dump(interactions, f, indent=2)
    logger.info(f"Created {interactions_file}")
    
    # Side effects
    side_effects = {
        "Lisinopril": {
            "common": ["Dizziness", "Headache", "Dry cough", "Fatigue"],
            "serious": ["Angioedema", "Severe hypotension", "Kidney problems", "High potassium"],
            "management": "Take at bedtime if dizziness occurs. Stay hydrated. Report persistent cough to doctor."
        },
        "Metformin": {
            "common": ["Nausea", "Diarrhea", "Stomach upset", "Metallic taste"],
            "serious": ["Lactic acidosis", "Vitamin B12 deficiency"],
            "management": "Take with food. Start with low dose and increase gradually. Extended-release formulation may reduce GI side effects."
        }
    }
    
    side_effects_file = settings.knowledge_base_dir / "side_effects.json"
    with open(side_effects_file, 'w') as f:
        json.dump(side_effects, f, indent=2)
    logger.info(f"Created {side_effects_file}")


def initialize_vector_store():
    """Initialize vector store with knowledge base"""
    try:
        from src.rag.vector_store import initialize_knowledge_base
        vector_store = initialize_knowledge_base()
        stats = vector_store.get_collection_stats()
        logger.info(f"Vector store initialized: {stats['document_count']} documents")
    except Exception as e:
        logger.error(f"Failed to initialize vector store: {e}")


def main():
    """Main initialization"""
    logger.info("Starting system initialization")
    
    print("🚀 RxAccess AI - System Initialization")
    print("=" * 50)
    
    print("\n1. Creating directories...")
    create_directories()
    
    print("\n2. Creating knowledge base...")
    create_knowledge_base()
    
    print("\n3. Initializing vector store...")
    initialize_vector_store()
    
    print("\n✅ System initialization complete!")
    print("\nNext steps:")
    print("1. Run: streamlit run streamlit_app/app.py")
    print("2. Upload a prescription to get started")
    print("\nNote: Train adherence model with: python scripts/train_adherence_model.py")


if __name__ == "__main__":
    main()
