# RxAccess AI — Project Documentation

**Version:** 1.0  
**Live App:** https://rxaccess-ai.streamlit.app  
**Repository:** https://github.com/Vishwasgore/RxAccess-AI  
**Stack:** Python · Streamlit · Groq API · LangChain · ChromaDB · XGBoost · Tesseract OCR

---

## 1. Project Overview

RxAccess AI is a healthcare intelligence platform that transforms a prescription image or PDF into a complete clinical workflow. A user uploads a prescription — even handwritten or blurry — and the system extracts medications, checks interactions, answers clinical questions, generates prior authorization forms, estimates costs, and predicts medication adherence risk.

The platform is designed to feel like a modern healthcare SaaS product, not a technical AI demo. All AI/ML implementation details (model names, vector databases, embeddings, OCR internals) are hidden from the user interface.

---

## 2. Core Workflow

```
Upload Prescription (image / PDF)
        ↓
Smart Extraction (Vision AI → OCR fallback)
        ↓
Medication Summary (name · dose · frequency · instructions)
        ↓
Clinical Analysis (interactions · side effects · dosage guidance)
        ↓
Healthcare Intelligence
    ├── Prior Authorization
    ├── Affordability & Coverage
    └── Adherence Risk & Support Plan
```

---

## 3. System Architecture

### 3.1 Frontend — Streamlit

Multi-page Streamlit application with 6 pages plus a homepage:

| Page | File | Purpose |
|------|------|---------|
| Home | `streamlit_app/app.py` | Hero, workflow guide, demo queries |
| Upload Prescription | `pages/1_Upload_Prescription.py` | File upload, extraction, medication summary |
| Medical Assistant | `pages/2_Medical_Assistant.py` | RAG-powered Q&A chat |
| Prior Authorization | `pages/3_Prior_Authorization.py` | PA form generation and approval prediction |
| Affordability | `pages/4_Affordability.py` | Coverage estimation, cost comparison, assistance programs |
| Adherence Intelligence | `pages/5_Adherence_Intelligence.py` | Risk prediction, intervention plan |
| Dashboards | `pages/6_Dashboards.py` | Multi-stakeholder analytics views |

### 3.2 Backend — Python Modules

```
src/
├── extraction/
│   ├── vision_extractor.py     # Groq Vision API (llama-4-scout)
│   ├── ocr_engine.py           # Tesseract OCR with image preprocessing
│   └── llm_extractor.py        # LLM-based structuring of OCR text
├── rag/
│   ├── vector_store.py         # ChromaDB vector store management
│   ├── document_ingester.py    # PDF ingestion and chunking
│   ├── qa_chain.py             # Hybrid retrieval + Groq LLM answering
│   ├── interaction_engine.py   # Drug interaction pair analysis
│   └── drug_normalizer.py      # Brand→generic mapping + OpenFDA fallback
├── prior_auth/
│   ├── pa_generator.py         # PA form generation with LLM justification
│   └── approval_predictor.py   # Rule-based approval likelihood scoring
├── affordability/
│   ├── coverage_estimator.py   # Insurance coverage calculation
│   └── assistance_finder.py    # Patient assistance program matching
├── adherence/
│   ├── risk_predictor.py       # XGBoost ML risk scoring
│   └── intervention_gen.py     # Personalized intervention generation
└── utils/
    ├── logger.py               # Loguru structured logging
    ├── pii_redaction.py        # Patient data anonymization
    └── disclaimer.py           # Medical disclaimer text
```

---

## 4. Feature Details

### 4.1 Prescription Extraction

**Pipeline:** Vision AI → OCR + LLM → OCR only (fallback chain)

**Vision path (primary):**
- Sends image bytes directly to Groq's `meta-llama/llama-4-scout-17b-16e-instruct` vision model
- Returns structured JSON: patient, doctor, medications, diagnosis, notes
- Works on blurry, handwritten, low-quality images

