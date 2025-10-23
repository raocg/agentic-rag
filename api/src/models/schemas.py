from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class DocumentInput(BaseModel):
    content: str = Field(..., description="Content of the document")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata for the document")
    knowledge_base_id: str = Field(default="default", description="Knowledge base identifier")

class RAGQueryRequest(BaseModel):
    query: str = Field(..., description="Query to search for")
    knowledge_base_id: str = Field(default="default", description="Knowledge base to query")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of documents to retrieve")
    include_sources: bool = Field(default=True, description="Include source documents in response")
    model: str = Field(default="claude-3-5-sonnet-20241022", description="Claude model to use")
    temperature: float = Field(default=0.7, ge=0, le=1, description="Temperature for generation")

class RAGQueryResponse(BaseModel):
    answer: str = Field(..., description="Generated answer")
    sources: Optional[List[Dict[str, Any]]] = Field(default=None, description="Source documents")
    usage: Optional[Dict[str, int]] = Field(default=None, description="Token usage")
    model: str = Field(..., description="Model used")

class AgentTaskRequest(BaseModel):
    task: str = Field(..., description="Task for the agent to execute")
    model: str = Field(default="claude-3-5-sonnet-20241022", description="Claude model to use")
    max_iterations: int = Field(default=5, ge=1, le=20, description="Maximum iterations for the agent")
    knowledge_base_id: Optional[str] = Field(default=None, description="Optional knowledge base to use")
    tools: Optional[List[str]] = Field(default_factory=list, description="Tools available to the agent")

class AgentTaskResponse(BaseModel):
    result: str = Field(..., description="Result of the agent task")
    steps: List[Dict[str, Any]] = Field(..., description="Steps taken by the agent")
    usage: Dict[str, int] = Field(..., description="Total token usage")
    success: bool = Field(..., description="Whether the task was completed successfully")

class DocumentUploadResponse(BaseModel):
    document_id: str = Field(..., description="ID of the uploaded document")
    knowledge_base_id: str = Field(..., description="Knowledge base the document was added to")
    chunks_created: int = Field(..., description="Number of chunks created from the document")
    status: str = Field(..., description="Status of the upload")

class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    knowledge_base_id: str = Field(default="default", description="Knowledge base to search")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results to return")
    filter: Optional[Dict[str, Any]] = Field(default=None, description="Metadata filters")

class SearchResult(BaseModel):
    content: str = Field(..., description="Content of the result")
    metadata: Dict[str, Any] = Field(..., description="Metadata of the result")
    score: float = Field(..., description="Relevance score")

class SearchResponse(BaseModel):
    results: List[SearchResult] = Field(..., description="Search results")
    total: int = Field(..., description="Total number of results")
    query: str = Field(..., description="Original query")
