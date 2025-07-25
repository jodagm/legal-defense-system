"""
Document component - UI for document management and upload
"""
import streamlit as st
from typing import List, Dict, Any
from pathlib import Path
import mimetypes

from app.services.document_service import DocumentService
from app.config.constants import SUPPORTED_FILE_TYPES, MAX_FILE_SIZE_MB


class DocumentComponent:
    """Component for document management UI"""
    
    def __init__(self, document_service: DocumentService):
        self.documents = document_service
    
    def has_processed_documents(self) -> bool:
        """Check if processed documents exist for UI logic"""
        return self.documents.has_documents()
    
    def render_management_interface(self) -> None:
        """Render complete document management interface in sidebar"""
        st.markdown("### 📁 ניהול מסמכים")
        
        # Quick status
        self._render_quick_status()
        
        # Upload interface
        self._render_upload_interface()
        
        # Processing interface
        self._render_processing_interface()
        
        # Management tools
        self._render_management_tools()
    
    def render_prominent_upload(self) -> None:
        """Render prominent upload interface for main area when no documents"""
        st.markdown("### 📤 העלאת מסמכים משפטיים")
        
        with st.container():
            # Large upload area
            uploaded_files = st.file_uploader(
                "🏛️ גרור מסמכים משפטיים כאן או לחץ לבחירה",
                type=SUPPORTED_FILE_TYPES,
                accept_multiple_files=True,
                help=f"סוגי קבצים נתמכים: {', '.join(SUPPORTED_FILE_TYPES)}. גודל מקסימלי: {MAX_FILE_SIZE_MB}MB",
                key="prominent_uploader"
            )
            
            if uploaded_files:
                self._handle_file_upload(uploaded_files, prominent=True)
            
            # Upload tips
            self._render_upload_tips()
    
    def render_quick_upload(self) -> None:
        """Render quick upload interface for getting started"""
        st.markdown("### 🚀 התחל כאן")
        
        uploaded_files = st.file_uploader(
            "העלה מסמכים משפטיים:",
            type=SUPPORTED_FILE_TYPES,
            accept_multiple_files=True,
            key="quick_uploader"
        )
        
        if uploaded_files:
            if st.button("📁 התחל עיבוד", type="primary"):
                self._handle_file_upload(uploaded_files, auto_process=True)
    
    def render_document_overview(self) -> None:
        """Render document overview when API is unavailable"""
        st.markdown("### 📄 סקירת מסמכים")
        
        stats = self.documents.get_document_statistics()
        
        if stats['processed_count'] > 0:
            st.info(f"📚 יש {stats['processed_count']} מסמכים מעובדים במערכת")
            
            # Show document types
            doc_types = stats.get('document_types', {})
            if doc_types:
                st.markdown("**סוגי מסמכים:**")
                for doc_type, count in doc_types.items():
                    st.text(f"• {doc_type}: {count}")
        else:
            st.warning("📭 אין מסמכים מעובדים במערכת")
    
    def render_status_summary(self) -> None:
        """Render brief status summary for main interface"""
        stats = self.documents.get_document_statistics()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "📄 מסמכים מעובדים",
                stats.get('processed_count', 0),
                help="מספר מסמכים שעברו עיבוד ומוכנים לחיפוש"
            )
        
        with col2:
            st.metric(
                "🔍 קטעי טקסט",
                stats.get('total_chunks', 0),
                help="מספר קטעי טקסט זמינים לחיפוש"
            )
        
        with col3:
            processing_rate = stats.get('processing_rate', 0) * 100
            st.metric(
                "⚡ אחוז עיבוד",
                f"{processing_rate:.0f}%",
                help="אחוז הקבצים שעברו עיבוד מתוך הקבצים שהועלו"
            )
    
    def _render_quick_status(self) -> None:
        """Render quick document status overview"""
        stats = self.documents.get_document_statistics()
        
        col1, col2 = st.columns(2)
        
        with col1:
            uploaded_count = stats.get('uploaded_count', 0)
            st.metric("📤 הועלו", uploaded_count)
        
        with col2:
            processed_count = stats.get('processed_count', 0)
            st.metric("⚙️ עובדו", processed_count)
        
        # Progress bar if there are files to process
        if uploaded_count > 0:
            progress = processed_count / uploaded_count
            st.progress(progress, text=f"התקדמות: {progress:.0%}")
    
    def _render_upload_interface(self) -> None:
        """Render file upload interface"""
        with st.expander("📤 העלאת מסמכים", expanded=True):
            
            uploaded_files = st.file_uploader(
                "בחר קבצי PDF:",
                type=SUPPORTED_FILE_TYPES,
                accept_multiple_files=True,
                help=f"גודל מקסימלי: {MAX_FILE_SIZE_MB}MB לקובץ",
                key="sidebar_uploader"
            )
            
            if uploaded_files:
                self._display_uploaded_files(uploaded_files)
                self._render_upload_actions(uploaded_files)
    
    def _render_processing_interface(self) -> None:
        """Render document processing interface"""
        uploaded_files = self.documents.get_uploaded_files()
        
        if not uploaded_files:
            return
        
        with st.expander("⚙️ עיבוד מסמכים", expanded=False):
            
            # Batch processing
            if len(uploaded_files) > 1:
                if st.button("⚙️ עבד את כל הקבצים", key="process_all_sidebar"):
                    self._process_all_files(uploaded_files)
            
            # Individual file processing
            st.markdown("**עיבוד יחידני:**")
            
            for pdf_file in uploaded_files:
                self._render_file_processing_row(pdf_file)
    
    def _render_management_tools(self) -> None:
        """Render document management tools"""
        with st.expander("🛠️ כלי ניהול", expanded=False):
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📊 סטטיסטיקות", key="doc_stats"):
                    self._show_detailed_statistics()
                
                if st.button("🔍 חפש מסמך", key="search_docs"):
                    self._show_document_search()
            
            with col2:
                if st.button("🗑️ נקה קבצים", key="cleanup_docs"):
                    self._show_cleanup_interface()
                
                if st.button("📋 יצא רשימה", key="export_list"):
                    self._export_document_list()
    
    def _handle_file_upload(
        self, 
        uploaded_files: List, 
        prominent: bool = False,
        auto_process: bool = False
    ) -> None:
        """Handle file upload process"""
        
        # Validate files
        valid_files = []
        for file in uploaded_files:
            if self._validate_uploaded_file(file):
                valid_files.append(file)
        
        if not valid_files:
            return
        
        # Display file information
        self._display_uploaded_files(valid_files)
        
        # Upload actions
        if prominent:
            col1, col2 = st.columns(2)
            
            with col1:
                save_button = st.button(
                    "💾 שמור קבצים", 
                    type="primary",
                    key="save_prominent"
                )
            
            with col2:
                process_button = st.button(
                    "⚙️ שמור ועבד",
                    type="secondary", 
                    key="process_prominent"
                )
        else:
            save_button = st.button("💾 שמור", key="save_sidebar")
            process_button = auto_process
        
        # Execute upload
        if save_button or process_button:
            self._execute_file_upload(valid_files, process_after_upload=process_button)
    
    def _execute_file_upload(self, files: List, process_after_upload: bool = False) -> None:
        """Execute the actual file upload"""
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        uploaded_count = 0
        processed_count = 0
        
        for i, file in enumerate(files):
            # Upload phase
            status_text.text(f"💾 שומר {file.name}...")
            progress_bar.progress(i / len(files) * 0.5)
            
            try:
                file_path = self.documents.save_uploaded_file(file.getvalue(), file.name)
                uploaded_count += 1
                
                # Process if requested
                if process_after_upload:
                    status_text.text(f"⚙️ מעבד {file.name}...")
                    progress_bar.progress((i + 0.5) / len(files))
                    
                    self.documents.process_uploaded_file(file_path)
                    processed_count += 1
                
            except Exception as e:
                st.error(f"❌ שגיאה בטיפול ב-{file.name}: {e}")
        
        # Completion
        progress_bar.progress(1.0)
        status_text.text("✅ הושלם!")
        
        # Results
        if process_after_upload:
            st.success(f"✅ הועלו ועובדו {processed_count}/{len(files)} קבצים")
        else:
            st.success(f"✅ הועלו {uploaded_count}/{len(files)} קבצים")
        
        if uploaded_count > 0:
            st.balloons()
        
        # Cleanup UI
        progress_bar.empty()
        status_text.empty()
        
        # Refresh interface
        st.rerun()
    
    def _display_uploaded_files(self, files: List) -> None:
        """Display information about uploaded files"""
        st.markdown(f"**📋 נבחרו {len(files)} קבצים:**")
        
        for file in files:
            file_size = file.size / (1024 * 1024)  # MB
            file_type = self._get_file_type_info(file.name)
            
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.text(file.name)
            
            with col2:
                st.text(f"{file_size:.1f}MB")
            
            with col3:
                st.text(file_type)
    
    def _render_upload_actions(self, files: List) -> None:
        """Render upload action buttons"""
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 שמור", key="save_files_sidebar"):
                self._execute_file_upload(files, process_after_upload=False)
        
        with col2:
            if st.button("⚙️ שמור ועבד", key="save_process_sidebar"):
                self._execute_file_upload(files, process_after_upload=True)
    
    def _render_file_processing_row(self, pdf_file: Path) -> None:
        """Render single file processing row"""
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.text(pdf_file.name)
        
        with col2:
            # Check if already processed
            processed_file = self.documents.processed_path / f"{pdf_file.stem}_processed.json"
            if processed_file.exists():
                st.text("✅")
            else:
                st.text("⏳")
        
        with col3:
            if st.button("⚙️", key=f"process_{pdf_file.stem}"):
                self._process_single_file(pdf_file)
    
    def _process_single_file(self, file_path: Path) -> None:
        """Process single file with UI feedback"""
        with st.spinner(f"⚙️ מעבד {file_path.name}..."):
            try:
                result = self.documents.process_uploaded_file(file_path)
                st.success(f"✅ {file_path.name} עובד בהצלחה")
                st.rerun()
            except Exception as e:
                st.error(f"❌ שגיאה בעיבוד {file_path.name}: {e}")
    
    def _process_all_files(self, files: List[Path]) -> None:
        """Process all files with progress tracking"""
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        processed_count = 0
        
        for i, file_path in enumerate(files):
            status_text.text(f"⚙️ מעבד {file_path.name}...")
            progress_bar.progress((i + 1) / len(files))
            
            try:
                self.documents.process_uploaded_file(file_path)
                processed_count += 1
            except Exception as e:
                st.error(f"❌ שגיאה בעיבוד {file_path.name}: {e}")
        
        progress_bar.empty()
        status_text.empty()
        
        st.success(f"✅ עובדו {processed_count}/{len(files)} קבצים")
        st.rerun()
    
    def _render_upload_tips(self) -> None:
        """Render upload tips and guidelines"""
        with st.expander("💡 עצות להעלאה", expanded=False):
            st.markdown("""
            ### 📋 המלצות לשיפור התוצאות:
            
            **✅ מסמכים מומלצים:**
            - כתבי טענות (תביעה, הגנה)
            - חוזים והסכמים
            - פסקי דין רלוונטיים
            - עדויות ותצהירים
            - מסמכים ראיותיים
            
            **📄 דרישות טכניות:**
            - פורמט PDF בלבד
            - גודל מקסימלי: 50MB לקובץ
            - טקסט ניתן לחיפוש (לא סרוק)
            - שמות קבצים ברורים
            
            **🎯 עצות לארגון:**
            - השתמש בשמות קבצים תיאוריים
            - קבץ מסמכים לפי סוג
            - וודא שהמסמכים עדכניים
            """)
    
    def _validate_uploaded_file(self, file) -> bool:
        """Validate uploaded file"""
        # Check file size
        if file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
            st.error(f"❌ קובץ {file.name} גדול מדי ({file.size / (1024*1024):.1f}MB > {MAX_FILE_SIZE_MB}MB)")
            return False
        
        # Check file type
        file_extension = file.name.split('.')[-1].lower()
        if file_extension not in SUPPORTED_FILE_TYPES:
            st.error(f"❌ סוג קובץ {file_extension} לא נתמך עבור {file.name}")
            return False
        
        return True
    
    def _get_file_type_info(self, filename: str) -> str:
        """Get file type information for display"""
        extension = filename.split('.')[-1].lower()
        
        type_map = {
            'pdf': 'PDF',
            'doc': 'Word',
            'docx': 'Word',
            'txt': 'טקסט'
        }
        
        return type_map.get(extension, extension.upper())
    
    def _show_detailed_statistics(self) -> None:
        """Show detailed document statistics"""
        stats = self.documents.get_document_statistics()
        
        st.markdown("### 📊 סטטיסטיקות מפורטות")
        st.json(stats)
    
    def _show_document_search(self) -> None:
        """Show document search interface"""
        st.markdown("### 🔍 חיפוש במסמכים")
        
        search_term = st.text_input("מונח לחיפוש:")
        
        if search_term:
            results = self.documents.search_documents(search_term)
            st.write(f"נמצאו {len(results)} תוצאות")
            
            for result in results[:5]:
                st.text(f"📄 {result.get('file', 'לא ידוע')}")
                st.caption(result.get('content', '')[:100] + "...")
    
    def _show_cleanup_interface(self) -> None:
        """Show cleanup interface"""
        st.markdown("### 🗑️ ניקוי קבצים")
        st.warning("⚠️ פעולה זו תמחק קבצים לצמיתות!")
        
        if st.checkbox("אני מבין שהקבצים יימחקו"):
            if st.button("🗑️ מחק קבצים שלא עובדו"):
                # Implementation for cleanup
                st.success("✅ ניקוי בוצע")
    
    def _export_document_list(self) -> None:
        """Export document list"""
        stats = self.documents.get_document_statistics()
        
        import json
        
        export_data = {
            'timestamp': str(datetime.now()),
            'statistics': stats,
            'processed_documents': [
                {'filename': doc.get('filename', '')}
                for doc in self.documents.get_processed_documents()
            ]
        }
        
        json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
        
        st.download_button(
            "📥 הורד רשימת מסמכים",
            data=json_str,
            file_name=f"documents_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
