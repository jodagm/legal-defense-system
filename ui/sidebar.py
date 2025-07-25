"""
סרגל צדדי מתקדם לניהול מערכת הגנה משפטית
גרסה 2.2.0 עם ממשק מתקדם, כלי ניהול וניטור מערכת
"""
import streamlit as st
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# ייבואים עם fallbacks
try:
    from ui.file_uploader import (
        show_smart_document_uploader, 
        show_document_processing, 
        show_files_status, 
        show_debug_info
    )
    FILE_UPLOADER_AVAILABLE = True
except ImportError:
    FILE_UPLOADER_AVAILABLE = False
    print("⚠️ File uploader module not available - using fallback")

try:
    from config.settings import (
        QUICK_QUESTIONS, COMPREHENSIVE_TASKS,
        DOCUMENT_TYPES, UI_MESSAGES
    )
    SETTINGS_AVAILABLE = True
except ImportError:
    SETTINGS_AVAILABLE = False
    # ברירות מחדל
    QUICK_QUESTIONS = [
        "מהן הטענות העיקריות בכתב התביעה?",
        "מה הראיות המרכזיות בתיק?",
        "אילו סתירות יש במסמכים?"
    ]
    COMPREHENSIVE_TASKS = [
        ("🏛️ אסטרטגיית הגנה מלאה", "defense_strategy"),
        ("🔍 ניתוח סתירות מקיף", "contradictions"),
        ("📋 סיכום מנהלים", "executive_summary")
    ]
    DOCUMENT_TYPES = {}
    UI_MESSAGES = {}

try:
    from core.file_manager import SmartFileManager
    FILE_MANAGER_AVAILABLE = True
except ImportError:
    FILE_MANAGER_AVAILABLE = False

try:
    from processors.legal_summary import LegalSummaryProcessor
    SUMMARY_PROCESSOR_AVAILABLE = True
except ImportError:
    SUMMARY_PROCESSOR_AVAILABLE = False


class SidebarManager:
    """מנהל סרגל צדדי מתקדם עם ניטור ומעקב"""
    
    def __init__(self):
        self.session_id = st.session_state.get('session_id', datetime.now().strftime("%Y%m%d_%H%M%S"))
        self.operation_count = 0
        
    def log_operation(self, operation: str, details: str = ""):
        """רשום פעולה"""
        self.operation_count += 1
        if 'sidebar_operations' not in st.session_state:
            st.session_state.sidebar_operations = []
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'details': details,
            'count': self.operation_count
        }
        
        st.session_state.sidebar_operations.append(entry)
        # הגבל ל-50 פעולות אחרונות
        if len(st.session_state.sidebar_operations) > 50:
            st.session_state.sidebar_operations = st.session_state.sidebar_operations[-50:]


# מנהל סרגל גלובלי
sidebar_manager = SidebarManager()


def show_sidebar(chatbot):
    """סרגל צדדי ראשי מתקדם"""
    with st.sidebar:
        # כותרת מתקדמת
        show_sidebar_header()
        
        # מצב מערכת מהיר
        show_quick_system_status(chatbot)
        
        st.divider()
        
        # ניהול מסמכים מתקדם
        show_advanced_document_management(chatbot)
        
        st.divider()
        
        # סיכומים משפטיים
        show_legal_summaries_section(chatbot)
        
        st.divider()
        
        # חיפוש וטעינה
        show_search_management(chatbot)
        
        st.divider()
        
        # שאלות מהירות ומשימות
        show_quick_actions_section(chatbot)
        
        st.divider()
        
        # כלי ניהול מתקדמים
        show_advanced_management_tools(chatbot)
        
        st.divider()
        
        # מידע וסטטיסטיקות
        show_system_info_section(chatbot)


