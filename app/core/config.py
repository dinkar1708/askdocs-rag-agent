"""Application configuration"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/askdocs"

    # LLM Provider
    LLM_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""
    OLLAMA_MODEL: str = "llama3.2"
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # Azure OpenAI (optional)
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_KEY: str = ""
    AZURE_OPENAI_DEPLOYMENT: str = ""

    # API
    API_KEY: str = "test-key"

    # App
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Reranking Configuration
    RERANKING_ENABLED: bool = True
    RERANKING_MODEL: str = "BAAI/bge-reranker-v2-m3"
    RETRIEVAL_INITIAL_K: int = 30  # Candidates to retrieve in stage 1
    RETRIEVAL_FINAL_K: int = 5     # Final results after reranking

    # Semantic Chunking Configuration
    SEMANTIC_CHUNKING_ENABLED: bool = False  # Default to False for backward compatibility
    SEMANTIC_SIMILARITY_THRESHOLD: float = 0.5
    MIN_CHUNK_SIZE: int = 200
    MAX_CHUNK_SIZE: int = 1000

    # Slack Integration
    SLACK_ENABLED: bool = False
    SLACK_BOT_TOKEN: str = ""
    SLACK_SIGNING_SECRET: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
