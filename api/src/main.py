from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import os
from dotenv import load_dotenv

from routes import rag_router, agent_router, documents_router
from services.vectorstore_service import VectorStoreService
from services.claude_service import ClaudeService

load_dotenv()

app = FastAPI(
    title="Agentic RAG API",
    description="API for RAG and Agentic workflows with Claude integration",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
vectorstore_service = VectorStoreService()
claude_service = ClaudeService()

# Include routers
app.include_router(rag_router.router, prefix="/api/rag", tags=["RAG"])
app.include_router(agent_router.router, prefix="/api/agent", tags=["Agent"])
app.include_router(documents_router.router, prefix="/api/documents", tags=["Documents"])

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("Starting Agentic RAG API...")
    await vectorstore_service.initialize()
    print("✓ Vector store initialized")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("Shutting down Agentic RAG API...")

@app.get("/")
async def root():
    return {
        "message": "Agentic RAG API",
        "version": "1.0.0",
        "endpoints": {
            "rag": "/api/rag",
            "agent": "/api/agent",
            "documents": "/api/documents",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services": {
            "vectorstore": vectorstore_service.is_ready(),
            "claude": claude_service.is_ready()
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
