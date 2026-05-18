"""
Advanced RAG QA Chain
- Intent detection & query routing
- Retrieval prioritization by section_type
- Structured clinical response generation
- Concise synthesis from multiple chunks
- Minimal disclaimers, maximum clinical value
"""
from typing import Dict, Any, List, Optional, Tuple
from src.rag.vector_store import get_vector_store
from src.config import get_llm_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ── Intent detection ─────────────────────────────────────────────────────────

INTENT_MAP = {
    "side_effects": [
        "side effect", "adverse", "reaction", "toxicity", "harm",
        "dangerous", "risk", "safe", "safety", "cause", "feel"
    ],
    "drug_interaction": [
        "interact", "combination", "combine", "together", "mix",
        "with alcohol", "with food", "contraindic", "avoid"
    ],
    "dosage": [
        "dose", "dosage", "how much", "how many", "how often",
        "frequency", "mg", "strength", "overdose", "missed dose", "miss a dose"
    ],
    "indication": [
        "used for", "treat", "indication", "prescribed for",
        "what is", "what does", "purpose", "work for"
    ],
    "duration": [
        "how long", "take to work", "onset", "duration",
        "when will", "start working", "kick in"
    ],
    "precaution": [
        "warning", "precaution", "caution", "avoid", "careful",
        "pregnancy", "breastfeed", "kidney", "liver", "elderly", "children"
    ],
    "mechanism": [
        "how does", "mechanism", "pharmacology", "work", "action"
    ],
}

# Structured prompts per intent
PROMPTS = {
    "side_effects": """You are a clinical pharmacist. Answer this side effects question concisely and completely.

PATIENT PRESCRIPTION: {prescription_context}
RETRIEVED KNOWLEDGE: {retrieved_context}
QUESTION: {question}

Respond in this exact structure (use markdown):

**Common Side Effects**
- [list the most frequent ones, with approximate frequency if known]

**Serious Side Effects** ⚠️
- [list serious/rare ones that require medical attention]

**What to Do**
- [1-2 practical patient instructions]

**For Your Prescription**
- [any specific note about their prescribed drug/dose if relevant]

Keep each section to 3-5 bullet points max. Be direct and clinical.""",

    "drug_interaction": """You are a clinical pharmacist reviewing drug interactions.

PATIENT PRESCRIPTION: {prescription_context}
RETRIEVED KNOWLEDGE: {retrieved_context}
QUESTION: {question}

Respond in this exact structure:

**Interaction Summary**
[1-2 sentence overview]

**Severity Level**
🔴 High / 🟡 Moderate / 🟢 Low — [brief reason]

**Clinical Details**
- [what happens when combined]
- [mechanism if relevant]

**Recommendation**
- [specific action: avoid / monitor / timing adjustment / alternative]

Be direct. No excessive disclaimers.""",

    "dosage": """You are a clinical pharmacist answering a dosage question.

PATIENT PRESCRIPTION: {prescription_context}
RETRIEVED KNOWLEDGE: {retrieved_context}
QUESTION: {question}

Respond in this exact structure:

**Standard Dosage**
- [typical adult dose and frequency]

**For Your Prescription**
- [specific to their prescribed dose if available]

**Missed Dose**
- [what to do if a dose is missed]

**Important Notes**
- [1-2 key dosing considerations: with food, timing, etc.]

Be concise and specific.""",

    "duration": """You are a clinical pharmacist.

PATIENT PRESCRIPTION: {prescription_context}
RETRIEVED KNOWLEDGE: {retrieved_context}
QUESTION: {question}

Respond in this exact structure:

**Onset of Action**
- [when effects typically begin]

**Full Effect**
- [when maximum benefit is reached]

**Duration of Action**
- [how long each dose lasts]

**For Your Condition**
- [any condition-specific timing notes]

Keep it brief and practical.""",

    "precaution": """You are a clinical pharmacist reviewing precautions.

PATIENT PRESCRIPTION: {prescription_context}
RETRIEVED KNOWLEDGE: {retrieved_context}
QUESTION: {question}

Respond in this exact structure:

**Key Precautions**
- [most important warnings]

**Who Should Avoid This**
- [contraindications: pregnancy, kidney disease, etc.]

**Monitoring Required**
- [any lab tests or vital signs to watch]

**Patient Instructions**
- [practical safety tips]

Be specific and clinically accurate.""",

    "general": """You are a knowledgeable clinical medical assistant.

PATIENT PRESCRIPTION: {prescription_context}
RETRIEVED KNOWLEDGE: {retrieved_context}
QUESTION: {question}

Instructions:
- If the drug is found in retrieved knowledge, give a structured clinical answer
- If the drug is NOT found, say so in ONE sentence, then use your general medical knowledge to answer
- Never repeat disclaimers more than once
- Be concise — max 150 words
- Use bullet points for clarity
- End with ONE brief recommendation

If the drug name looks like a brand name or regional name, mention what it likely is.""",
}