**OCR path (fallback):**
- Tesseract OCR with advanced preprocessing: grayscale → 2× upscale → denoise → contrast enhancement → sharpening → binarization
- Confidence scoring per word
- LLM correction pass using `llama-3.1-8b-instant` to structure raw OCR text into JSON

**Output schema:**
```json
{
  "patient_name": "...",
  "patient_age": 52,
  "patient_gender": "Male",
  "doctor_name": "...",
  "doctor_specialty": "...",
  "clinic_name": "...",
  "prescription_date": "...",
  "diagnosis": "...",
  "medications": [
    {
      "name": "Lisinopril",
      "dosage": "10mg",
      "frequency": "Once daily",
      "duration": "30 days",
      "quantity": "30 tablets",
      "instructions": "Take in the morning"
    }
  ],
  "notes": "..."
}
```

### 4.2 Medical Knowledge Base (RAG)

**Documents ingested:** 3,844 indexed documents from 4 source PDFs:
- WHO Standard Treatment Guidelines
- Drug Interaction Studies (FDA)
- Drugs and Poison Information reference
- Clinical pharmacology reference

**Retrieval strategy:** Hybrid search
- 70% semantic similarity (ChromaDB + all-MiniLM-L6-v2 embeddings)
- 30% keyword matching (BM25-style)
- Intent detection: side_effects · interactions · dosage · general · safety
- Section-type boosting: interaction sections boosted for interaction queries

**Answer generation:**
- Groq `llama-3.1-8b-instant` with structured prompts per intent type
- Sources returned with relevance scores and section metadata

### 4.3 Drug Interaction Engine

- 200+ brand→generic name mappings (hardcoded + OpenFDA API fallback)
- Pair-based interaction analysis across all medication combinations
- Severity scoring from text keywords: contraindicated / major / moderate / minor
- Deduplication of symmetric pairs (A+B = B+A)
- Confidence scoring per drug name resolution

### 4.4 Prior Authorization

**Form generation:**
- Extracts medication, diagnosis, patient, and insurance data
- Generates clinical justification text via LLM
- Produces required documents checklist
- Assigns PA tracking ID

**Approval prediction:**
- Rule-based scoring across 5 factors: diagnosis documentation, prior treatment failures, clinical urgency, formulary tier, insurance plan type
- Weighted score → approval likelihood percentage
- Missing elements checklist and improvement suggestions

### 4.5 Affordability & Coverage

**Coverage estimation:**
- Formulary tier assignment per medication (Tier 1–4)
- Copay calculation based on deductible status and OOP maximum
- Per-medication and total cost breakdown
- Generic availability flag

**Cost comparison:**
- Insurance vs. cash-pay comparison
- Recommendation based on actual cost difference
- GoodRx/discount card guidance when cash-pay wins

**Patient assistance programs:**
- 7+ program types: manufacturer PAP, Medicare Extra Help, state programs, GoodRx, NeedyMeds, Partnership for Prescription Assistance, HRSA
- Eligibility scoring based on age, income, insurance status
- Application steps and contact information

**Generic alternatives:**
- Brand→generic mapping with bioequivalence confirmation
- Potential savings estimate per medication

### 4.6 Adherence Intelligence

**Risk prediction model:**
- XGBoost classifier trained on synthetic adherence data
- 9 features: age, medication count, doses/day, regimen complexity, cost burden, side effects, chronic condition, previous adherence rate, support system score
- Output: risk score (0–1) + category (Low / Moderate / High Risk)
- Fallback: rule-based scoring when model unavailable

**Risk factors identified:**
- Advanced age (≥65)
- Polypharmacy (≥5 medications)
- Complex regimen (multiple schedules)
- High cost burden
- Side effects present
- Poor past adherence (<70%)
- Limited support system

**Intervention generation:**
- Medication reminder schedule (time-based, per frequency)
- Educational messages tailored to medications and diagnosis
- Motivational messages
- Behavioral nudges (habit stacking, visual cues, progress tracking)
- 30-day support plan with intensity and check-in frequency

### 4.7 Dashboards

