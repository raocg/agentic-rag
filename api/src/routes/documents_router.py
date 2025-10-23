from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from typing import Optional, List
from models.schemas import DocumentInput, DocumentUploadResponse
from services.document_service import DocumentService
from services.vectorstore_service import VectorStoreService

router = APIRouter()

def get_document_service():
    """Dependency to get Document service instance"""
    vectorstore = VectorStoreService()
    return DocumentService(vectorstore)

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    knowledge_base_id: str = Form(default="default"),
    metadata: Optional[str] = Form(default="{}"),
    doc_service: DocumentService = Depends(get_document_service)
):
    """
    Upload a document to the knowledge base.
    Supports: txt, pdf, md, json, csv
    """
    try:
        import json
        metadata_dict = json.loads(metadata) if metadata else {}

        content = await file.read()
        response = await doc_service.upload_file(
            file_content=content,
            filename=file.filename,
            knowledge_base_id=knowledge_base_id,
            metadata=metadata_dict
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add-text", response_model=DocumentUploadResponse)
async def add_text_document(
    document: DocumentInput,
    doc_service: DocumentService = Depends(get_document_service)
):
    """
    Add a text document directly to the knowledge base.
    """
    try:
        response = await doc_service.add_text(
            content=document.content,
            knowledge_base_id=document.knowledge_base_id,
            metadata=document.metadata
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-upload")
async def batch_upload_documents(
    files: List[UploadFile] = File(...),
    knowledge_base_id: str = Form(default="default"),
    doc_service: DocumentService = Depends(get_document_service)
):
    """
    Upload multiple documents at once.
    """
    try:
        results = []
        for file in files:
            content = await file.read()
            response = await doc_service.upload_file(
                file_content=content,
                filename=file.filename,
                knowledge_base_id=knowledge_base_id,
                metadata={}
            )
            results.append(response)

        return {
            "total_uploaded": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete/{document_id}")
async def delete_document(
    document_id: str,
    knowledge_base_id: str = "default",
    doc_service: DocumentService = Depends(get_document_service)
):
    """Delete a document from the knowledge base"""
    try:
        await doc_service.delete_document(document_id, knowledge_base_id)
        return {"status": "success", "message": f"Document {document_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_documents(
    knowledge_base_id: str = "default",
    limit: int = 100,
    doc_service: DocumentService = Depends(get_document_service)
):
    """List all documents in a knowledge base"""
    try:
        documents = await doc_service.list_documents(knowledge_base_id, limit)
        return {"documents": documents, "total": len(documents)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