INTERACTION_PROMPT = """You are a clinical pharmacist performing a drug interaction check.

MEDICATIONS: {medications}
RETRIEVED INTERACTION DATA: {retrieved_context}

Provide a structured interaction analysis:

**Interactions Found**
[For each interaction:]
- Drug A + Drug B: [severity 🔴/🟡/🟢] — [brief description]

**Clinical Recommendations**
- [specific action for each significant interaction]

**Overall Safety Assessment**
[1-2 sentence summary]

If no interactions found in the data, state clearly and suggest consulting a pharmacist.
Be direct and clinically useful."""


# ── Query intent detection ────────────────────────────────────────────────────

def detect_intent(question: str) -> str:
    """Detect the clinical intent of a question"""
    q = question.lower()
    scores = {intent: 0 for intent in INTENT_MAP}
    for intent, keywords in INTENT_MAP.items():
        for kw in keywords:
            if kw in q:
                scores[intent] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general"


def get_section_priority(intent: str) -> List[str]:
    """Return preferred section_types for retrieval based on intent"""
    priority_map = {
        "side_effects":      ["side_effects", "drug_information", "warning", "general"],
        "drug_interaction":  ["drug_interaction", "warning", "drug_information", "general"],
        "dosage":            ["dosage", "drug_information", "general"],
        "indication":        ["indication", "drug_information", "general"],
        "duration":          ["dosage", "drug_information", "pharmacology", "general"],
        "precaution":        ["warning", "drug_information", "side_effects", "general"],
        "mechanism":         ["pharmacology", "drug_information", "general"],
        "general":           ["drug_information", "side_effects", "general", "drug_interaction"],
    }
    return priority_map.get(intent, ["drug_information", "general"])


# ── Retrieval helpers ─────────────────────────────────────────────────────────

def keyword_score(query: str, document: str) -> float:
    stop = {"the","a","an","is","are","was","were","be","have","has","do","does",
            "of","in","on","at","to","for","with","by","and","or","not","what",
            "how","when","where","i","my","your","this","that","it","can","will"}
    q_words = set(query.lower().split()) - stop
    d_words = set(document.lower().split())
    if not q_words:
        return 0.0
    return len(q_words & d_words) / len(q_words)


def rerank_with_priority(
    query: str,
    documents: List[str],
    metadatas: List[Dict],
    distances: List[float],
    section_priority: List[str],
    top_k: int = 6
) -> List[Dict[str, Any]]:
    """Rerank using vector score + keyword score + section priority boost"""
    scored = []
    for doc, meta, dist in zip(documents, metadatas, distances):
        if not doc:
            continue
        meta = meta or {}
        safe_dist = dist if dist is not None else 1.0

        vector_score = max(0.0, 1.0 - safe_dist)
        kw_score = keyword_score(query, doc)

        # Section priority boost
        section = meta.get("section_type", "general")
        try:
            priority_rank = section_priority.index(section)
            priority_boost = max(0.0, (len(section_priority) - priority_rank) / len(section_priority)) * 0.2
        except ValueError:
            priority_boost = 0.0

        combined = 0.6 * vector_score + 0.2 * kw_score + 0.2 * priority_boost

        scored.append({
            "document": doc,
            "metadata": meta,
            "vector_score": round(vector_score, 3),
            "keyword_score": round(kw_score, 3),
            "priority_boost": round(priority_boost, 3),
            "combined_score": round(combined, 3),
            "relevance": round(combined, 3),
        })

    scored.sort(key=lambda x: x["combined_score"], reverse=True)
    return scored[:top_k]


# ── Main QA chain ─────────────────────────────────────────────────────────────

