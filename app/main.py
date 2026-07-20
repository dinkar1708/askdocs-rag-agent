"""FastAPI application entry point"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.documents import router as documents_router
from app.api.questions import router as questions_router

app = FastAPI(
    title="AskDocs RAG Agent",
    description="Document Q&A with grounded, cited answers",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents_router)
app.include_router(questions_router)


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
