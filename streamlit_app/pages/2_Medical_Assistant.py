"""
RAG-Powered Medical Assistant Page
Dynamic suggested questions based on actual prescription data
"""
import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

st.title("💬 AI Medical Assistant")
st.markdown("Ask questions about your prescription, medications, side effects, and interactions.")

# ── Get prescription data ────────────────────────────────────────────────────
prescription_data = st.session_state.get("prescription_data")

meds = []
diagnosis = None

if prescription_data:
    meds = [m.get("name", "") for m in prescription_data.get("medications", []) if m.get("name")]
    diagnosis = prescription_data.get("diagnosis")
    med_list = ", ".join(meds) if meds else "your medications"
    st.success(f"📋 Prescription loaded — **{med_list}**" + (f" | Diagnosis: **{diagnosis}**" if diagnosis else ""))
else:
    st.info("💡 No prescription loaded. Go to **Upload Prescription** first, or ask general questions below.")

st.markdown("---")

# ── Generate dynamic suggested questions ────────────────────────────────────
def build_suggestions(meds: list, diagnosis: str) -> list:
    """Build questions tailored to the actual prescription"""
    suggestions = []

    if meds:
        primary = meds[0]

        # Per-medication questions
        suggestions.append(f"What are the side effects of {primary}?")
        suggestions.append(f"How should I take {primary} correctly?")
        suggestions.append(f"What should I avoid while taking {primary}?")

        if len(meds) >= 2:
            suggestions.append(f"Are there any interactions between {meds[0]} and {meds[1]}?")
            suggestions.append(f"Can I take {meds[0]} and {meds[1]} at the same time?")

        suggestions.append(f"What happens if I miss a dose of {primary}?")
        suggestions.append(f"Can I take {primary} with food or alcohol?")
        suggestions.append(f"How long does {primary} take to work?")

    if diagnosis:
        # Diagnosis-specific questions
        diag_lower = diagnosis.lower()

        if any(w in diag_lower for w in ["hypertension", "blood pressure", "htn"]):
            suggestions += [
                "What lifestyle changes help with hypertension?",
                "What blood pressure reading is considered dangerous?",
                "Can stress cause high blood pressure?",
            ]
        if any(w in diag_lower for w in ["diabetes", "diabetic", "glucose", "sugar"]):
            suggestions += [
                "What foods should I avoid with diabetes?",
                "How often should I check my blood sugar?",
                "What are signs of low blood sugar?",
            ]
        if any(w in diag_lower for w in ["cholesterol", "lipid", "statin"]):
            suggestions += [
                "What foods lower cholesterol naturally?",
                "How often should I get my cholesterol checked?",
            ]
        if any(w in diag_lower for w in ["heart", "cardiac", "coronary"]):
            suggestions += [
                "What symptoms should I watch for with heart disease?",
                "Is exercise safe with my heart condition?",
            ]
        if any(w in diag_lower for w in ["thyroid", "hypothyroid", "hyperthyroid"]):
            suggestions += [
                "How does thyroid medication affect my body?",
                "What time of day should I take thyroid medication?",
            ]
        if any(w in diag_lower for w in ["infection", "antibiotic", "bacterial"]):
            suggestions += [
                "Should I complete the full antibiotic course?",
                "What are signs the infection is getting worse?",
            ]

    # Always include general fallbacks if we don't have enough
    general = [
        "Summarize my prescription in simple terms",
        "What precautions should I take with my medications?",
        "Are my medications safe to take long-term?",
        "What are the most important things to know about my medications?",
    ]

    # Combine and deduplicate, limit to 9
    all_suggestions = suggestions + general
    seen = set()
    unique = []
    for s in all_suggestions:
        if s not in seen:
            seen.add(s)
            unique.append(s)

    return unique[:9]


suggestions = build_suggestions(meds, diagnosis)

# ── Render suggestion buttons ────────────────────────────────────────────────
st.markdown("### 💡 Suggested Questions")

if not prescription_data:
    st.caption("Load a prescription to see personalized questions")

