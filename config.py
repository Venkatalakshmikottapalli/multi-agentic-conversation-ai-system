import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional

class Settings(BaseSettings):
    """Application settings configuration."""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid"
    )
    
    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "your_openai_api_key_here")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    
    # Database Configuration
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./crm_chatbot.db")
    
    # Vector Database Configuration
    chroma_db_path: str = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    
    # API Configuration
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your_secret_key_here_change_in_production")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # RAG Configuration
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_retrieval_docs: int = 5
    
    # Chat Configuration
    max_conversation_history: int = 50
    default_temperature: float = 0.7
    max_tokens: int = 1000
    
    # Embedding Model
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

# Global settings instance
settings = Settings() 