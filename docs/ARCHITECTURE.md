# RxAccess AI - Architecture Documentation

## System Overview

RxAccess AI is a comprehensive healthcare AI platform built with a modular, microservices-inspired architecture. The system processes prescription data through multiple AI-powered pipelines to provide intelligent insights for patients, providers, and pharmaceutical companies.

## Architecture Layers

### 1. Presentation Layer (Streamlit)
- **Technology**: Streamlit web framework
- **Components**:
  - Main dashboard
  - Prescription upload interface
  - Medical Q&A interface
  - Prior authorization forms
  - Affordability calculator
  - Adherence dashboard
  - Multi-stakeholder views

### 2. Application Layer (Python)
- **Core Modules**:
  - `extraction/`: OCR and LLM-based data extraction
  - `rag/`: Retrieval-Augmented Generation for Q&A
  - `prior_auth/`: PA form generation and approval prediction
  - `affordability/`: Coverage estimation and assistance finder
  - `adherence/`: ML-based risk prediction and interventions
  - `utils/`: Shared utilities (logging, PII redaction, disclaimers)

### 3. AI/ML Layer
- **LLM Integration**: LangChain framework
  - Ollama (local models)
  - OpenAI API
  - Groq API
- **Vector Store**: ChromaDB for semantic search
- **ML Models**: XGBoost for adherence prediction
- **OCR**: Tesseract with preprocessing

### 4. Data Layer
- **Knowledge Base**: JSON files with drug information
- **Vector Database**: ChromaDB persistent storage
- **File Storage**: Local filesystem (S3-ready)
- **Synthetic Data**: Generated training datasets

## Data Flow

### Prescription Processing Flow
```
User Upload → OCR Engine → Raw Text → LLM Extractor → Structured Data → Storage
                                                              ↓
                                                        Vector Store
```

### RAG Q&A Flow
```
User Question → Query Embedding → Vector Search → Context Retrieval → LLM → Answer
                                                         ↑
                                                  Knowledge Base
```

### Prior Authorization Flow
```
Prescription Data → PA Generator → Form Creation → Approval Predictor → Risk Score
        ↓                                                    ↓
  Patient Data                                        Recommendations
```

### Adherence Prediction Flow
```
Patient Features → Feature Engineering → ML Model → Risk Score → Intervention Generator
                                            ↓
                                    Personalized Interventions
```

## Component Details

### OCR Engine
- **Input**: Images (JPG, PNG) or PDFs
- **Processing**:
  1. Image preprocessing (grayscale, contrast, sharpness)
  2. Tesseract OCR extraction
  3. Confidence scoring
- **Output**: Raw text with metadata

### LLM Extractor
- **Input**: Raw OCR text
- **Processing**:
  1. Prompt engineering for structured extraction
  2. LLM inference
  3. JSON parsing and validation
- **Output**: Structured prescription data

### RAG System
- **Components**:
  - Vector Store (ChromaDB)
  - Embedding Model (sentence-transformers)
  - Retrieval Chain
  - Q&A Chain
- **Features**:
  - Semantic search
  - Context-aware responses
  - Source attribution

### Prior Authorization
- **Components**:
  - Form Generator
  - Approval Predictor
  - Status Tracker
- **Features**:
  - Automated form population
  - Multi-factor approval scoring
  - Missing document detection

### Adherence System
- **Components**:
  - Risk Predictor (XGBoost)
  - Intervention Generator (LLM)
- **Features**:
  - 9-feature risk model
  - Personalized interventions
  - Behavioral nudges

## Security & Compliance

### PII Protection
- Redaction utilities for sensitive data
- Configurable anonymization modes
- Field-level masking

### HIPAA Considerations
- Audit logging
- Encrypted storage (production)
- Access controls
- Data retention policies

### Disclaimers
- Medical advice disclaimers
- PA prediction disclaimers
- Adherence risk disclaimers

## Scalability Considerations

### Horizontal Scaling
- Stateless application design
- Containerized deployment
- Load balancer ready

### Vertical Scaling
- Efficient vector search
- Batch processing support
- Caching strategies

### Cloud Deployment
- AWS-ready architecture
- S3 for file storage
- ECS/Fargate for containers
- RDS for structured data

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit |
| Backend | Python 3.10+, FastAPI |
| LLM Framework | LangChain |
| Vector DB | ChromaDB |
| ML | scikit-learn, XGBoost |
| OCR | Tesseract |
| Containerization | Docker |
| Orchestration | Docker Compose |

## Future Enhancements

### Short-term
- Real-time pharmacy integration
- Multi-language support
- Mobile app
- SMS/Email notifications

### Long-term
- EHR integration (HL7 FHIR)
- Blockchain for prescription verification
- Federated learning for privacy
- Real-world evidence generation
