"""Application configuration"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings

    All settings must be provided via environment variables.
    Copy .env.example to .env.dev and configure your settings.
    """

    # Database - REQUIRED
    DATABASE_URL: str  # No default - must be set in env file

    # LLM Provider - REQUIRED
    LLM_PROVIDER: str  # No default - must be set in env file
    GEMINI_API_KEY: str = ""  # Optional - only needed if using Gemini
    OLLAMA_MODEL: str = "llama3.2"  # Has default for convenience
    OLLAMA_BASE_URL: str = "http://localhost:11434"  # Has default for convenience

    # Azure OpenAI (optional)
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_KEY: str = ""
    AZURE_OPENAI_DEPLOYMENT: str = ""

    # API - REQUIRED
    API_KEY: str  # No default - must be set in env file

    # App
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Reranking Configuration
    RERANKING_ENABLED: bool = True
    RERANKING_MODEL: str = "BAAI/bge-reranker-v2-m3"
    RETRIEVAL_INITIAL_K: int = 30  # Candidates to retrieve in stage 1
    RETRIEVAL_FINAL_K: int = 5     # Final results after reranking

    # Hybrid Search Configuration
    HYBRID_SEARCH_ENABLED: bool = True  # Enable BM25 + Vector + RRF hybrid search

    # Semantic Chunking Configuration
    SEMANTIC_CHUNKING_ENABLED: bool = False  # Default to False for backward compatibility
    SEMANTIC_SIMILARITY_THRESHOLD: float = 0.5
    MIN_CHUNK_SIZE: int = 200
    MAX_CHUNK_SIZE: int = 1000

    # Slack Integration
    SLACK_ENABLED: bool = False
    SLACK_BOT_TOKEN: str = ""
    SLACK_SIGNING_SECRET: str = ""

    # CORS Configuration
    # Comma-separated list of allowed origins
    # Defaults to localhost for development - override in production with env var
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080"

    class Config:
        # Load from .env.dev for development, or .env.test for testing
        # Can be overridden with environment variables
        env_file = ".env.dev"
        extra = "ignore"


settings = Settings()
