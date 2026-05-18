"""
Multi-Stakeholder Dashboards Page
"""
import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import streamlit as st
import sys
from pathlib import Path
import random
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

st.title("📈 Multi-Stakeholder Dashboards")
st.markdown("Role-specific views for patients, providers, pharmacies, and pharma companies.")

# Role selector
role = st.selectbox(
    "👤 Select Your Role",
    ["🧑‍⚕️ Patient", "🏥 Provider / Pharmacy", "💊 Pharma Insights"],
    help="Switch between different stakeholder views"
)

prescription_data = st.session_state.get("prescription_data", {})
meds = [m.get("name", "Unknown") for m in prescription_data.get("medications", [])]

st.markdown("---")

# ─── PATIENT DASHBOARD ───────────────────────────────────────────────────────
if role == "🧑‍⚕️ Patient":
    st.markdown("## 🧑‍⚕️ Patient Dashboard")

    patient_name = prescription_data.get("patient_name", "Patient")
    st.markdown(f"### Welcome, {patient_name}!")

    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Active Medications", len(meds) or 2)
    col2.metric("Adherence Score", "87%", delta="+3% this week")
    col3.metric("Next Refill", "12 days")
    col4.metric("PA Status", "Approved ✅")

    st.markdown("---")

    # Today's medications
    st.markdown("### 💊 Today's Medications")
    today_meds = prescription_data.get("medications", [
        {"name": "Lisinopril", "dosage": "10mg", "frequency": "Once daily", "instructions": "Morning"},
        {"name": "Metformin", "dosage": "500mg", "frequency": "Twice daily", "instructions": "With meals"}
    ])

    for med in today_meds:
        col_m, col_t, col_s = st.columns([3, 2, 1])
        col_m.write(f"💊 **{med.get('name')}** {med.get('dosage', '')}")
        col_t.write(f"📋 {med.get('instructions', med.get('frequency', 'As directed'))}")
        taken = col_s.checkbox("Taken", key=f"taken_{med.get('name')}")
        if taken:
            st.success(f"✅ {med.get('name')} marked as taken!")

    # Adherence chart
    st.markdown("---")
    st.markdown("### 📊 Adherence History (Last 30 Days)")
    dates = pd.date_range(end=pd.Timestamp.today(), periods=30)
    adherence_data = pd.DataFrame({
        "Date": dates,
        "Adherence %": [random.randint(70, 100) for _ in range(30)]
    })
    st.line_chart(adherence_data.set_index("Date"))

    # Upcoming appointments
    st.markdown("### 📅 Upcoming")
    col_a, col_b = st.columns(2)
    with col_a:
        st.info("📅 **Next Appointment:** June 15, 2024 — Dr. Sarah Johnson")
        st.info("💊 **Refill Due:** June 10, 2024 — Lisinopril 10mg")
    with col_b:
        st.warning("⚠️ **Lab Work Due:** Kidney function test (overdue)")
        st.success("✅ **PA Status:** Approved through Dec 2024")

    # Health tips
    st.markdown("### 💡 Personalized Health Tips")
    tips = [
        "Take Lisinopril at the same time each morning for best results.",
        "Monitor your blood pressure daily and log readings.",
        "Stay hydrated — aim for 8 glasses of water per day.",
        "Avoid NSAIDs (like ibuprofen) while on Lisinopril."
    ]
    for tip in tips:
        st.success(f"💡 {tip}")

# ─── PROVIDER / PHARMACY DASHBOARD ───────────────────────────────────────────
elif role == "🏥 Provider / Pharmacy":
    st.markdown("## 🏥 Provider / Pharmacy Dashboard")

    tab1, tab2, tab3 = st.tabs(["📋 Patient Summary", "📊 PA Management", "💊 Prescription Queue"])

    with tab1:
        st.markdown("### 📋 Extracted Prescription Summary")

        if prescription_data:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Patient Information**")
                st.table({
                    "Field": ["Name", "Age", "Gender", "Diagnosis"],
                    "Value": [
                        prescription_data.get("patient_name", "N/A"),
                        str(prescription_data.get("patient_age", "N/A")),
                        prescription_data.get("patient_gender", "N/A"),
                        prescription_data.get("diagnosis", "N/A")
                    ]
                })
            with col2:
                st.markdown("**Provider Information**")
                st.table({
                    "Field": ["Doctor", "Specialty", "Clinic", "Date"],
                    "Value": [
                        prescription_data.get("doctor_name", "N/A"),
                        prescription_data.get("doctor_specialty", "N/A"),
                        prescription_data.get("clinic_name", "N/A"),
                        prescription_data.get("prescription_date", "N/A")
                    ]
                })

            st.markdown("**Prescribed Medications**")
            if meds:
                med_df = pd.DataFrame(prescription_data.get("medications", []))
                st.dataframe(med_df, use_container_width=True)
            else:
                st.info("No medications extracted yet.")
        else:
            st.info("Upload a prescription to see patient summary.")

        # Verification checklist
        st.markdown("### ✅ Verification Checklist")
        checks = [
            "Patient identity verified",
            "Prescriber credentials validated",
            "Drug-drug interactions checked",
            "Dosage within therapeutic range",
            "Insurance eligibility confirmed",
            "Prior authorization obtained (if required)"
        ]
        for check in checks:
            st.checkbox(check, key=f"check_{check}")

    with tab2:
        st.markdown("### 📊 Prior Authorization Management")

        # Mock PA queue
        pa_data = pd.DataFrame({
            "Patient": ["John Doe", "Mary Smith", "Robert Johnson", "Patricia Brown"],
            "Medication": ["Lisinopril 10mg", "Humira 40mg", "Enbrel 50mg", "Metformin 500mg"],
            "Payer": ["BCBS", "Aetna", "UnitedHealth", "Cigna"],
            "Status": ["✅ Approved", "🔄 Under Review", "⏳ Pending", "✅ Approved"],
            "Submitted": ["2024-01-10", "2024-01-12", "2024-01-14", "2024-01-08"],
            "Decision": ["2024-01-13", "TBD", "TBD", "2024-01-11"]
        })
        st.dataframe(pa_data, use_container_width=True)

        col_pa1, col_pa2, col_pa3 = st.columns(3)
        col_pa1.metric("Total PAs", "24")
        col_pa2.metric("Approval Rate", "79%", delta="+5% vs last month")
        col_pa3.metric("Avg Decision Time", "3.2 days")

    with tab3:
        st.markdown("### 💊 Prescription Processing Queue")

        queue_data = pd.DataFrame({
            "Rx #": ["RX-001", "RX-002", "RX-003", "RX-004", "RX-005"],
            "Patient": ["John Doe", "Mary Smith", "Robert J.", "Patricia B.", "James W."],
            "Medication": ["Lisinopril 10mg", "Metformin 500mg", "Atorvastatin 20mg", "Amlodipine 5mg", "Omeprazole 20mg"],
            "Status": ["Ready", "Insurance Pending", "Ready", "PA Required", "Ready"],
            "Priority": ["Normal", "High", "Normal", "Urgent", "Normal"]
        })
        st.dataframe(queue_data, use_container_width=True)

