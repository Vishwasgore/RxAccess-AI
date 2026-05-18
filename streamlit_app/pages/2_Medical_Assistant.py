"""
Medical Assistant Page
"""
import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

st.markdown("""
<style>
.context-card {
    background: #f0f4ff;
    border-radius: 10px;
    padding: 0.9rem 1.1rem;
    border-left: 4px solid #1a73e8;
    margin-bottom: 0.8rem;
}
.quick-action {
    background: #fff;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 0.5rem 0.8rem;
    font-size: 0.85rem;
    cursor: pointer;
}
.source-badge {
    background: #e8f0fe;
    color: #1a73e8;
    border-radius: 4px;
    padding: 0.1rem 0.4rem;
    font-size: 0.75rem;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## 💬 Medication Assistant")
st.caption("Ask questions about your medications, interactions, dosage, and clinical guidance.")

# ── Prescription context ──────────────────────────────────────────────────────
prescription_data = st.session_state.get("prescription_data")
meds, diagnosis = [], None

if prescription_data:
    meds = [m.get("name", "") for m in prescription_data.get("medications", []) if m.get("name")]
    diagnosis = prescription_data.get("diagnosis")

# Context summary card
if prescription_data and meds:
    with st.container(border=True):
        col_ctx1, col_ctx2, col_ctx3 = st.columns([2, 2, 1])
        with col_ctx1:
            st.markdown("**📋 Active Prescription**")
            for m in meds:
                st.caption(f"💊 {m}")
        with col_ctx2:
            if diagnosis:
                st.markdown("**🏥 Diagnosis**")
                st.caption(diagnosis)
            patient = prescription_data.get("patient_name")
            if patient:
                st.markdown("**👤 Patient**")
                st.caption(patient)
        with col_ctx3:
            st.page_link("pages/1_Upload_Prescription.py", label="Change Rx", icon="🔄")
else:
    st.info("💡 No prescription loaded. [Upload one](pages/1_Upload_Prescription.py) for personalized answers, or ask general questions below.")

st.markdown("---")

# ── Quick action buttons ──────────────────────────────────────────────────────
def build_suggestions(meds, diagnosis):
    s = []
    if meds:
        p = meds[0]
        s += [
            f"What are the side effects of {p}?",
            f"How should I take {p} correctly?",
            f"What should I avoid while taking {p}?",
        ]
        if len(meds) >= 2:
            s.append(f"Are there interactions between {meds[0]} and {meds[1]}?")
        s += [
            f"What happens if I miss a dose of {p}?",
            f"How long does {p} take to work?",
        ]
    if diagnosis:
        d = diagnosis.lower()
        if any(w in d for w in ["hypertension", "blood pressure"]):
            s += ["What lifestyle changes help with hypertension?", "What blood pressure is dangerous?"]
        if any(w in d for w in ["diabetes", "glucose"]):
            s += ["What foods should I avoid with diabetes?", "Signs of low blood sugar?"]
        if any(w in d for w in ["heart", "cardiac"]):
            s += ["Is exercise safe with my heart condition?"]
    s += [
        "Summarize my prescription in simple terms",
        "What precautions should I take?",
        "Are my medications safe long-term?",
    ]
    seen, unique = set(), []
    for x in s:
        if x not in seen:
            seen.add(x)
            unique.append(x)
    return unique[:9]

suggestions = build_suggestions(meds, diagnosis)

col_left, col_right = st.columns([2, 1])

with col_right:
    st.markdown("**💡 Quick Questions**")
    for i, sug in enumerate(suggestions):
        if st.button(sug, key=f"sug_{i}", use_container_width=True):
            st.session_state["pending_question"] = sug

    st.markdown("---")
    st.markdown("**🔍 Interaction Check**")
    default_drugs = ", ".join(meds) if meds else ""
    drugs_input = st.text_input("Medications to check", value=default_drugs,
                                 placeholder="e.g., Lisinopril, Ibuprofen",
                                 label_visibility="collapsed")
    if st.button("Check Interactions", use_container_width=True):
        if drugs_input:
            st.session_state["pending_question"] = f"Check interactions between: {drugs_input}"

with col_left:
    st.markdown("**🗨️ Conversation**")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Chat history display
    chat_container = st.container(height=420)
    with chat_container:
        if not st.session_state.chat_history:
            st.markdown("""
            <div style="text-align:center;padding:2rem;color:#999;">
                <div style="font-size:2rem">💬</div>
                <div>Ask a question or select one from the right panel</div>
            </div>
            """, unsafe_allow_html=True)
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("sources"):
                    with st.expander(f"📚 {len(msg['sources'])} clinical references", expanded=False):
                        for src in msg["sources"]:
                            meta = src.get("metadata") or {}
                            rel = src.get("relevance", 0)
                            src_name = meta.get("source", "Clinical Reference")
                            st.markdown(f'<span class="source-badge">{src_name}</span> {src.get("text","")[:160]}', unsafe_allow_html=True)

    # Input
    question = st.chat_input("Ask about your medications...")
    if "pending_question" in st.session_state:
        question = st.session_state.pop("pending_question")

    if question:
        st.session_state.chat_history.append({"role": "user", "content": question})

        with st.spinner("Searching clinical knowledge base..."):
            try:
                from src.rag.qa_chain import MedicalQAChain
                qa_chain = MedicalQAChain()

                # Detect interaction check
                if "interaction" in question.lower() and "between:" in question.lower():
                    drug_str = question.split("between:")[-1].strip()
                    drugs = [d.strip() for d in drug_str.split(",") if d.strip()]
                    result = qa_chain.check_interactions(drugs)
                else:
                    result = qa_chain.answer_question(question=question, prescription_context=prescription_data)

                if result["status"] in ("success", "clarification_needed"):
                    answer = result.get("answer") or result.get("analysis", "")
                    sources = result.get("sources", [])
                    st.session_state.chat_history.append({
                        "role": "assistant", "content": answer, "sources": sources
                    })
                else:
                    answer = f"I wasn't able to find a clear answer. Please consult your healthcare provider."
                    st.session_state.chat_history.append({"role": "assistant", "content": answer})
            except Exception as e:
                answer = "I encountered an issue retrieving that information. Please try again."
                st.session_state.chat_history.append({"role": "assistant", "content": answer})

        st.rerun()

    if st.session_state.chat_history:
        if st.button("🗑️ Clear conversation", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

st.caption("⚠️ For informational purposes only. Always consult your healthcare provider for medical decisions.")
