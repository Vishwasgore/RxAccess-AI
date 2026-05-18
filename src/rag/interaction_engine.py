"""
Dedicated drug interaction engine.
- Drug normalization before analysis
- Deduplication of interactions
- Confidence scoring
- Metadata-filtered retrieval (interaction chunks only)
- Safe clinical language
"""
import re
from typing import Dict, Any, List, Tuple, Optional
from src.rag.drug_normalizer import normalize_drug_list, get_interaction_pairs
from src.utils.logger import get_logger

logger = get_logger(__name__)

# ── Severity scoring ─────────────────────────────────────────────────────────
# Keyword-based severity detection from retrieved text
SEVERITY_KEYWORDS = {
    "high": [
        "contraindicated", "avoid", "fatal", "life-threatening", "severe",
        "do not use", "never combine", "cardiac arrest", "death", "serious",
        "dangerous", "major", "significant risk"
    ],
    "moderate": [
        "monitor", "caution", "may increase", "may decrease", "reduce dose",
        "use with caution", "moderate", "clinically significant", "adjust"
    ],
    "low": [
        "minor", "minimal", "unlikely", "theoretical", "rare", "low risk",
        "generally safe", "no significant"
    ],
}


def score_severity_from_text(text: str) -> Tuple[str, float]:
    """
    Detect severity from retrieved text using keyword scoring.
    Returns (severity_level, confidence_score)
    """
    text_lower = text.lower()
    scores = {"high": 0, "moderate": 0, "low": 0}

    for level, keywords in SEVERITY_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                scores[level] += 1

    total = sum(scores.values())
    if total == 0:
        return "unknown", 0.0

    best = max(scores, key=scores.get)
    confidence = scores[best] / total
    return best, round(confidence, 2)


def deduplicate_interactions(interactions: List[Dict]) -> List[Dict]:
    """Remove duplicate interactions (same drug pair, different chunks)"""
    seen = set()
    unique = []
    for interaction in interactions:
        key = tuple(sorted([
            interaction.get("drug1", "").lower(),
            interaction.get("drug2", "").lower()
        ]))
        if key not in seen:
            seen.add(key)
            unique.append(interaction)
    return unique


def filter_interaction_chunks(retrieved: List[Dict]) -> List[Dict]:
    """Keep only chunks relevant to drug interactions, filter out unrelated content"""
    relevant = []
    for chunk in retrieved:
        meta = chunk.get("metadata", {}) or {}
        doc = chunk.get("document", "")
        doc_lower = doc.lower()

        # Keep if metadata says it's an interaction
        if meta.get("type") in ("drug_interaction", "side_effects", "warning"):
            relevant.append(chunk)
            continue

        # Keep if text contains interaction keywords
        interaction_signals = [
            "interact", "combination", "combined with", "concurrent",
            "concomitant", "avoid", "contraindic", "potentiate",
            "inhibit", "induce", "increase.*level", "decrease.*effect"
        ]
        if any(re.search(sig, doc_lower) for sig in interaction_signals):
            relevant.append(chunk)

    return relevant if relevant else retrieved[:3]  # fallback to top 3


INTERACTION_SYSTEM_PROMPT = """You are a clinical pharmacist performing a drug interaction safety review.

NORMALIZED MEDICATIONS: {medications}
DRUG PAIRS TO CHECK: {pairs}

RETRIEVED INTERACTION DATA:
{retrieved_context}

Provide a structured, clinically accurate interaction analysis. Use ONLY information from the retrieved data above.
Do NOT hallucinate interactions not supported by the retrieved data.

Format your response exactly as:

## Drug Interaction Analysis

{pair_sections}

## Overall Safety Assessment
[1-2 sentences. Use conservative language: "recommend monitoring", "consult your pharmacist/physician", not "switch to X drug"]

## Clinical Recommendations
- [Specific, actionable, safe recommendations]
- [Use: monitor / consult / timing adjustment / dose review]
- [Avoid: suggesting specific drug replacements]

---
*Confidence based on available data. Consult your healthcare provider for personalized advice.*"""

