from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import ModelNames, GlobalVariables


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "development"
    log_level: str = "INFO"

    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_anon_key: str = ""
    database_url: str = ""

    openrouter_api_key: str = ""
    embedding_model: str = ModelNames.EMBEDDING
    embedding_dimension: int = GlobalVariables.EMBEDDING_DIMENSION
    embedding_version: str = GlobalVariables.EMBEDDING_VERSION

    gemini_api_key: str = ""
    gemini_model_name: str = ModelNames.GEMINI

    pi_agent_api_key: str = ""
    pi_agent_base_url: Optional[str] = None
    max_agent_iterations: int = 2

    ollama_cloud_api_key: str = ""
    ollama_cloud_base_url: str = ""
    ollama_cloud_model_name: str = ModelNames.OLLAMA

    ollama_local_base_url: str = "http://localhost:11434"
    ollama_local_model_name: str = "llama3.1"

    reranker_enabled: bool = True
    reranker_provider: str = "cohere"
    reranker_model_name: str = ModelNames.RERANKER
    cohere_api_key: str = ""
    jina_api_key: str = ""
    voyageai_api_key: str = ""

    chunk_target_tokens: int = GlobalVariables.CHUNK_TARGET_TOKENS
    chunk_min_tokens: int = GlobalVariables.CHUNK_MIN_TOKENS
    chunk_max_tokens: int = GlobalVariables.CHUNK_MAX_TOKENS
    chunk_overlap_tokens: int = GlobalVariables.CHUNK_OVERLAP_TOKENS

    vector_top_k: int = GlobalVariables.VECTOR_TOP_K
    lexical_top_k: int = GlobalVariables.LEXICAL_TOP_K
    fusion_top_k: int = GlobalVariables.FUSION_TOP_K
    rerank_top_k: int = GlobalVariables.RERANK_TOP_K
    final_context_chunks: int = GlobalVariables.FINAL_CONTEXT_CHUNKS
    similarity_threshold: float = GlobalVariables.SIMILARITY_THRESHOLD

    retrieval_cache_ttl: int = 300

    transcripts_repo_path: str = "../lennys-podcast-transcripts"
    ingestion_batch_limit: int = Field(default=0, ge=0)
    embedding_batch_size: int = Field(default=100, gt=0)

    frontend_origin: str = "http://localhost:3000"


settings = Settings()
