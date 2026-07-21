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

    # API
    API_KEY: str = "test-key"

    # App
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
