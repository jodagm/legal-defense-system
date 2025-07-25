"""
Legal Defense System - Clean Architecture Entry Point
"""
import streamlit as st
from pathlib import Path

from app.core.app_factory import create_legal_app
from app.core.dependency_resolver import resolve_dependencies
from app.core.error_handler import handle_startup_error
from app.config.page_config import configure_streamlit_page
from app.config.constants import APP_VERSION


def main() -> None:
    """Application entry point - single responsibility"""
    try:
        configure_streamlit_page()
        dependencies = resolve_dependencies()
        app = create_legal_app(dependencies)
        app.run()
    except Exception as e:
        handle_startup_error(e)


if __name__ == "__main__":
    main()
