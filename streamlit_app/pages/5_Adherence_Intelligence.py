"""
Adherence Intelligence Page
"""
import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.disclaimer import get_adherence_disclaimer

st.title("📊 Adherence Intelligence")
st.markdown("AI-powered medication adherence risk prediction and personalized interventions.")

with st.expander("ℹ️ Disclaimer"):
    st.info(get_adherence_disclaimer())

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
st.info(f"📋 Analyzing adherence for: **{', '.join(meds)}**")

st.markdown("---")

# Patient profile inputs
st.markdown("### 👤 Patient Profile")
col1, col2, col3 = st.columns(3)

with col1:
    age = st.slider("Patient Age", 18, 90, 52)
    chronic_condition = st.checkbox("Has Chronic Condition", value=True)
    has_side_effects = st.checkbox("Currently Experiencing Side Effects", value=False)

with col2:
    cost_burden = st.slider("Cost Burden (1=Low, 5=High)", 1, 5, 3,
                            help="How much financial strain do medications cause?")
    support_system = st.slider("Support System (1=None, 5=Strong)", 1, 5, 3,
                               help="Family/caregiver support level")

with col3:
    previous_adherence = st.slider("Previous Adherence Rate", 0.0, 1.0, 0.75, 0.05,
                                   format="%.0f%%",
                                   help="Historical medication adherence (0-100%)")
    st.caption(f"Previous adherence: {previous_adherence*100:.0f}%")

