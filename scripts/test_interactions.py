"""Test drug normalization and interaction engine"""
import sys
sys.path.insert(0, '.')

from src.rag.drug_normalizer import normalize_drug_list
from src.rag.qa_chain import MedicalQAChain

# Test 1: Drug normalization
print("=== Drug Normalization ===")
tests = ["Lipitor", "Warfarin", "Zithromax", "T-minic", "Combiflam", "Paracetamol", "UnknownDrug123"]
results = normalize_drug_list(tests)
for r in results:
    conf = int(r["confidence"] * 100)
    flag = "NEEDS CLARIFICATION" if r["needs_clarification"] else "OK"
    print(f"  {r['original']:20} -> {r['normalized']:30} ({conf}% via {r['method']}) [{flag}]")

# Test 2: Full interaction check
print("\n=== Interaction Check: Warfarin + Aspirin + Metformin ===")
qa = MedicalQAChain()
result = qa.check_interactions(["Warfarin", "Aspirin", "Metformin"])
print("Status:", result["status"])
print("Pairs checked:", result.get("pairs_checked", 0))
print("Sources:", result.get("num_sources", 0))
print("\nNormalized drugs:")
for d in result.get("normalized_drugs", []):
    print(f"  {d['original']} -> {d['normalized']} ({int(d['confidence']*100)}%)")
print("\nAnalysis preview:")
analysis = result.get("analysis", "")
print(analysis[:600].encode("ascii", "replace").decode())
