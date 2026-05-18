"""
Prescription Upload & Extraction Page
Vision-first pipeline: image → Groq Vision AI → structured data
Falls back to Tesseract OCR + LLM if vision fails
"""
import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import streamlit as st
import sys
from pathlib import Path
import io

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.disclaimer import get_disclaimer

st.title("📄 Prescription Upload & Extraction")
st.markdown("Upload a prescription image or PDF — AI reads it even if blurry or handwritten.")

with st.expander("⚠️ Disclaimer", expanded=False):
    st.warning(get_disclaimer())

# ── Cached resource loaders ──────────────────────────────────────────────────
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

# ── Upload UI ────────────────────────────────────────────────────────────────
st.markdown("---")
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📁 Upload File")
    uploaded_file = st.file_uploader(
        "Choose a prescription image or PDF",
        type=["jpg", "jpeg", "png", "bmp", "tiff", "pdf"],
        help="Supports JPG, PNG, BMP, TIFF, PDF — even blurry or handwritten"
    )

    if uploaded_file:
        file_ext = Path(uploaded_file.name).suffix.lower()
        st.success(f"✅ **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")

        if file_ext in [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]:
            st.image(uploaded_file.getvalue(), caption="Uploaded Prescription", use_column_width=True)
        else:
            st.info("📄 PDF ready for extraction")

with col2:
    st.markdown("### ⚙️ Extraction Settings")

    extraction_mode = st.radio(
        "Extraction Method",
        ["🤖 AI Vision (Recommended)", "📝 OCR + AI", "📝 OCR Only"],
        help="AI Vision sends the image directly to Groq — best for blurry/handwritten prescriptions"
    )

    show_raw = st.checkbox("Show raw extracted text", value=False)
    redact_pii = st.checkbox("Redact patient PII", value=False)

    st.markdown("---")
    st.markdown("**💡 Tips for best results:**")
    st.caption("• Good lighting, no shadows")
    st.caption("• Hold camera directly above")
    st.caption("• Keep text in focus")
    st.caption("• AI Vision works even on blurry images")

# ── Extract button ───────────────────────────────────────────────────────────
st.markdown("---")

