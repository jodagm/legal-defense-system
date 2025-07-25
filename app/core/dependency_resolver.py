"""
Dependency resolver - clean dependency injection
"""
import os
import streamlit as st
from typing import Dict, Any, Optional
from pathlib import Path

from app.config.constants import REQUIRED_DIRECTORIES, CLAUDE_MODEL
from app.utils.file_utils import ensure_directories_exist


class DependencyResolutionError(Exception):
    """Raised when critical dependencies cannot be resolved"""
    pass


def resolve_dependencies() -> Dict[str, Any]:
    """Resolve all application dependencies with proper error handling"""
    dependencies = {}
    
    # File system dependencies - always required
    dependencies['data_paths'] = _resolve_data_paths()
    
    # Claude API dependency - may be None if not available
    dependencies['claude_client'] = _resolve_claude_client()
    
    # Configuration dependencies
    dependencies['settings'] = _resolve_settings()
    
    return dependencies


def _resolve_data_paths() -> Dict[str, Path]:
    """Resolve and create required data directories"""
    ensure_directories_exist(REQUIRED_DIRECTORIES)
    
    return {
        'upload': Path("data/uploaded_documents"),
        'processed': Path("data/processed"),
        'summaries': Path("data/summaries"),
        'metadata': Path("data/metadata"),
        'logs': Path("data/logs")
    }


def _resolve_claude_client() -> Optional[Any]:
    """Resolve Claude API client - returns None if not available"""
    try:
        import anthropic
        
        api_key = _get_claude_api_key()
        if not api_key:
            return None
        
        return anthropic.Anthropic(api_key=api_key)
    
    except ImportError:
        return None


def _get_claude_api_key() -> str:
    """Get Claude API key from multiple sources"""
    # Try Streamlit secrets first
    try:
        if hasattr(st, 'secrets') and 'CLAUDE_API_KEY' in st.secrets:
            return st.secrets["CLAUDE_API_KEY"]
    except (KeyError, FileNotFoundError, AttributeError):
        pass
    
    # Try environment variable
    if api_key := os.getenv("CLAUDE_API_KEY"):
        return api_key
    
    return ""


def _resolve_settings() -> Dict[str, Any]:
    """Resolve application settings"""
    return {
        'claude_model': CLAUDE_MODEL,
        'app_version': '3.0.0',
        'debug_mode': os.getenv('DEBUG', 'False').lower() == 'true'
    }