# ─── PHARMA INSIGHTS DASHBOARD ───────────────────────────────────────────────
elif role == "💊 Pharma Insights":
    st.markdown("## 💊 Pharma Insights Dashboard")
    st.caption("Aggregated analytics — all data is synthetic for demonstration purposes")

    # KPI metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Prescriptions", "12,847", delta="+8.3% MoM")
    col2.metric("Avg Adherence Rate", "73.2%", delta="+2.1%")
    col3.metric("PA Approval Rate", "81.4%", delta="-1.2%")
    col4.metric("Patient Assistance Enrollments", "1,243", delta="+15.7%")

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📊 Adherence Analytics", "📋 PA Analytics", "💰 Access & Affordability"])

    with tab1:
        st.markdown("### 📊 Adherence Rate by Medication Class")
        adherence_by_class = pd.DataFrame({
            "Medication Class": ["ACE Inhibitors", "Statins", "Biguanides", "Beta Blockers", "ARBs", "Calcium Channel Blockers"],
            "Adherence Rate %": [74, 68, 71, 79, 76, 72],
            "Patient Count": [3200, 2800, 2400, 1900, 1600, 947]
        })
        st.bar_chart(adherence_by_class.set_index("Medication Class")["Adherence Rate %"])
        st.dataframe(adherence_by_class, use_container_width=True)

        st.markdown("### 📈 Adherence Trend (12 Months)")
        months = pd.date_range(start="2023-01-01", periods=12, freq="MS")
        trend_data = pd.DataFrame({
            "Month": months,
            "Adherence %": [68, 69, 71, 70, 72, 73, 71, 74, 73, 75, 74, 73]
        })
        st.line_chart(trend_data.set_index("Month"))

    with tab2:
        st.markdown("### 📋 PA Approval Rates by Payer")
        pa_by_payer = pd.DataFrame({
            "Payer": ["BCBS", "Aetna", "UnitedHealth", "Cigna", "Humana", "Medicare"],
            "Approval Rate %": [84, 79, 76, 82, 71, 88],
            "Avg Days to Decision": [2.8, 3.4, 4.1, 3.0, 4.8, 2.1]
        })
        st.bar_chart(pa_by_payer.set_index("Payer")["Approval Rate %"])
        st.dataframe(pa_by_payer, use_container_width=True)

        st.markdown("### 🔄 PA Denial Reasons")
        denial_data = pd.DataFrame({
            "Reason": ["Missing Documentation", "Step Therapy Required", "Not Medically Necessary", "Formulary Exception", "Other"],
            "Count": [142, 98, 67, 45, 31]
        })
        st.bar_chart(denial_data.set_index("Reason"))

    with tab3:
        st.markdown("### 💰 Patient Assistance Program Utilization")
        pap_data = pd.DataFrame({
            "Program Type": ["Manufacturer PAP", "Discount Cards", "Government Programs", "State Programs", "Nonprofit"],
            "Enrollments": [487, 312, 198, 143, 103],
            "Avg Monthly Savings $": [245, 67, 189, 134, 98]
        })
        st.bar_chart(pap_data.set_index("Program Type")["Enrollments"])
        st.dataframe(pap_data, use_container_width=True)

        st.markdown("### 🗺️ Access Barriers by Region")
        barrier_data = pd.DataFrame({
            "Barrier": ["High Cost", "Insurance Gaps", "PA Delays", "Pharmacy Access", "Health Literacy"],
            "Impact Score": [8.4, 7.2, 6.8, 5.1, 4.9]
        })
        st.bar_chart(barrier_data.set_index("Barrier"))