def show_sidebar_header():
    """כותרת סרגל מתקדמת"""
    st.markdown("""
    <div style="text-align: center; padding: 1rem; background: linear-gradient(90deg, #1f4e79, #2d5a8b); 
                color: white; border-radius: 10px; margin-bottom: 1rem;">
        <h3>🏛️ מערכת הגנה משפטית</h3>
        <p style="margin: 0; font-size: 0.9rem;">ממשק ניהול מתקדם</p>
    </div>
    """, unsafe_allow_html=True)


def show_quick_system_status(chatbot):
    """מצב מערכת מהיר"""
    st.markdown("### 📊 מצב מערכת")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # מצב Claude API
        if hasattr(chatbot, 'claude_client') and chatbot.claude_client:
            st.metric(
                "🤖 AI", 
                "מחובר", 
                delta="Claude",
                help="חיבור Claude API פעיל - מערכת AI מלאה זמינה"
            )
        else:
            st.metric(
                "🤖 AI", 
                "לא זמין", 
                delta="בדוק API",
                delta_color="inverse",
                help="אין חיבור ל-Claude - בדוק API key"
            )
    
    with col2:
        # מסמכים טעונים
        try:
            if hasattr(chatbot, 'get_documents_info'):
                docs_info = chatbot.get_documents_info()
                chunks_count = docs_info.get('total_chunks', 0)
            elif hasattr(chatbot, 'document_chunks'):
                chunks_count = len(chatbot.document_chunks)
            else:
                chunks_count = count_files_safe("data/processed", "*.json")
            
            st.metric(
                "📄 מסמכים", 
                chunks_count,
                help="מספר קטעי מסמכים טעונים למערכת החיפוש"
            )
        except Exception as e:
            st.metric("📄 מסמכים", "שגיאה", help=f"שגיאה: {e}")


def show_advanced_document_management(chatbot):
    """ניהול מסמכים מתקדם"""
    st.markdown("### 📁 ניהול מסמכים")
    
    # העלאת מסמכים
    with st.expander("📤 העלאת מסמכים חדשים", expanded=False):
        if FILE_UPLOADER_AVAILABLE:
            show_smart_document_uploader()
        else:
            show_basic_file_uploader()
    
    # עיבוד מסמכים
    with st.expander("⚙️ עיבוד מסמכים", expanded=False):
        if FILE_UPLOADER_AVAILABLE:
            show_document_processing()
        else:
            show_basic_document_processing()
    
    # מצב קבצים
    show_files_overview()


def show_basic_file_uploader():
    """העלאת קבצים בסיסית"""
    st.markdown("**העלאה בסיסית:**")
    
    uploaded_files = st.file_uploader(
        "בחר קבצי PDF:",
        type=['pdf'],
        accept_multiple_files=True,
        help="העלה קבצי PDF משפטיים לעיבוד"
    )
    
    if uploaded_files:
        st.success(f"✅ נבחרו {len(uploaded_files)} קבצים")
        
        if st.button("💾 שמור קבצים", key="basic_save_files"):
            saved_count = 0
            upload_dir = Path("data/uploaded_documents")
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            for file in uploaded_files:
                try:
                    file_path = upload_dir / file.name
                    with open(file_path, 'wb') as f:
                        f.write(file.getvalue())
                    saved_count += 1
                except Exception as e:
                    st.error(f"שגיאה בשמירת {file.name}: {e}")
            
            if saved_count:
                st.success(f"✅ נשמרו {saved_count} קבצים")
                sidebar_manager.log_operation("basic_file_upload", f"Saved {saved_count} files")


def show_basic_document_processing():
    """עיבוד מסמכים בסיסי"""
    uploaded_dir = Path("data/uploaded_documents")
    
    if not uploaded_dir.exists():
        st.info("📁 אין קבצים להעברה - העלה קבצים תחילה")
        return
    
    pdf_files = list(uploaded_dir.glob("*.pdf"))
    
    if not pdf_files:
        st.info("📄 אין קבצי PDF לעיבוד")
        return
    
    st.markdown(f"**קבצים זמינים לעיבוד:** {len(pdf_files)}")
    
    for pdf_file in pdf_files:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text(pdf_file.name)
        with col2:
            if st.button("⚙️", key=f"process_{pdf_file.stem}", help="עבד קובץ"):
                process_single_file_basic(pdf_file)


