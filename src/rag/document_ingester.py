"""
Advanced document ingestion pipeline.
Supports: PDF, TXT, DOCX, MD
Features: semantic chunking, recursive splitting, rich metadata
"""
import re
import io
import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ── Text extraction ──────────────────────────────────────────────────────────

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF — tries PyMuPDF, pdfplumber, then OCR"""
    # PyMuPDF (fastest, best quality)
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages = [page.get_text() for page in doc]
        doc.close()
        text = "\n\n".join(p for p in pages if p.strip())
        if len(text.strip()) > 100:
            logger.info(f"PDF extracted via PyMuPDF: {len(text)} chars, {len(pages)} pages")
            return text
    except Exception as e:
        logger.debug(f"PyMuPDF: {e}")

    # pdfplumber fallback
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pages = [p.extract_text() or "" for p in pdf.pages]
        text = "\n\n".join(p for p in pages if p.strip())
        if len(text.strip()) > 100:
            logger.info(f"PDF extracted via pdfplumber: {len(text)} chars")
            return text
    except Exception as e:
        logger.debug(f"pdfplumber: {e}")

    # OCR last resort
    try:
        from src.extraction.ocr_engine import OCREngine
        result = OCREngine().extract_from_pdf(pdf_bytes)
        text = result.get("text", "")
        logger.info(f"PDF extracted via OCR: {len(text)} chars")
        return text
    except Exception as e:
        logger.error(f"All PDF extraction failed: {e}")
        return ""


def extract_text_from_docx(docx_bytes: bytes) -> str:
    try:
        import docx
        doc = docx.Document(io.BytesIO(docx_bytes))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as e:
        logger.error(f"DOCX extraction failed: {e}")
        return ""


# ── Semantic / recursive chunking ────────────────────────────────────────────

def recursive_chunk(text: str, chunk_size: int = 600, overlap: int = 80) -> List[str]:
    """
    Split text into overlapping chunks on natural boundaries.
    Non-recursive implementation to avoid stack overflow on large documents.
    """
    if not text or not text.strip():
        return []

    # Normalize whitespace
    text = re.sub(r'\n{3,}', '\n\n', text).strip()

    chunks: List[str] = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)

        # Try to find a good break point (paragraph > sentence > word)
        if end < text_len:
            for sep in ["\n\n", "\n", ". ", " "]:
                pos = text.rfind(sep, start, end)
                if pos > start + chunk_size // 2:
                    end = pos + len(sep)
                    break

        chunk = text[start:end].strip()
        if len(chunk) > 40:
            chunks.append(chunk)

        # Move forward with overlap
        start = max(start + 1, end - overlap)

    return chunks


def detect_section_type(text: str) -> str:
    """Detect the medical content type of a chunk for metadata tagging"""
    text_lower = text.lower()
    if any(w in text_lower for w in ["side effect", "adverse", "reaction", "toxicity"]):
        return "side_effects"
    if any(w in text_lower for w in ["interaction", "contraindic", "avoid with"]):
        return "drug_interaction"
    if any(w in text_lower for w in ["dosage", "dose", "mg", "mcg", "administration"]):
        return "dosage"
    if any(w in text_lower for w in ["indication", "used for", "treatment of", "therapy"]):
        return "indication"
    if any(w in text_lower for w in ["warning", "precaution", "caution", "monitor"]):
        return "warning"
    if any(w in text_lower for w in ["mechanism", "pharmacology", "pharmacokinetic"]):
        return "pharmacology"
    return "general"


# ── Main ingester ─────────────────────────────────────────────────────────────

class DocumentIngester:
    """Ingest documents into ChromaDB with rich metadata"""

    def __init__(self):
        from src.rag.vector_store import get_vector_store
        self.vector_store = get_vector_store()

    def _doc_id(self, source: str, chunk_idx: int) -> str:
        """Generate stable, unique chunk ID"""
        h = hashlib.md5(source.encode()).hexdigest()[:8]
        return f"doc_{h}_{chunk_idx}"

    def ingest_text(
        self,
        text: str,
        source_name: str,
        doc_type: str = "custom",
        chunk_size: int = 600
    ) -> Dict[str, Any]:
        """Chunk and ingest plain text"""
        if not text or not text.strip():
            return {"status": "error", "error": "Empty text"}

        chunks = recursive_chunk(text, chunk_size=chunk_size)
        if not chunks:
            return {"status": "error", "error": "No chunks extracted"}

        existing = self.vector_store.get_collection_stats()["document_count"]

        documents = chunks
        metadatas = [
            {
                "source": source_name,
                "type": doc_type,
                "section_type": detect_section_type(chunk),
                "chunk_index": i,
                "total_chunks": len(chunks),
                "char_count": len(chunk),
            }
            for i, chunk in enumerate(chunks)
        ]
        ids = [self._doc_id(source_name, existing + i) for i in range(len(chunks))]

        self.vector_store.add_documents(documents, metadatas, ids)
        logger.info(f"Ingested '{source_name}': {len(chunks)} chunks")

        return {
            "status": "success",
            "source": source_name,
            "chunks_added": len(chunks),
            "total_docs": existing + len(chunks)
        }

    def ingest_file(
        self,
        file_bytes: bytes,
        filename: str,
        doc_type: str = "custom",
        chunk_size: int = 600
    ) -> Dict[str, Any]:
        """Extract text from file and ingest"""
        ext = Path(filename).suffix.lower()
        source_name = Path(filename).stem[:60]

        if ext == ".pdf":
            text = extract_text_from_pdf(file_bytes)
        elif ext in (".txt", ".md"):
            text = file_bytes.decode("utf-8", errors="ignore")
        elif ext == ".docx":
            text = extract_text_from_docx(file_bytes)
        else:
            return {"status": "error", "error": f"Unsupported: {ext}"}

        if not text.strip():
            return {"status": "error", "error": "No text extracted from file"}

        return self.ingest_text(text, source_name, doc_type, chunk_size)

    def list_sources(self) -> List[Dict[str, Any]]:
        """List all unique sources with chunk counts"""
        try:
            results = self.vector_store.collection.get(limit=2000, include=["metadatas"])
            sources: Dict[str, Dict] = {}
            for meta in results.get("metadatas", []):
                src = meta.get("source", "unknown")
                if src not in sources:
                    sources[src] = {"source": src, "type": meta.get("type", "?"), "chunks": 0}
                sources[src]["chunks"] += 1
            return sorted(sources.values(), key=lambda x: x["chunks"], reverse=True)
        except Exception as e:
            logger.error(f"list_sources failed: {e}")
            return []

    def delete_source(self, source_name: str) -> Dict[str, Any]:
        """Delete all chunks from a source"""
        try:
            results = self.vector_store.collection.get(
                where={"source": source_name}, include=["metadatas"]
            )
            ids = results.get("ids", [])
            if not ids:
                return {"status": "error", "error": "Source not found"}
            self.vector_store.collection.delete(ids=ids)
            return {"status": "success", "deleted_chunks": len(ids)}
        except Exception as e:
            return {"status": "error", "error": str(e)}


_ingester = None

def get_ingester() -> DocumentIngester:
    global _ingester
    if _ingester is None:
        _ingester = DocumentIngester()
    return _ingester
