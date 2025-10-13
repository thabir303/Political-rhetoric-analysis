"""
Configuration settings for the RAG-IR application.
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "RAG-IR API"
    app_version: str = "1.0.0"
    environment: str = "development"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # ChromaDB
    chroma_persist_directory: str = "./chroma_db"
    chroma_collection_name: str = "articles"
    
    # Embedding Model
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # LLM/Groq Settings (optional)
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    
    # CORS
    allowed_origins: str = "http://localhost:3000,http://localhost:8000"
    
    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # Allow extra fields from .env


# Global settings instance
settings = Settings()
