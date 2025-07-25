"""
Configuration and settings
"""
from .constants import (
    APP_TITLE,
    APP_VERSION,
    APP_ICON,
    CLAUDE_MODEL,
    REQUIRED_DIRECTORIES,
    MESSAGES,
    SUPPORTED_FILE_TYPES
)
from .page_config import configure_streamlit_page

__all__ = [
    'APP_TITLE',
    'APP_VERSION', 
    'APP_ICON',
    'CLAUDE_MODEL',
    'REQUIRED_DIRECTORIES',
    'MESSAGES',
    'SUPPORTED_FILE_TYPES',
    'configure_streamlit_page'
]