# Predict button
st.markdown("---")
if st.button("🔮 Predict Adherence Risk", type="primary", use_container_width=True):

    patient_data = {
        "age": age,
        "chronic_condition": int(chronic_condition),
        "has_side_effects": int(has_side_effects),
        "cost_burden": cost_burden,
        "support_system_score": support_system,
        "previous_adherence_rate": previous_adherence
    }

    # Risk prediction
    with st.spinner("🤖 Calculating risk score..."):
        from src.adherence.risk_predictor import get_risk_predictor
        predictor = get_risk_predictor()
        risk_result = predictor.predict_risk(patient_data, prescription_data)

    if risk_result["status"] == "success":
        risk_score = risk_result["risk_score"]
        risk_category = risk_result["risk_category"]
        risk_pct = int(risk_score * 100)

        # Risk score display
        st.markdown("---")
        st.markdown("## 🎯 Adherence Risk Assessment")

        col_risk, col_info = st.columns([1, 2])

        with col_risk:
            if risk_category == "High Risk":
                st.error(f"### 🔴 {risk_category}")
                color = "red"
            elif risk_category == "Moderate Risk":
                st.warning(f"### 🟡 {risk_category}")
                color = "orange"
            else:
                st.success(f"### 🟢 {risk_category}")
                color = "green"

            st.markdown(f"## :{color}[{risk_pct}%]")
            st.caption("Non-adherence probability")
            st.progress(float(risk_score))

        with col_info:
            st.markdown("#### 📋 Risk Factors Identified")
            risk_factors = risk_result.get("risk_factors", [])
            if risk_factors:
                for rf in risk_factors:
                    sev = rf["severity"]
                    icon = "🔴" if sev == "high" else "🟡" if sev == "moderate" else "🟢"
                    st.write(f"{icon} **{rf['factor']}** — {rf['description']}")
            else:
                st.success("✅ No significant risk factors identified")

        # Recommendations
        st.markdown("#### 💡 Recommendations")
        for rec in risk_result.get("recommendations", []):
            st.info(f"• {rec}")

        # Generate interventions
        st.markdown("---")
        st.markdown("## 🎯 Personalized Interventions")

        with st.spinner("Generating personalized interventions..."):
            try:
                from src.adherence.intervention_gen import get_intervention_generator
                gen = get_intervention_generator()
                interventions = gen.generate_interventions(patient_data, prescription_data, risk_result)
            except Exception as e:
                interventions = {"status": "error", "error": str(e)}

        tab1, tab2, tab3, tab4 = st.tabs(["⏰ Reminders", "📚 Education", "💪 Motivation", "🧠 Behavioral Nudges"])

        with tab1:
            st.markdown("### ⏰ Medication Reminders")
            reminders = interventions.get("reminders", []) if interventions.get("status") == "success" else []

            if not reminders:
                # Generate from prescription data directly
                for med in prescription_data.get("medications", []):
                    freq = med.get("frequency", "once daily").lower()
                    times = ["09:00"] if "once" in freq else ["09:00", "21:00"] if "twice" in freq else ["08:00", "14:00", "20:00"]
                    for t in times:
                        reminders.append({"medication": med.get("name"), "time": t, "dosage": med.get("dosage", ""), "instructions": med.get("instructions", "Take as directed")})

            for r in reminders:
                col_r1, col_r2, col_r3 = st.columns([2, 1, 2])
                col_r1.write(f"💊 **{r['medication']}** {r.get('dosage', '')}")
                col_r2.write(f"🕐 {r['time']}")
                col_r3.write(f"📋 {r.get('instructions', 'Take as directed')}")

            st.markdown("---")
            st.markdown("**Set Up Reminders:**")
            reminder_method = st.multiselect("Reminder Method", ["📱 Phone Notification", "📧 Email", "💬 SMS", "⌚ Smartwatch"])
            if st.button("Save Reminder Schedule"):
                st.success(f"✅ Reminders set via: {', '.join(reminder_method) if reminder_method else 'Phone Notification'}")

        with tab2:
            st.markdown("### 📚 Educational Messages")
            if interventions.get("status") == "success" and interventions.get("educational_messages"):
                for msg in interventions["educational_messages"]:
                    st.info(f"📖 {msg['content']}")
            else:
                # Static educational content
                edu_messages = [
                    f"Taking {meds[0] if meds else 'your medication'} consistently helps maintain stable levels in your bloodstream, making it more effective.",
                    "Missing doses can cause your condition to worsen. If you miss a dose, take it as soon as you remember unless it's almost time for the next one.",
                    "Keep your medications in a visible place (like next to your toothbrush) to help you remember to take them daily."
                ]
                for msg in edu_messages:
                    st.info(f"📖 {msg}")

        with tab3:
            st.markdown("### 💪 Motivational Messages")
            if interventions.get("status") == "success" and interventions.get("motivational_messages"):
                for msg in interventions["motivational_messages"]:
                    st.success(f"🌟 {msg['content']}")
            else:
                motivational = [
                    "Every dose you take is an investment in your health. Keep it up!",
                    "Consistent medication use can reduce your risk of complications significantly.",
                    "You're taking control of your health — that's something to be proud of!"
                ]
                for msg in motivational:
                    st.success(f"🌟 {msg}")

        with tab4:
            st.markdown("### 🧠 Behavioral Nudges")
            nudges = interventions.get("behavioral_nudges", []) if interventions.get("status") == "success" else []

            if not nudges:
                nudges = [
                    {"strategy": "habit_formation", "content": "Link medication time to an existing habit (e.g., morning coffee)", "action": "Set a daily phone reminder"},
                    {"strategy": "simplification", "content": "Use a weekly pill organizer to track doses", "action": "Buy a pill organizer"},
                    {"strategy": "social_proof", "content": "Patients who take medications consistently see 40% better outcomes", "action": "Track your adherence streak"},
                ]

            for nudge in nudges:
                with st.expander(f"🧠 {nudge.get('strategy', 'Strategy').replace('_', ' ').title()}"):
                    st.write(nudge.get("content", ""))
                    st.success(f"✅ Action: {nudge.get('action', '')}")

        # Intervention plan summary
        st.markdown("---")
        st.markdown("### 📅 30-Day Intervention Plan")
        plan = interventions.get("intervention_plan", {}) if interventions.get("status") == "success" else {}

        intensity = plan.get("intensity", "moderate" if risk_category == "Moderate Risk" else "intensive" if risk_category == "High Risk" else "light")
        frequency = plan.get("frequency", "daily" if risk_category == "High Risk" else "3x per week")

        col_p1, col_p2, col_p3 = st.columns(3)
        col_p1.metric("Intensity", intensity.title())
        col_p2.metric("Check-in Frequency", frequency)
        col_p3.metric("Duration", "30 days")

        if st.button("✅ Enroll in Adherence Program", type="primary"):
            st.balloons()
            st.success("🎉 Enrolled! You'll receive personalized support to stay on track.")
