"""
Search component - UI for search functionality and quick actions
"""
import streamlit as st
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.services.search_service import SearchService
from app.config.constants import MAX_SEARCH_RESULTS, DEFAULT_SIMILARITY_THRESHOLD


class SearchComponent:
    """Component for search UI and quick actions"""
    
    def __init__(self, search_service: SearchService):
        self.search = search_service
    
    def execute_search(self, query: str, **kwargs) -> Dict[str, Any]:
        """Execute search through service layer"""
        return self.search.execute_comprehensive_search(query, **kwargs)
    
    def render_quick_actions(self) -> None:
        """Render quick search actions in sidebar"""
        st.markdown("### ⚡ פעולות מהירות")
        
        # Quick search suggestions
        self._render_search_suggestions()
        
        # Search tools
        self._render_search_tools()
        
        # Search statistics
        self._render_search_statistics()
    
    def render_advanced_search_interface(self) -> None:
        """Render advanced search interface for main area"""
        st.markdown("### 🔍 חיפוש מתקדם")
        
        with st.expander("🛠️ חיפוש מתקדם במסמכים", expanded=False):
            
            # Search input
            search_query = st.text_input(
                "🔍 מונח לחיפוש:",
                placeholder="הקלד מילות מפתח לחיפוש במסמכים...",
                help="חיפוש ישיר במסמכים ללא עיבוד AI"
            )
            
            # Advanced options
            col1, col2 = st.columns(2)
            
            with col1:
                max_results = st.slider(
                    "מספר תוצאות מקסימלי:",
                    min_value=5,
                    max_value=50,
                    value=MAX_SEARCH_RESULTS,
                    help="מספר התוצאות המקסימלי שיוחזר מהחיפוש"
                )
                
                search_mode = st.selectbox(
                    "מצב חיפוש:",
                    ["comprehensive", "quick", "exact_match"],
                    help="Comprehensive: חיפוש מקיף\nQuick: חיפוש מהיר\nExact Match: התאמה מדויקת"
                )
            
            with col2:
                min_similarity = st.slider(
                    "רמת דמיון מינימלית:",
                    min_value=0.1,
                    max_value=0.9,
                    value=DEFAULT_SIMILARITY_THRESHOLD,
                    step=0.1,
                    help="רמת הדמיון המינימלית הנדרשת לתוצאות החיפוש"
                )
                
                include_metadata = st.checkbox(
                    "כלול מטא-דטה",
                    value=True,
                    help="הצג מידע נוסף על המסמכים בתוצאות"
                )
            
            # Search execution
            if st.button("🔍 בצע חיפוש מתקדם", type="primary"):
                if search_query.strip():
                    self._execute_advanced_search(
                        search_query,
                        max_results=max_results,
                        min_similarity=min_similarity,
                        search_mode=search_mode,
                        include_metadata=include_metadata
                    )
                else:
                    st.warning("⚠️ אנא הקלד מונח לחיפוש")
    
    def render_search_suggestions_interface(self) -> None:
        """Render search suggestions interface"""
        st.markdown("### 💡 הצעות חיפוש")
        
        # Get dynamic suggestions
        suggestions = self.search.get_search_suggestions("")
        
        if suggestions:
            st.markdown("**🎯 שאלות מומלצות:**")
            
            for i, suggestion in enumerate(suggestions[:8], 1):
                if st.button(
                    f"{i}. {suggestion}",
                    key=f"suggestion_{i}",
                    help=f"לחץ לחיפוש: {suggestion}",
                    use_container_width=True
                ):
                    st.session_state.suggested_query = suggestion
                    st.rerun()
        
        # Custom suggestion input
        st.markdown("**✏️ חיפוש מותאם אישית:**")
        
        partial_input = st.text_input(
            "התחל להקליד...",
            placeholder="הקלד מילות מפתח לקבלת הצעות",
            help="המערכת תציע שאלות רלוונטיות בהתבסס על הקלט שלך"
        )
        
        if partial_input:
            dynamic_suggestions = self.search.get_search_suggestions(partial_input)
            
            if dynamic_suggestions:
                st.markdown("**הצעות מותאמות:**")
                
                for suggestion in dynamic_suggestions[:5]:
                    if st.button(
                        f"💡 {suggestion}",
                        key=f"dynamic_{hash(suggestion)}",
                        use_container_width=True
                    ):
                        st.session_state.suggested_query = suggestion
                        st.rerun()
    
    def _render_search_suggestions(self) -> None:
        """Render quick search suggestions in sidebar"""
        with st.expander("🎯 חיפושים מהירים", expanded=False):
            
            quick_searches = [
                "טענות עיקריות",
                "ראיות מרכזיות", 
                "סתירות במסמכים",
                "נקודות חולשה",
                "זכויות נתבע",
                "אסטרטגיית הגנה"
            ]
            
            for search_term in quick_searches:
                if st.button(
                    f"🔍 {search_term}",
                    key=f"quick_search_{search_term.replace(' ', '_')}",
                    help=f"חיפוש מהיר עבור: {search_term}",
                    use_container_width=True
                ):
                    self._execute_quick_search(search_term)
    
    def _render_search_tools(self) -> None:
        """Render search management tools"""
        with st.expander("🛠️ כלי חיפוש", expanded=False):
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📊 סטטיסטיקות", key="search_stats_detailed"):
                    self._show_detailed_search_statistics()
                
                if st.button("🧹 נקה היסטוריה", key="clear_search_history"):
                    self._clear_search_history()
            
            with col2:
                if st.button("📋 יצא תוצאות", key="export_search_results"):
                    self._export_search_results()
                
                if st.button("🔧 אפשרויות", key="search_settings"):
                    self._show_search_settings()
    
    def _render_search_statistics(self) -> None:
        """Render search usage statistics"""
        stats = self.search.get_search_statistics()
        
        if stats.get('total_searches', 0) > 0:
            st.markdown("**📈 סטטיסטיקות חיפוש:**")
            
            total = stats.get('total_searches', 0)
            successful = stats.get('successful_searches', 0)
            success_rate = stats.get('success_rate', 0) * 100
            
            st.metric("🔍 חיפושים כ\"ס", total)
            st.metric("✅ הצלחה", f"{success_rate:.0f}%")
            
            # Most used strategies
            strategies = stats.get('strategies_used', {})
            if strategies:
                st.caption("שיטות נפוצות:")
                for strategy, count in strategies.items():
                    st.caption(f"• {strategy}: {count}")
    
    def _execute_quick_search(self, search_term: str) -> None:
        """Execute quick search and display results"""
        with st.spinner(f"🔍 מחפש: {search_term}..."):
            try:
                result = self.search.execute_quick_search(search_term)
                self._display_search_results(result, quick_search=True)
                
            except Exception as e:
                st.error(f"❌ שגיאה בחיפוש מהיר: {e}")
    
    def _execute_advanced_search(
        self,
        query: str,
        max_results: int,
        min_similarity: float,
        search_mode: str,
        include_metadata: bool
    ) -> None:
        """Execute advanced search with options"""
        
        with st.spinner(f"🔍 מבצע חיפוש מתקדם: {query}..."):
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("📖 מחפש במסמכים...")
                progress_bar.progress(25)
                
                # Execute search based on mode
                if search_mode == "comprehensive":
                    result = self.search.execute_comprehensive_search(
                        query,
                        max_results=max_results,
                        min_similarity=min_similarity
                    )
                elif search_mode == "quick":
                    result = self.search.execute_quick_search(query)
                else:  # exact_match
                    result = self._execute_exact_match_search(query, max_results)
                
                progress_bar.progress(75)
                status_text.text("📝 מעבד תוצאות...")
                
                # Display results
                self._display_advanced_search_results(
                    result,
                    include_metadata=include_metadata,
                    search_mode=search_mode
                )
                
                progress_bar.progress(100)
                status_text.text("✅ הושלם!")
                
                # Cleanup
                progress_bar.empty()
                status_text.empty()
                
            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                st.error(f"❌ שגיאה בחיפוש מתקדם: {e}")
    
    def _execute_exact_match_search(self, query: str, max_results: int) -> Dict[str, Any]:
        """Execute exact match search"""
        # Implementation for exact match search
        return {
            'answer': f"חיפוש התאמה מדויקת עבור: '{query}' - לא מומש עדיין",
            'sources': [],
            'search_strategy': 'exact_match',
            'note': 'חיפוש התאמה מדויקת - בפיתוח'
        }
    
    def _display_search_results(self, result: Dict[str, Any], quick_search: bool = False) -> None:
        """Display search results in expandable section"""
        st.markdown("### 🔍 תוצאות חיפוש")
        
        if quick_search:
            st.info("⚡ תוצאות חיפוש מהיר")
        
        # Display answer
        answer = result.get('answer', 'לא התקבלה תשובה')
        st.markdown(answer)
        
        # Display sources if available
        sources = result.get('sources', [])
        if sources:
            with st.expander(f"📚 מקורות ({len(sources)} נמצאו)", expanded=True):
                for i, source in enumerate(sources, 1):
                    self._render_search_source(source, i)
        
        # Display metadata
        if result.get('search_strategy'):
            st.caption(f"🔍 שיטת חיפוש: {result['search_strategy']}")
    
    def _display_advanced_search_results(
        self,
        result: Dict[str, Any],
        include_metadata: bool,
        search_mode: str
    ) -> None:
        """Display advanced search results with full details"""
        
        st.markdown("## 🔍 תוצאות חיפוש מתקדם")
        
        # Search info header
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.caption(f"🔧 מצב: {search_mode}")
        
        with col2:
            sources_count = len(result.get('sources', []))
            st.caption(f"📚 מקורות: {sources_count}")
        
        with col3:
            strategy = result.get('search_strategy', 'לא ידוע')
            st.caption(f"⚙️ אסטרטגיה: {strategy}")
        
        # Main answer
        answer = result.get('answer', 'לא התקבלה תשובה')
        st.markdown(answer)
        
        # Sources with metadata
        sources = result.get('sources', [])
        if sources:
            with st.expander(f"📚 מקורות מפורטים ({len(sources)})", expanded=True):
                
                for i, source in enumerate(sources, 1):
                    with st.container():
                        self._render_detailed_search_source(source, i, include_metadata)
                        st.divider()
        
        # Advanced metadata
        if include_metadata:
            self._render_search_metadata(result)
    
    def _render_search_source(self, source: Dict[str, Any], index: int) -> None:
        """Render basic search source"""
        col1, col2 = st.columns([3, 1])
        
        with col1:
            file_name = source.get('file', 'מסמך לא ידוע')
            st.markdown(f"**{index}. {file_name}**")
        
        with col2:
            relevance = source.get('relevance_score', 0)
            if isinstance(relevance, (int, float)):
                st.metric("רלוונטיות", f"{relevance:.1%}")
        
        # Content preview
        content = source.get('content', '')
        if content:
            st.text(content[:300] + "..." if len(content) > 300 else content)
    
    def _render_detailed_search_source(
        self,
        source: Dict[str, Any],
        index: int,
        include_metadata: bool
    ) -> None:
        """Render detailed search source with full metadata"""
        
        # Header
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            file_name = source.get('file', 'מסמך לא ידוע')
            doc_type = source.get('document_type', 'מסמך')
            st.markdown(f"**{index}. {file_name}**")
            st.caption(f"סוג: {doc_type}")
        
        with col2:
            relevance = source.get('relevance_score', 0)
            if isinstance(relevance, (int, float)):
                st.metric("רלוונטיות", f"{relevance:.2%}")
        
        with col3:
            chunk_index = source.get('chunk_index', '')
            if chunk_index:
                st.metric("קטע", str(chunk_index))
        
        with col4:
            # Additional info button
            if st.button("ℹ️", key=f"info_{index}"):
                self._show_source_details(source)
        
        # Content
        content = source.get('content', '')
        if content:
            with st.expander(f"📄 תוכן מקור {index}", expanded=False):
                st.markdown(content)
        
        # Metadata if requested
        if include_metadata:
            metadata = source.get('source_metadata', {})
            if metadata:
                with st.expander(f"🔧 מטא-דטה מקור {index}", expanded=False):
                    st.json(metadata)
    
    def _render_search_metadata(self, result: Dict[str, Any]) -> None:
        """Render search metadata and performance info"""
        with st.expander("🔧 מידע טכני על החיפוש", expanded=False):
            
            metadata = {
                'search_strategy': result.get('search_strategy', 'לא ידוע'),
                'timestamp': result.get('timestamp', ''),
                'has_context': result.get('has_context', False),
                'processing_time': result.get('processing_time', 'לא ידוע'),
                'sources_count': len(result.get('sources', [])),
                'model_used': result.get('model_used', 'לא ידוע')
            }
            
            st.json(metadata)
    
    def _show_source_details(self, source: Dict[str, Any]) -> None:
        """Show detailed source information in modal-like interface"""
        st.markdown("### 📄 פרטי מקור מפורטים")
        
        # All source information
        source_info = {
            'קובץ': source.get('file', 'לא ידוע'),
            'סוג מסמך': source.get('document_type', 'לא ידוע'),
            'רלוונטיות': f"{source.get('relevance_score', 0):.2%}",
            'אינדקס קטע': source.get('chunk_index', 'לא ידוע'),
            'תוכן': source.get('content', 'לא זמין')[:500] + "..."
        }
        
        for key, value in source_info.items():
            st.text(f"{key}: {value}")
        
        # Full metadata if available
        metadata = source.get('source_metadata', {})
        if metadata:
            st.markdown("**מטא-דטה מלא:**")
            st.json(metadata)
    
    def _show_detailed_search_statistics(self) -> None:
        """Show detailed search statistics"""
        stats = self.search.get_search_statistics()
        
        st.markdown("### 📊 סטטיסטיקות חיפוש מפורטות")
        
        if stats.get('total_searches', 0) > 0:
            # Overview metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("🔍 סה\"כ חיפושים", stats.get('total_searches', 0))
            
            with col2:
                success_rate = stats.get('success_rate', 0) * 100
                st.metric("✅ אחוז הצלחה", f"{success_rate:.1f}%")
            
            with col3:
                successful = stats.get('successful_searches', 0)
                st.metric("✅ חיפושים מוצלחים", successful)
            
            # Strategy breakdown
            strategies = stats.get('strategies_used', {})
            if strategies:
                st.markdown("**📈 פילוח לפי שיטות:**")
                
                for strategy, count in strategies.items():
                    percentage = (count / stats['total_searches']) * 100
                    st.text(f"• {strategy}: {count} ({percentage:.1f}%)")
            
            # Last search info
            last_search = stats.get('last_search')
            if last_search:
                try:
                    last_time = datetime.fromisoformat(last_search)
                    formatted_time = last_time.strftime("%d/%m/%Y %H:%M")
                    st.caption(f"🕐 חיפוש אחרון: {formatted_time}")
                except:
                    st.caption(f"🕐 חיפוש אחרון: {last_search}")
        
        else:
            st.info("📭 עדיין לא בוצעו חיפושים במערכת")
    
    def _clear_search_history(self) -> None:
        """Clear search history with confirmation"""
        st.markdown("### 🗑️ ניקוי היסטוריית חיפוש")
        
        stats = self.search.get_search_statistics()
        total_searches = stats.get('total_searches', 0)
        
        if total_searches == 0:
            st.info("📭 אין היסטוריית חיפוש למחיקה")
            return
        
        st.warning(f"⚠️ פעולה זו תמחק את כל היסטוריית החיפוש ({total_searches} רשומות)")
        
        if st.checkbox("✅ אני מבין שההיסטוריה תימחק לצמיתות"):
            if st.button("🗑️ מחק היסטוריה", type="primary"):
                # Clear search history
                self.search.search_history.clear()
                st.success("✅ היסטוריית החיפוש נמחקה")
    
    def _export_search_results(self) -> None:
        """Export search results to downloadable file"""
        stats = self.search.get_search_statistics()
        
        if stats.get('total_searches', 0) == 0:
            st.info("📭 אין תוצאות חיפוש לייצוא")
            return
        
        # Prepare export data
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'search_statistics': stats,
            'search_history': self.search.search_history[-50:]  # Last 50 searches
        }
        
        import json
        json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
        
        st.download_button(
            "📥 הורד תוצאות חיפוש",
            data=json_str,
            file_name=f"search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    def _show_search_settings(self) -> None:
        """Show search configuration settings"""
        st.markdown("### ⚙️ הגדרות חיפוש")
        
        # Default settings
        st.markdown("**🔧 הגדרות ברירת מחדל:**")
        
        default_max_results = st.number_input(
            "מספר תוצאות מקסימלי:",
            min_value=5,
            max_value=100,
            value=MAX_SEARCH_RESULTS,
            help="מספר התוצאות המקסימלי בחיפוש רגיל"
        )
        
        default_similarity = st.slider(
            "רמת דמיון מינימלית:",
            min_value=0.1,
            max_value=0.9,
            value=DEFAULT_SIMILARITY_THRESHOLD,
            step=0.1,
            help="רמת הדמיון המינימלית הנדרשת בחיפוש"
        )
        
        enable_auto_suggestions = st.checkbox(
            "הפעל הצעות אוטומטיות",
            value=True,
            help="הצג הצעות חיפוש בהתבסס על המסמכים"
        )
        
        # Performance settings
        st.markdown("**⚡ הגדרות ביצועים:**")
        
        search_timeout = st.number_input(
            "זמן המתנה מקסימלי (שניות):",
            min_value=10,
            max_value=120,
            value=30,
            help="זמן המתנה מקסימלי לחיפוש לפני timeout"
        )
        
        cache_results = st.checkbox(
            "שמור תוצאות בזיכרון",
            value=True,
            help="שמירת תוצאות חיפוש בזיכרון לביצועים טובים יותר"
        )
        
        # Save settings
        if st.button("💾 שמור הגדרות"):
            settings = {
                'default_max_results': default_max_results,
                'default_similarity': default_similarity,
                'enable_auto_suggestions': enable_auto_suggestions,
                'search_timeout': search_timeout,
                'cache_results': cache_results,
                'updated_at': datetime.now().isoformat()
            }
            
            # Save to session state or persistent storage
            st.session_state.search_settings = settings
            st.success("✅ הגדרות נשמרו")
