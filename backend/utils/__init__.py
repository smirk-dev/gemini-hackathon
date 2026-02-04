"""Utilities module initialization."""

try:
    from .database_utils import get_connection
except ImportError:
    get_connection = None
    
from .thinking_log_viewer import render_thinking_log_viewer

__all__ = [
    'get_connection',
    'render_thinking_log_viewer'
]