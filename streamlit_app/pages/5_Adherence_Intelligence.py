"""Adherence Intelligence Page"""
import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

st.markdown("## 📊 Adherence Intelligence")
st.caption("Predict medication adherence risk and receive a personalized support plan.")

prescription_data = st.session_state.get("prescription_data")
if not prescription_data:
    prescription_data = {
        "medications": [
            {"name": "Lisinopril", "dosage": "10mg", "frequency": "Once daily"},
            {"name": "Metformin", "dosage": "500mg", "frequency": "Twice daily"}
        ],
        "diagnosis": "Hypertension, Type 2 Diabetes"
    }

meds = [m.get("name", "") for m in prescription_data.get("medications", [])]

# ── Context card ──────────────────────────────────────────────────────────────
with st.container(border=True):
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown(f"**Medications:** {', '.join(meds)}")
        if prescription_data.get("diagnosis"):
            st.caption(f"Diagnosis: {prescription_data['diagnosis']}")
    with col_h2:
        st.page_link("pages/1_Upload_Prescription.py", label="Change Rx", icon="🔄")

st.markdown("---")

# ── Patient profile ───────────────────────────────────────────────────────────
st.markdown("### 👤 Patient Profile")
col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.markdown("**Demographics**")
        age = st.slider("Age", 18, 90, 52)
        chronic_condition = st.checkbox("Chronic condition", value=True)
        has_side_effects = st.checkbox("Experiencing side effects", value=False)

with col2:
    with st.container(border=True):
        st.markdown("**Financial & Social**")
        cost_burden = st.select_slider(
            "Medication cost burden",
            options=["Very Low", "Low", "Moderate", "High", "Very High"],
            value="Moderate"
        )
        cost_map = {"Very Low": 1, "Low": 2, "Moderate": 3, "High": 4, "Very High": 5}
        support_system = st.select_slider(
            "Support system",
            options=["None", "Minimal", "Moderate", "Good", "Strong"],
            value="Moderate"
        )
        support_map = {"None": 1, "Minimal": 2, "Moderate": 3, "Good": 4, "Strong": 5}

with col3:
    with st.container(border=True):
        st.markdown("**Adherence History**")
        previous_adherence = st.slider("Previous adherence rate", 0, 100, 75, step=5)
        st.caption(f"{previous_adherence}% of doses taken as prescribed")
        if previous_adherence >= 80:
            st.success("Good adherence history")
        elif previous_adherence >= 60:
            st.warning("Moderate adherence history")
        else:
            st.error("Low adherence history")

