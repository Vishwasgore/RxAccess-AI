"""Prior Authorization Assistant Page"""
import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

st.markdown("## 📋 Prior Authorization")
st.caption("Generate PA forms, assess approval likelihood, and prepare submission documentation.")

_DEMO = {
    "patient_name": "John Doe", "patient_age": 52,
    "doctor_name": "Dr. Sarah Johnson", "doctor_specialty": "Cardiology",
    "diagnosis": "Hypertension",
    "medications": [{"name": "Lisinopril", "dosage": "10mg", "frequency": "Once daily", "duration": "30 days"}]
}

prescription_data = st.session_state.get("prescription_data") or _DEMO

if not st.session_state.get("prescription_data"):
    col_info, col_btn = st.columns([3, 1])
    with col_info:
        st.info("No prescription loaded — showing demo data.")
    with col_btn:
        if st.button("Load Demo", use_container_width=True):
            st.session_state["prescription_data"] = _DEMO
            st.rerun()

meds = prescription_data.get("medications", [])

col_left, col_right = st.columns([1, 1])

with col_left:
    st.markdown("### Request Details")
    with st.container(border=True):
        st.markdown("**Prescription**")
        for m in meds:
            st.caption(f"💊 {m.get('name','')} {m.get('dosage','')} — {m.get('frequency','')}")
        if prescription_data.get("diagnosis"):
            st.caption(f"🏥 {prescription_data['diagnosis']}")
    with st.container(border=True):
        st.markdown("**Patient & Clinical**")
        patient_name = st.text_input("Patient Name", value=prescription_data.get("patient_name") or "")
        patient_age = st.number_input("Age", value=int(prescription_data.get("patient_age") or 52), min_value=1, max_value=120)
        icd10_code = st.text_input("Diagnosis Code (ICD-10)", value="I10")
        previous_treatments = st.text_area("Prior Treatments Attempted", value="Hydrochlorothiazide 25mg — discontinued\nAmlodipine 5mg — insufficient response", height=80)
    with st.container(border=True):
        st.markdown("**Insurance**")
        payer_name = st.text_input("Insurance Payer", value="BlueCross BlueShield")
        plan_type = st.selectbox("Plan Type", ["PPO", "HMO", "EPO", "POS", "HDHP"])
        member_id = st.text_input("Member ID", value="BCB123456789")
        provider_npi = st.text_input("Provider NPI", value="1234567890")

with col_right:
    st.markdown("### Authorization Intelligence")
    if not st.session_state.get("pa_form"):
        with st.container(border=True):
            st.markdown("**Pre-Assessment**")
            checks = [("Prescription data", True), ("Diagnosis documented", bool(prescription_data.get("diagnosis"))), ("Prior treatments noted", True), ("Insurance information", True)]
            for label, ok in checks:
                st.write(f"{'✅' if ok else '⚠️'} {label}")
            readiness = sum(1 for _, ok in checks if ok) / len(checks)
            st.progress(readiness)
            st.caption(f"Submission readiness: {int(readiness*100)}%")
        with st.container(border=True):
            st.markdown("**Typical PA Requirements**")
            for req in ["Clinical diagnosis with ICD-10 code", "Prior treatment failure documentation", "Medical necessity justification", "Provider signature and NPI", "Insurance member information"]:
                st.caption(f"• {req}")
    if st.session_state.get("pa_form"):
        pa_form = st.session_state["pa_form"]
        pred = st.session_state.get("pa_prediction", {})
        score = pred.get("approval_score", 0.5)
        score_pct = int(score * 100)
        likelihood = pred.get("likelihood", "Moderate")
        color = "green" if score >= 0.65 else "orange" if score >= 0.4 else "red"
        with st.container(border=True):
            st.markdown("**Approval Likelihood**")
            st.markdown(f"## :{color}[{score_pct}%]")
            st.caption(likelihood)
            st.progress(float(score))
        with st.container(border=True):
            st.markdown("**Submission Status**")
            st.write(f"PA ID: `{pa_form.get('pa_id', '—')}`")
            st.write(f"Status: **{pa_form.get('status', 'Draft').upper()}**")
            st.write(f"Created: {datetime.now().strftime('%m/%d/%Y')}")
        if pred.get("missing_elements"):
            with st.container(border=True):
                st.markdown("**⚠️ Missing Requirements**")
                for item in pred["missing_elements"]:
                    st.caption(f"• {item}")
        if pred.get("suggestions"):
            with st.container(border=True):
                st.markdown("**💡 Recommendations**")
                for s in pred["suggestions"]:
                    st.caption(f"• {s}")

