"""
Status component - displays system status and metrics with Phase 1 enhancements
"""
import streamlit as st
from datetime import datetime
from typing import Dict, Any, Optional

from app.services.chatbot_service import ChatbotService
from app.services.document_service import DocumentService
from app.config.constants import APP_VERSION


class StatusComponent:
    """Component for displaying system status with Phase 1 enhancements"""
    
    def __init__(
        self, 
        chatbot_service: ChatbotService, 
        document_service: DocumentService,
        evidence_service: Optional[Any] = None,
        conversation_manager: Optional[Any] = None
    ):
        self.chatbot = chatbot_service
        self.documents = document_service
        self.evidence_service = evidence_service
        self.conversation_manager = conversation_manager
    
    def render_header_status(self) -> None:
        """Render enhanced status overview in header with Phase 1 features"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            api_status = "🟢 מחובר" if self.chatbot.is_available() else "🔴 לא זמין"
            st.metric("🤖 מצב AI", api_status)
        
        with col2:
            docs_count = len(self.documents.get_processed_documents())
            st.metric("📄 מסמכים מעובדים", docs_count)
        
        with col3:
            # Evidence analysis status
            if self.evidence_service:
                try:
                    evidence_summary = self.evidence_service.get_evidence_summary()
                    evidence_count = evidence_summary.get('total_items', 0)
                    st.metric("🧠 ראיות מנותחות", evidence_count)
                except:
                    st.metric("🧠 ראיות מנותחות", "N/A")
            else:
                st.metric("🧠 ראיות מנותחות", "לא פעיל")
        
        with col4:
            # Conversation quality status
            if self.conversation_manager:
                try:
                    conv_stats = self.chatbot.get_conversation_statistics()
                    quality_items = conv_stats.get('context_quality_items', 0)
                    st.metric("💬 הקשר איכותי", quality_items)
                except:
                    st.metric("💬 הקשר איכותי", "N/A")
            else:
                st.metric("💬 הקשר איכותי", "לא פעיל")
        
        with col3:
            stats = self.documents.get_document_statistics()
            total_chunks = stats.get('total_chunks', 0)
            st.metric("🔍 קטעי חיפוש", total_chunks)
        
        with col4:
            processing_rate = stats.get('processing_rate', 0) * 100
            st.metric("⚡ אחוז עיבוד", f"{processing_rate:.0f}%")
    
    def render_sidebar_header(self) -> None:
        """Render sidebar header with branding"""
        st.markdown("""
        <div style="text-align: center; padding: 1rem; 
                    background: linear-gradient(90deg, #1f4e79, #2d5a8b); 
                    color: white; border-radius: 10px; margin-bottom: 1rem;">
            <h3>🏛️ מערכת הגנה משפטית</h3>
            <p style="margin: 0; font-size: 0.9rem;">ממשק ניהול מתקדם</p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_system_metrics(self) -> None:
        """Render detailed system metrics"""
        st.markdown("### 📊 מצב מערכת")
        
        # API Connection Status
        api_available = self.chatbot.is_available()
        if api_available:
            st.success("🤖 Claude AI מחובר ופעיל")
        else:
            st.error("🤖 Claude AI לא זמין - בדוק API key")
        
        # Document Statistics
        stats = self.documents.get_document_statistics()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "📁 קבצים שהועלו",
                stats.get('uploaded_count', 0),
                help="מספר קבצי PDF שהועלו למערכת"
            )
            
            st.metric(
                "⚙️ קבצים מעובדים", 
                stats.get('processed_count', 0),
                help="מספר קבצים שעברו עיבוד אוטומטי"
            )
        
        with col2:
            st.metric(
                "🔍 קטעי טקסט",
                stats.get('total_chunks', 0),
                help="מספר קטעי טקסט זמינים לחיפוש"
            )
            
            total_size = stats.get('total_size_mb', 0)
            st.metric(
                "💾 גודל נתונים",
                f"{total_size:.1f} MB",
                help="גודל כולל של המסמכים המעובדים"
            )
        
        # Processing Progress
        if stats.get('uploaded_count', 0) > 0:
            processing_rate = stats.get('processing_rate', 0)
            st.progress(processing_rate, text=f"התקדמות עיבוד: {processing_rate:.0%}")
        
        # Document Types Breakdown
        doc_types = stats.get('document_types', {})
        if doc_types:
            st.markdown("**📋 סוגי מסמכים:**")
            for doc_type, count in doc_types.items():
                st.text(f"• {doc_type}: {count}")
    
    def render_advanced_tools(self) -> None:
        """Render advanced system tools"""
        with st.expander("🛠️ כלים מתקדמים", expanded=False):
            
            # System Information
            st.markdown("**ℹ️ מידע מערכת:**")
            st.text(f"גרסה: {APP_VERSION}")
            st.text(f"זמן הפעלה: {self._get_uptime()}")
            
            # Quick Actions
            st.markdown("**⚡ פעולות מהירות:**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔄 רענן מערכת", key="refresh_system"):
                    st.cache_data.clear()
                    st.success("✅ המערכת רועננה")
                
                if st.button("📊 סטטיסטיקות", key="show_stats"):
                    self._show_detailed_statistics()
            
            with col2:
                if st.button("🧹 נקה זיכרון", key="clear_cache"):
                    self._clear_system_cache()
                    st.success("✅ זיכרון נוקה")
                
                if st.button("📈 דוח מערכת", key="system_report"):
                    self._generate_system_report()
            
            # System Clear Section
            st.divider()
            self._render_system_clear_section()
    
    def render_usage_tips(self) -> None:
        """Render usage tips and best practices"""
        st.markdown("""
        ### 💡 עצות שימוש מתקדם:
        - **שאלות ספציפיות** מניבות תוצאות טובות יותר
        - **העלה מסמכים מסוגים שונים** לניתוח מקיף
        - **בדוק מקורות** בכל תשובה שמתקבלת
        - **השתמש בהיסטוריה** לשאלות חוזרות
        """)
    
    def render_technical_details(self) -> None:
        """Render technical system details"""
        with st.expander("🔧 פרטים טכניים", expanded=False):
            
            # System Health
            health_score = self._calculate_system_health()
            health_color = self._get_health_color(health_score)
            
            st.markdown(f"""
            **🏥 בריאות מערכת:** 
            <span style='color: {health_color}; font-weight: bold;'>{health_score:.0f}%</span>
            """, unsafe_allow_html=True)
            
            # Component Status
            st.markdown("**🔗 מצב רכיבים:**")
            components = self._get_component_status()
            for component, status in components.items():
                icon = "✅" if status else "❌"
                st.text(f"{icon} {component}")
            
            # Performance Metrics
            if self.chatbot.is_available():
                history = self.chatbot.get_conversation_history()
                st.text(f"💬 שיחות: {len(history)}")
            
            stats = self.documents.get_document_statistics()
            st.text(f"📄 קבצים: {stats.get('uploaded_count', 0)}/{stats.get('processed_count', 0)}")
    
    def _get_uptime(self) -> str:
        """Get system uptime"""
        if 'app_start_time' not in st.session_state:
            st.session_state.app_start_time = datetime.now()
        
        uptime = datetime.now() - st.session_state.app_start_time
        total_minutes = int(uptime.total_seconds() / 60)
        
        if total_minutes < 60:
            return f"{total_minutes} דקות"
        else:
            hours = total_minutes // 60
            minutes = total_minutes % 60
            return f"{hours}:{minutes:02d} שעות"
    
    def _calculate_system_health(self) -> float:
        """Calculate overall system health score"""
        score = 0.0
        
        # API availability (40 points)
        if self.chatbot.is_available():
            score += 40.0
        
        # Document processing (40 points)
        stats = self.documents.get_document_statistics()
        if stats.get('uploaded_count', 0) > 0:
            processing_rate = stats.get('processing_rate', 0)
            score += processing_rate * 40.0
        else:
            score += 40.0  # No files = healthy state
        
        # System components (20 points)
        components = self._get_component_status()
        working_components = sum(components.values())
        total_components = len(components)
        if total_components > 0:
            score += (working_components / total_components) * 20.0
        
        return min(100.0, score)
    
    def _get_health_color(self, health_score: float) -> str:
        """Get color based on health score"""
        if health_score >= 80:
            return "#28a745"  # Green
        elif health_score >= 60:
            return "#ffc107"  # Yellow
        elif health_score >= 40:
            return "#fd7e14"  # Orange
        else:
            return "#dc3545"  # Red
    
    def _get_component_status(self) -> Dict[str, bool]:
        """Get status of system components"""
        return {
            'Claude API': self.chatbot.is_available(),
            'Document Service': True,  # Always available
            'File System': self.documents.upload_path.exists(),
            'Search Service': self.documents.has_documents() or self.chatbot.is_available()
        }
    
    def _show_detailed_statistics(self) -> None:
        """Show detailed system statistics"""
        stats = self.documents.get_document_statistics()
        
        st.markdown("### 📈 סטטיסטיקות מפורטות")
        
        # File statistics
        st.json({
            'document_statistics': stats,
            'conversation_count': len(self.chatbot.get_conversation_history()),
            'system_health': f"{self._calculate_system_health():.1f}%",
            'api_available': self.chatbot.is_available()
        })
    
    def _clear_system_cache(self) -> None:
        """Clear system cache"""
        # Clear conversation history
        self.chatbot.clear_history()
        
        # Clear Streamlit cache
        st.cache_data.clear()
    
    def _generate_system_report(self) -> None:
        """Generate comprehensive system report"""
        st.markdown("### 📋 דוח מערכת מקיף")
        
        # System overview
        stats = self.documents.get_document_statistics()
        health = self._calculate_system_health()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'system_health': f"{health:.1f}%",
            'api_status': 'available' if self.chatbot.is_available() else 'unavailable',
            'document_statistics': stats,
            'conversation_count': len(self.chatbot.get_conversation_history()),
            'uptime': self._get_uptime(),
            'component_status': self._get_component_status()
        }
        
        st.json(report)
        
        # Download option
        import json
        report_json = json.dumps(report, ensure_ascii=False, indent=2)
        st.download_button(
            "📥 הורד דוח",
            data=report_json,
            file_name=f"system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    def _render_system_clear_section(self) -> None:
        """Render system clear/reset functionality"""
        st.markdown("### 🗑️ **איפוס מערכת**")
        
        # Warning message
        st.warning("⚠️ **אזהרה**: פעולה זו תמחק את כל הנתונים באופן בלתי הפיך!")
        
        # Clear options
        col1, col2 = st.columns(2)
        
        with col1:
            clear_docs = st.checkbox("📄 מחק מסמכים", help="מחיקת כל המסמכים המועלים והמעובדים")
            clear_evidence = st.checkbox("🧠 מחק ניתוח ראיות", help="מחיקת כל ניתוחי הראיות")
        
        with col2:
            clear_conversations = st.checkbox("💬 מחק היסטוריית שיחות", help="מחיקת כל השיחות והקשר האיכותי")
            clear_all = st.checkbox("🔥 מחק הכל", help="איפוס מלא של המערכת")
        
        # Clear button
        if st.button("🗑️ **בצע מחיקה**", type="primary", disabled=not any([clear_docs, clear_evidence, clear_conversations, clear_all])):
            self._execute_system_clear(clear_docs or clear_all, clear_evidence or clear_all, clear_conversations or clear_all)
    
    def _execute_system_clear(self, clear_docs: bool, clear_evidence: bool, clear_conversations: bool) -> None:
        """Execute system clear with confirmation dialog"""
        
        # Double confirmation for safety
        if not st.session_state.get('clear_confirmed', False):
            st.session_state.clear_confirmed = True
            st.error("🛑 **אישור נדרש**: לחץ שוב על 'בצע מחיקה' לאישור סופי")
            st.rerun()
            return
        
        # Reset confirmation flag
        st.session_state.clear_confirmed = False
        
        results = {
            'documents': {'uploaded_files_deleted': 0, 'processed_files_deleted': 0, 'errors': []},
            'evidence': {'evidence_files_deleted': 0, 'errors': []},
            'conversations': {'sessions_deleted': 0, 'entries_deleted': 0, 'errors': []}
        }
        
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_operations = sum([clear_docs, clear_evidence, clear_conversations])
        current_operation = 0
        
        try:
            # Clear documents
            if clear_docs:
                current_operation += 1
                status_text.text("🗂️ מוחק מסמכים...")
                progress_bar.progress(current_operation / total_operations * 0.8)
                results['documents'] = self.documents.clear_all_documents()
            
            # Clear evidence
            if clear_evidence and self.evidence_service:
                current_operation += 1
                status_text.text("🧠 מוחק ניתוח ראיות...")
                progress_bar.progress(current_operation / total_operations * 0.8)
                results['evidence'] = self.evidence_service.clear_all_evidence()
            
            # Clear conversations
            if clear_conversations and self.conversation_manager:
                current_operation += 1
                status_text.text("💬 מוחק היסטוריית שיחות...")
                progress_bar.progress(current_operation / total_operations * 0.8)
                results['conversations'] = self.conversation_manager.clear_all_conversations()
            
            # Final cleanup
            status_text.text("🧹 מסיים ניקוי...")
            progress_bar.progress(0.9)
            
            # Clear Streamlit cache
            if hasattr(st, 'cache_data'):
                st.cache_data.clear()
            
            progress_bar.progress(1.0)
            status_text.text("✅ מחיקה הושלמה!")
            
            # Display results
            self._display_clear_results(results, clear_docs, clear_evidence, clear_conversations)
            
            # Success animation
            st.balloons()
            
            # Small delay then refresh
            import time
            time.sleep(2)
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ שגיאה במחיקת מערכת: {e}")
            progress_bar.empty()
            status_text.empty()
    
    def _display_clear_results(self, results: Dict, clear_docs: bool, clear_evidence: bool, clear_conversations: bool) -> None:
        """Display results of system clear operation"""
        
        st.success("🎉 **איפוס מערכת הושלם בהצלחה!**")
        
        # Documents results
        if clear_docs:
            doc_results = results['documents']
            if doc_results['uploaded_files_deleted'] > 0 or doc_results['processed_files_deleted'] > 0:
                st.info(f"📄 **מסמכים**: נמחקו {doc_results['uploaded_files_deleted']} קבצים מועלים ו-{doc_results['processed_files_deleted']} קבצים מעובדים")
            
            if doc_results['errors']:
                st.warning(f"⚠️ **שגיאות במסמכים**: {len(doc_results['errors'])} שגיאות")
                with st.expander("פרטי שגיאות"):
                    for error in doc_results['errors']:
                        st.text(error)
        
        # Evidence results
        if clear_evidence:
            ev_results = results['evidence']
            if ev_results['evidence_files_deleted'] > 0:
                st.info(f"🧠 **ראיות**: נמחקו {ev_results['evidence_files_deleted']} קבצי ניתוח")
            
            if ev_results['errors']:
                st.warning(f"⚠️ **שגיאות בראיות**: {len(ev_results['errors'])} שגיאות")
        
        # Conversation results
        if clear_conversations:
            conv_results = results['conversations']
            if conv_results['sessions_deleted'] > 0 or conv_results['entries_deleted'] > 0:
                st.info(f"💬 **שיחות**: נמחקו {conv_results['sessions_deleted']} סשנים ו-{conv_results['entries_deleted']} הודעות")
            
            if conv_results['errors']:
                st.warning(f"⚠️ **שגיאות בשיחות**: {len(conv_results['errors'])} שגיאות")
        
        st.markdown("---")
        st.markdown("🔄 **המערכת מוכנה לשימוש חדש**")
