"""Check RAG knowledge base status"""
import sys
sys.path.insert(0, '.')

from src.rag.vector_store import get_vector_store

vs = get_vector_store()
stats = vs.get_collection_stats()
print(f"Documents in ChromaDB: {stats['document_count']}")

results = vs.query("lisinopril side effects", n_results=3)
print("\nSample RAG retrieval for: 'lisinopril side effects'")
for i, (doc, meta) in enumerate(zip(results['documents'], results['metadatas']), 1):
    print(f"  [{i}] Source: {meta['source']} | Type: {meta['type']}")
    print(f"      {doc[:150]}")
    print()
