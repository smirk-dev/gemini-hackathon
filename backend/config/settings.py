"""
LegalMind Configuration Settings
Google Cloud / Gemini API Configuration
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # -------------------------------------------------------------------------
    # Gemini API Configuration
    # -------------------------------------------------------------------------
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    
    # -------------------------------------------------------------------------
    # Google Cloud Project Configuration
    # -------------------------------------------------------------------------
    google_cloud_project: str = ""
    google_application_credentials: Optional[str] = None
    
    # -------------------------------------------------------------------------
    # Firestore Configuration
    # -------------------------------------------------------------------------
    firestore_database: str = "(default)"
    
    # -------------------------------------------------------------------------
    # Cloud Storage Configuration
    # -------------------------------------------------------------------------
    gcs_bucket_name: str = "legalmind-contracts"
    gcs_contracts_folder: str = "contracts"
    gcs_documents_folder: str = "generated-documents"
    
    # -------------------------------------------------------------------------
    # Application Settings
    # -------------------------------------------------------------------------
    app_name: str = "LegalMind"
    app_env: str = "development"
    debug: bool = True
    
    # API Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Session Configuration
    session_timeout_minutes: int = 60
    max_tokens_per_request: int = 8192
    
    # Rate Limiting
    rate_limit_requests_per_minute: int = 30
    
    # -------------------------------------------------------------------------
    # Feature Flags
    # -------------------------------------------------------------------------
    enable_search_grounding: bool = True
    enable_thinking_logs: bool = True
    enable_citations: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.
    
    Returns:
        Settings: Application settings
    """
    return Settings()


def get_gemini_api_key() -> str:
    """Get the Gemini API key from settings.
    
    Returns:
        str: The Gemini API key
        
    Raises:
        ValueError: If the API key is not configured
    """
    settings = get_settings()
    if not settings.gemini_api_key:
        raise ValueError(
            "Missing required environment variable: GEMINI_API_KEY. "
            "Please set it in your .env file or environment."
        )
    return settings.gemini_api_key


def get_google_cloud_project() -> str:
    """Get the Google Cloud project ID.
    
    Returns:
        str: The Google Cloud project ID
        
    Raises:
        ValueError: If the project ID is not configured
    """
    settings = get_settings()
    if not settings.google_cloud_project:
        raise ValueError(
            "Missing required environment variable: GOOGLE_CLOUD_PROJECT. "
            "Please set it in your .env file or environment."
        )
    return settings.google_cloud_project


def get_gcs_bucket_name() -> str:
    """Get the Google Cloud Storage bucket name.
    
    Returns:
        str: The GCS bucket name
    """
    return get_settings().gcs_bucket_name


def validate_settings() -> bool:
    """Validate that all required settings are configured.
    
    Returns:
        bool: True if all settings are valid
        
    Raises:
        ValueError: If any required settings are missing
    """
    settings = get_settings()
    
    required = [
        ("GEMINI_API_KEY", settings.gemini_api_key),
        ("GOOGLE_CLOUD_PROJECT", settings.google_cloud_project),
    ]
    
    missing = [name for name, value in required if not value]
    
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Please check your .env file."
        )
    
    return True