class MedicalQAChain:

    def __init__(self):
        self.vector_store = get_vector_store()
        self.llm_config = get_llm_config()
        logger.info("Medical QA Chain initialized")

    def _get_llm(self):
        cfg = self.llm_config
        if cfg["provider"] in ("groq", "openai"):
            from langchain_openai import ChatOpenAI
            kwargs = dict(api_key=cfg["api_key"], model=cfg["model"], temperature=0.2)
            if cfg["provider"] == "groq":
                kwargs["base_url"] = "https://api.groq.com/openai/v1"
            return ChatOpenAI(**kwargs)
        from langchain_community.llms import Ollama
        return Ollama(model=cfg["model"], base_url=cfg["base_url"], temperature=0.2)

    def _retrieve(self, query: str, section_priority: List[str], n_candidates: int = 15, top_k: int = 6) -> List[Dict]:
        raw = self.vector_store.query(query, n_results=n_candidates)
        if not raw["documents"]:
            return []
        return rerank_with_priority(
            query, raw["documents"], raw["metadatas"], raw["distances"],
            section_priority, top_k=top_k
        )

    def _format_prescription(self, data: Optional[Dict]) -> str:
        if not data:
            return "No prescription loaded."
        parts = []
        if data.get("diagnosis"):
            parts.append(f"Diagnosis: {data['diagnosis']}")
        for m in data.get("medications", []):
            line = f"- {m.get('name','?')} {m.get('dosage','')} {m.get('frequency','')}".strip()
            if m.get("instructions"):
                line += f" ({m['instructions']})"
            parts.append(line)
        return "\n".join(parts) if parts else "No details available."

    def _build_context(self, retrieved: List[Dict]) -> str:
        if not retrieved:
            return "No relevant information found."
        parts = []
        for i, r in enumerate(retrieved, 1):
            src = r["metadata"].get("source", "?") if r.get("metadata") else "?"
            sec = r["metadata"].get("section_type", "general") if r.get("metadata") else "general"
            parts.append(f"[{i}] {src} ({sec}):\n{r['document']}")
        return "\n\n".join(parts)

    def answer_question(
        self,
        question: str,
        prescription_context: Optional[Dict] = None,
        n_results: int = 6
    ) -> Dict[str, Any]:
        try:
            logger.info(f"RAG query: {question[:80]}")

            # Detect intent and get section priority
            intent = detect_intent(question)
            section_priority = get_section_priority(intent)
            logger.info(f"Intent: {intent} | Priority: {section_priority[:3]}")

            # Retrieve with priority-aware reranking
            retrieved = self._retrieve(question, section_priority, n_candidates=20, top_k=n_results)

            # Build prompt
            rx_ctx = self._format_prescription(prescription_context)
            kb_ctx = self._build_context(retrieved)
            prompt_template = PROMPTS.get(intent, PROMPTS["general"])
            prompt = prompt_template.format(
                prescription_context=rx_ctx,
                retrieved_context=kb_ctx,
                question=question
            )

            # Generate
            llm = self._get_llm()
            response = llm.invoke(prompt)
            answer = response.content if hasattr(response, "content") else str(response)

            # Add single brief disclaimer
            answer += "\n\n*Always consult your healthcare provider before making medication changes.*"

            sources = [
                {
                    "text": r["document"][:200] + "..." if len(r["document"]) > 200 else r["document"],
                    "metadata": r.get("metadata", {}),
                    "relevance": r["combined_score"],
                    "vector_score": r["vector_score"],
                    "keyword_score": r["keyword_score"],
                }
                for r in retrieved
            ]

            logger.info(f"Answer generated using {len(retrieved)} sources (intent={intent})")
            return {"status": "success", "answer": answer, "sources": sources,
                    "num_sources": len(sources), "intent": intent}

        except Exception as e:
            logger.error(f"Failed to answer question: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"status": "error", "answer": f"Error: {str(e)}", "error": str(e), "sources": []}

    def check_interactions(self, medications: List[str]) -> Dict[str, Any]:
        if len(medications) < 2:
            return {"status": "success", "interactions": [], "message": "Need at least 2 medications"}

        from src.rag.interaction_engine import InteractionEngine
        engine = InteractionEngine(self.vector_store, self.llm_config)
        return engine.analyze(medications)


_qa_chain = None

def get_qa_chain() -> MedicalQAChain:
    global _qa_chain
    if _qa_chain is None:
        _qa_chain = MedicalQAChain()
    return _qa_chain
