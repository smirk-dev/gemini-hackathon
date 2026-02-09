"""
LegalMind Configuration Settings
Google Cloud / Gemini API Configuration
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator, Field
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # -------------------------------------------------------------------------
    # Gemini API Configuration
    # -------------------------------------------------------------------------
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    # Use Vertex AI by default - reads from USE_VERTEX_AI env var (true/false)
    use_vertex_ai: bool = Field(
        default=True,
        description="Use Vertex AI instead of public Gemini API. Set USE_VERTEX_AI=true/false in environment"
    )
    
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

    # Security Settings
    api_secret_key: str = ""
    allowed_origins: str = ""
    
    # API Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Session Configuration
    session_timeout_minutes: int = 60
    max_tokens_per_request: int = 8192
    
    # Rate Limiting
    rate_limit_requests_per_minute: int = 30

    # Caching
    response_cache_ttl_seconds: int = 60
    
    # -------------------------------------------------------------------------
    # Feature Flags
    # -------------------------------------------------------------------------
    enable_search_grounding: bool = True
    enable_thinking_logs: bool = True
    enable_citations: bool = True

    @field_validator("use_vertex_ai", mode="before")
    @classmethod
    def read_use_vertex_ai(cls, v):
        """Read USE_VERTEX_AI from environment variable."""
        # If called during init, v is the field default
        # Check environment variable first
        env_val = os.getenv("USE_VERTEX_AI", "true").lower()
        if env_val in ("true", "1", "yes"):
            return True
        elif env_val in ("false", "0", "no"):
            return False
        # Default to True (use Vertex AI) for production
        return True

    @field_validator("gemini_api_key", mode="after")
    @classmethod
    def validate_api_key(cls, v, info):
        """Validate API key is set if not using Vertex AI."""
        # Check if using Vertex AI from environment (default to true for production)
        use_vertex_ai = os.getenv("USE_VERTEX_AI", "true").lower() == "true"
        if not use_vertex_ai and not v:
            # Only warn, don't fail - Vertex AI might use ADC
            print("⚠️ GEMINI_API_KEY not set - will attempt Vertex AI or ADC authentication")
        return v or ""

    @field_validator("google_cloud_project", mode="after")
    @classmethod
    def validate_project(cls, v):
        """Validate Google Cloud project is configured."""
        if not v:
            raise ValueError(
                "Missing required environment variable: GOOGLE_CLOUD_PROJECT. "
                "Please set it in your .env.local file."
            )
        return v
    
    def model_post_init(self, __context):
        """Ensure USE_VERTEX_AI environment variable is respected after initialization."""
        env_val = os.getenv("USE_VERTEX_AI", "true").lower()
        if env_val in ("true", "1", "yes"):
            self.use_vertex_ai = True
            print(f"✅ USE_VERTEX_AI=true from environment - using Vertex AI")
        elif env_val in ("false", "0", "no"):
            self.use_vertex_ai = False
            print(f"⚠️ USE_VERTEX_AI=false from environment - using public Gemini API")
        else:
            self.use_vertex_ai = True
            print(f"✅ USE_VERTEX_AI not set, defaulting to True - using Vertex AI")
    
    class Config:
        env_file = ".env.local"
        env_file_encoding = "utf-8"
        case_sensitive = False
        # Extra config to ensure environment variables are read
        extra = "allow"
        # Populate from environment variables even if defaults are set
        validate_assignment = True


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
        ValueError: If the API key is not configured and not using Vertex AI
    """
    settings = get_settings()
    if settings.use_vertex_ai:
        return ""
    return settings.gemini_api_key


def get_google_cloud_project() -> str:
    """Get the Google Cloud project ID.
    
    Returns:
        str: The Google Cloud project ID
        
    Raises:
        ValueError: If the project ID is not configured
    """
    settings = get_settings()
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
    
    # GOOGLE_CLOUD_PROJECT is always required
    if not settings.google_cloud_project:
        raise ValueError(
            "Missing required environment variable: GOOGLE_CLOUD_PROJECT. "
            "Please check your .env file."
        )
    
    # API key is only required if not using Vertex AI
    if not settings.use_vertex_ai and not settings.gemini_api_key:
        raise ValueError(
            "Missing required environment variable: GEMINI_API_KEY. "
            "Please set it in your .env file or set USE_VERTEX_AI=true to use Vertex AI."
        )
    
    return True