from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="ShikshaSetu Backend", validation_alias="APP_NAME")
    app_env: str = Field(default="development", validation_alias="APP_ENV")
    debug: bool = Field(default=False, validation_alias="DEBUG")
    mongodb_uri: str = Field(default="mongodb://localhost:27017", validation_alias="MONGODB_URI")
    mongodb_database: str = Field(default="shikshasetu", validation_alias="MONGODB_DATABASE")
    api_prefix: str = Field(default="/api/v1", validation_alias="API_PREFIX")
    jwt_secret: str = Field(default="change-this-development-secret-32", validation_alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=60, gt=0, le=1440, validation_alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")

    # Phase 6: AI & Document Processing
    llm_provider: str = Field(default="mock", validation_alias="LLM_PROVIDER")
    llm_api_key: str = Field(default="", validation_alias="LLM_API_KEY")
    llm_model: str = Field(default="gpt-3.5-turbo", validation_alias="LLM_MODEL")
    embedding_provider: str = Field(default="mock", validation_alias="EMBEDDING_PROVIDER")
    embedding_model: str = Field(default="mock-embedding", validation_alias="EMBEDDING_MODEL")
    embedding_dimension: int = Field(default=384, validation_alias="EMBEDDING_DIMENSION")
    
    # Document processing limits
    max_upload_size_mb: int = Field(default=50, validation_alias="MAX_UPLOAD_SIZE_MB")
    chunk_size: int = Field(default=500, validation_alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=100, validation_alias="CHUNK_OVERLAP")
    max_questions_per_generation: int = Field(default=5, validation_alias="MAX_QUESTIONS_PER_GENERATION")
    generation_retry_count: int = Field(default=3, validation_alias="GENERATION_RETRY_COUNT")
    # Phase 3A: iGOT Karmayogi Ecosystem Integration
    igot_integration_mode: str = Field(default="prototype", validation_alias="IGOT_INTEGRATION_MODE")
    igot_api_base_url: str = Field(default="", validation_alias="IGOT_API_BASE_URL")
    igot_client_id: str = Field(default="", validation_alias="IGOT_CLIENT_ID")
    igot_client_secret: str = Field(default="", validation_alias="IGOT_CLIENT_SECRET")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
