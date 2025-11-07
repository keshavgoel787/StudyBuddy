from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str

    # Google OAuth
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 168  # 1 week

    # AI APIs
    gemini_api_key: str
    groq_api_key: str | None = None
    openai_api_key: str | None = None

    # Frontend
    frontend_url: str

    # File Upload
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 10

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
