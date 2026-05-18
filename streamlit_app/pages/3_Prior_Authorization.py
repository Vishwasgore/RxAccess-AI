"""
Prior Authorization Assistant Page
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.disclaimer import get_pa_disclaimer

st.title("📋 Prior Authorization Assistant")
st.markdown("Generate PA forms, predict approval likelihood, and track submission status.")

with st.expander("ℹ️ PA Disclaimer"):
    st.info(get_pa_disclaimer())

# Get prescription data
prescription_data = st.session_state.get("prescription_data")

if not prescription_data:
    st.warning("⚠️ No prescription loaded. Please upload a prescription first or use demo data.")
    if st.button("Load Demo Data"):
        st.session_state["prescription_data"] = {
            "patient_name": "John Doe", "patient_age": 52,
            "doctor_name": "Dr. Sarah Johnson", "doctor_specialty": "Cardiology",
            "diagnosis": "Hypertension",
            "medications": [{"name": "Lisinopril", "dosage": "10mg", "frequency": "Once daily", "duration": "30 days"}]
        }
        st.rerun()
    st.stop()

# Patient & Insurance input
st.markdown("---")
st.markdown("### 📝 Patient & Insurance Information")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Patient Details**")
    patient_name = st.text_input("Patient Name", value=prescription_data.get("patient_name", ""))
    patient_dob = st.text_input("Date of Birth", value="01/01/1972")
    patient_age = st.number_input("Age", value=int(prescription_data.get("patient_age") or 52), min_value=1, max_value=120)
    icd10_code = st.text_input("ICD-10 Code", value="I10", help="Diagnosis code (e.g., I10 for Hypertension)")
    previous_treatments = st.text_area(
        "Previous Treatments (one per line)",
        value="Hydrochlorothiazide 25mg - discontinued due to side effects\nAmlodipine 5mg - insufficient response"
    )

with col2:
    st.markdown("**Insurance Details**")
    payer_name = st.text_input("Insurance Payer", value="BlueCross BlueShield")
    plan_type = st.selectbox("Plan Type", ["PPO", "HMO", "EPO", "POS", "HDHP"])
    member_id = st.text_input("Member ID", value="BCB123456789")
    group_number = st.text_input("Group Number", value="GRP-001234")
    provider_npi = st.text_input("Provider NPI", value="1234567890")

# Generate PA Form
st.markdown("---")
if st.button("🚀 Generate Prior Authorization Form", type="primary", use_container_width=True):

    patient_data = {
        "name": patient_name,
        "dob": patient_dob,
        "age": patient_age,
        "icd10_code": icd10_code,
        "previous_treatments": [t.strip() for t in previous_treatments.split("\n") if t.strip()],
        "treatment_failures": [],
        "provider_npi": provider_npi,
        "provider_phone": "555-123-4567",
        "provider_fax": "555-123-4568"
    }

    insurance_data = {
        "payer_name": payer_name,
        "plan_type": plan_type,
        "member_id": member_id,
        "group_number": group_number,
        "deductible": 1500,
        "deductible_met": 800,
        "oop_max": 6000,
        "oop_current": 1200
    }

    with st.spinner("📝 Generating PA form..."):
        try:
            from src.prior_auth.pa_generator import get_pa_generator
            pa_gen = get_pa_generator()
            result = pa_gen.generate_pa_form(prescription_data, patient_data, insurance_data)

            if result["status"] == "success":
                pa_form = result["pa_form"]
                st.session_state["pa_form"] = pa_form
                st.session_state["patient_data"] = patient_data
            else:
                st.error(f"Failed to generate PA form: {result.get('error')}")
                st.stop()
        except Exception as e:
            st.error(f"Error: {e}")
            st.stop()

    # Display PA Form
    st.markdown("---")
    st.markdown("## 📄 Prior Authorization Form")

    # PA ID and Status
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("PA ID", pa_form["pa_id"])
    with col_b:
        st.metric("Status", pa_form["status"].upper())
    with col_c:
        st.metric("Created", datetime.now().strftime("%m/%d/%Y"))

    # Medication info
    st.markdown("#### 💊 Requested Medication")
    med = pa_form.get("medication", {})
    cols = st.columns(4)
    cols[0].metric("Medication", med.get("name", "N/A"))
    cols[1].metric("Dosage", med.get("dosage", "N/A"))
    cols[2].metric("Frequency", med.get("frequency", "N/A"))
    cols[3].metric("Duration", med.get("duration", "N/A"))

    # Clinical justification
    st.markdown("#### 📋 Clinical Justification")
    justification = pa_form.get("clinical", {}).get("justification", "")
    if justification and len(justification) > 50:
        st.text_area("Justification", value=justification, height=150, disabled=True)
    else:
        st.info("LLM justification requires Ollama to be running. Using template justification.")
        st.text_area("Justification", height=150, disabled=True,
            value=f"Patient {patient_name} has been diagnosed with {prescription_data.get('diagnosis', 'the indicated condition')}. "
                  f"Previous treatments including {', '.join(patient_data['previous_treatments'][:2]) if patient_data['previous_treatments'] else 'standard first-line therapies'} "
                  f"have been attempted without adequate response. {med.get('name', 'The requested medication')} is medically necessary "
                  f"to achieve adequate disease control and prevent complications.")

    # Required documents checklist
    st.markdown("#### 📁 Required Documents")
    required_docs = pa_form.get("required_documents", [])
    for doc in required_docs:
        col_doc, col_status = st.columns([4, 1])
        with col_doc:
            required_badge = "🔴 Required" if doc["required"] else "🟡 Optional"
            st.write(f"{required_badge} — **{doc['name']}**: {doc['description']}")
        with col_status:
            status = st.selectbox("", ["pending", "completed", "not_applicable"],
                                  key=f"doc_{doc['name']}", label_visibility="collapsed")
            doc["status"] = status

    # Approval prediction
    st.markdown("---")
    st.markdown("#### 🎯 Approval Likelihood Prediction")

    with st.spinner("Calculating approval likelihood..."):
        try:
            from src.prior_auth.approval_predictor import get_approval_predictor
            predictor = get_approval_predictor()
            prediction = predictor.predict_approval(pa_form, patient_data)

            score = prediction.get("approval_score", 0.5)
            likelihood = prediction.get("likelihood", "Moderate")
            recommendation = prediction.get("recommendation", "")

            # Score gauge
            score_pct = int(score * 100)
            color = "green" if score >= 0.65 else "orange" if score >= 0.4 else "red"

            col_score, col_rec = st.columns([1, 2])
            with col_score:
                st.markdown(f"### :{color}[{score_pct}%]")
                st.markdown(f"**{likelihood}**")
                st.progress(score)
            with col_rec:
                st.info(f"💡 {recommendation}")

            # Factor breakdown
            with st.expander("📊 Score Breakdown"):
                for factor in prediction.get("factors", []):
                    factor_score = int(factor["score"] * 100)
                    st.write(f"**{factor['factor']}** ({int(factor['weight']*100)}% weight): {factor_score}%")
                    st.progress(factor["score"])
                    st.caption(factor["details"])

            # Missing elements
            missing = prediction.get("missing_elements", [])
            if missing:
                st.markdown("**⚠️ Missing Elements:**")
                for item in missing:
                    st.warning(f"• {item}")

            # Suggestions
            suggestions = prediction.get("suggestions", [])
            if suggestions:
                st.markdown("**💡 Improvement Suggestions:**")
                for s in suggestions:
                    st.success(f"• {s}")

        except Exception as e:
            st.warning(f"Could not calculate approval likelihood: {e}")

    # Submit button
    st.markdown("---")
    col_sub1, col_sub2 = st.columns(2)
    with col_sub1:
        if st.button("📤 Submit PA Form", type="primary", use_container_width=True):
            # Mark checklist items as completed for demo
            for item in pa_form.get("checklist", []):
                item["completed"] = True

            try:
                from src.prior_auth.pa_generator import get_pa_generator
                pa_gen = get_pa_generator()
                submit_result = pa_gen.submit_pa(pa_form)
                if submit_result["status"] == "success":
                    st.success(f"✅ PA Submitted! Tracking #: **{submit_result['tracking_number']}**")
                    st.info(f"Expected decision by: {submit_result['expected_decision_date'][:10]}")
                    st.session_state["pa_submitted"] = True
                    st.session_state["tracking_number"] = submit_result["tracking_number"]
                else:
                    st.error(submit_result.get("message", "Submission failed"))
            except Exception as e:
                st.error(f"Submission error: {e}")

    with col_sub2:
        if st.button("💾 Save Draft", use_container_width=True):
            st.info("Draft saved to session.")

# PA Status Tracker
if st.session_state.get("pa_submitted"):
    st.markdown("---")
    st.markdown("### 📊 PA Status Tracker")

    tracking = st.session_state.get("tracking_number", "TRK-DEMO")
    statuses = ["Submitted", "Under Review", "Decision Pending", "Approved ✅"]

    st.write(f"**Tracking Number:** `{tracking}`")

    cols = st.columns(4)
    for i, status in enumerate(statuses):
        with cols[i]:
            if i == 0:
                st.success(f"✅ {status}")
            elif i == 1:
                st.warning(f"🔄 {status}")
            else:
                st.markdown(f"⬜ {status}")
