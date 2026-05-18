"""
RxAccess AI — Homepage
Clean, guided workflow UX for healthcare professionals and patients.
"""
import streamlit as st

st.set_page_config(
    page_title="RxAccess AI",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Hide default Streamlit header padding */
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }

    /* Hero */
    .hero-title {
        font-size: 3rem;
        font-weight: 800;
        color: #1a73e8;
        margin-bottom: 0.2rem;
        letter-spacing: -1px;
    }
    .hero-subtitle {
        font-size: 1.25rem;
        color: #5f6368;
        margin-bottom: 0.5rem;
        font-weight: 400;
    }
    .hero-desc {
        font-size: 1rem;
        color: #80868b;
        max-width: 600px;
        line-height: 1.6;
    }

    /* Workflow steps */
    .step-card {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        border-left: 4px solid #1a73e8;
        margin-bottom: 0.5rem;
    }
    .step-number {
        font-size: 0.75rem;
        font-weight: 700;
        color: #1a73e8;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .step-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #202124;
        margin: 0.2rem 0;
    }
    .step-desc {
        font-size: 0.88rem;
        color: #5f6368;
    }

    /* Demo queries */
    .query-chip {
        display: inline-block;
        background: #e8f0fe;
        color: #1a73e8;
        border-radius: 20px;
        padding: 0.3rem 0.9rem;
        font-size: 0.85rem;
        margin: 0.2rem;
        cursor: pointer;
    }

    /* Divider */
    .section-label {
        font-size: 0.75rem;
        font-weight: 700;
        color: #9aa0a6;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 0.8rem;
    }

    /* Trust badges */
    .badge {
        display: inline-block;
        background: #f1f3f4;
        border-radius: 6px;
        padding: 0.25rem 0.7rem;
        font-size: 0.8rem;
        color: #5f6368;
        margin-right: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ── HERO SECTION ──────────────────────────────────────────────────────────────
col_hero, col_img = st.columns([3, 2])

with col_hero:
    st.markdown('<div class="hero-title">💊 RxAccess AI</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-subtitle">AI-powered prescription intelligence platform</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="hero-desc">Upload a prescription to analyze medications, '
        'detect interactions, retrieve clinical insights, and support healthcare workflows — '
        'powered by Vision AI and a 3,800+ document medical knowledge base.</div>',
        unsafe_allow_html=True
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Primary + Secondary CTAs
    cta1, cta2, _ = st.columns([1.4, 1.4, 1])
    with cta1:
        if st.button("📄 Upload Prescription", type="primary", use_container_width=True):
            st.switch_page("pages/1_Upload_Prescription.py")
    with cta2:
        if st.button("🎯 Try Demo Prescription", use_container_width=True):
            st.session_state["prescription_data"] = {
                "patient_name": "John Doe",
                "patient_age": 52,
                "patient_gender": "Male",
                "doctor_name": "Dr. Sarah Johnson",
                "doctor_specialty": "Cardiology",
                "clinic_name": "City Medical Center",
                "prescription_date": "2024-01-15",
                "diagnosis": "Hypertension, Type 2 Diabetes",
                "medications": [
                    {"name": "Lisinopril", "dosage": "10mg", "frequency": "Once daily",
                     "duration": "30 days", "quantity": "30 tablets",
                     "instructions": "Take in the morning"},
                    {"name": "Metformin", "dosage": "500mg", "frequency": "Twice daily",
                     "duration": "30 days", "quantity": "60 tablets",
                     "instructions": "Take with meals"}
                ],
                "notes": "Follow up in 30 days. Monitor blood pressure daily."
            }
            st.success("✅ Demo prescription loaded. Navigate to any page to explore.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<span class="badge">🔒 PHI-Safe</span>'
        '<span class="badge">⚡ Groq Vision AI</span>'
        '<span class="badge">📚 3,844 Medical Documents</span>'
        '<span class="badge">🤖 XGBoost ML</span>',
        unsafe_allow_html=True
    )

with col_img:
    # Visual workflow diagram using native Streamlit
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("**How it works**")
        st.markdown("""
```
📷 Upload Prescription
        ↓
🤖 Vision AI Extraction
        ↓
💊 Medication Analysis
        ↓
🏥 Healthcare Intelligence
```
""")
        st.caption("Handwritten, blurry, image, or PDF — all supported")

# ── DISCLAIMER ────────────────────────────────────────────────────────────────
st.warning("⚠️ **Prototype for demonstration only.** Not intended for actual clinical use. Always consult a licensed healthcare professional.")

st.markdown("---")

# ── WORKFLOW STEPS ────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">How RxAccess AI Works</div>', unsafe_allow_html=True)

s1, s2, s3, s4 = st.columns(4)

with s1:
    with st.container(border=True):
        st.markdown("**Step 1**")
        st.markdown("### 📷 Upload")
        st.markdown("Upload a prescription photo or PDF — even handwritten or blurry images are supported.")
        st.caption("JPG · PNG · PDF · Handwritten")

with s2:
    with st.container(border=True):
        st.markdown("**Step 2**")
        st.markdown("### 🤖 Extract")
        st.markdown("Vision AI reads the prescription and extracts medications, dosages, and doctor details.")
        st.caption("Groq Vision · OCR fallback · Auto-correction")

with s3:
    with st.container(border=True):
        st.markdown("**Step 3**")
        st.markdown("### 💊 Analyze")
        st.markdown("Ask questions about side effects, interactions, and dosage using AI-powered medical search.")
        st.caption("3,844 medical documents · Drug interaction check")

with s4:
    with st.container(border=True):
        st.markdown("**Step 4**")
        st.markdown("### 🏥 Act")
        st.markdown("Generate prior authorization forms, check affordability, and predict adherence risk.")
        st.caption("PA automation · Cost analysis · ML risk scoring")

st.markdown("---")

# ── DEMO QUERIES ──────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Example Questions You Can Ask</div>', unsafe_allow_html=True)

col_q1, col_q2 = st.columns(2)

with col_q1:
    st.markdown("**Medication Safety**")
    demo_questions = [
        "What are the side effects of Azithromycin?",
        "Can I take Metformin with alcohol?",
        "How long does Lisinopril take to work?",
        "What should I avoid while taking Warfarin?",
    ]
    for q in demo_questions:
        if st.button(q, key=f"dq_{q[:20]}", use_container_width=True):
            st.session_state["pending_question"] = q
            st.switch_page("pages/2_Medical_Assistant.py")

with col_q2:
    st.markdown("**Clinical Workflows**")
    clinical_questions = [
        "Check interactions between Warfarin and Aspirin",
        "Does Humira require prior authorization?",
        "What patient assistance programs exist for insulin?",
        "Predict adherence risk for a complex regimen",
    ]
    for q in clinical_questions:
        if st.button(q, key=f"cq_{q[:20]}", use_container_width=True):
            st.session_state["pending_question"] = q
            st.switch_page("pages/2_Medical_Assistant.py")

st.markdown("---")

# ── CAPABILITIES SUMMARY ──────────────────────────────────────────────────────
st.markdown('<div class="section-label">Platform Capabilities</div>', unsafe_allow_html=True)

cap1, cap2, cap3 = st.columns(3)

with cap1:
    with st.container(border=True):
        st.markdown("#### 🔍 Prescription Intelligence")
        st.markdown("""
- Vision AI reads any prescription format
- Extracts medications, dosages, instructions
- Corrects OCR errors automatically
- Supports handwritten prescriptions
""")

with cap2:
    with st.container(border=True):
        st.markdown("#### 💬 Medical Knowledge Search")
        st.markdown("""
- 3,844 indexed medical documents
- Drug interaction detection
- Side effect profiles
- Clinical treatment guidelines
""")

with cap3:
    with st.container(border=True):
        st.markdown("#### 📋 Healthcare Workflows")
        st.markdown("""
- Prior authorization automation
- Insurance coverage estimation
- Patient assistance programs
- Adherence risk prediction (ML)
""")

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "RxAccess AI · Built with Groq Vision AI, LangChain RAG, ChromaDB, XGBoost · "
    "For demonstration purposes only · Not for clinical use"
)
