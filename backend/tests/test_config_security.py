import pytest
from app.core.config import Settings


def test_development_config_defaults():
    """Verify default settings initialize cleanly in development mode."""
    settings = Settings(app_env="development")
    assert settings.app_env == "development"
    assert settings.jwt_secret == "change-this-development-secret-32"
    assert settings.jwt_algorithm == "HS256"
    assert settings.jwt_access_token_expire_minutes == 60


def test_production_config_rejects_default_secret():
    """Verify production mode strictly rejects default/weak secrets."""
    with pytest.raises(ValueError, match="CRITICAL CONFIGURATION ERROR"):
        Settings(
            app_env="production",
            jwt_secret="change-this-development-secret-32",
        )


def test_production_config_rejects_short_secret():
    """Verify production mode rejects secrets shorter than 16 characters."""
    with pytest.raises(ValueError, match="CRITICAL CONFIGURATION ERROR"):
        Settings(
            app_env="production",
            jwt_secret="short-sec",
        )


def test_production_config_accepts_strong_secret():
    """Verify production mode accepts strong secrets."""
    settings = Settings(
        app_env="production",
        jwt_secret="super-strong-production-signing-key-9988",
    )
    assert settings.app_env == "production"
    assert settings.jwt_secret == "super-strong-production-signing-key-9988"


def test_config_alias_resolution():
    """Verify compatibility aliases for Render and standard cloud environments."""
    settings = Settings(
        app_env="development",
        SECRET_KEY="alias-secret-key-for-auth-testing",
        ACCESS_TOKEN_EXPIRE_MINUTES=120,
        GEMINI_API_KEY="test-gemini-key",
    )
    assert settings.jwt_secret == "alias-secret-key-for-auth-testing"
    assert settings.jwt_access_token_expire_minutes == 120
    assert settings.llm_api_key == "test-gemini-key"
