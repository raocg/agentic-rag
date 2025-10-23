from typing import List, Dict, Any, Optional
from services.vectorstore_service import VectorStoreService
from models.schemas import DocumentUploadResponse
import uuid
import io

class DocumentService:
    """Service for document management and processing"""

    def __init__(self, vectorstore: VectorStoreService):
        self.vectorstore = vectorstore

    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        knowledge_base_id: str = "default",
        metadata: Optional[Dict[str, Any]] = None
    ) -> DocumentUploadResponse:
        """Upload and process a file"""

        # Extract text from file based on type
        text_content = await self._extract_text(file_content, filename)

        # Chunk the content
        chunks = self._chunk_text(text_content)

        # Add metadata
        if metadata is None:
            metadata = {}

        metadata["source"] = filename
        metadata["type"] = self._get_file_type(filename)

        # Create metadata for each chunk
        chunk_metadatas = []
        for i, chunk in enumerate(chunks):
            chunk_meta = metadata.copy()
            chunk_meta["chunk_index"] = i
            chunk_metadatas.append(chunk_meta)

        # Add to vector store
        document_id = str(uuid.uuid4())
        chunk_ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]

        await self.vectorstore.add_documents(
            documents=chunks,
            metadatas=chunk_metadatas,
            knowledge_base_id=knowledge_base_id,
            ids=chunk_ids
        )

        return DocumentUploadResponse(
            document_id=document_id,
            knowledge_base_id=knowledge_base_id,
            chunks_created=len(chunks),
            status="success"
        )

    async def add_text(
        self,
        content: str,
        knowledge_base_id: str = "default",
        metadata: Optional[Dict[str, Any]] = None
    ) -> DocumentUploadResponse:
        """Add text content directly"""

        # Chunk the content
        chunks = self._chunk_text(content)

        # Add metadata
        if metadata is None:
            metadata = {}

        metadata["type"] = "text"

        # Create metadata for each chunk
        chunk_metadatas = []
        for i, chunk in enumerate(chunks):
            chunk_meta = metadata.copy()
            chunk_meta["chunk_index"] = i
            chunk_metadatas.append(chunk_meta)

        # Add to vector store
        document_id = str(uuid.uuid4())
        chunk_ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]

        await self.vectorstore.add_documents(
            documents=chunks,
            metadatas=chunk_metadatas,
            knowledge_base_id=knowledge_base_id,
            ids=chunk_ids
        )

        return DocumentUploadResponse(
            document_id=document_id,
            knowledge_base_id=knowledge_base_id,
            chunks_created=len(chunks),
            status="success"
        )

    async def delete_document(self, document_id: str, knowledge_base_id: str = "default"):
        """Delete a document and all its chunks"""
        # Note: This is a simplified version
        # In production, you'd want to query for all chunk IDs first
        await self.vectorstore.delete_document(document_id, knowledge_base_id)

    async def list_documents(
        self,
        knowledge_base_id: str = "default",
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List documents in a knowledge base"""
        # This is a placeholder - ChromaDB doesn't have direct document listing
        # You'd need to maintain a separate index or use metadata queries
        count = await self.vectorstore.get_collection_count(knowledge_base_id)
        return [{"knowledge_base_id": knowledge_base_id, "document_count": count}]

    async def _extract_text(self, file_content: bytes, filename: str) -> str:
        """Extract text from various file formats"""
        file_type = self._get_file_type(filename)

        if file_type in ["txt", "md"]:
            return file_content.decode("utf-8")

        elif file_type == "pdf":
            # Placeholder - integrate with PyPDF2 or similar
            try:
                import PyPDF2
                pdf_file = io.BytesIO(file_content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                return text
            except ImportError:
                return "PDF processing not available. Install PyPDF2."

        elif file_type == "json":
            import json
            data = json.loads(file_content.decode("utf-8"))
            return json.dumps(data, indent=2)

        elif file_type == "csv":
            # Placeholder - integrate with pandas or csv module
            return file_content.decode("utf-8")

        else:
            return file_content.decode("utf-8", errors="ignore")

    def _chunk_text(
        self,
        text: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> List[str]:
        """Chunk text into smaller pieces with overlap"""
        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]

            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind(".")
                last_newline = chunk.rfind("\n")
                break_point = max(last_period, last_newline)

                if break_point > chunk_size // 2:
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1

            chunks.append(chunk.strip())
            start = end - chunk_overlap

        return [c for c in chunks if c]  # Remove empty chunks

    def _get_file_type(self, filename: str) -> str:
        """Get file type from filename"""
        return filename.split(".")[-1].lower() if "." in filename else "unknown"