def process_single_file_basic(pdf_file: Path):
    """עבד קובץ יחיד בעיבוד בסיסי"""
    try:
        with st.spinner(f"עובד {pdf_file.name}..."):
            # זו דוגמה בסיסית - במערכת אמיתית צריך מעבד PDF
            processed_data = {
                'filename': pdf_file.name,
                'processed_at': datetime.now().isoformat(),
                'status': 'completed',
                'chunks': [{'id': 1, 'text': 'תוכן בסיסי - דרוש מעבד PDF מתקדם'}]
            }
            
            processed_dir = Path("data/processed")
            processed_dir.mkdir(parents=True, exist_ok=True)
            
            output_file = processed_dir / f"{pdf_file.stem}_processed.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, ensure_ascii=False, indent=2)
            
            st.success(f"✅ {pdf_file.name} עובד בהצלחה")
            sidebar_manager.log_operation("basic_file_processing", pdf_file.name)
            
    except Exception as e:
        st.error(f"❌ שגיאה בעיבוד {pdf_file.name}: {e}")


def show_files_overview():
    """סקירת קבצים מהירה"""
    st.markdown("**📊 סקירת קבצים:**")
    
    try:
        stats = {
            'PDF': count_files_safe("data/uploaded_documents", "*.pdf"),
            'מעובדים': count_files_safe("data/processed", "*.json"),
            'סיכומים': count_files_safe("data/summaries", "*.json")
        }
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📄", stats['PDF'], help="קבצי PDF שהועלו")
        with col2:
            st.metric("⚙️", stats['מעובדים'], help="מסמכים מעובדים")
        with col3:
            st.metric("📋", stats['סיכומים'], help="סיכומים משפטיים")
            
        # אחוז השלמה
        if stats['PDF'] > 0:
            processing_pct = (stats['מעובדים'] / stats['PDF']) * 100
            summary_pct = (stats['סיכומים'] / stats['PDF']) * 100
            
            st.progress(processing_pct / 100, text=f"עיבוד: {processing_pct:.0f}%")
            st.progress(summary_pct / 100, text=f"סיכומים: {summary_pct:.0f}%")
            
    except Exception as e:
        st.error(f"שגיאה בהצגת סטטיסטיקות: {e}")


def show_legal_summaries_section(chatbot):
    """סקציית סיכומים משפטיים"""
    st.markdown("### 📋 סיכומים משפטיים")
    
    # בדוק זמינות מעבד הסיכומים
    if not SUMMARY_PROCESSOR_AVAILABLE:
        st.warning("⚠️ מעבד הסיכומים לא זמין")
        return
    
    try:
        summary_processor = LegalSummaryProcessor(chatbot)
        existing_summaries = summary_processor.get_all_summaries()
        
        # הצג מצב נוכחי
        if existing_summaries:
            st.info(f"📋 קיימים {len(existing_summaries)} סיכומים משפטיים")
        else:
            st.info("📋 אין סיכומים משפטיים")
        
        # יצירת סיכומים חדשים
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📝 צור סיכומים", key="create_summaries_main", 
                        help="יוצר סיכומים משפטיים לכל המסמכים המעובדים"):
                create_legal_summaries(chatbot, summary_processor)
        
        with col2:
            if st.button("🗑️ מחק סיכומים", key="delete_summaries_main",
                        help="מוחק את כל הסיכומים הקיימים"):
                delete_all_summaries(summary_processor)
        
        # הצג סיכומים קיימים
        if existing_summaries:
            with st.expander("📋 סיכומים קיימים", expanded=False):
                for summary in existing_summaries[:5]:  # הצג עד 5 ראשונים
                    doc_name = summary.get('document_name', 'לא ידוע')
                    doc_type = summary.get('document_type', 'מסמך')
                    created = summary.get('created_at', '')
                    
                    st.markdown(f"**{doc_name}** ({doc_type})")
                    if created:
                        try:
                            created_date = datetime.fromisoformat(created).strftime("%d/%m/%Y %H:%M")
                            st.caption(f"נוצר: {created_date}")
                        except:
                            st.caption(f"נוצר: {created}")
                    st.markdown("---")
                
                if len(existing_summaries) > 5:
                    st.caption(f"ועוד {len(existing_summaries) - 5} סיכומים...")
                        
    except Exception as e:
        st.error(f"❌ שגיאה בסקציית הסיכומים: {e}")


