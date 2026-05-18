"""
Ingest all documents from the 'rag data' folder into ChromaDB.
Run once: python scripts/ingest_rag_data.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.document_ingester import DocumentIngester
from src.utils.logger import get_logger

logger = get_logger(__name__)

RAG_DATA_DIR = Path(r"c:\Users\USER\Desktop\RxAccess AI\rag data")

# Map filename keywords to document categories
CATEGORY_MAP = {
    "interaction": "drug_interaction",
    "drug": "drug_guide",
    "poison": "drug_guide",
    "treatment": "treatment_guideline",
    "standard": "treatment_guideline",
    "guideline": "treatment_guideline",
    "protocol": "clinical_protocol",
    "formulary": "formulary",
}

def detect_category(filename: str) -> str:
    name_lower = filename.lower()
    for keyword, category in CATEGORY_MAP.items():
        if keyword in name_lower:
            return category
    return "medical_reference"


def main():
    ingester = DocumentIngester()

    before = ingester.vector_store.get_collection_stats()["document_count"]
    print(f"Knowledge base before: {before} chunks")
    print(f"Scanning: {RAG_DATA_DIR}\n")

    if not RAG_DATA_DIR.exists():
        print(f"ERROR: Folder not found: {RAG_DATA_DIR}")
        return

    pdf_files = list(RAG_DATA_DIR.glob("*.pdf"))
    txt_files = list(RAG_DATA_DIR.glob("*.txt"))
    md_files  = list(RAG_DATA_DIR.glob("*.md"))
    all_files = pdf_files + txt_files + md_files

    if not all_files:
        print("No files found.")
        return

    print(f"Found {len(all_files)} files to ingest:\n")

    for file_path in all_files:
        category = detect_category(file_path.name)
        size_kb = file_path.stat().st_size / 1024
        print(f"  Processing: {file_path.name} ({size_kb:.0f} KB) -> [{category}]")

        try:
            file_bytes = file_path.read_bytes()
            result = ingester.ingest_file(
                file_bytes=file_bytes,
                filename=file_path.name,
                doc_type=category,
                chunk_size=600
            )

            if result["status"] == "success":
                print(f"    OK: {result['chunks_added']} chunks added")
            else:
                print(f"    FAILED: {result['error']}")

        except Exception as e:
            print(f"    ERROR: {e}")

    after = ingester.vector_store.get_collection_stats()["document_count"]
    added = after - before
    print(f"\nDone. Knowledge base: {before} -> {after} chunks (+{added} new)")

    # Quick retrieval test
    print("\nRetrieval test: 'drug interaction warfarin'")
    results = ingester.vector_store.query("drug interaction warfarin", n_results=2)
    for doc, meta in zip(results["documents"], results["metadatas"]):
        print(f"  [{meta.get('source','?')}] {doc[:120]}...")


if __name__ == "__main__":
    main()
