"""FastAPI application entry point"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.documents import router as documents_router
from app.api.questions import router as questions_router
from app.api.sessions import router as sessions_router
from app.api.extraction import router as extraction_router
from app.api.slack import router as slack_router
from app.core.config import settings

app = FastAPI(
    title="AskDocs RAG Agent",
    description="Document Q&A with grounded, cited answers",
    version="0.1.0"
)

# CORS middleware - configured from environment
# Parse comma-separated origins from config
allowed_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,  # Set to False when using allow_origins (browsers reject credentials with *)
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Content-Type", "X-API-Key"],
)

# Include routers
app.include_router(documents_router)
app.include_router(questions_router)
app.include_router(sessions_router)
app.include_router(extraction_router)
app.include_router(slack_router)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "AskDocs API",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "service": "askdocs-rag-agent",
        "version": "0.1.0"
    }
