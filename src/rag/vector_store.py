"""
Vector store management using ChromaDB
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class VectorStore:
    """ChromaDB vector store for RAG"""
    
    def __init__(self, collection_name: str = "medical_knowledge"):
        """
        Initialize vector store
        
        Args:
            collection_name: Name of the ChromaDB collection
        """
        self.collection_name = collection_name
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(f"Loaded existing collection: {collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "Medical knowledge base for RAG"}
            )
            logger.info(f"Created new collection: {collection_name}")
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> None:
        """
        Add documents to vector store
        
        Args:
            documents: List of document texts
            metadatas: Optional list of metadata dictionaries
            ids: Optional list of document IDs
        """
        try:
            if ids is None:
                ids = [f"doc_{i}" for i in range(len(documents))]
            
            if metadatas is None:
                metadatas = [{"source": "unknown"} for _ in documents]
            
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(documents)} documents to vector store")
        
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise
    
    def query(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Query vector store for similar documents
        
        Args:
            query_text: Query string
            n_results: Number of results to return
            where: Optional metadata filter
        
        Returns:
            Query results with documents and metadata
        """
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where
            )
            
            logger.info(f"Query returned {len(results['documents'][0])} results")
            
            return {
                "documents": results["documents"][0],
                "metadatas": results["metadatas"][0],
                "distances": results["distances"][0],
                "ids": results["ids"][0]
            }
        
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {
                "documents": [],
                "metadatas": [],
                "distances": [],
                "ids": []
            }
    
    def delete_collection(self) -> None:
        """Delete the collection"""
        try:
            self.client.delete_collection(name=self.collection_name)
            logger.info(f"Deleted collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            count = self.collection.count()
            return {
                "name": self.collection_name,
                "document_count": count,
                "status": "active"
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                "name": self.collection_name,
                "document_count": 0,
                "status": "error",
                "error": str(e)
            }


def initialize_knowledge_base() -> VectorStore:
    """
    Initialize vector store with medical knowledge base
    
    Returns:
        Initialized VectorStore instance
    """
    logger.info("Initializing knowledge base")
    
    vector_store = VectorStore(collection_name="medical_knowledge")
    
    # Check if already populated
    stats = vector_store.get_collection_stats()
    if stats["document_count"] > 0:
        logger.info(f"Knowledge base already populated with {stats['document_count']} documents")
        return vector_store
    
    # Load knowledge base files
    kb_dir = settings.knowledge_base_dir
    
    documents = []
    metadatas = []
    ids = []
    
    # Load drug information
    drug_info_file = kb_dir / "drug_info.json"
    if drug_info_file.exists():
        with open(drug_info_file, 'r') as f:
            drug_data = json.load(f)
            for drug in drug_data:
                doc_text = f"""
Drug Name: {drug.get('name', 'Unknown')}
Generic Name: {drug.get('generic_name', 'N/A')}
Class: {drug.get('class', 'N/A')}
Uses: {drug.get('uses', 'N/A')}
Dosage: {drug.get('dosage', 'N/A')}
Side Effects: {drug.get('side_effects', 'N/A')}
Precautions: {drug.get('precautions', 'N/A')}
Interactions: {drug.get('interactions', 'N/A')}
"""
                documents.append(doc_text.strip())
                metadatas.append({
                    "source": "drug_info",
                    "drug_name": drug.get('name', 'Unknown'),
                    "type": "drug_information"
                })
                ids.append(f"drug_{drug.get('name', 'unknown').lower().replace(' ', '_')}")
    
    # Load interaction data
    interactions_file = kb_dir / "interactions.json"
    if interactions_file.exists():
        with open(interactions_file, 'r') as f:
            interaction_data = json.load(f)
            for idx, interaction in enumerate(interaction_data):
                doc_text = f"""
Drug Interaction: {interaction.get('drug1', 'Unknown')} and {interaction.get('drug2', 'Unknown')}
Severity: {interaction.get('severity', 'Unknown')}
Description: {interaction.get('description', 'N/A')}
Recommendation: {interaction.get('recommendation', 'N/A')}
"""
                documents.append(doc_text.strip())
                metadatas.append({
                    "source": "interactions",
                    "type": "drug_interaction",
                    "severity": interaction.get('severity', 'unknown')
                })
                ids.append(f"interaction_{idx}")
    
    # Load side effects
    side_effects_file = kb_dir / "side_effects.json"
    if side_effects_file.exists():
        with open(side_effects_file, 'r') as f:
            side_effects_data = json.load(f)
            for drug_name, effects in side_effects_data.items():
                doc_text = f"""
Drug: {drug_name}
Common Side Effects: {', '.join(effects.get('common', []))}
Serious Side Effects: {', '.join(effects.get('serious', []))}
Management: {effects.get('management', 'N/A')}
"""
                documents.append(doc_text.strip())
                metadatas.append({
                    "source": "side_effects",
                    "drug_name": drug_name,
                    "type": "side_effects"
                })
                ids.append(f"side_effects_{drug_name.lower().replace(' ', '_')}")
    
    # Add documents to vector store
    if documents:
        vector_store.add_documents(documents, metadatas, ids)
        logger.info(f"Initialized knowledge base with {len(documents)} documents")
    else:
        logger.warning("No knowledge base documents found")
    
    return vector_store


# Global vector store instance
_vector_store = None

def get_vector_store() -> VectorStore:
    """Get or create global vector store instance"""
    global _vector_store
    if _vector_store is None:
        _vector_store = initialize_knowledge_base()
    return _vector_store
