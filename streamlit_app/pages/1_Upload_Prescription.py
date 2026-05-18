"""
Prescription Upload & Extraction Page
"""
import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

st.markdown("""
<style>
.rx-card {
    background: #f8f9fa;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    border-left: 4px solid #1a73e8;
    margin-bottom: 0.6rem;
}
.med-card {
    background: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 0.8rem 1rem;
    margin-bottom: 0.5rem;
}
.warn-card {
    background: #fff8e1;
    border-left: 4px solid #f9a825;
    border-radius: 8px;
    padding: 0.7rem 1rem;
    margin-bottom: 0.4rem;
}
.step-badge {
    background: #1a73e8;
    color: white;
    border-radius: 50%;
    width: 24px;
    height: 24px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    font-weight: 700;
    margin-right: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

# ── Cached loaders ────────────────────────────────────────────────────────────
@st.cache_resource
def get_ocr_engine():
    from src.extraction.ocr_engine import OCREngine
    return OCREngine()

@st.cache_resource
def get_vision_extractor():
    from src.extraction.vision_extractor import VisionExtractor
    return VisionExtractor()

@st.cache_resource
def get_llm_extractor():
    from src.extraction.llm_extractor import LLMExtractor
    return LLMExtractor()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## 📄 Prescription Upload")
st.caption("Upload a prescription to begin your medication analysis workflow.")

# ── Workflow steps ────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown('<div class="rx-card"><b>① Upload</b><br><small>Photo or PDF</small></div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="rx-card"><b>② Extract</b><br><small>Smart analysis</small></div>', unsafe_allow_html=True)
with c3:
    st.markdown('<div class="rx-card"><b>③ Review</b><br><small>Medications & alerts</small></div>', unsafe_allow_html=True)
with c4:
    st.markdown('<div class="rx-card"><b>④ Act</b><br><small>PA · Cost · Adherence</small></div>', unsafe_allow_html=True)

st.markdown("---")

# ── Upload area ───────────────────────────────────────────────────────────────
col_upload, col_preview = st.columns([1, 1])

with col_upload:
    uploaded_file = st.file_uploader(
        "Choose a prescription file",
        type=["jpg", "jpeg", "png", "bmp", "tiff", "pdf"],
        help="Supports photos, scans, and PDFs — including handwritten prescriptions"
    )

    if uploaded_file:
        file_ext = Path(uploaded_file.name).suffix.lower()
        st.success(f"✅ **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")

    # Advanced settings (collapsed by default)
    with st.expander("⚙️ Advanced Settings", expanded=False):
        extraction_mode = st.radio(
            "Extraction Mode",
            ["Smart Extraction (Recommended)", "Document Scan Mode", "Basic Text Mode"],
            help="Smart Extraction handles blurry, handwritten, and low-quality images best."
        )
        show_raw = st.checkbox("Show raw extracted text", value=False)
        redact_pii = st.checkbox("Anonymize patient information", value=False)
    
    # Map display names to internal modes
    mode_map = {
        "Smart Extraction (Recommended)": "vision",
        "Document Scan Mode": "ocr_llm",
        "Basic Text Mode": "ocr_only"
    }
    internal_mode = mode_map.get(extraction_mode if 'extraction_mode' in dir() else "Smart Extraction (Recommended)", "vision")

with col_preview:
    if uploaded_file:
        file_ext = Path(uploaded_file.name).suffix.lower()
        if file_ext in [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]:
            st.image(uploaded_file.getvalue(), caption="Uploaded Prescription", use_column_width=True)
        else:
            st.markdown("""
            <div style="background:#f0f4ff;border-radius:10px;padding:2rem;text-align:center;border:2px dashed #1a73e8;">
                <div style="font-size:3rem">📄</div>
                <div style="color:#1a73e8;font-weight:600">PDF Ready</div>
                <div style="color:#666;font-size:0.85rem">Document will be processed automatically</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:#f8f9fa;border-radius:10px;padding:2rem;text-align:center;border:2px dashed #ccc;">
            <div style="font-size:3rem">📷</div>
            <div style="color:#666;font-weight:500">Preview will appear here</div>
            <div style="color:#999;font-size:0.8rem;margin-top:0.5rem">JPG · PNG · PDF · Handwritten</div>
        </div>
        """, unsafe_allow_html=True)

# ── Extract button ────────────────────────────────────────────────────────────
st.markdown("---")

if uploaded_file:
    if st.button("🔍 Analyze Prescription", type="primary", use_container_width=True):

        file_bytes = uploaded_file.getvalue()
        file_ext = Path(uploaded_file.name).suffix.lower()
        file_type = "pdf" if file_ext == ".pdf" else "image"
        structured_data = None

        # Smart extraction (vision first, OCR fallback)
        if internal_mode == "vision" and file_type == "image":
            with st.status("Analyzing prescription...", expanded=True) as status:
                st.write("Reading prescription content...")
                try:
                    vision = get_vision_extractor()
                    result = vision.extract(file_bytes)
                    if result["status"] in ("success", "partial") and result.get("data"):
                        structured_data = result["data"]
                        status.update(label="✅ Analysis complete", state="complete")
                        st.write(f"Found **{len(structured_data.get('medications', []))} medication(s)**")
                        if show_raw and result.get("raw_response"):
                            with st.expander("Raw response"):
                                st.text(result["raw_response"][:800])
                    else:
                        st.write("Switching to document scan mode...")
                        status.update(label="Switching to scan mode...", state="running")
                except Exception:
                    st.write("Switching to document scan mode...")

        # OCR + AI path
        if structured_data is None:
            with st.status("Processing document...", expanded=True) as status:
                st.write("Scanning document text...")
                ocr_engine = get_ocr_engine()
                ocr_result = ocr_engine.extract(file_bytes, file_type=file_type)
                conf = ocr_result.get("confidence", 0)
                text = ocr_result.get("text", "")

                if ocr_result["status"] == "error":
                    status.update(label="❌ Could not read document", state="error")
                    st.error("Unable to read this file. Try a clearer image or different format.")
                    st.stop()

                if show_raw and text:
                    with st.expander("Extracted text"):
                        st.text(text[:800])

                if internal_mode != "ocr_only" and text:
                    st.write("Structuring medication data...")
                    try:
                        extractor = get_llm_extractor()
                        llm_result = extractor.extract_structured_data(text, confidence=conf)
                        if llm_result["status"] in ("success", "partial") and llm_result.get("data"):
                            structured_data = llm_result["data"]
                        else:
                            structured_data = {"medications": [], "notes": text[:300]}
                    except Exception:
                        structured_data = {"medications": [], "notes": text[:300]}
                else:
                    structured_data = {"medications": [], "notes": text[:300]}

                status.update(label="✅ Processing complete", state="complete")

        # PII redaction
        if redact_pii and structured_data:
            try:
                from src.utils.pii_redaction import anonymize_prescription_data
                structured_data = anonymize_prescription_data(structured_data, mode="partial")
            except Exception:
                pass

        st.session_state["prescription_data"] = structured_data

        # ── Results ───────────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("## ✅ Prescription Summary")

        medications = structured_data.get("medications", [])

        # Patient & Provider cards
        col_a, col_b = st.columns(2)
        with col_a:
            with st.container(border=True):
                st.markdown("**👤 Patient**")
                st.write(f"**Name:** {structured_data.get('patient_name') or '—'}")
                st.write(f"**Age:** {structured_data.get('patient_age') or '—'}")
                st.write(f"**Gender:** {structured_data.get('patient_gender') or '—'}")
        with col_b:
            with st.container(border=True):
                st.markdown("**🩺 Prescriber**")
                st.write(f"**Doctor:** {structured_data.get('doctor_name') or '—'}")
                st.write(f"**Specialty:** {structured_data.get('doctor_specialty') or '—'}")
                st.write(f"**Date:** {structured_data.get('prescription_date') or '—'}")

        # Diagnosis
        if structured_data.get("diagnosis"):
            st.info(f"🏥 **Diagnosis:** {structured_data['diagnosis']}")

        # Medications
        st.markdown(f"### 💊 Medications ({len(medications)} prescribed)")
        if medications:
            for i, med in enumerate(medications, 1):
                with st.container(border=True):
                    col_name, col_dose, col_freq, col_dur = st.columns([2, 1, 1, 1])
                    col_name.markdown(f"**{i}. {med.get('name', 'Unknown')}**")
                    col_dose.metric("Dose", med.get("dosage") or "—")
                    col_freq.metric("Frequency", med.get("frequency") or "—")
                    col_dur.metric("Duration", med.get("duration") or "—")
                    if med.get("instructions"):
                        st.caption(f"📋 {med['instructions']}")
        else:
            st.warning("No medications detected. Try uploading a clearer image.")

        # Notes
        if structured_data.get("notes"):
            with st.expander("📝 Clinical Notes"):
                st.write(structured_data["notes"])

        # Next steps
        st.markdown("---")
        st.markdown("### 🚀 Recommended Next Steps")
        n1, n2, n3, n4 = st.columns(4)
        with n1:
            st.page_link("pages/2_Medical_Assistant.py", label="💬 Ask About Medications", icon="💬")
        with n2:
            st.page_link("pages/3_Prior_Authorization.py", label="📋 Prior Authorization", icon="📋")
        with n3:
            st.page_link("pages/4_Affordability.py", label="💰 Check Costs", icon="💰")
        with n4:
            st.page_link("pages/5_Adherence_Intelligence.py", label="📊 Adherence Plan", icon="📊")

else:
    # No file uploaded — demo option
    st.markdown("""
    <div style="background:#f0f4ff;border-radius:12px;padding:1.5rem;text-align:center;border:1px solid #c5d8ff;">
        <div style="font-size:2.5rem;margin-bottom:0.5rem">📋</div>
        <div style="font-weight:600;color:#1a73e8;margin-bottom:0.3rem">Upload a prescription to get started</div>
        <div style="color:#666;font-size:0.9rem">Or try the demo to explore all features</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")
    if st.button("🎯 Load Demo Prescription", use_container_width=True):
        st.session_state["prescription_data"] = {
            "patient_name": "John Doe", "patient_age": 52, "patient_gender": "Male",
            "doctor_name": "Dr. Sarah Johnson", "doctor_specialty": "Cardiology",
            "clinic_name": "City Medical Center", "prescription_date": "2024-01-15",
            "diagnosis": "Hypertension, Type 2 Diabetes",
            "medications": [
                {"name": "Lisinopril", "dosage": "10mg", "frequency": "Once daily",
                 "duration": "30 days", "quantity": "30 tablets", "instructions": "Take in the morning"},
                {"name": "Metformin", "dosage": "500mg", "frequency": "Twice daily",
                 "duration": "30 days", "quantity": "60 tablets", "instructions": "Take with meals"}
            ],
            "notes": "Follow up in 30 days. Monitor blood pressure daily."
        }
        st.success("✅ Demo prescription loaded!")
        st.rerun()

    st.markdown("")
    st.caption("⚠️ For demonstration purposes only. Not for clinical use.")