def create_legal_summaries(chatbot, summary_processor):
    """יצור סיכומים משפטיים עם פרוגרס"""
    if not hasattr(chatbot, 'claude_client') or not chatbot.claude_client:
        st.error("❌ נדרש חיבור Claude API ליצירת סיכומים משפטיים")
        return
    
    with st.spinner("📝 יוצר סיכומים משפטיים מתקדמים..."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text("🔍 מאתר מסמכים לעיבוד...")
            progress_bar.progress(10)
            
            summaries = summary_processor.process_all_documents_to_summaries()
            
            progress_bar.progress(50)
            status_text.text("📝 מעבד סיכומים...")
            
            if summaries:
                progress_bar.progress(100)
                status_text.text("✅ הושלם!")
                
                st.success(f"✅ נוצרו {len(summaries)} סיכומים משפטיים!")
                st.balloons()
                sidebar_manager.log_operation("create_summaries", f"Created {len(summaries)} summaries")
                
                time.sleep(2)
                progress_bar.empty()
                status_text.empty()
                st.rerun()
            else:
                progress_bar.empty()
                status_text.empty()
                st.warning("⚠️ לא נוצרו סיכומים - וודא שיש מסמכים מעובדים")
                
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"❌ שגיאה ביצירת סיכומים: {e}")


def delete_all_summaries(summary_processor):
    """מחק את כל הסיכומים עם אישור"""
    with st.expander("🗑️ אישור מחיקת סיכומים", expanded=True):
        st.warning("⚠️ פעולה זו תמחק את כל הסיכומים המשפטיים!")
        
        if st.checkbox("✅ אני מבין שהסיכומים יימחקו לצמיתות"):
            if st.button("🗑️ מחק את כל הסיכומים", key="confirm_delete_summaries"):
                try:
                    summary_processor.delete_all_summaries()
                    st.success("✅ כל הסיכומים נמחקו")
                    sidebar_manager.log_operation("delete_summaries", "All summaries deleted")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ שגיאה במחיקת סיכומים: {e}")


def show_search_management(chatbot):
    """ניהול חיפוש וטעינה"""
    st.markdown("### 🔍 ניהול חיפוש")
    
    # טעינת מסמכים לחיפוש
    if st.button("📚 טען מסמכים לחיפוש", key="load_docs_search", 
                help="טוען את כל המסמכים המעובדים למערכת החיפוש"):
        load_documents_for_search(chatbot)
    
    # רענון מסמכים
    if st.button("🔄 רענן מסמכים", key="reload_docs",
                help="טוען מחדש את כל המסמכים מהדיסק"):
        reload_documents(chatbot)
    
    # נקה cache חיפוש
    if st.button("🧹 נקה cache חיפוש", key="clear_search_cache",
                help="מנקה את cache המערכת חיפוש"):
        clear_search_cache(chatbot)


