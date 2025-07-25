"""
Streamlit page configuration
"""
import streamlit as st

from app.config.constants import APP_TITLE, APP_ICON


def configure_streamlit_page() -> None:
    """Configure Streamlit page settings and styles"""
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    _apply_custom_css()


def _apply_custom_css() -> None:
    """Apply custom CSS styles"""
    st.markdown("""
    <style>
    /* Clean, professional styling */
    .main-header {
        background: linear-gradient(90deg, #1f4e79, #2d5a8b);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .status-metric {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #007bff;
        margin: 0.5rem 0;
    }
    
    .success-message {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #c3e6cb;
    }
    
    .warning-message {
        background: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #ffeaa7;
    }
    
    .error-message {
        background: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #f5c6cb;
    }
    </style>
    """, unsafe_allow_html=True)
