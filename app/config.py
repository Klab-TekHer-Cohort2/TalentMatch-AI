from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "TalentMatch AI"
    environment: str = "development"
    secret_key: str = "dev-secret-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    reset_token_expire_minutes: int = 60
    email_verification_expire_minutes: int = 24 * 60

    database_url: str = "sqlite:///./talentmatch.db"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    frontend_url: str = "http://localhost:5173"

    upload_dir: str = "uploads"
    max_upload_mb: int = 5

    min_apply_match_score: float = 50.0

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-5-20250929"
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_backend: str = "auto"

    chroma_dir: str = "./chroma_data"
    vector_collection: str = "courses"
    rag_top_k: int = 4

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "TalentMatch AI"
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