def load_documents_for_search(chatbot):
    """טען מסמכים לחיפוש"""
    with st.spinner("📖 טוען מסמכים לחיפוש..."):
        try:
            if hasattr(chatbot, 'load_documents_for_search'):
                success = chatbot.load_documents_for_search()
            elif hasattr(chatbot, 'reload_documents'):
                chatbot.reload_documents()
                success = True
            elif hasattr(chatbot, '_load_documents'):
                chatbot._load_documents()
                success = True
            else:
                st.warning("⚠️ פונקציית טעינה לא זמינה")
                return
            
            if success:
                docs_info = get_documents_info_safe(chatbot)
                chunks_count = docs_info.get('total_chunks', 0)
                st.success(f"✅ נטענו {chunks_count} קטעי טקסט לחיפוש!")
                sidebar_manager.log_operation("load_documents", f"Loaded {chunks_count} chunks")
            else:
                st.error("❌ שגיאה בטעינת המסמכים")
                
        except Exception as e:
            st.error(f"❌ שגיאה בטעינה: {e}")


def reload_documents(chatbot):
    """רענן מסמכים"""
    with st.spinner("🔄 מרענן מסמכים..."):
        try:
            if hasattr(chatbot, 'reload_documents'):
                chatbot.reload_documents()
                st.success("✅ מסמכים ריפש מוצלח!")
                sidebar_manager.log_operation("reload_documents", "Documents reloaded")
            else:
                st.warning("⚠️ פונקציית רענון לא זמינה")
        except Exception as e:
            st.error(f"❌ שגיאה ברענון: {e}")


def clear_search_cache(chatbot):
    """נקה cache חיפוש"""
    try:
        if hasattr(chatbot, 'clear_search_cache'):
            chatbot.clear_search_cache()
        
        # נקה גם Streamlit cache
        st.cache_data.clear()
        
        st.success("✅ Cache נוקה!")
        sidebar_manager.log_operation("clear_cache", "Search cache cleared")
        
    except Exception as e:
        st.error(f"❌ שגיאה בניקוי cache: {e}")


def show_quick_actions_section(chatbot):
    """סקציית פעולות מהירות"""
    st.markdown("### ⚡ פעולות מהירות")
    
    # שאלות מהירות
    with st.expander("🎯 שאלות מהירות", expanded=False):
        st.markdown("**חיפוש מהיר ללא הגבלות:**")
        
        for i, question in enumerate(QUICK_QUESTIONS[:5]):  # הגבל ל-5
            if st.button(
                f"❓ {question[:40]}{'...' if len(question) > 40 else ''}", 
                key=f"quick_{i}",
                help=f"שאלה מהירה: {question}"
            ):
                st.session_state.quick_question = question
                sidebar_manager.log_operation("quick_question", question[:50])
    
    # משימות מקיפות
    with st.expander("🏛️ משימות מקיפות", expanded=False):
        st.markdown("**ניתוח מקיף על בסיס סיכומים:**")
        
        # בדוק זמינות סיכומים
        summaries_available = check_summaries_availability()
        
        if not summaries_available:
            st.info("ℹ️ צור סיכומים משפטיים תחילה")
        
        for task_name, task_type in COMPREHENSIVE_TASKS[:5]:  # הגבל ל-5
            if st.button(
                task_name, 
                key=f"comp_{task_type}",
                disabled=not summaries_available,
                help=f"משימה מקיפה: {task_name}"
            ):
                if summaries_available:
                    st.session_state.comprehensive_task = task_type
                    sidebar_manager.log_operation("comprehensive_task", task_type)
                else:
                    st.warning("⚠️ צור סיכומים משפטיים תחילה!")


def check_summaries_availability() -> bool:
    """בדוק זמינות סיכומים"""
    try:
        if SUMMARY_PROCESSOR_AVAILABLE:
            from processors.legal_summary import LegalSummaryProcessor
            chatbot = st.session_state.get('chatbot')
            if chatbot:
                summary_processor = LegalSummaryProcessor(chatbot)
                summaries = summary_processor.get_all_summaries()
                return len(summaries) > 0
    except:
        pass
    
    # בדיקה חלופית
    summaries_dir = Path("data/summaries")
    if summaries_dir.exists():
        summary_files = list(summaries_dir.glob("*.json"))
        return len(summary_files) > 0
    
    return False