cols = st.columns(3)
for i, suggestion in enumerate(suggestions):
    with cols[i % 3]:
        if st.button(suggestion, key=f"sug_{i}", use_container_width=True):
            st.session_state["pending_question"] = suggestion

# ── Chat interface ───────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🗨️ Chat")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display chat history
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input — handle both typed and suggested questions
question = st.chat_input("Ask about your medications, side effects, interactions...")

if "pending_question" in st.session_state:
    question = st.session_state.pop("pending_question")

if question:
    st.session_state.chat_history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("🤔 Thinking..."):
            try:
                from src.rag.qa_chain import MedicalQAChain
                # Always create fresh instance — avoids stale cache issues
                qa_chain = MedicalQAChain()
                result = qa_chain.answer_question(
                    question=question,
                    prescription_context=prescription_data
                )

                if result["status"] == "success":
                    answer = result["answer"]
                    st.markdown(answer)

                    if result.get("sources"):
                        with st.expander(f"📚 {result['num_sources']} sources used", expanded=False):
                            for i, src in enumerate(result["sources"], 1):
                                rel = src.get("relevance", 0)
                                src_name = src["metadata"].get("source", "Unknown") if src.get("metadata") else "Unknown"
                                sec_type = src["metadata"].get("section_type", "general") if src.get("metadata") else "general"
                                st.markdown(f"**[{i}] {src_name}** — `{sec_type}` — relevance: **{rel:.0%}**")
                                st.caption(src.get("text", ""))
                                st.divider()
                else:
                    answer = f"⚠️ Error: {result.get('error', 'Unknown error')}"
                    st.warning(answer)

            except Exception as e:
                import traceback
                answer = f"⚠️ Exception: {str(e)}"
                st.error(answer)
                with st.expander("Debug info"):
                    st.code(traceback.format_exc())

    st.session_state.chat_history.append({"role": "assistant", "content": answer})

# Clear chat
if st.session_state.chat_history:
    st.markdown("---")
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()

# ── Drug interaction checker ─────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🔍 Quick Drug Interaction Check")

default_drugs = ", ".join(meds) if meds else ""
col1, col2 = st.columns([3, 1])
with col1:
    drugs_input = st.text_input(
        "Enter medications (comma-separated)",
        value=default_drugs,
        placeholder="e.g., Lisinopril, Ibuprofen, Metformin"
    )
with col2:
    check_btn = st.button("Check Interactions", type="primary", use_container_width=True)

if check_btn and drugs_input:
    drugs = [d.strip() for d in drugs_input.split(",") if d.strip()]
    with st.spinner("Analyzing interactions..."):
        try:
            from src.rag.qa_chain import MedicalQAChain
            qa_chain = MedicalQAChain()
            result = qa_chain.check_interactions(drugs)

            if result["status"] == "clarification_needed":
                st.warning(result["analysis"])
                for d in result.get("low_confidence_drugs", []):
                    st.caption(f"⚠️ '{d['original']}' — not found in drug database ({int(d['confidence']*100)}% confidence)")

            elif result["status"] == "success":
                # Show normalization results
                normalized = result.get("normalized_drugs", [])
                if normalized:
                    with st.expander("💊 Drug Name Resolution", expanded=False):
                        for d in normalized:
                            conf = int(d["confidence"] * 100)
                            icon = "✅" if conf >= 80 else "⚠️" if conf >= 50 else "❓"
                            st.write(f"{icon} **{d['original']}** → `{d['normalized']}` ({conf}% confidence via {d['method']})")

                # Main analysis
                if result.get("analysis"):
                    st.markdown(result["analysis"])

                # Sources
                if result.get("sources"):
                    with st.expander(f"📚 {result['num_sources']} sources checked"):
                        for src in result["sources"][:5]:
                            meta = src.get("metadata", {}) or {}
                            st.caption(f"**{meta.get('source','?')}** ({meta.get('type','?')}): {src.get('document','')[:180]}")

        except Exception as e:
            import traceback
            st.error(f"Interaction check failed: {e}")
            with st.expander("Debug"):
                st.code(traceback.format_exc())
