from functools import lru_cache

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="ShikshaSetu Backend", validation_alias=AliasChoices("APP_NAME", "app_name"))
    app_env: str = Field(default="development", validation_alias=AliasChoices("APP_ENV", "app_env", "ENVIRONMENT"))
    debug: bool = Field(default=False, validation_alias=AliasChoices("DEBUG", "debug"))
    mongodb_uri: str = Field(default="mongodb://localhost:27017", validation_alias=AliasChoices("MONGODB_URI", "DATABASE_URL"))
    mongodb_database: str = Field(default="shikshasetu", validation_alias=AliasChoices("MONGODB_DATABASE", "mongodb_database"))
    api_prefix: str = Field(default="/api/v1", validation_alias=AliasChoices("API_PREFIX", "api_prefix"))
    jwt_secret: str = Field(
        default="change-this-development-secret-32",
        validation_alias=AliasChoices("JWT_SECRET", "SECRET_KEY"),
    )
    jwt_algorithm: str = Field(default="HS256", validation_alias=AliasChoices("JWT_ALGORITHM", "jwt_algorithm"))
    jwt_access_token_expire_minutes: int = Field(
        default=60,
        gt=0,
        le=1440,
        validation_alias=AliasChoices("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "ACCESS_TOKEN_EXPIRE_MINUTES"),
    )
    cors_allowed_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:3002",
            "http://localhost:5173",
            "http://localhost:5174",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            "http://127.0.0.1:3002",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174",
        ],
        validation_alias=AliasChoices("CORS_ALLOWED_ORIGINS", "cors_allowed_origins"),
    )

    # Phase 6: AI & Document Processing
    llm_provider: str = Field(default="mock", validation_alias=AliasChoices("LLM_PROVIDER", "llm_provider"))
    llm_api_key: str = Field(default="", validation_alias=AliasChoices("LLM_API_KEY", "GEMINI_API_KEY", "OPENAI_API_KEY"))
    llm_model: str = Field(default="gpt-3.5-turbo", validation_alias=AliasChoices("LLM_MODEL", "GEMINI_MODEL"))
    embedding_provider: str = Field(default="mock", validation_alias=AliasChoices("EMBEDDING_PROVIDER", "embedding_provider"))
    embedding_model: str = Field(default="mock-embedding", validation_alias=AliasChoices("EMBEDDING_MODEL", "embedding_model"))
    embedding_dimension: int = Field(default=384, validation_alias=AliasChoices("EMBEDDING_DIMENSION", "embedding_dimension"))
    
    # Document processing limits
    max_upload_size_mb: int = Field(default=50, validation_alias="MAX_UPLOAD_SIZE_MB")
    chunk_size: int = Field(default=500, validation_alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=100, validation_alias="CHUNK_OVERLAP")
    max_questions_per_generation: int = Field(default=20, validation_alias="MAX_QUESTIONS_PER_GENERATION")
    generation_retry_count: int = Field(default=3, validation_alias="GENERATION_RETRY_COUNT")

    # RAG tuning — P0 upgrade
    embedding_api_key: str = Field(default="", validation_alias="EMBEDDING_API_KEY")
    rag_top_k_keyword: int = Field(default=8, validation_alias="RAG_TOP_K_KEYWORD")
    rag_top_k_vector: int = Field(default=8, validation_alias="RAG_TOP_K_VECTOR")
    rag_chat_vector_enabled: bool = Field(default=True, validation_alias="RAG_CHAT_VECTOR_ENABLED")
    rag_rerank_top_k: int = Field(default=4, validation_alias="RAG_RERANK_TOP_K")
    rag_groundedness_threshold: float = Field(default=0.25, validation_alias="RAG_GROUNDEDNESS_THRESHOLD")
    rag_enable_query_rewrite: bool = Field(default=False, validation_alias="RAG_ENABLE_QUERY_REWRITE")
    rag_mmr_lambda: float = Field(default=0.7, validation_alias="RAG_MMR_LAMBDA")
    rag_mcq_top_k: int = Field(default=6, validation_alias="RAG_MCQ_TOP_K")
    
    # MongoDB Connection Pool Settings
    mongodb_max_pool_size: int = Field(default=50, validation_alias="MONGODB_MAX_POOL_SIZE")
    mongodb_min_pool_size: int = Field(default=10, validation_alias="MONGODB_MIN_POOL_SIZE")
    mongodb_max_idle_time_ms: int = Field(default=30000, validation_alias="MONGODB_MAX_IDLE_TIME_MS")
    mongodb_server_selection_timeout_ms: int = Field(default=3000, validation_alias="MONGODB_SERVER_SELECTION_TIMEOUT_MS")
    # Phase 3A: iGOT Karmayogi Ecosystem Integration
    igot_integration_mode: str = Field(default="prototype", validation_alias="IGOT_INTEGRATION_MODE")
    igot_api_base_url: str = Field(default="", validation_alias="IGOT_API_BASE_URL")
    igot_client_id: str = Field(default="", validation_alias="IGOT_CLIENT_ID")
    igot_client_secret: str = Field(default="", validation_alias="IGOT_CLIENT_SECRET")

    # Phase 6D: Email / SMTP Configuration
    EMAIL_HOST: str = Field(default="", validation_alias=AliasChoices("EMAIL_HOST", "SMTP_HOST", "email_host"))
    EMAIL_PORT: int = Field(default=587, validation_alias=AliasChoices("EMAIL_PORT", "SMTP_PORT", "email_port"))
    EMAIL_USER: str = Field(default="", validation_alias=AliasChoices("EMAIL_USER", "SMTP_USER", "email_user"))
    EMAIL_PASSWORD: str = Field(default="", validation_alias=AliasChoices("EMAIL_PASSWORD", "SMTP_PASSWORD", "email_password"))
    EMAIL_FROM: str = Field(default="noreply@shikshasetu.com", validation_alias=AliasChoices("EMAIL_FROM", "SMTP_FROM", "email_from"))

    @property
    def email_host(self) -> str:
        return self.EMAIL_HOST

    @property
    def email_port(self) -> int:
        return self.EMAIL_PORT

    @property
    def email_user(self) -> str:
        return self.EMAIL_USER

    @property
    def email_password(self) -> str:
        return self.EMAIL_PASSWORD

    @property
    def email_from(self) -> str:
        return self.EMAIL_FROM

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        """Ensure critical secrets are explicitly supplied and non-default in production."""
        is_production = self.app_env.lower() in ("production", "prod")
        if is_production:
            insecure_defaults = (
                "change-this-development-secret-32",
                "development-secret",
                "secret",
                "changeme",
            )
            if not self.jwt_secret or self.jwt_secret in insecure_defaults or len(self.jwt_secret) < 32:
                raise ValueError(
                    "CRITICAL CONFIGURATION ERROR: In production mode (APP_ENV=production), "
                    "JWT_SECRET (or SECRET_KEY) must be securely set via environment variable "
                    "with at least 32 characters (256-bit entropy)."
                )
            # Force debug to False in production mode to prevent information leakage
            self.debug = False
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()

