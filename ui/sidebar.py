"""
סרגל צדדי לניהול המערכת
"""
import streamlit as st

from ui.file_uploader import (
    show_smart_document_uploader, 
    show_document_processing, 
    show_files_status, 
    show_debug_info
)
from config.settings import QUICK_QUESTIONS, COMPREHENSIVE_TASKS


def show_sidebar(chatbot):
    """הצג סרגל צדדי מלא"""
    with st.sidebar:
        st.header("📁 ניהול מסמכים וסיכומים")
        
        # בדיקת API עם הודעה על הגבלות
        if chatbot.claude_client:
            st.success("🤖 Claude API: מחובר")
            st.info("🛡️ הוקפד הקשר משפטי מלא ללא הגבלות")
        else:
            st.warning("🤖 Claude API: לא זמין (Ollama)")
        
        # העלאת מסמכים חדשים
        with st.expander("📤 העלאת מסמכים"):
            show_smart_document_uploader()
        
        # עיבוד מסמכים
        show_document_processing()
        
        st.divider()
        
        # ====== ניהול סיכומים משפטיים ======
        st.subheader("📋 סיכומים משפטיים")
        
        # יצירת סיכומים
        if st.button("📝 צור סיכומים משפטיים", key="create_summaries"):
            if not chatbot.claude_client:
                st.error("❌ נדרש Claude API ליצירת סיכומים משפטיים")
            else:
                with st.spinner("📝 יוצר סיכומים משפטיים ללא הגבלות... זה יכול לקחת כמה דקות..."):
                    # יצור מעבד סיכומים
                    from processors.legal_summary import LegalSummaryProcessor
                    summary_processor = LegalSummaryProcessor(chatbot)
                    summaries = summary_processor.process_all_documents_to_summaries()
                    
                    if summaries:
                        st.success(f"✅ נוצרו {len(summaries)} סיכומים משפטיים!")
                        st.balloons()
                    else:
                        st.warning("⚠️ לא נוצרו סיכומים - וודא שיש מסמכים מעובדים")
        
        # מחיקת סיכומים
        if st.button("🗑️ מחק כל הסיכומים", key="delete_summaries"):
            from processors.legal_summary import LegalSummaryProcessor
            summary_processor = LegalSummaryProcessor(chatbot)
            summary_processor.delete_all_summaries()
            st.rerun()
        
        st.divider()
        
        # טעינת מסמכים לחיפוש רגיל
        if st.button("📚 טען מסמכים לחיפוש רגיל", key="load_docs"):
            with st.spinner("📖 טוען מסמכים למאגר החיפוש..."):
                success = chatbot.load_documents_for_search()
                if success:
                    docs_info = chatbot.get_documents_info()
                    st.success(f"✅ המסמכים נטענו בהצלחה! טענו {docs_info['total_chunks']} קטעי טקסט")
                    st.balloons()
                else:
                    st.error("❌ שגיאה בטעינת המסמכים")
        
        st.divider()
        
        # ======== סטטוס כללי ========
        from core.file_manager import SmartFileManager
        file_manager = SmartFileManager()
        show_files_status(file_manager)
        
        # מידע על מסמכים טעונים לחיפוש
        docs_info = chatbot.get_documents_info()
        if docs_info['total_chunks'] > 0:
            st.metric("🔍 קטעי טקסט טעונים", docs_info['total_chunks'])
        
        # מידע debug
        show_debug_info()
        
        st.divider()
        
        # ======== שאלות מהירות ========
        st.subheader("🎯 שאלות מהירות", help="חיפוש מהיר בטקסט הגולמי - ללא הגבלות")
        
        for question in QUICK_QUESTIONS:
            if st.button(question, key=f"quick_{hash(question)}"):
                st.session_state.quick_question = question
        
        st.divider()
        
        # ======== משימות מקיפות ========
        st.subheader("🏛️ משימות מקיפות", help="ניתוח מקיף על בסיס הסיכומים המשפטיים - ללא הגבלות")
        
        # בדוק אם יש סיכומים
        from processors.legal_summary import LegalSummaryProcessor
        summary_processor = LegalSummaryProcessor(chatbot)
        summaries_exist = len(summary_processor.get_all_summaries()) > 0
        
        if not summaries_exist:
            st.info("ℹ️ צור סיכומים משפטיים תחילה")
        
        for task_name, task_type in COMPREHENSIVE_TASKS:
            if st.button(task_name, key=f"comp_{task_type}", disabled=not summaries_exist):
                if summaries_exist:
                    st.session_state.comprehensive_task = task_type
                else:
                    st.warning("⚠️ צור סיכומים משפטיים תחילה!")


def show_system_status_summary(chatbot):
    """הצג סיכום מהיר של מצב המערכת"""
    col1, col2, col3 = st.columns(3)
    
    # סטטוס API
    with col1:
        if chatbot.claude_client:
            st.metric("🤖 Claude API", "✅ מחובר", delta="ללא הגבלות")
        else:
            st.metric("🤖 API", "⚠️ Ollama", delta="מוגבל")
    
    # מסמכים טעונים
    with col2:
        docs_info = chatbot.get_documents_info()
        st.metric("📚 טקסט טעון", f"{docs_info['total_chunks']} קטעים")
    
    # סיכומים משפטיים
    with col3:
        from processors.legal_summary import LegalSummaryProcessor
        summary_processor = LegalSummaryProcessor(chatbot)
        summaries_count = len(summary_processor.get_all_summaries())
        st.metric("📋 סיכומים", f"{summaries_count} מסמכים")

def show_system_management():
    """הצג אפשרויות ניהול המערכת"""
    with st.expander("🛠️ ניהול המערכת", expanded=False):
        
        st.subheader("📊 כלים מתקדמים")
        
        # ניהול סיכומים רגיל
        if st.button("📋 נהל סיכומים", key="manage_summaries_btn"):
            summary_processor = LegalSummaryProcessor(st.session_state.get('chatbot'))
            summary_processor.get_summary_management_options()
        
        st.divider()
        
        # איפוס מלא - עם הגנות
        st.subheader("🚨 איפוס מלא")
        st.write("לפיתוח ובדיקות - מחיקה מלאה של כל הנתונים")
        
        if st.button("🗑️ איפוס מלא של המערכת", key="full_reset_btn"):
            summary_processor = LegalSummaryProcessor(st.session_state.get('chatbot'))
            summary_processor.reset_entire_system()