Multi-stakeholder views:
- **Patient view:** medication schedule, adherence streak, upcoming refills, cost summary
- **Provider view:** patient panel, adherence alerts, PA status, clinical flags
- **Pharmacy view:** refill queue, interaction alerts, generic opportunities
- **Pharma/Research view:** adherence trends, population analytics, program effectiveness

---

## 5. Technology Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Streamlit 1.57 |
| LLM provider | Groq API |
| Vision model | meta-llama/llama-4-scout-17b-16e-instruct |
| Text model | llama-3.1-8b-instant |
| RAG framework | LangChain + LangChain-Core |
| Vector store | ChromaDB (persistent) |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 (via ChromaDB ONNX) |
| OCR | Tesseract 5.x + pytesseract |
| PDF processing | pdf2image + poppler, PyMuPDF, pdfplumber |
| ML model | XGBoost + scikit-learn |
| Drug data | OpenFDA API (fallback) |
| Logging | Loguru |
| Deployment | Streamlit Cloud |
| CI/CD | GitHub (auto-deploy on push to main) |

---

## 6. Deployment

### 6.1 Streamlit Cloud Configuration

**Main file:** `streamlit_app/app.py`  
**Python version:** 3.11 (`runtime.txt`)  
**System packages:** `packages.txt`

```
libglib2.0-0t64
tesseract-ocr
tesseract-ocr-eng
poppler-utils
```

**Required secrets** (Streamlit Cloud → App Settings → Secrets):
```toml
GROQ_API_KEY = "gsk_..."
PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION = "python"
```

### 6.2 Environment Variables

```env
GROQ_API_KEY=gsk_...
LLM_PROVIDER=groq
LLM_MODEL=llama-3.1-8b-instant
VISION_MODEL=meta-llama/llama-4-scout-17b-16e-instruct
TESSERACT_CMD=tesseract          # Linux/Cloud: system path
POPPLER_PATH=                    # Linux/Cloud: system path
CHROMA_PERSIST_DIR=data/chroma_db
KNOWLEDGE_BASE_DIR=data/knowledge_base
```

### 6.3 Local Setup

```bash
# 1. Clone
git clone https://github.com/Vishwasgore/RxAccess-AI.git
cd RxAccess-AI

# 2. Virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env: add GROQ_API_KEY, set Tesseract/Poppler paths

# 5. Initialize knowledge base (first run only)
python scripts/init_system.py
python scripts/ingest_rag_data.py

# 6. Run
streamlit run streamlit_app/app.py
```

**Windows-specific paths in `.env`:**
```env
TESSERACT_CMD=E:\tesseract\tesseract.exe
POPPLER_PATH=E:\poppler\poppler-24.02.0\Library\bin
```

---

## 7. Data & Knowledge Base

### 7.1 RAG Source Documents

Located in `rag data/`:
- `standard-treatment-guidelines.pdf` — WHO clinical guidelines
- `51919312fnl-M12 Drug Interaction Studies.pdf` — FDA interaction data
- `drugs_and_poison_information.pdf` — Drug reference
- `9789240121966-eng.pdf` — WHO pharmacology reference

### 7.2 Structured Knowledge Base

Located in `data/knowledge_base/`:
- `drug_info.json` — Drug profiles (dosage, mechanism, class)
- `interactions.json` — Known drug-drug interactions
- `side_effects.json` — Side effect profiles per drug
- `conditions.json` — Condition-to-medication mappings

### 7.3 ML Training Data

Located in `data/synthetic/`:
- `adherence_data.csv` — 1,000 synthetic patient adherence records
- Generated by `scripts/generate_synthetic_data.py`
- Model trained by `scripts/train_adherence_model.py`
- Saved to `models/adherence_model.pkl` + `models/scaler.pkl`

---

## 8. Key Design Decisions

**Vision-first extraction:** Groq's vision model handles handwritten and blurry prescriptions better than OCR alone. OCR is kept as a reliable fallback for PDFs and cases where the API is unavailable.

**Hybrid RAG retrieval:** Pure semantic search misses exact drug names. Combining vector similarity (70%) with keyword matching (30%) improves recall for specific medication queries.

