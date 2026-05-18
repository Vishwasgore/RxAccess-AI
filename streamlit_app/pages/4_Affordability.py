"""
Affordability & Access Intelligence Page
"""
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.disclaimer import get_affordability_disclaimer

st.title("💰 Affordability & Access Intelligence")
st.markdown("Estimate insurance coverage, compare costs, and find patient assistance programs.")

with st.expander("ℹ️ Disclaimer"):
    st.info(get_affordability_disclaimer())

# Get prescription data
prescription_data = st.session_state.get("prescription_data")

if not prescription_data:
    st.warning("No prescription loaded. Loading demo data.")
    prescription_data = {
        "medications": [
            {"name": "Lisinopril", "dosage": "10mg", "frequency": "Once daily"},
            {"name": "Metformin", "dosage": "500mg", "frequency": "Twice daily"}
        ]
    }

meds = [m.get("name", "") for m in prescription_data.get("medications", [])]
st.info(f"📋 Analyzing costs for: **{', '.join(meds)}**")

st.markdown("---")

# Insurance details
st.markdown("### 🏥 Insurance Information")
col1, col2, col3 = st.columns(3)

with col1:
    payer_name = st.text_input("Insurance Provider", value="BlueCross BlueShield")
    plan_type = st.selectbox("Plan Type", ["PPO", "HMO", "EPO", "HDHP"])

with col2:
    deductible = st.number_input("Annual Deductible ($)", value=1500, step=100)
    deductible_met = st.number_input("Deductible Met So Far ($)", value=800, step=50)

with col3:
    oop_max = st.number_input("Out-of-Pocket Maximum ($)", value=6000, step=100)
    oop_current = st.number_input("OOP Spent So Far ($)", value=1200, step=50)

# Patient profile for assistance programs
st.markdown("### 👤 Patient Profile (for assistance programs)")
col_a, col_b, col_c = st.columns(3)
with col_a:
    patient_age = st.number_input("Age", value=52, min_value=1, max_value=120)
with col_b:
    income_level = st.selectbox("Income Level", ["low", "moderate", "high"],
                                help="Used to match assistance programs")
with col_c:
    insurance_status = st.selectbox("Insurance Status", ["insured", "underinsured", "uninsured"])