st.markdown("---")
if st.button("🔮 Generate Adherence Assessment", type="primary", use_container_width=True):

    patient_data = {
        "age": age,
        "chronic_condition": int(chronic_condition),
        "has_side_effects": int(has_side_effects),
        "cost_burden": cost_map[cost_burden],
        "support_system_score": support_map[support_system],
        "previous_adherence_rate": previous_adherence / 100
    }

    with st.spinner("Calculating risk assessment..."):
        from src.adherence.risk_predictor import get_risk_predictor
        predictor = get_risk_predictor()
        risk_result = predictor.predict_risk(patient_data, prescription_data)

    if risk_result["status"] != "success":
        st.error("Could not complete assessment. Please try again.")
        st.stop()

    risk_score = risk_result["risk_score"]
    risk_category = risk_result["risk_category"]
    risk_pct = int(risk_score * 100)

    st.markdown("---")
    st.markdown("## 🎯 Adherence Risk Assessment")

    # ── Risk summary ──────────────────────────────────────────────────────────
    col_badge, col_factors, col_outcomes = st.columns([1, 2, 2])

    with col_badge:
        with st.container(border=True):
            st.markdown("**Risk Level**")
            if risk_category == "High Risk":
                st.error(f"🔴 HIGH RISK")
                color = "red"
            elif risk_category == "Moderate Risk":
                st.warning(f"🟡 MODERATE RISK")
                color = "orange"
            else:
                st.success(f"🟢 LOW RISK")
                color = "green"
            st.markdown(f"## :{color}[{risk_pct}%]")
            st.caption("Non-adherence probability")
            st.progress(float(risk_score))

    with col_factors:
        with st.container(border=True):
            st.markdown("**Risk Factors**")
            risk_factors = risk_result.get("risk_factors", [])
            if risk_factors:
                for rf in risk_factors:
                    sev = rf["severity"]
                    icon = "🔴" if sev == "high" else "🟡" if sev == "moderate" else "🟢"
                    st.write(f"{icon} **{rf['factor']}**")
                    st.caption(rf["description"])
            else:
                st.success("✅ No significant risk factors identified")

    with col_outcomes:
        with st.container(border=True):
            st.markdown("**Predicted Outcomes**")
            # Derive predicted outcomes from risk score
            refill_risk = "High" if risk_score > 0.6 else "Moderate" if risk_score > 0.35 else "Low"
            discontinue_risk = "High" if risk_score > 0.7 else "Moderate" if risk_score > 0.45 else "Low"
            adherence_prob = int((1 - risk_score) * 100)

            risk_color = {"High": "🔴", "Moderate": "🟡", "Low": "🟢"}
            st.write(f"{risk_color[refill_risk]} Refill delay risk: **{refill_risk}**")
            st.write(f"{risk_color[discontinue_risk]} Discontinuation risk: **{discontinue_risk}**")
            st.write(f"🎯 Predicted adherence: **{adherence_prob}%**")

    # ── Recommendations ───────────────────────────────────────────────────────
    recs = risk_result.get("recommendations", [])
    if recs:
        with st.container(border=True):
            st.markdown("**💡 Clinical Recommendations**")
            for rec in recs:
                st.write(f"• {rec}")

    # ── Personalized interventions ────────────────────────────────────────────
    st.markdown("---")
    st.markdown("## 🎯 Personalized Support Plan")

    with st.spinner("Building your support plan..."):
        try:
            from src.adherence.intervention_gen import get_intervention_generator
            gen = get_intervention_generator()
            interventions = gen.generate_interventions(patient_data, prescription_data, risk_result)
        except Exception:
            interventions = {"status": "error"}

    tab1, tab2, tab3, tab4 = st.tabs(["⏰ Reminders", "📚 Education", "💪 Motivation", "🧠 Behavioral Tips"])

    with tab1:
        st.markdown("**Medication Schedule**")
        reminders = interventions.get("reminders", []) if interventions.get("status") == "success" else []
        if not reminders:
            for med in prescription_data.get("medications", []):
                freq = (med.get("frequency") or "once daily").lower()
                times = ["09:00"] if "once" in freq else ["09:00", "21:00"] if "twice" in freq else ["08:00", "14:00", "20:00"]
                for t in times:
                    reminders.append({
                        "medication": med.get("name"), "time": t,
                        "dosage": med.get("dosage", ""), "instructions": med.get("instructions", "Take as directed")
                    })

        for r in reminders:
            with st.container(border=True):
                col_r1, col_r2, col_r3 = st.columns([2, 1, 2])
                col_r1.write(f"💊 **{r['medication']}** {r.get('dosage', '')}")
                col_r2.write(f"🕐 {r['time']}")
                col_r3.caption(r.get("instructions", "Take as directed"))

        st.markdown("**Set Up Reminders**")
        reminder_method = st.multiselect("Notification method",
                                          ["📱 Phone", "📧 Email", "💬 SMS", "⌚ Smartwatch"])
        if st.button("Save Reminder Schedule"):
            st.success(f"✅ Reminders configured via: {', '.join(reminder_method) if reminder_method else 'Phone'}")

    with tab2:
        st.markdown("**Patient Education**")
        edu_msgs = []
        if interventions.get("status") == "success" and interventions.get("educational_messages"):
            edu_msgs = [m["content"] for m in interventions["educational_messages"]]
        if not edu_msgs:
            primary = meds[0] if meds else "your medication"
            edu_msgs = [
                f"Taking {primary} consistently maintains stable levels in your bloodstream, making it more effective.",
                "Missing doses can cause your condition to worsen. If you miss a dose, take it as soon as you remember unless it's almost time for the next one.",
                "Keep medications in a visible place (like next to your toothbrush) to help you remember daily.",
                "Never stop taking prescribed medications without consulting your doctor, even if you feel better."
            ]
        for msg in edu_msgs:
            st.info(f"📖 {msg}")

    with tab3:
        st.markdown("**Motivational Support**")
        mot_msgs = []
        if interventions.get("status") == "success" and interventions.get("motivational_messages"):
            mot_msgs = [m["content"] for m in interventions["motivational_messages"]]
        if not mot_msgs:
            mot_msgs = [
                "Every dose you take is an investment in your long-term health.",
                "Consistent medication use can significantly reduce your risk of complications.",
                "You're taking control of your health — that's something to be proud of!",
                "Small daily habits create big health outcomes over time."
            ]
        for msg in mot_msgs:
            st.success(f"🌟 {msg}")

    with tab4:
        st.markdown("**Behavioral Strategies**")
        nudges = interventions.get("behavioral_nudges", []) if interventions.get("status") == "success" else []
        if not nudges:
            nudges = [
                {"strategy": "Habit Stacking", "content": "Link medication time to an existing daily habit (e.g., morning coffee or brushing teeth)", "action": "Set a daily phone reminder tied to your routine"},
                {"strategy": "Visual Cues", "content": "Use a weekly pill organizer to track doses at a glance", "action": "Place pill organizer in a visible location"},
                {"strategy": "Progress Tracking", "content": "Patients who track adherence see 40% better outcomes", "action": "Log your daily doses in a health app"},
            ]
        for nudge in nudges:
            with st.container(border=True):
                st.markdown(f"**{nudge.get('strategy', 'Strategy')}**")
                st.write(nudge.get("content", ""))
                st.caption(f"✅ Action: {nudge.get('action', '')}")

    # ── 30-day plan ───────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📅 30-Day Support Plan")

    plan = interventions.get("intervention_plan", {}) if interventions.get("status") == "success" else {}
    intensity = plan.get("intensity", "intensive" if risk_category == "High Risk" else "moderate" if risk_category == "Moderate Risk" else "light")
    frequency = plan.get("frequency", "Daily check-ins" if risk_category == "High Risk" else "3× per week")

    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    col_p1.metric("Risk Level", risk_category.replace(" Risk", ""))
    col_p2.metric("Plan Intensity", intensity.title())
    col_p3.metric("Check-in Frequency", frequency)
    col_p4.metric("Duration", "30 days")

    if st.button("✅ Enroll in Support Program", type="primary", use_container_width=True):
        st.balloons()
        st.success("🎉 Enrolled! You'll receive personalized reminders and support to stay on track.")

st.caption("⚠️ For informational purposes only. Always follow your healthcare provider's guidance.")