**Protobuf compatibility:** ChromaDB uses protobuf internally. On Python 3.11+, `PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python` must be set before any imports to avoid descriptor errors. This is set at the top of every page file.

**No `st.stop()` on missing prescription:** Pages use demo data as fallback instead of blocking with `st.stop()`. This ensures the app is always usable even without a loaded prescription.

**Session state for prescription data:** The extracted prescription is stored in `st.session_state["prescription_data"]` and shared across all pages. This is the single source of truth for the current patient context.

**XGBoost model versioning:** The adherence model was trained with scikit-learn 1.4.0 but deployed on 1.8.0. A `UserWarning` is expected and harmless — the model still functions correctly.

**Transformers file watcher noise:** `sentence-transformers` pulls in `transformers`, which triggers Streamlit's file watcher to scan all transformer model files. These produce hundreds of `[transformers]` log lines but do not affect functionality. Suppressed via `folderWatchBlacklist` in `.streamlit/config.toml`.

---

## 9. Known Limitations

- **Not for clinical use.** All outputs are for demonstration and educational purposes only.
- **Groq API dependency.** Vision extraction and LLM answering require a valid Groq API key. Without it, the app falls back to OCR-only extraction and cannot answer questions.
- **Session state is ephemeral.** Prescription data is lost on page refresh or session timeout. There is no persistent patient database.
- **Adherence model is trained on synthetic data.** Real-world accuracy would require clinical validation data.
- **PA forms are not submittable.** The prior authorization workflow generates realistic forms but does not connect to actual insurance payer systems.
- **Cost estimates are approximate.** Affordability calculations use representative pricing, not real-time pharmacy or insurance data.

---

## 10. File Structure

```
RxAccess-AI/
├── streamlit_app/
│   ├── app.py                          # Homepage
│   ├── pages/
│   │   ├── 1_Upload_Prescription.py
│   │   ├── 2_Medical_Assistant.py
│   │   ├── 3_Prior_Authorization.py
│   │   ├── 4_Affordability.py
│   │   ├── 5_Adherence_Intelligence.py
│   │   └── 6_Dashboards.py
│   └── admin/
│       └── knowledge_base_admin.py
├── src/
│   ├── config.py
│   ├── extraction/
│   ├── rag/
│   ├── prior_auth/
│   ├── affordability/
│   ├── adherence/
│   └── utils/
├── scripts/
│   ├── init_system.py
│   ├── ingest_rag_data.py
│   ├── expand_knowledge_base.py
│   ├── generate_synthetic_data.py
│   ├── train_adherence_model.py
│   └── check_rag.py
├── data/
│   ├── chroma_db/                      # Persistent vector store
│   ├── knowledge_base/                 # Structured JSON data
│   ├── synthetic/                      # Training data
│   └── uploads/                        # Temporary upload storage
├── models/
│   ├── adherence_model.pkl
│   └── scaler.pkl
├── rag data/                           # Source PDFs for ingestion
├── docs/
│   ├── ARCHITECTURE.md
│   └── PROJECT_DOCUMENTATION.md       # This file
├── .streamlit/
│   └── config.toml
├── requirements.txt
├── packages.txt
├── runtime.txt
├── .env.example
└── README.md
```

---

## 11. Scripts Reference

| Script | Purpose |
|--------|---------|
| `init_system.py` | Full system initialization (KB + model + RAG) |
| `ingest_rag_data.py` | Ingest PDFs from `rag data/` into ChromaDB |
| `expand_knowledge_base.py` | Expand structured JSON knowledge base |
| `generate_synthetic_data.py` | Generate synthetic adherence training data |
| `train_adherence_model.py` | Train and save XGBoost adherence model |
| `check_rag.py` | Verify RAG system and document count |
| `test_rag.py` | Run test queries against the knowledge base |
| `test_interactions.py` | Test drug interaction detection |

---

*RxAccess AI — Built for demonstration and educational purposes. Not intended for clinical use.*
