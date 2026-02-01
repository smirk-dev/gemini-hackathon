"""API module initialization."""

try:
    from .app_new import app
except ImportError:
    try:
        from .app import app
    except ImportError:
        app = None

__all__ = [
    'app'
]