def show_advanced_management_tools(chatbot):
    """כלי ניהול מתקדמים"""
    with st.expander("🛠️ כלי ניהול מתקדמים", expanded=False):
        
        # ניהול מערכת
        st.markdown("**⚡ ניהול מערכת:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # בדיקת מערכת
            if st.button("🔍 בדוק מערכת", key="check_system_sidebar"):
                run_system_check(chatbot)
            
            # ניקוי כללי
            if st.button("🧹 ניקוי כללי", key="general_cleanup"):
                perform_general_cleanup()
        
        with col2:
            # גיבוי הגדרות
            if st.button("💾 גבה הגדרות", key="backup_settings"):
                backup_system_settings()
            
            # איפוס מוגן
            if st.button("🔄 איפוס מוגן", key="protected_reset"):
                show_protected_reset_interface()


def run_system_check(chatbot):
    """בצע בדיקת מערכת מקיפה"""
    with st.spinner("🔍 בודק מערכת..."):
        checks = {
            'Claude API': check_claude_connection(chatbot),
            'מסמכים': check_documents_status(chatbot),
            'תיקיות': check_directories(),
            'Cache': check_cache_status(chatbot)
        }
        
        st.markdown("**📊 תוצאות בדיקה:**")
        for check_name, (status, details) in checks.items():
            status_icon = "✅" if status else "❌"
            st.write(f"{status_icon} **{check_name}**: {details}")
        
        sidebar_manager.log_operation("system_check", f"Checked {len(checks)} components")


def check_claude_connection(chatbot) -> tuple:
    """בדוק חיבור Claude"""
    try:
        if hasattr(chatbot, 'claude_client') and chatbot.claude_client:
            if hasattr(chatbot, 'test_connection'):
                success, message = chatbot.test_connection()
                return success, message
            else:
                return True, "אותחל אבל לא נבדק"
        else:
            return False, "לא מחובר - בדוק API key"
    except Exception as e:
        return False, f"שגיאה: {e}"


def check_documents_status(chatbot) -> tuple:
    """בדוק מצב מסמכים"""
    try:
        docs_info = get_documents_info_safe(chatbot)
        chunks_count = docs_info.get('total_chunks', 0)
        
        if chunks_count > 0:
            return True, f"{chunks_count} קטעי טקסט טעונים"
        else:
            return False, "אין מסמכים טעונים"
    except Exception as e:
        return False, f"שגיאה: {e}"


def check_directories() -> tuple:
    """בדוק תיקיות מערכת"""
    required_dirs = [
        "data", "data/uploaded_documents", "data/processed",
        "data/summaries", "data/metadata", "data/logs"
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)
    
    if not missing_dirs:
        return True, "כל התיקיות קיימות"
    else:
        return False, f"חסרות: {missing_dirs}"


def check_cache_status(chatbot) -> tuple:
    """בדוק מצב cache"""
    try:
        # בדוק אם יש vectorizer
        has_vectorizer = hasattr(chatbot, 'vectorizer') and chatbot.vectorizer is not None
        
        if has_vectorizer:
            return True, "Cache חיפוש פעיל"
        else:
            return False, "אין cache חיפוש"
    except Exception as e:
        return False, f"שגיאה: {e}"


def perform_general_cleanup():
    """בצע ניקוי כללי"""
    with st.spinner("🧹 מבצע ניקוי כללי..."):
        cleanup_results = []
        
        try:
            # נקה Streamlit cache
            st.cache_data.clear()
            cleanup_results.append("✅ Streamlit cache נוקה")
            
            # נקה קבצי temp (אם קיימים)
            temp_dir = Path("data/temp")
            if temp_dir.exists():
                import shutil
                shutil.rmtree(temp_dir)
                temp_dir.mkdir(parents=True, exist_ok=True)
                cleanup_results.append("✅ קבצי temp נוקו")
            
            # נקה לוגים ישנים
            logs_dir = Path("data/logs")
            if logs_dir.exists():
                old_logs = [f for f in logs_dir.glob("*.log") if f.stat().st_size > 10 * 1024 * 1024]  # > 10MB
                for log_file in old_logs:
                    log_file.unlink()
                if old_logs:
                    cleanup_results.append(f"✅ {len(old_logs)} לוגים ישנים נמחקו")
            
            st.success("✅ ניקוי הושלם!")
            for result in cleanup_results:
                st.text(result)
                
            sidebar_manager.log_operation("general_cleanup", f"Completed {len(cleanup_results)} operations")
            
        except Exception as e:
            st.error(f"❌ שגיאה בניקוי: {e}")


def backup_system_settings():
    """גבה הגדרות מערכת"""
    try:
        backup_data = {
            'timestamp': datetime.now().isoformat(),
            'session_operations': st.session_state.get('sidebar_operations', []),
            'system_stats': {
                'pdf_files': count_files_safe("data/uploaded_documents", "*.pdf"),
                'processed_files': count_files_safe("data/processed", "*.json"),
                'summaries': count_files_safe("data/summaries", "*.json")
            }
        }
        
        backup_dir = Path("data/backups")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        backup_file = backup_dir / f"system_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        st.success(f"✅ גיבוי נשמר: {backup_file.name}")
        sidebar_manager.log_operation("backup_settings", backup_file.name)
        
    except Exception as e:
        st.error(f"❌ שגיאה בגיבוי: {e}")


def show_protected_reset_interface():
    """הצג ממשק איפוס מוגן"""
    st.markdown("### 🚨 איפוס מוגן")
    st.warning("⚠️ פעולה זו תמחק את כל הנתונים!")
    
    # הצג מה יימחק
    stats = {
        'PDF files': count_files_safe("data/uploaded_documents", "*.pdf"),
        'Processed': count_files_safe("data/processed", "*.json"),
        'Summaries': count_files_safe("data/summaries", "*.json")
    }
    
    total_files = sum(stats.values())
    
    if total_files == 0:
        st.info("📭 אין נתונים למחיקה")
        return
    
    st.markdown(f"**קבצים שיימחקו: {total_files}**")
    for category, count in stats.items():
        st.write(f"• {category}: {count}")
    
    # אישורים
    confirm1 = st.checkbox(f"☑️ אני מבין ש-{total_files} קבצים יימחקו")
    
    if confirm1:
        confirm_text = st.text_input(
            "✍️ כתוב 'מחק הכל' לאישור:",
            help="חייב להקליד בדיוק: מחק הכל"
        )
        
        if confirm_text == "מחק הכל":
            if st.button("🗑️ בצע איפוס מוגן", type="primary"):
                perform_protected_reset()


def perform_protected_reset():
    """בצע איפוס מוגן"""
    try:
        with st.spinner("🔄 מבצע איפוס מוגן..."):
            import shutil
            
            # רשימת תיקיות לאיפוס
            dirs_to_reset = [
                "data/uploaded_documents",
                "data/processed", 
                "data/summaries",
                "data/metadata"
            ]
            
            reset_count = 0
            
            for dir_path in dirs_to_reset:
                path = Path(dir_path)
                if path.exists():
                    shutil.rmtree(path)
                    path.mkdir(parents=True, exist_ok=True)
                    reset_count += 1
            
            # נקה session state
            keys_to_preserve = ['session_id']
            keys_to_delete = [k for k in st.session_state.keys() if k not in keys_to_preserve]
            for key in keys_to_delete:
                del st.session_state[key]
            
            st.success(f"✅ איפוס הושלם! {reset_count} תיקיות אופסו")
            sidebar_manager.log_operation("protected_reset", f"Reset {reset_count} directories")
            
            time.sleep(2)
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ שגיאה באיפוס: {e}")


def show_system_info_section(chatbot):
    """סקציית מידע מערכת"""
    with st.expander("📊 מידע מערכת מתקדם", expanded=False):
        
        # סטטיסטיקות כלליות
        st.markdown("**📈 סטטיסטיקות:**")
        
        try:
            docs_info = get_documents_info_safe(chatbot)
            
            info_col1, info_col2 = st.columns(2)
            
            with info_col1:
                st.metric("📄 מסמכים ייחודיים", docs_info.get('unique_documents', 0))
                st.metric("🔍 קטעי חיפוש", docs_info.get('total_chunks', 0))
            
            with info_col2:
                st.metric("📋 סיכומים", docs_info.get('summaries_count', 0))
                st.metric("⚡ פעולות", len(st.session_state.get('sidebar_operations', [])))
            
        except Exception as e:
            st.error(f"שגיאה בהצגת סטטיסטיקות: {e}")
        
        # זמן פעילות
        if 'session_start_time' not in st.session_state:
            st.session_state.session_start_time = datetime.now()
        
        uptime = datetime.now() - st.session_state.session_start_time
        st.caption(f"⏱️ זמן פעילות: {uptime.total_seconds()/60:.1f} דקות")
        
        # מידע debug אם זמין
        if FILE_UPLOADER_AVAILABLE:
            show_debug_info()


def show_system_status_summary(chatbot):
    """הצג סיכום מצב המערכת בממשק הראשי"""
    
    col1, col2, col3 = st.columns(3)
    
    # מצב API
    with col1:
        if hasattr(chatbot, 'claude_client') and chatbot.claude_client:
            st.metric(
                "🤖 Claude API", 
                "מחובר", 
                delta="פעיל",
                help="מערכת AI פעילה עם הקשר משפטי מלא"
            )
        else:
            st.metric(
                "🤖 API", 
                "לא זמין", 
                delta="בדוק הגדרות",
                delta_color="inverse",
                help="נדרש API key ל-Claude"
            )
    
    # מסמכים טעונים  
    with col2:
        try:
            docs_info = get_documents_info_safe(chatbot)
            chunks_count = docs_info.get('total_chunks', 0)
            documents_count = docs_info.get('unique_documents', 0)
            
            st.metric(
                "📚 טקסט טעון", 
                f"{chunks_count} קטעים",
                delta=f"{documents_count} מסמכים",
                help="קטעי טקסט הטעונים במערכת החיפוש"
            )
        except:
            st.metric("📚 טקסט טעון", "0 קטעים")
    
    # סיכומים משפטיים
    with col3:
        try:
            summaries_count = count_files_safe("data/summaries", "*.json")
            summaries_status = "יש סיכומים" if summaries_count > 0 else "אין סיכומים"
            
            st.metric(
                "📋 סיכומים", 
                f"{summaries_count} מסמכים",
                delta=summaries_status,
                help="סיכומים משפטיים מתקדמים לניתוח מקיף"
            )
        except:
            st.metric("📋 סיכומים", "0 מסמכים")


def get_documents_info_safe(chatbot) -> Dict:
    """קבל מידע מסמכים בדרך בטוחה"""
    try:
        if hasattr(chatbot, 'get_documents_info'):
            return chatbot.get_documents_info()
        elif hasattr(chatbot, 'get_document_stats'):
            return chatbot.get_document_stats()
        else:
            # fallback ידני
            return {
                'total_chunks': len(getattr(chatbot, 'document_chunks', [])),
                'unique_documents': 0,
                'summaries_count': count_files_safe("data/summaries", "*.json")
            }
    except Exception as e:
        print(f"Error getting documents info: {e}")
        return {
            'total_chunks': 0,
            'unique_documents': 0,
            'summaries_count': 0
        }


def count_files_safe(directory: str, pattern: str = "*") -> int:
    """ספור קבצים בבטחה"""
    try:
        path = Path(directory)
        return len(list(path.glob(pattern))) if path.exists() else 0
    except:
        return 0
