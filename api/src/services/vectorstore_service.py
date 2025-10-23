import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import uuid

class VectorStoreService:
    """Service for managing vector store operations with ChromaDB"""

    def __init__(self):
        self.client = None
        self.embedding_model = None
        self._initialized = False

    async def initialize(self):
        """Initialize the vector store and embedding model"""
        if self._initialized:
            return

        # Initialize ChromaDB client
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory="./data/chroma"
        ))

        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

        self._initialized = True

    def is_ready(self) -> bool:
        """Check if the service is ready"""
        return self._initialized

    def get_or_create_collection(self, knowledge_base_id: str):
        """Get or create a collection for a knowledge base"""
        if not self._initialized:
            raise RuntimeError("VectorStore not initialized")

        return self.client.get_or_create_collection(
            name=knowledge_base_id,
            metadata={"description": f"Knowledge base: {knowledge_base_id}"}
        )

    async def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        knowledge_base_id: str = "default",
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """Add documents to the vector store"""
        if not documents:
            return []

        collection = self.get_or_create_collection(knowledge_base_id)

        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]

        # Generate embeddings
        embeddings = self.embedding_model.encode(documents).tolist()

        # Add to collection
        collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

        return ids

    async def search(
        self,
        query: str,
        knowledge_base_id: str = "default",
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        collection = self.get_or_create_collection(knowledge_base_id)

        # Generate query embedding
        query_embedding = self.embedding_model.encode([query]).tolist()[0]

        # Search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter
        )

        # Format results
        formatted_results = []
        if results['documents'] and len(results['documents']) > 0:
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'score': 1 - results['distances'][0][i] if results['distances'] else 0,
                    'id': results['ids'][0][i] if results['ids'] else None
                })

        return formatted_results

    async def delete_document(self, document_id: str, knowledge_base_id: str = "default"):
        """Delete a document from the vector store"""
        collection = self.get_or_create_collection(knowledge_base_id)
        collection.delete(ids=[document_id])

    async def list_collections(self) -> List[str]:
        """List all knowledge bases (collections)"""
        collections = self.client.list_collections()
        return [col.name for col in collections]

    async def get_collection_count(self, knowledge_base_id: str = "default") -> int:
        """Get the number of documents in a collection"""
        collection = self.get_or_create_collection(knowledge_base_id)
        return collection.count()
