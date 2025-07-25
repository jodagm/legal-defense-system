"""
Centralized error handling
"""
import streamlit as st
import traceback
from typing import Any


class ApplicationError(Exception):
    """Base application error"""
    pass


class APIError(ApplicationError):
    """API related errors"""
    pass


class DocumentProcessingError(ApplicationError):
    """Document processing related errors"""
    pass


class SearchError(ApplicationError):
    """Search related errors"""
    pass


def handle_startup_error(error: Exception) -> None:
    """Handle application startup errors"""
    st.error("❌ שגיאה באתחול המערכת")
    
    with st.expander("🔍 פרטי השגיאה", expanded=False):
        st.code(str(error))
        st.code(traceback.format_exc())
    
    st.markdown("""
    ### 💡 פתרונות מוצעים:
    1. ודא שקובץ `.env` קיים עם `CLAUDE_API_KEY`
    2. התקן את כל החבילות הנדרשות: `pip install -r requirements.txt`
    3. בדוק שיש הרשאות כתיבה בתיקיית הפרויקט
    4. רענן את הדף ונסה שוב
    """)


def handle_component_error(component_name: str, error: Exception) -> None:
    """Handle component-specific errors"""
    st.error(f"❌ שגיאה ברכיב {component_name}")
    
    if st.checkbox(f"הצג פרטים טכניים - {component_name}"):
        st.code(str(error))
