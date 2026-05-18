"""Affordability & Access Intelligence Page"""
import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

st.markdown("## 💰 Affordability & Coverage")
st.caption("Understand your medication costs, insurance coverage, and savings opportunities.")

prescription_data = st.session_state.get("prescription_data")
if not prescription_data:
    prescription_data = {
        "medications": [
            {"name": "Lisinopril", "dosage": "10mg", "frequency": "Once daily"},
            {"name": "Metformin", "dosage": "500mg", "frequency": "Twice daily"}
        ]
    }

meds = [m.get("name", "") for m in prescription_data.get("medications", [])]

# ── Summary header ────────────────────────────────────────────────────────────
with st.container(border=True):
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown(f"**Analyzing costs for:** {', '.join(meds)}")
        if prescription_data.get("diagnosis"):
            st.caption(f"Diagnosis: {prescription_data['diagnosis']}")
    with col_h2:
        st.page_link("pages/1_Upload_Prescription.py", label="Change Rx", icon="🔄")

st.markdown("---")

# ── Input: two columns ────────────────────────────────────────────────────────
col_ins, col_pat = st.columns(2)

with col_ins:
    with st.container(border=True):
        st.markdown("**🏥 Insurance Details**")
        payer_name = st.text_input("Insurance Provider", value="BlueCross BlueShield")
        plan_type = st.selectbox("Plan Type", ["PPO", "HMO", "EPO", "HDHP"])
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            deductible = st.number_input("Annual Deductible ($)", value=1500, step=100)
            deductible_met = st.number_input("Deductible Met ($)", value=800, step=50)
        with col_d2:
            oop_max = st.number_input("OOP Maximum ($)", value=6000, step=100)
            oop_current = st.number_input("OOP Spent ($)", value=1200, step=50)

with col_pat:
    with st.container(border=True):
        st.markdown("**👤 Patient Profile**")
        patient_age = st.number_input("Age", value=52, min_value=1, max_value=120)
        income_level = st.selectbox("Income Level", ["low", "moderate", "high"],
                                    help="Used to match assistance programs")
        insurance_status = st.selectbox("Coverage Status", ["insured", "underinsured", "uninsured"])

        # Deductible progress
        if deductible > 0:
            ded_pct = min(deductible_met / deductible, 1.0)
            st.caption(f"Deductible: ${deductible_met} / ${deductible} met")
            st.progress(ded_pct)
        if oop_max > 0:
            oop_pct = min(oop_current / oop_max, 1.0)
            st.caption(f"Out-of-pocket: ${oop_current} / ${oop_max}")
            st.progress(oop_pct)