PAIR_SECTION_TEMPLATE = """### {drug1} + {drug2}
**Severity:** {severity_icon} {severity} (confidence: {confidence}%)
**Interaction:** {description}
**Recommendation:** {recommendation}"""


class InteractionEngine:
    """Dedicated drug interaction analysis engine"""

    def __init__(self, vector_store, llm_config):
        self.vector_store = vector_store
        self.llm_config = llm_config

    def _get_llm(self):
        cfg = self.llm_config
        if cfg["provider"] in ("groq", "openai"):
            from langchain_openai import ChatOpenAI
            kwargs = dict(api_key=cfg["api_key"], model=cfg["model"], temperature=0.1)
            if cfg["provider"] == "groq":
                kwargs["base_url"] = "https://api.groq.com/openai/v1"
            return ChatOpenAI(**kwargs)
        from langchain_community.llms import Ollama
        return Ollama(model=cfg["model"], base_url=cfg["base_url"], temperature=0.1)

    def _retrieve_for_pair(self, drug1: str, drug2: str, n: int = 8) -> List[Dict]:
        """Retrieve interaction-specific chunks for a drug pair"""
        queries = [
            f"drug interaction {drug1} {drug2}",
            f"{drug1} {drug2} adverse combination",
            f"{drug1} interaction",
            f"{drug2} interaction",
        ]

        all_chunks = []
        seen_docs = set()

        for query in queries[:2]:  # Use top 2 queries
            raw = self.vector_store.query(query, n_results=n)
            for doc, meta, dist in zip(
                raw.get("documents", []),
                raw.get("metadatas", []),
                raw.get("distances", [])
            ):
                if doc and doc not in seen_docs:
                    seen_docs.add(doc)
                    safe_dist = dist if dist is not None else 1.0
                    all_chunks.append({
                        "document": doc,
                        "metadata": meta or {},
                        "combined_score": round(max(0.0, 1.0 - safe_dist), 3),
                        "relevance": round(max(0.0, 1.0 - safe_dist), 3),
                    })

        # Filter to interaction-relevant chunks only
        filtered = filter_interaction_chunks(all_chunks)

        # Sort by relevance
        filtered.sort(key=lambda x: x["combined_score"], reverse=True)
        return filtered[:5]

    def analyze(self, medications: List[str]) -> Dict[str, Any]:
        """
        Full interaction analysis pipeline:
        normalize → pair → retrieve → score → deduplicate → synthesize
        """
        if len(medications) < 2:
            return {
                "status": "success",
                "message": "Need at least 2 medications to check interactions.",
                "normalized_drugs": [],
                "interactions": [],
                "analysis": "Please provide at least 2 medications.",
                "low_confidence_drugs": []
            }

        # Step 1: Normalize all drug names
        normalized = normalize_drug_list(medications)
        logger.info(f"Normalized drugs: {[(d['original'], d['normalized'], d['confidence']) for d in normalized]}")

        # Separate low-confidence drugs
        low_conf = [d for d in normalized if d["needs_clarification"]]
        high_conf = [d for d in normalized if not d["needs_clarification"]]

        if len(high_conf) < 2:
            return {
                "status": "clarification_needed",
                "message": "Could not confidently identify the medications.",
                "normalized_drugs": normalized,
                "low_confidence_drugs": low_conf,
                "interactions": [],
                "analysis": self._build_clarification_message(low_conf, normalized)
            }

        # Step 2: Generate drug pairs
        pairs = get_interaction_pairs(normalized)
        logger.info(f"Checking {len(pairs)} drug pairs")

        # Step 3: Retrieve and analyze each pair
        pair_results = []
        all_sources = []

        for drug1, drug2 in pairs:
            chunks = self._retrieve_for_pair(drug1, drug2)
            all_sources.extend(chunks)

            # Score severity from retrieved text
            combined_text = " ".join(c["document"] for c in chunks)
            severity, sev_confidence = score_severity_from_text(combined_text)

            pair_results.append({
                "drug1": drug1.title(),
                "drug2": drug2.title(),
                "severity": severity,
                "severity_confidence": sev_confidence,
                "chunks": chunks,
                "has_data": len(chunks) > 0
            })

        # Step 4: Deduplicate
        pair_results = deduplicate_interactions(pair_results)

        # Step 5: Build context for LLM
        context_parts = []
        for pr in pair_results:
            if pr["chunks"]:
                chunk_texts = "\n".join(
                    f"  [{c['metadata'].get('source','?')}]: {c['document'][:300]}"
                    for c in pr["chunks"][:3]
                )
                context_parts.append(
                    f"=== {pr['drug1']} + {pr['drug2']} ===\n{chunk_texts}"
                )

        retrieved_context = "\n\n".join(context_parts) if context_parts else "No specific interaction data found."

        # Step 6: Generate structured analysis with LLM
        severity_icons = {"high": "🔴", "moderate": "🟡", "low": "🟢", "unknown": "⚪"}

        pair_sections = "\n\n".join([
            f"### {pr['drug1']} + {pr['drug2']}\n"
            f"**Severity:** {severity_icons.get(pr['severity'], '⚪')} {pr['severity'].title()} "
            f"(data confidence: {int(pr['severity_confidence']*100)}%)\n"
            f"[Analyze interaction based on retrieved data above]"
            for pr in pair_results
        ])

        prompt = INTERACTION_SYSTEM_PROMPT.format(
            medications=", ".join(d["display_name"] for d in normalized),
            pairs=", ".join(f"{p[0].title()} + {p[1].title()}" for p in pairs),
            retrieved_context=retrieved_context,
            pair_sections=pair_sections
        )

        try:
            llm = self._get_llm()
            response = llm.invoke(prompt)
            analysis = response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            logger.error(f"LLM interaction analysis failed: {e}")
            analysis = self._build_fallback_analysis(pair_results)

        # Deduplicate sources
        seen = set()
        unique_sources = []
        for s in all_sources:
            key = s["document"][:100]
            if key not in seen:
                seen.add(key)
                unique_sources.append(s)

        return {
            "status": "success",
            "normalized_drugs": normalized,
            "low_confidence_drugs": low_conf,
            "pairs_checked": len(pairs),
            "pair_results": pair_results,
            "analysis": analysis,
            "sources": unique_sources[:8],
            "num_sources": len(unique_sources)
        }

    def _build_clarification_message(self, low_conf: List[Dict], all_drugs: List[Dict]) -> str:
        lines = ["## Drug Interaction Check\n"]
        lines.append("⚠️ **Could not confidently identify all medications:**\n")
        for d in low_conf:
            lines.append(f"- **{d['original']}** — not found in drug database (confidence: {int(d['confidence']*100)}%)")
        lines.append("\n**Please verify the medication names and try again, or consult your pharmacist.**")
        return "\n".join(lines)

    def _build_fallback_analysis(self, pair_results: List[Dict]) -> str:
        """Fallback when LLM is unavailable"""
        lines = ["## Drug Interaction Analysis\n"]
        severity_icons = {"high": "🔴", "moderate": "🟡", "low": "🟢", "unknown": "⚪"}
        for pr in pair_results:
            icon = severity_icons.get(pr["severity"], "⚪")
            lines.append(f"### {pr['drug1']} + {pr['drug2']}")
            lines.append(f"**Severity:** {icon} {pr['severity'].title()}")
            if pr["chunks"]:
                lines.append(f"**Data:** {pr['chunks'][0]['document'][:200]}...")
            lines.append("")
        lines.append("\n*Consult your pharmacist or physician for personalized interaction guidance.*")
        return "\n".join(lines)
