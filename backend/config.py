# backend/config.py

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # OpenRouter
    openrouter_api_key: str

    # Vector DB (ChromaDB — local)
    chroma_persist_dir: str = "./chroma_db"
    collection_name: str = "nyayasetu_statutes"

    # Models
    llm_model: str = "openai/gpt-3.5-turbo"
    embedding_model: str = "all-MiniLM-L6-v2"

    # RAG
    retrieval_top_k: int = 3
    max_iterations: int = 3

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    cors_origins: list[str] = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()