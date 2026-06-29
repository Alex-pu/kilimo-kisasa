import json

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Any
from typing import Optional


class Settings(BaseSettings):
    # API Configuration
    api_title: str = "Kilimo Kisasa API"
    api_version: str = "1.0.0"
    api_description: str = "Agricultural Social Media Platform"
    debug: bool = True
    environment: str = "development"
    
    # Database
    database_url: str = "postgresql://kisasa_user:kisasa_password@localhost:5432/kisasa_db"
    sqlalchemy_echo: bool = True
    
    # Firebase
    firebase_project_id: str
    firebase_api_key: str
    firebase_auth_domain: str
    firebase_storage_bucket: str
    firebase_credentials_path: str = "./firebase-credentials.json"
    firebase_credentials_json: Optional[str] = None

    # Cloudinary
    cloudinary_url: Optional[str] = None
    
    # JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # CORS
    cors_origins: Any = ["http://localhost:3000", "http://localhost:8080"]
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Uploads
    max_upload_bytes: int = 5 * 1024 * 1024

    # Jack assistant fallback
    grok_api_key: Optional[str] = None
    jack_grok_fallback_enabled: bool = True
    jack_grok_fallback_model: str = "grok-latest"
    jack_grok_base_url: str = "https://api.x.ai/v1"
    openai_api_key: Optional[str] = None
    jack_codex_fallback_enabled: bool = True
    jack_codex_fallback_model: str = "gpt-4.1-mini"
    jack_codex_fallback_timeout_seconds: int = 20

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value: Any) -> Any:
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "1", "yes", "on"}:
                return True
            if normalized in {"false", "0", "no", "off"}:
                return False
            if normalized in {"release", "production", "prod"}:
                return False
            if normalized in {"debug", "development", "dev"}:
                return True
        return value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            normalized = value.strip()
            if not normalized:
                return []
            if normalized.startswith("["):
                parsed = json.loads(normalized)
                return [str(item).strip() for item in parsed if str(item).strip()]
            return [item.strip() for item in normalized.split(",") if item.strip()]
        return [str(value).strip()]

    @field_validator("cors_origins", mode="after")
    @classmethod
    def include_mobile_dev_origins(cls, value: list[str]) -> list[str]:
        dev_origins = [
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            "http://127.0.0.1:3002",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:3002",
            "http://localhost:5173",
            "http://10.0.2.2:3000",
            "http://10.0.2.2:3001",
            "http://10.0.2.2:5173",
            "capacitor://localhost",
            "ionic://localhost",
            "http://localhost",
            "https://localhost",
        ]
        return list(dict.fromkeys([*value, *dev_origins]))
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


settings = Settings()
