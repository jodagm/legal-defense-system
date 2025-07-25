"""
Main application class - orchestrates all components
"""
import streamlit as st
from typing import Optional

from app.components.chatbot_component import ChatbotComponent
from app.components.document_component import DocumentComponent
from app.components.search_component import SearchComponent
from app.components.status_component import StatusComponent
from app.config.constants import APP_TITLE, APP_VERSION


class LegalApp:
    """Main legal defense application - single responsibility coordinator"""
    
    def __init__(
        self,
        chatbot_component: ChatbotComponent,
        document_component: DocumentComponent,
        search_component: SearchComponent,
        status_component: StatusComponent
    ):
        self.chatbot = chatbot_component
        self.documents = document_component
        self.search = search_component
        self.status = status_component
    
    def run(self) -> None:
        """Run the complete application - main orchestration"""
        self._render_header()
        self._render_sidebar()
        self._render_main_content()
        self._render_footer()
    
    def _render_header(self) -> None:
        """Render application header with system status"""
        st.title(f"🏛️ {APP_TITLE}")
        st.markdown(f"### ⚖️ מערכת AI מתקדמת לניתוח משפטי - גרסה {APP_VERSION}")
        
        # Quick system overview
        self.status.render_header_status()
        st.markdown("---")
    
    def _render_sidebar(self) -> None:
        """Render sidebar with all management components"""
        with st.sidebar:
            self.status.render_sidebar_header()
            st.divider()
            
            self.status.render_system_metrics()
            st.divider()
            
            self.documents.render_management_interface()
            st.divider()
            
            self.search.render_quick_actions()
            st.divider()
            
            self.status.render_advanced_tools()
    
    def _render_main_content(self) -> None:
        """Render main content based on system state"""
        has_documents = self.documents.has_processed_documents()
        api_available = self.chatbot.is_api_available()
        
        if not has_documents:
            self._render_document_upload_state()
        elif not api_available:
            self._render_api_unavailable_state()
        else:
            self._render_active_chat_interface()
    
    def _render_document_upload_state(self) -> None:
        """Render state when no documents are available"""
        st.info("📁 העלה מסמכים משפטיים כדי להתחיל בניתוח")
        
        # Prominent upload interface
        self.documents.render_prominent_upload()
        
        # Usage instructions
        self._render_usage_instructions()
    
    def _render_api_unavailable_state(self) -> None:
        """Render state when API is not available"""
        st.warning("⚠️ שירות AI לא זמין - ודא הגדרת API key")
        
        # Show documents but limited functionality
        self.documents.render_document_overview()
        
        # API setup instructions
        self._render_api_setup_instructions()
    
    def _render_active_chat_interface(self) -> None:
        """Render full active chat interface"""
        # Document overview
        self.documents.render_status_summary()
        
        # Main query interface
        self.chatbot.render_query_interface()
        
        # Process any pending queries
        self._handle_user_interactions()
    
    def _handle_user_interactions(self) -> None:
        """Handle user query submissions and interactions"""
        if query := st.session_state.get('user_query'):
            self._process_user_query(query)
            # Clear the query to prevent reprocessing
            del st.session_state['user_query']
        
        if quick_question := st.session_state.get('quick_question'):
            self._process_user_query(quick_question)
            del st.session_state['quick_question']
    
    def _process_user_query(self, query: str) -> None:
        """Process user query through the search system"""
        with st.spinner("🔍 מעבד שאלה משפטית..."):
            try:
                # Get advanced options from session state
                advanced_options = st.session_state.get('advanced_options', {})
                
                # Execute search with correct parameters
                search_result = self.search.execute_search(
                    query,
                    max_results=advanced_options.get('max_sources', 15),
                    min_similarity=advanced_options.get('min_similarity', 0.2)
                )
                
                # Display results
                self.chatbot.display_search_response(search_result)
                
            except Exception as e:
                st.error(f"❌ שגיאה בעיבוד השאלה: {e}")
    
    def _render_usage_instructions(self) -> None:
        """Render usage instructions for new users"""
        with st.expander("📖 מדריך שימוש", expanded=False):
            st.markdown("""
            ### 🚀 כיצד להתחיל:
            1. **העלה מסמכים** - גרור קבצי PDF לאזור ההעלאה
            2. **עבד מסמכים** - לחץ על "עבד" לניתוח האוטומטי
            3. **שאל שאלות** - כתוב שאלות משפטיות ספציפיות
            
            ### 💡 עצות לתוצאות טובות:
            - שאלות ספציפיות מביאות תשובות מדויקות יותר
            - השתמש במילות מפתח משפטיות רלוונטיות
            - בדוק את המקורות שמוצגים בתשובות
            """)
    
    def _render_api_setup_instructions(self) -> None:
        """Render API setup instructions"""
        with st.expander("⚙️ הגדרת API", expanded=True):
            st.markdown("""
            ### 🔑 הגדרת Claude API:
            1. השג API key מ-Anthropic
            2. הוסף למשתני סביבה: `CLAUDE_API_KEY=your_key`
            3. או צור קובץ `.streamlit/secrets.toml`:
            ```toml
            CLAUDE_API_KEY = "your_api_key_here"
            ```
            4. רענן את הדף
            """)
    
    def _render_footer(self) -> None:
        """Render application footer with additional info"""
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            self._render_system_tips()
        
        with col2:
            self._render_support_info()
        
        with col3:
            self.status.render_technical_details()
    
    def _render_system_tips(self) -> None:
        """Render system usage tips"""
        st.markdown("""
        ### 💡 עצות שימוש:
        - **ניסוח מדויק** של שאלות
        - **ארגון מסמכים** לפי סוגים
        - **בדיקת מקורות** בתשובות
        - **שמירת שאלות** חוזרות
        """)
    
    def _render_support_info(self) -> None:
        """Render support and help information"""
        st.markdown("""
        ### 🆘 תמיכה:
        - **בעיות טכניות** - בדוק logs
        - **שאלות שימוש** - מדריך המערכת  
        - **שגיאות API** - ודא API key
        - **ביצועים** - נקה cache
        """)