st.markdown("---")
if st.button("🚀 Generate Prior Authorization Form", type="primary", use_container_width=True):
    patient_data = {"name": patient_name, "age": patient_age, "dob": "01/01/1972", "icd10_code": icd10_code, "previous_treatments": [t.strip() for t in previous_treatments.split("\n") if t.strip()], "treatment_failures": [], "provider_npi": provider_npi, "provider_phone": "555-123-4567", "provider_fax": "555-123-4568"}
    insurance_data = {"payer_name": payer_name, "plan_type": plan_type, "member_id": member_id, "group_number": "GRP-001234", "deductible": 1500, "deductible_met": 800, "oop_max": 6000, "oop_current": 1200}
    with st.spinner("Generating authorization form..."):
        try:
            from src.prior_auth.pa_generator import get_pa_generator
            pa_gen = get_pa_generator()
            result = pa_gen.generate_pa_form(prescription_data, patient_data, insurance_data)
            if result["status"] == "success":
                st.session_state["pa_form"] = result["pa_form"]
                st.session_state["patient_data"] = patient_data
            else:
                st.error(f"Could not generate form: {result.get('error')}")
        except Exception as e:
            st.error(f"Error: {e}")
    with st.spinner("Calculating approval likelihood..."):
        try:
            from src.prior_auth.approval_predictor import get_approval_predictor
            predictor = get_approval_predictor()
            prediction = predictor.predict_approval(st.session_state.get("pa_form", {}), patient_data)
            st.session_state["pa_prediction"] = prediction
        except Exception:
            st.session_state["pa_prediction"] = {"approval_score": 0.5, "likelihood": "Moderate"}
    st.rerun()

if st.session_state.get("pa_form"):
    pa_form = st.session_state["pa_form"]
    patient_data = st.session_state.get("patient_data", {})
    with st.expander("📄 Full Authorization Form", expanded=False):
        med = pa_form.get("medication", {})
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Medication", med.get("name", "—"))
        c2.metric("Dosage", med.get("dosage", "—"))
        c3.metric("Frequency", med.get("frequency", "—"))
        c4.metric("Duration", med.get("duration", "—"))
        st.markdown("**Clinical Justification**")
        justification = pa_form.get("clinical", {}).get("justification", "")
        if not justification or len(justification) < 50:
            justification = f"Patient {patient_data.get('name','[Patient]')} has been diagnosed with {prescription_data.get('diagnosis','the indicated condition')}. Prior treatments have been attempted without adequate response. {med.get('name','The requested medication')} is medically necessary to achieve adequate disease control and prevent complications."
        st.text_area("", value=justification, height=120, disabled=True, label_visibility="collapsed")
        st.markdown("**Required Documents**")
        for doc in pa_form.get("required_documents", []):
            st.write(f"{'🔴 Required' if doc['required'] else '🟡 Optional'} — **{doc['name']}**: {doc['description']}")
    with st.expander("📊 Approval Score Breakdown", expanded=False):
        pred = st.session_state.get("pa_prediction", {})
        for factor in pred.get("factors", []):
            st.write(f"**{factor['factor']}** ({int(factor['weight']*100)}% weight): {int(factor['score']*100)}%")
            st.progress(float(factor["score"]))
            st.caption(factor["details"])
    col_sub1, col_sub2 = st.columns(2)
    with col_sub1:
        if st.button("📤 Submit Authorization", type="primary", use_container_width=True):
            try:
                from src.prior_auth.pa_generator import get_pa_generator
                pa_gen = get_pa_generator()
                submit_result = pa_gen.submit_pa(pa_form)
                if submit_result["status"] == "success":
                    st.success(f"✅ Submitted — Tracking #: **{submit_result['tracking_number']}**")
                    st.session_state["pa_submitted"] = True
                    st.session_state["tracking_number"] = submit_result["tracking_number"]
            except Exception as e:
                st.error(f"Submission error: {e}")
    with col_sub2:
        if st.button("💾 Save Draft", use_container_width=True):
            st.info("Draft saved.")

if st.session_state.get("pa_submitted"):
    st.markdown("---")
    st.markdown("### 📊 Submission Tracker")
    st.write(f"Tracking: `{st.session_state.get('tracking_number', 'TRK-DEMO')}`")
    cols = st.columns(4)
    for col, (label, kind) in zip(cols, [("Submitted","success"),("Under Review","warning"),("Decision Pending","info"),("Outcome","info")]):
        with col:
            if kind == "success": st.success(f"✅ {label}")
            elif kind == "warning": st.warning(f"🔄 {label}")
            else: st.info(f"⬜ {label}")

st.caption("⚠️ For demonstration purposes only. Not for actual insurance submission.")
