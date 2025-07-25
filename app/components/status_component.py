"""
Status component - displays system status and metrics
"""
import streamlit as st
from datetime import datetime
from typing import Dict, Any

from app.services.chatbot_service import ChatbotService
from app.services.document_service import DocumentService
from app.config.constants import APP_VERSION


class StatusComponent:
    """Component for displaying system status - UI responsibility only"""
    
    def __init__(self, chatbot_service: ChatbotService, document_service: DocumentService):
        self.chatbot = chatbot_service
        self.documents = document_service
    
    def render_header_status(self) -> None:
        """Render status overview in header"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            api_status = "🟢 מחובר" if self.chatbot.is_available() else "🔴 לא זמין"
            st.metric("🤖 מצב AI", api_status)
        
        with col2:
            docs_count = len(self.documents.get_processed_documents())
            st.metric("📄 מסמכים מעובדים", docs_count)
        
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
