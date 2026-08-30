import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Config:
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./backend/data/chroma_db")
    
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")
    
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", 500))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", 50))
    
    TOP_K: int = int(os.getenv("TOP_K", 3))
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", 0.35))
    
    INGEST_API_KEY: str = os.getenv("INGEST_API_KEY", "sk_ingest_test")
    
    # Process ALLOWED_ORIGINS string into a list
    _allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:5500,http://localhost:3000,http://127.0.0.1:5500")
    ALLOWED_ORIGINS: List[str] = [origin.strip() for origin in _allowed_origins_str.split(",") if origin.strip()]

config = Config()
