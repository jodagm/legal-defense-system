
"""
Core application components
"""
from .app_factory import create_legal_app
from .legal_app import LegalApp
from .dependency_resolver import resolve_dependencies
from .error_handler import (
    ApplicationError,
    APIError, 
    DocumentProcessingError,
    SearchError,
    handle_startup_error,
    handle_component_error
)

__all__ = [
    'create_legal_app',
    'LegalApp',
    'resolve_dependencies',
    'ApplicationError',
    'APIError', 
    'DocumentProcessingError',
    'SearchError',
    'handle_startup_error',
    'handle_component_error'
]