# Analyze button
st.markdown("---")
if st.button("💡 Analyze Affordability", type="primary", use_container_width=True):

    insurance_data = {
        "payer_name": payer_name,
        "plan_type": plan_type,
        "member_id": "MBR123456",
        "deductible": deductible,
        "deductible_met": deductible_met,
        "oop_max": oop_max,
        "oop_current": oop_current
    }

    patient_data = {
        "age": patient_age,
        "income_level": income_level,
        "insurance_status": insurance_status
    }

    from src.affordability.coverage_estimator import get_coverage_estimator
    from src.affordability.assistance_finder import get_assistance_finder
    estimator = get_coverage_estimator()
    finder = get_assistance_finder()

    # Tab layout for results
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Coverage Estimate", "⚖️ Cost Comparison", "🤝 Assistance Programs", "💊 Generic Alternatives"])

    with tab1:
        st.markdown("### 📊 Insurance Coverage Estimate")
        with st.spinner("Calculating coverage..."):
            coverage = estimator.estimate_coverage(prescription_data, insurance_data)

        if coverage["status"] == "success":
            # Summary metrics
            summary = coverage["summary"]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Retail Price", f"${summary['total_retail_price']:.2f}")
            c2.metric("Insurance Pays", f"${summary['total_insurance_pays']:.2f}")
            c3.metric("Your Copay", f"${summary['total_copay']:.2f}", delta=f"-{summary['overall_coverage_percentage']:.0f}% covered")
            c4.metric("Coverage %", f"{summary['overall_coverage_percentage']:.1f}%")

            # Per-medication breakdown
            st.markdown("#### Per-Medication Breakdown")
            for detail in coverage["coverage_details"]:
                with st.expander(f"💊 {detail['medication']}"):
                    cols = st.columns(4)
                    cols[0].metric("Retail Price", f"${detail['retail_price']:.2f}")
                    cols[1].metric("Formulary Tier", detail["formulary_tier"])
                    cols[2].metric("Your Copay", f"${detail['copay']:.2f}")
                    cols[3].metric("Coverage", f"{detail['coverage_percentage']:.1f}%")
                    if detail["generic_available"]:
                        st.success("✅ Generic version available — may reduce cost further")

            # Deductible & OOP info
            st.markdown("#### 📈 Deductible & Out-of-Pocket Status")
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                ded_info = coverage["deductible_info"]
                st.write(f"**Deductible:** ${ded_info['deductible_met']:.0f} / ${ded_info['annual_deductible']:.0f} met")
                st.progress(min(ded_info['deductible_met'] / ded_info['annual_deductible'], 1.0))
                st.caption(f"${ded_info['remaining']:.0f} remaining")
            with col_d2:
                oop_info = coverage["out_of_pocket_max"]
                st.write(f"**Out-of-Pocket:** ${oop_info['current']:.0f} / ${oop_info['annual_max']:.0f}")
                st.progress(min(oop_info['current'] / oop_info['annual_max'], 1.0))
                st.caption(f"${oop_info['remaining']:.0f} until max reached")

    with tab2:
        st.markdown("### ⚖️ Insurance vs. Cash-Pay Comparison")
        with st.spinner("Comparing options..."):
            comparison = estimator.compare_options(prescription_data, insurance_data)

        if comparison["status"] == "success":
            ins_cost = comparison["insurance_option"]["total_cost"]
            cash_cost = comparison["cash_pay_option"]["total_cost"]
            rec = comparison["recommendation"]
            savings = comparison["savings"]

            col_ins, col_cash = st.columns(2)

            with col_ins:
                border = "green" if rec == "insurance" else "gray"
                st.markdown(f"#### 🏥 Insurance Option")
                st.metric("Monthly Cost", f"${ins_cost:.2f}",
                          delta="✅ Recommended" if rec == "insurance" else None)
                for d in comparison["insurance_option"]["details"]:
                    st.write(f"• {d['medication']}: **${d['copay']:.2f}** copay")

            with col_cash:
                st.markdown(f"#### 💵 Cash-Pay Option")
                st.metric("Monthly Cost", f"${cash_cost:.2f}",
                          delta="✅ Recommended" if rec == "cash_pay" else None)
                for d in comparison["cash_pay_option"]["details"]:
                    st.write(f"• {d['medication']}: **${d['cash_price']:.2f}** (retail: ${d['retail_price']:.2f})")

            st.markdown("---")
            if rec == "cash_pay":
                st.success(f"💡 {comparison['message']} — Consider using GoodRx or SingleCare discount cards")
            else:
                st.success(f"💡 {comparison['message']}")

    with tab3:
        st.markdown("### 🤝 Patient Assistance Programs")
        with st.spinner("Finding programs..."):
            total_cost = coverage.get("summary", {}).get("total_copay", 100) if "coverage" in dir() else 100
            programs = finder.find_programs(patient_data, prescription_data, cost_burden=total_cost)

        if programs["status"] == "success":
            st.success(f"Found **{programs['programs_found']} eligible programs**")

            # Savings estimate
            savings_est = programs.get("estimated_savings", {})
            if savings_est:
                c1, c2, c3 = st.columns(3)
                c1.metric("Min Potential Savings", f"${savings_est['min_savings']:.2f}/mo")
                c2.metric("Max Potential Savings", f"${savings_est['max_savings']:.2f}/mo")
                c3.metric("Average Savings", f"${savings_est['average_savings']:.2f}/mo")

            # Program list
            for prog in programs["programs"]:
                score = prog.get("eligibility_score", 0)
                score_pct = int(score * 100)
                color = "green" if score >= 0.8 else "orange" if score >= 0.5 else "blue"

                with st.expander(f":{color}[{score_pct}% match] — **{prog['name']}** ({prog['type'].replace('_', ' ').title()})"):
                    col_p1, col_p2 = st.columns(2)
                    with col_p1:
                        st.write(f"**Eligibility:** {prog['eligibility']}")
                        st.write(f"**Coverage:** {prog['coverage']}")
                        st.write(f"**Why you match:** {prog.get('match_reason', 'N/A')}")
                    with col_p2:
                        st.write(f"**Website:** {prog['website']}")
                        st.write(f"**Phone:** {prog['phone']}")
                        st.progress(score)

            # Application steps
            st.markdown("#### 📋 How to Apply")
            for i, step in enumerate(programs.get("application_steps", []), 1):
                st.write(f"{i}. {step}")

    with tab4:
        st.markdown("### 💊 Generic Alternatives")
        with st.spinner("Finding generics..."):
            generics = finder.get_generic_alternatives(prescription_data)

        if generics["status"] == "success":
            if generics["alternatives_found"] > 0:
                for alt in generics["alternatives"]:
                    with st.expander(f"💊 {alt['brand_name']} → {alt['generic_name']}"):
                        col_g1, col_g2, col_g3 = st.columns(3)
                        col_g1.metric("Brand Name", alt["brand_name"])
                        col_g2.metric("Generic Name", alt["generic_name"])
                        col_g3.metric("Potential Savings", alt["potential_savings"])
                        st.success(f"✅ Bioequivalent: {alt['bioequivalent']} — {alt['recommendation']}")
            else:
                st.info("No generic alternatives found for your current medications, or they are already generics.")
