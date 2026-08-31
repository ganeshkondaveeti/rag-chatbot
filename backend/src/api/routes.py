import os
from fastapi import APIRouter, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, Dict, Any

from src.config import config
from src.pipeline.llm_client import LLMClient
from src.pipeline.prompt_builder import PromptBuilder
from src.pipeline.response_formatter import ResponseFormatter
from src.pipeline.retriever import Retriever, QueryPipeline
from src.ingestion.vectorstore import VectorStoreManager
from src.ingestion.embedder import Embedder

router = APIRouter()
security = HTTPBearer()

# Dependency Injection for API Key Auth
def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != config.INGEST_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return credentials.credentials

# Models
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    source_url: Optional[str] = None
    last_updated: Optional[str] = None
    refused: bool = False
    refusal_category: Optional[str] = None

# Global pipeline instances
_query_pipeline: Optional[QueryPipeline] = None
_llm_client: Optional[LLMClient] = None
_vectorstore_manager: Optional[VectorStoreManager] = None

def init_pipeline():
    global _query_pipeline, _llm_client, _vectorstore_manager
    print("Initializing pipeline components...")
    
    embedder = Embedder(model_name=config.EMBEDDING_MODEL)
    _vectorstore_manager = VectorStoreManager(embedder.embeddings)
    retriever = Retriever(_vectorstore_manager)
    _query_pipeline = QueryPipeline(retriever)
    _llm_client = LLMClient()

@router.post("/query", response_model=QueryResponse)
async def query_assistant(request: QueryRequest):
    if not _query_pipeline or not _llm_client:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
        
    # 1. Process query (Guardrails + Retrieve)
    pipeline_res = _query_pipeline.process_query(request.query)
    
    # 2. Check for refusal
    if pipeline_res.get("refused"):
        return QueryResponse(
            answer=pipeline_res["refusal_message"],
            refused=True,
            refusal_category=pipeline_res["refusal_category"]
        )
        
    # 3. Retrieve context chunks
    context_chunks = pipeline_res.get("context", [])
    
    # 4. Build prompt
    prompt = PromptBuilder.build_prompt(request.query, context_chunks)
    
    # 5. Generate LLM response
    try:
        raw_response = _llm_client.generate(prompt)
    except Exception as e:
        print(f"LLM generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate response")
        
    # 6. Format final response
    formatted_res = ResponseFormatter.format_response(raw_response, context_chunks)
    
    return QueryResponse(**formatted_res)

@router.post("/ingest/refresh")
async def ingest_refresh(api_key: str = Depends(verify_api_key)):
    """Triggers the full ingestion pipeline (scrape -> clean -> chunk -> embed -> store)"""
    from src.ingestion.ingest import main as run_ingestion
    try:
        # Running the ingestion script logic
        await run_ingestion()
        # Re-initialize the pipeline to pick up the new ChromaDB collection
        init_pipeline()
        return {"status": "success", "message": "Ingestion completed successfully."}
    except Exception as e:
        print(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@router.get("/health")
async def health_check():
    status = "healthy"
    # Basic check
    if not _query_pipeline or not _llm_client or not _vectorstore_manager:
        status = "uninitialized"
        
    return {"status": status}

@router.get("/status")
async def get_status():
    if not _vectorstore_manager:
        raise HTTPException(status_code=503, detail="Not initialized")
        
    try:
        count = _vectorstore_manager.db._collection.count()
    except Exception:
        count = 0
        
    return {
        "status": "ready",
        "chunks_stored": count,
    }
