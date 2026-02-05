"""
LegalMind Backend Entry Point
Run with: python main_new.py
"""

import uvicorn
from dotenv import load_dotenv
import os

# Load environment variables from .env.local first, then .env
load_dotenv(".env.local")
load_dotenv(".env")


def main():
    """Run the LegalMind API server."""
    from config.settings import get_settings
    
    settings = get_settings()
    
    # Cloud Run sets PORT env var, default to 8000 for local dev
    port = int(os.environ.get("PORT", 8000))
    
    print("=" * 60)
    print("LegalMind API Server")
    print("=" * 60)
    print(f"Project: {settings.google_cloud_project}")
    print(f"Debug Mode: {settings.debug}")
    print(f"Port: {port}")
    print(f"API Docs: http://localhost:{port}/docs")
    print("=" * 60)
    
    uvicorn.run(
        "api.app_new:app",
        host="0.0.0.0",
        port=port,
        reload=settings.debug,
        log_level="info" if settings.debug else "warning",
    )


if __name__ == "__main__":
    main()
