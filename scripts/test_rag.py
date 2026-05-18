"""Quick RAG quality test"""
import sys
sys.path.insert(0, '.')
from src.rag.qa_chain import MedicalQAChain, detect_intent

tests = [
    ("What are the side effects of Azithromycin?", "side_effects"),
    ("How long does Tramadol take to work?", "duration"),
    ("Can I take Metformin with alcohol?", "drug_interaction"),
    ("What is the dosage for Lisinopril?", "dosage"),
    ("What are the side effects of T-minic drops?", "side_effects"),
]

print("=== Intent Detection ===")
for q, expected in tests:
    detected = detect_intent(q)
    status = "OK" if detected == expected else f"MISMATCH (expected {expected})"
    print(f"  [{status}] '{q[:50]}' -> {detected}")

print("\n=== Live RAG Test: Azithromycin side effects ===")
qa = MedicalQAChain()
result = qa.answer_question("What are the side effects of Azithromycin?")
print(f"Status: {result['status']} | Intent: {result.get('intent')} | Sources: {result['num_sources']}")
print("\nAnswer preview:")
print(result['answer'][:600])
print("\nTop source:", result['sources'][0]['metadata'].get('source') if result['sources'] else 'none')