if uploaded_file and st.button("🔍 Extract Prescription Data", type="primary", use_container_width=True):

    file_bytes = uploaded_file.getvalue()
    file_ext = Path(uploaded_file.name).suffix.lower()
    file_type = "pdf" if file_ext == ".pdf" else "image"

    structured_data = None
    extraction_method_used = ""

    # ── PATH A: AI Vision (image files only) ────────────────────────────────
    if "Vision" in extraction_mode and file_type == "image":
        with st.status("🤖 Analyzing image with Groq Vision AI...", expanded=True) as status:
            st.write("Sending image to Groq Vision model...")
            try:
                vision = get_vision_extractor()
                result = vision.extract(file_bytes)

                if result["status"] in ("success", "partial") and result.get("data"):
                    structured_data = result["data"]
                    extraction_method_used = "Groq Vision AI (llama-4-scout)"
                    status.update(label="✅ Vision extraction complete!", state="complete")
                    st.write(f"Medications found: **{len(structured_data.get('medications', []))}**")

                    if show_raw and result.get("raw_response"):
                        with st.expander("📝 Raw AI Response"):
                            st.text(result["raw_response"][:1000])
                else:
                    st.warning(f"Vision extraction issue: {result.get('error', 'Unknown')}. Falling back to OCR...")
                    status.update(label="⚠️ Falling back to OCR...", state="running")

            except Exception as e:
                st.warning(f"Vision failed ({e}). Falling back to OCR...")
                status.update(label="⚠️ Falling back to OCR...", state="running")

    # ── PATH B: OCR + LLM (fallback or user choice) ─────────────────────────
    if structured_data is None:
        with st.status("🔎 Running OCR extraction...", expanded=True) as status:
            st.write("Preprocessing image for better OCR accuracy...")

            ocr_engine = get_ocr_engine()
            ocr_result = ocr_engine.extract(file_bytes, file_type=file_type)

            conf = ocr_result.get("confidence", 0)
            text = ocr_result.get("text", "")

            if ocr_result["status"] == "error":
                status.update(label="❌ OCR failed", state="error")
                st.error(f"OCR error: {ocr_result.get('error')}")
                if file_type == "pdf":
                    st.info("💡 Try saving the PDF as a PNG/JPG image and re-uploading.")
                st.stop()

            st.write(f"OCR confidence: **{conf:.1f}%** | Words extracted: **{ocr_result['word_count']}**")

            if conf < 20:
                st.warning("⚠️ Very low OCR confidence — image may be blurry. AI will attempt to interpret.")
            elif conf < 50:
                st.info("ℹ️ Moderate OCR confidence — AI will correct errors.")

            if show_raw and text:
                with st.expander("📝 Raw OCR Text"):
                    st.text(text[:1000])

            # LLM correction step
            if "OCR Only" not in extraction_mode and text:
                st.write("🤖 Sending to Groq AI for intelligent structuring...")
                try:
                    extractor = get_llm_extractor()
                    llm_result = extractor.extract_structured_data(text, confidence=conf)

                    if llm_result["status"] in ("success", "partial") and llm_result.get("data"):
                        structured_data = llm_result["data"]
                        extraction_method_used = f"Tesseract OCR ({conf:.0f}%) + Groq AI correction"
                        status.update(label="✅ OCR + AI extraction complete!", state="complete")
                    else:
                        structured_data = {"patient_name": None, "doctor_name": None,
                                           "medications": [], "notes": text[:300], "diagnosis": None}
                        extraction_method_used = f"Tesseract OCR only ({conf:.0f}%)"
                        status.update(label="⚠️ Partial extraction", state="complete")
                except Exception as e:
                    st.warning(f"AI structuring failed: {e}")
                    structured_data = {"patient_name": None, "doctor_name": None,
                                       "medications": [], "notes": text[:300], "diagnosis": None}
                    extraction_method_used = f"Tesseract OCR only ({conf:.0f}%)"
                    status.update(label="⚠️ OCR only (AI unavailable)", state="complete")
            else:
                structured_data = {"patient_name": None, "doctor_name": None,
                                   "medications": [], "notes": text[:300], "diagnosis": None}
                extraction_method_used = f"Tesseract OCR only ({conf:.0f}%)"
                status.update(label="✅ OCR extraction complete!", state="complete")

    # ── Apply PII redaction ──────────────────────────────────────────────────
    if redact_pii and structured_data:
        from src.utils.pii_redaction import anonymize_prescription_data
        structured_data = anonymize_prescription_data(structured_data, mode="partial")

    # ── Save to session state ────────────────────────────────────────────────
    st.session_state["prescription_data"] = structured_data

    # ── Display results ──────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("## ✅ Extracted Prescription Data")
    st.caption(f"Extracted using: **{extraction_method_used}**")

    # Patient & Doctor
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### 👤 Patient")
        st.info(f"""
**Name:** {structured_data.get('patient_name') or '—'}
**Age:** {structured_data.get('patient_age') or '—'}
**Gender:** {structured_data.get('patient_gender') or '—'}
        """)
    with col_b:
        st.markdown("#### 🩺 Provider")
        st.info(f"""
**Doctor:** {structured_data.get('doctor_name') or '—'}
**Specialty:** {structured_data.get('doctor_specialty') or '—'}
**Clinic:** {structured_data.get('clinic_name') or '—'}
**Date:** {structured_data.get('prescription_date') or '—'}
        """)

    # Diagnosis
    if structured_data.get("diagnosis"):
        st.markdown("#### 🏥 Diagnosis")
        st.success(f"**{structured_data['diagnosis']}**")

    # Medications
    st.markdown("#### 💊 Medications")
    medications = structured_data.get("medications", [])

    if medications:
        for i, med in enumerate(medications, 1):
            with st.expander(f"💊 {i}. {med.get('name', 'Unknown Medication')}", expanded=True):
                c1, c2, c3 = st.columns(3)
                c1.metric("Dosage", med.get("dosage") or "—")
                c2.metric("Frequency", med.get("frequency") or "—")
                c3.metric("Duration", med.get("duration") or "—")
                if med.get("quantity"):
                    st.caption(f"📦 Quantity: {med['quantity']}")
                if med.get("instructions"):
                    st.caption(f"📋 Instructions: {med['instructions']}")
    else:
        st.warning("No medications detected. Try **AI Vision** mode or use a clearer image.")

    # Notes
    if structured_data.get("notes"):
        with st.expander("📝 Additional Notes"):
            st.write(structured_data["notes"])

    # Raw JSON
    with st.expander("🔧 Full JSON Data"):
        st.json(structured_data)

    # Navigation
    st.markdown("---")
    st.success("✅ Done! Navigate to other pages to explore features.")
    c1, c2, c3 = st.columns(3)
    c1.page_link("pages/2_Medical_Assistant.py", label="💬 Medical Assistant", icon="💬")
    c2.page_link("pages/3_Prior_Authorization.py", label="📋 Prior Authorization", icon="📋")
    c3.page_link("pages/4_Affordability.py", label="💰 Affordability", icon="💰")

# ── Demo mode ────────────────────────────────────────────────────────────────
elif not uploaded_file:
    st.info("👆 Upload a prescription above, or load demo data to explore features.")

    if st.button("🎯 Load Demo Prescription", use_container_width=True):
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
                 "duration": "30 days", "quantity": "30 tablets", "instructions": "Take in the morning"},
                {"name": "Metformin", "dosage": "500mg", "frequency": "Twice daily",
                 "duration": "30 days", "quantity": "60 tablets", "instructions": "Take with meals"}
            ],
            "notes": "Follow up in 30 days. Monitor blood pressure daily."
        }
        st.success("✅ Demo prescription loaded!")
        st.rerun()
