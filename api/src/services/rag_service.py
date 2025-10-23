from typing import List, Dict, Any, Optional
from services.vectorstore_service import VectorStoreService
from services.claude_service import ClaudeService
from models.schemas import RAGQueryResponse, SearchResponse, SearchResult

class RAGService:
    """Service for RAG (Retrieval-Augmented Generation) operations"""

    def __init__(self, vectorstore: VectorStoreService, claude: ClaudeService):
        self.vectorstore = vectorstore
        self.claude = claude

    async def query(
        self,
        query: str,
        knowledge_base_id: str = "default",
        top_k: int = 5,
        model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.7,
        include_sources: bool = True
    ) -> RAGQueryResponse:
        """
        Query the RAG system.
        Retrieves relevant documents and generates an answer using Claude.
        """

        # Retrieve relevant documents
        search_results = await self.vectorstore.search(
            query=query,
            knowledge_base_id=knowledge_base_id,
            top_k=top_k
        )

        # Build context from retrieved documents
        context = self._build_context(search_results)

        # Build prompt
        system_prompt = """You are a helpful AI assistant that answers questions based on the provided context.
If the context doesn't contain relevant information, say so clearly.
Always cite your sources when possible."""

        prompt = f"""Context:
{context}

Question: {query}

Please provide a comprehensive answer based on the context above."""

        # Generate response with Claude
        claude_response = await self.claude.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            temperature=temperature,
            max_tokens=4096
        )

        # Prepare sources if requested
        sources = None
        if include_sources:
            sources = [
                {
                    "content": result["content"],
                    "metadata": result["metadata"],
                    "score": result["score"]
                }
                for result in search_results
            ]

        return RAGQueryResponse(
            answer=claude_response["response"],
            sources=sources,
            usage=claude_response["usage"],
            model=claude_response["model"]
        )

    async def search(
        self,
        query: str,
        knowledge_base_id: str = "default",
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> SearchResponse:
        """Search for documents without generation"""

        search_results = await self.vectorstore.search(
            query=query,
            knowledge_base_id=knowledge_base_id,
            top_k=top_k,
            filter=filter
        )

        results = [
            SearchResult(
                content=result["content"],
                metadata=result["metadata"],
                score=result["score"]
            )
            for result in search_results
        ]

        return SearchResponse(
            results=results,
            total=len(results),
            query=query
        )

    async def list_knowledge_bases(self) -> List[str]:
        """List all available knowledge bases"""
        return await self.vectorstore.list_collections()

    def _build_context(self, search_results: List[Dict[str, Any]]) -> str:
        """Build context string from search results"""
        context_parts = []

        for i, result in enumerate(search_results, 1):
            source_info = ""
            if "source" in result["metadata"]:
                source_info = f" (Source: {result['metadata']['source']})"

            context_parts.append(
                f"[{i}]{source_info}\n{result['content']}\n"
            )

        return "\n".join(context_parts)
