from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import config
from src.api.routes import router as api_router, init_pipeline

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize the LLM pipeline, vectorstore and models
    init_pipeline()
    yield
    # Shutdown: Clean up resources if necessary
    pass

app = FastAPI(
    title="Mutual Fund FAQ Assistant API",
    description="Backend API for the facts-only HDFC Mutual Fund chatbot",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(api_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