st.markdown("---")
if st.button("💡 Analyze Affordability", type="primary", use_container_width=True):

    insurance_data = {
        "payer_name": payer_name, "plan_type": plan_type, "member_id": "MBR123456",
        "deductible": deductible, "deductible_met": deductible_met,
        "oop_max": oop_max, "oop_current": oop_current
    }
    patient_data = {"age": patient_age, "income_level": income_level, "insurance_status": insurance_status}

    from src.affordability.coverage_estimator import get_coverage_estimator
    from src.affordability.assistance_finder import get_assistance_finder
    estimator = get_coverage_estimator()
    finder = get_assistance_finder()

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Coverage", "⚖️ Cost Comparison", "🤝 Assistance Programs", "💊 Generic Options"])

    with tab1:
        with st.spinner("Calculating coverage..."):
            coverage = estimator.estimate_coverage(prescription_data, insurance_data)

        if coverage["status"] == "success":
            summary = coverage["summary"]

            # Summary metrics row
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Retail Price", f"${summary['total_retail_price']:.2f}")
            c2.metric("Insurance Pays", f"${summary['total_insurance_pays']:.2f}")
            c3.metric("Your Copay", f"${summary['total_copay']:.2f}")
            c4.metric("Coverage", f"{summary['overall_coverage_percentage']:.0f}%")

            st.markdown("---")
            st.markdown("**Medication-by-Medication Breakdown**")
            for detail in coverage["coverage_details"]:
                with st.container(border=True):
                    col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns([2, 1, 1, 1, 1])
                    col_m1.markdown(f"**💊 {detail['medication']}**")
                    col_m2.metric("Retail", f"${detail['retail_price']:.2f}")
                    col_m3.metric("Tier", detail["formulary_tier"])
                    col_m4.metric("Copay", f"${detail['copay']:.2f}")
                    col_m5.metric("Covered", f"{detail['coverage_percentage']:.0f}%")
                    if detail.get("generic_available"):
                        st.caption("✅ Generic available — may reduce cost")

    with tab2:
        with st.spinner("Comparing options..."):
            comparison = estimator.compare_options(prescription_data, insurance_data)

        if comparison["status"] == "success":
            ins_cost = comparison["insurance_option"]["total_cost"]
            cash_cost = comparison["cash_pay_option"]["total_cost"]
            rec = comparison["recommendation"]

            col_ins2, col_cash = st.columns(2)
            with col_ins2:
                with st.container(border=True):
                    st.markdown("**🏥 With Insurance**")
                    st.metric("Monthly Cost", f"${ins_cost:.2f}",
                              delta="✅ Recommended" if rec == "insurance" else None)
                    for d in comparison["insurance_option"]["details"]:
                        st.caption(f"• {d['medication']}: ${d['copay']:.2f} copay")

            with col_cash:
                with st.container(border=True):
                    st.markdown("**💵 Cash Pay / Discount Card**")
                    st.metric("Monthly Cost", f"${cash_cost:.2f}",
                              delta="✅ Recommended" if rec == "cash_pay" else None)
                    for d in comparison["cash_pay_option"]["details"]:
                        st.caption(f"• {d['medication']}: ${d['cash_price']:.2f}")

            st.info(f"💡 {comparison['message']}")
            if rec == "cash_pay":
                st.caption("Consider GoodRx, SingleCare, or RxSaver discount cards at your pharmacy.")

    with tab3:
        with st.spinner("Finding assistance programs..."):
            total_cost = coverage.get("summary", {}).get("total_copay", 100) if "coverage" in dir() else 100
            programs = finder.find_programs(patient_data, prescription_data, cost_burden=total_cost)

        if programs["status"] == "success":
            savings_est = programs.get("estimated_savings", {})
            if savings_est:
                c1, c2, c3 = st.columns(3)
                c1.metric("Min Monthly Savings", f"${savings_est['min_savings']:.2f}")
                c2.metric("Max Monthly Savings", f"${savings_est['max_savings']:.2f}")
                c3.metric("Programs Found", programs['programs_found'])

            st.markdown("---")
            for prog in programs["programs"]:
                score = prog.get("eligibility_score", 0)
                score_pct = int(score * 100)
                color = "green" if score >= 0.8 else "orange" if score >= 0.5 else "blue"
                with st.expander(f":{color}[{score_pct}% match] — **{prog['name']}**"):
                    col_p1, col_p2 = st.columns(2)
                    with col_p1:
                        st.write(f"**Eligibility:** {prog['eligibility']}")
                        st.write(f"**Coverage:** {prog['coverage']}")
                        st.write(f"**Why you qualify:** {prog.get('match_reason', '—')}")
                    with col_p2:
                        st.write(f"**Website:** {prog['website']}")
                        st.write(f"**Phone:** {prog['phone']}")
                        st.progress(float(score))

            if programs.get("application_steps"):
                st.markdown("**How to Apply**")
                for i, step in enumerate(programs["application_steps"], 1):
                    st.write(f"{i}. {step}")

    with tab4:
        with st.spinner("Finding generic alternatives..."):
            generics = finder.get_generic_alternatives(prescription_data)

        if generics["status"] == "success":
            if generics["alternatives_found"] > 0:
                for alt in generics["alternatives"]:
                    with st.container(border=True):
                        col_g1, col_g2, col_g3 = st.columns([2, 2, 1])
                        col_g1.markdown(f"**{alt['brand_name']}** → **{alt['generic_name']}**")
                        col_g2.write(f"Potential savings: **{alt['potential_savings']}**")
                        col_g3.write("✅ Bioequivalent" if alt["bioequivalent"] else "⚠️ Check with doctor")
                        st.caption(alt["recommendation"])
            else:
                st.info("Your medications are already generics or no alternatives are available.")

st.caption("⚠️ Cost estimates are approximate. Verify with your pharmacy and insurance provider.")
