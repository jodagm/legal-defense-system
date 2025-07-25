"""
Chatbot component - UI for chat interactions and response display
"""
import streamlit as st
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.services.chatbot_service import ChatbotService
from app.config.constants import QUERY_HISTORY_LIMIT


class ChatbotComponent:
    """Component for chatbot UI - handles chat interface and response display"""
    
    def __init__(self, chatbot_service: ChatbotService):
        self.chatbot = chatbot_service
    
    def is_api_available(self) -> bool:
        """Check if API is available for the UI layer"""
        return self.chatbot.is_available()
    
    def render_query_interface(self) -> None:
        """Render main query input interface"""
        st.markdown("## 💬 ממשק שאלות משפטיות")
        
        # Quick questions suggestions
        self._render_quick_suggestions()
        
        # Main query input
        self._render_query_input()
        
        # Query history
        self._render_query_history()
    
    def render_simple_query_interface(self) -> None:
        """Render simplified query interface for limited functionality"""
        st.markdown("### 💬 שאל שאלה כללית")
        
        query = st.text_area(
            "השאלה שלך:",
            height=100,
            placeholder="שאל שאלה משפטית כללית...",
            help="ללא מסמכים ספציפיים - תשובה כללית בלבד"
        )
        
        if st.button("🔍 שאל שאלה כללית", type="primary"):
            if query.strip():
                self._process_simple_query(query)
            else:
                st.warning("⚠️ אנא כתוב שאלה")
    
    def display_response(self, result: Dict[str, Any]) -> None:
        """Display response from search results"""
        if not result:
            st.error("❌ לא התקבלה תשובה")
            return
        
        self._render_response_header(result)
        self._render_main_answer(result)
        self._render_response_metadata(result)
        self._render_sources_section(result)
        self._save_to_history(result)
    
    def display_search_response(self, search_result: Dict[str, Any]) -> None:
        """Display response from search service"""
        self.display_response(search_result)
    
    def render_conversation_history(self) -> None:
        """Render conversation history in sidebar or main area"""
        history = self.chatbot.get_conversation_history()
        
        if not history:
            st.info("📭 אין היסטוריית שיחות")
            return
        
        st.markdown(f"### 📋 היסטוריית שיחות ({len(history)})")
        
        for i, entry in enumerate(reversed(history[-10:]), 1):
            with st.expander(f"🗨️ שיחה {i} - {self._format_timestamp(entry.get('timestamp'))}"):
                st.markdown(f"**שאלה:** {entry.get('query', 'לא זמין')}")
                st.markdown(f"**תשובה:** {entry.get('response_preview', 'לא זמין')}")
                st.caption(f"מקורות: {entry.get('sources_count', 0)} | מודל: {entry.get('model_used', 'לא ידוע')}")
    
    def _render_quick_suggestions(self) -> None:
        """Render quick question suggestions"""
        quick_questions = self._get_quick_questions()
        
        if quick_questions:
            st.markdown("**💡 שאלות מהירות:**")
            
            # Display in columns for better layout
            cols = st.columns(min(len(quick_questions), 3))
            
            for i, question in enumerate(quick_questions[:6]):  # Max 6 suggestions
                with cols[i % 3]:
                    short_question = self._truncate_text(question, 25)
                    if st.button(
                        f"❓ {short_question}",
                        key=f"quick_question_{i}",
                        help=question,
                        use_container_width=True
                    ):
                        st.session_state.user_query = question
                        st.rerun()
    
    def _render_query_input(self) -> None:
        """Render main query input area"""
        # Advanced options toggle
        show_advanced = st.checkbox("⚙️ אפשרויות מתקדמות", key="show_advanced_options")
        
        # Query input
        query = st.text_area(
            "🔍 שאל את השאלה המשפטית שלך:",
            value=st.session_state.get('user_query', ''),
            height=120,
            placeholder="דוגמה: מהן הטענות המרכזיות בכתב התביעה ומה נקודות החולשה?",
            help="שאל שאלות ספציפיות ומפורטות לקבלת ניתוח משפטי מקצועי",
            key="main_query_input"
        )
        
        # Advanced options
        advanced_options = {}
        if show_advanced:
            advanced_options = self._render_advanced_options()
        
        # Submit button
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            submit_button = st.button(
                "🏛️ בצע ניתוח משפטי",
                type="primary",
                key="submit_query",
                use_container_width=True
            )
        
        with col2:
            if st.button("🧹 נקה", key="clear_query"):
                st.session_state.user_query = ""
                st.rerun()
        
        with col3:
            if st.button("📋 היסטוריה", key="show_history"):
                self._show_history_modal()
        
        # Process query
        if submit_button and query.strip():
            st.session_state.user_query = query.strip()
            st.session_state.advanced_options = advanced_options
            st.rerun()
        elif submit_button and not query.strip():
            st.warning("⚠️ אנא כתוב שאלה")
    
    def _render_advanced_options(self) -> Dict[str, Any]:
        """Render advanced search options"""
        with st.expander("⚙️ הגדרות מתקדמות", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                search_method = st.selectbox(
                    "שיטת חיפוש:",
                    ["comprehensive", "quick", "document_only", "ai_only"],
                    help="""
                    • Comprehensive: חיפוש מקיף עם כל השיטות
                    • Quick: חיפוש מהיר לתוצאות מיידיות  
                    • Document Only: רק במסמכים ללא AI
                    • AI Only: רק תשובה כללית מ-AI
                    """
                )
                
                response_style = st.selectbox(
                    "סגנון תשובה:",
                    ["professional", "detailed", "concise", "strategic"],
                    help="""
                    • Professional: תשובה משפטית מקצועית
                    • Detailed: תשובה מפורטת וממצה
                    • Concise: תשובה קצרה ולעניין
                    • Strategic: התמקדות באסטרטגיית הגנה
                    """
                )
            
            with col2:
                max_sources = st.slider(
                    "מספר מקורות מקסימלי:",
                    min_value=3,
                    max_value=20,
                    value=10,
                    help="מספר המקורות המקסימלי שיוצגו בתוצאה"
                )
                
                include_history = st.checkbox(
                    "כלול הקשר מהיסטוריה",
                    value=False,
                    help="השתמש בשיחות קודמות לחיפוש מדויק יותר"
                )
        
        return {
            'search_method': search_method,
            'response_style': response_style,
            'max_sources': max_sources,
            'include_history': include_history
        }
    
    def _render_response_header(self, result: Dict[str, Any]) -> None:
        """Render response header with metadata"""
        st.markdown("## 📝 תשובה משפטית מתקדמת")
        
        # Response metadata in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            strategy = result.get('search_strategy', 'לא ידוע')
            st.caption(f"🔍 שיטה: {strategy}")
        
        with col2:
            model = result.get('model_used', 'לא ידוע')
            st.caption(f"🤖 מודל: {model}")
        
        with col3:
            sources_count = len(result.get('sources', []))
            st.caption(f"📚 מקורות: {sources_count}")
        
        with col4:
            timestamp = result.get('timestamp', '')
            if timestamp:
                formatted_time = self._format_timestamp(timestamp)
                st.caption(f"🕐 זמן: {formatted_time}")
    
    def _render_main_answer(self, result: Dict[str, Any]) -> None:
        """Render main answer content"""
        answer = result.get('answer', 'לא התקבלה תשובה')
        
        # Display answer with proper formatting
        st.markdown(answer)
        
        # Special notes or warnings
        if 'note' in result:
            st.info(f"📝 הערה: {result['note']}")
        
        if 'error' in result and result['error']:
            st.warning(f"⚠️ התרחשה שגיאה חלקית: {result['error']}")
        
        if result.get('type') == 'general_response':
            st.info("💭 זוהי תשובה כללית ללא מסמכים ספציפיים מהתיק")
    
    def _render_response_metadata(self, result: Dict[str, Any]) -> None:
        """Render response metadata and quality indicators"""
        with st.expander("📊 מטא-דטה ואיכות התשובה", expanded=False):
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🔍 פרטי החיפוש:**")
                st.text(f"• שיטה: {result.get('search_strategy', 'לא ידוע')}")
                st.text(f"• יש הקשר: {'כן' if result.get('has_context', False) else 'לא'}")
                st.text(f"• מספר מקורות: {len(result.get('sources', []))}")
            
            with col2:
                st.markdown("**🤖 פרטי AI:**")
                st.text(f"• מודל: {result.get('model_used', 'לא ידוע')}")
                st.text(f"• סוג תשובה: {result.get('type', 'רגילה')}")
                
                # Quality indicators
                quality_score = self._calculate_response_quality(result)
                st.metric("🎯 ציון איכות", f"{quality_score:.0f}%")
    
    def _render_sources_section(self, result: Dict[str, Any]) -> None:
        """Render sources section with detailed information"""
        sources = result.get('sources', [])
        
        if not sources:
            return
        
        with st.expander(f"📚 מקורות משפטיים ({len(sources)} נמצאו)", expanded=True):
            
            # Group sources by document type
            grouped_sources = self._group_sources_by_type(sources)
            
            for doc_type, type_sources in grouped_sources.items():
                if len(grouped_sources) > 1:
                    st.markdown(f"### 📋 {doc_type}")
                
                for i, source in enumerate(type_sources, 1):
                    self._render_single_source(source, i)
    
    def _render_single_source(self, source: Dict[str, Any], index: int) -> None:
        """Render individual source with all details"""
        with st.container():
            # Source header
            col1, col2, col3 = st.columns([4, 1, 1])
            
            with col1:
                file_name = source.get('file', 'מסמך לא ידוע')
                doc_type = source.get('document_type', source.get('type', 'מסמך'))
                st.markdown(f"**מקור {index}: {file_name}**")
                st.caption(f"סוג: {doc_type}")
            
            with col2:
                relevance = source.get('relevance_score', source.get('similarity', 0))
                if isinstance(relevance, (int, float)):
                    st.metric("רלוונטיות", f"{relevance:.2%}")
            
            with col3:
                chunk_info = source.get('chunk_index', source.get('chunk', ''))
                if chunk_info:
                    st.metric("חלק", str(chunk_info))
            
            # Source content
            content = source.get('content', '')
            if content:
                with st.expander(f"📄 תוכן מקור {index}", expanded=False):
                    st.markdown(content)
                    
                    # Additional metadata if available
                    metadata = source.get('source_metadata', {})
                    if metadata:
                        st.caption("מידע נוסף:")
                        for key, value in metadata.items():
                            if value:
                                st.caption(f"• {key}: {value}")
            
            st.divider()
    
    def _render_query_history(self) -> None:
        """Render query history in main interface"""
        if 'query_history' not in st.session_state:
            st.session_state.query_history = []
        
        history = st.session_state.query_history
        
        if history:
            with st.expander(f"📋 שאלות אחרונות ({len(history[:5])})", expanded=False):
                for entry in reversed(history[-5:]):  # Show last 5
                    query = entry.get('question', '')
                    timestamp = entry.get('timestamp', '')
                    
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        if st.button(
                            f"🔄 {self._truncate_text(query, 60)}",
                            key=f"history_{hash(query + timestamp)}",
                            help=f"חזור על השאלה: {query}"
                        ):
                            st.session_state.user_query = query
                            st.rerun()
                    
                    with col2:
                        if timestamp:
                            try:
                                time_str = datetime.fromisoformat(timestamp).strftime("%H:%M")
                                st.caption(time_str)
                            except:
                                pass
    
    def _process_simple_query(self, query: str) -> None:
        """Process simple query without document search"""
        with st.spinner("🤖 מכין תשובה כללית..."):
            result = self.chatbot.generate_simple_response(query)
            self.display_response(result)
    
    def _show_history_modal(self) -> None:
        """Show conversation history in modal-like interface"""
        st.markdown("### 📋 היסטוריית שיחות מלאה")
        self.render_conversation_history()
    
    def _get_quick_questions(self) -> List[str]:
        """Get quick question suggestions"""
        return [
            "מהן הטענות המרכזיות בכתב התביעה?",
            "מה הראיות העיקריות בתיק?",
            "אילו סתירות יש במסמכים?",
            "מה נקודות החולשה בטענות התובע?",
            "אילו זכויות יש לנתבע?",
            "מהן האסטרטגיות הטובות ביותר להגנה?"
        ]
    
    def _group_sources_by_type(self, sources: List[Dict]) -> Dict[str, List[Dict]]:
        """Group sources by document type"""
        grouped = {}
        
        for source in sources:
            doc_type = source.get('document_type', source.get('type', 'מסמך כללי'))
            if doc_type not in grouped:
                grouped[doc_type] = []
            grouped[doc_type].append(source)
        
        return grouped
    
    def _calculate_response_quality(self, result: Dict[str, Any]) -> float:
        """Calculate response quality score"""
        score = 0.0
        
        # Has answer
        if result.get('answer'):
            score += 40.0
        
        # Has sources
        sources_count = len(result.get('sources', []))
        if sources_count > 0:
            score += min(30.0, sources_count * 5.0)  # Max 30 points
        
        # Has context
        if result.get('has_context', False):
            score += 20.0
        
        # No errors
        if not result.get('error'):
            score += 10.0
        
        return min(100.0, score)
    
    def _save_to_history(self, result: Dict[str, Any]) -> None:
        """Save interaction to history"""
        if 'query_history' not in st.session_state:
            st.session_state.query_history = []
        
        # Get the original query from session state or result
        query = st.session_state.get('user_query', result.get('query', 'שאלה לא ידועה'))
        
        history_entry = {
            'timestamp': datetime.now().isoformat(),
            'question': query,
            'answer_preview': result.get('answer', '')[:200] + "...",
            'sources_count': len(result.get('sources', [])),
            'method': result.get('search_strategy', 'לא ידוע'),
            'quality_score': self._calculate_response_quality(result)
        }
        
        st.session_state.query_history.append(history_entry)
        
        # Limit history size
        if len(st.session_state.query_history) > QUERY_HISTORY_LIMIT:
            st.session_state.query_history = st.session_state.query_history[-QUERY_HISTORY_LIMIT:]
    
    def _format_timestamp(self, timestamp: str) -> str:
        """Format timestamp for display"""
        try:
            dt = datetime.fromisoformat(timestamp)
            return dt.strftime("%H:%M")
        except:
            return "לא ידוע"
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to max length"""
        if len(text) <= max_length:
            return text
        return f"{text[:max_length-3]}..."
