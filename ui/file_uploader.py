"""
ממשק העלאת קבצים חכם עם ניהול גרסאות ותיוג סוגי מסמכים משפטיים מלא
"""
import streamlit as st
import pandas as pd
import json
from pathlib import Path
from typing import List

from core.file_manager import SmartFileManager
from utils.helpers import process_documents_function


def guess_document_type(filename: str) -> str:
    """נחש סוג מסמך לפי שם הקובץ - זיהוי מתקדם"""
    filename_lower = filename.lower()
    
    # זיהוי לפי מילות מפתח - בסדר עדיפות
    if any(word in filename_lower for word in ['דופן', 'תגובה_לתגובה', 'תשובה_לתגובה']):
        return "🔄 דופן (תגובה לתגובה)"
    elif any(word in filename_lower for word in ['תגובה', 'תשובה']) and any(word in filename_lower for word in ['הגנה', 'נתבע']):
        return "📝 תגובה לכתב הגנה"
    elif any(word in filename_lower for word in ['תביעה_צדדית', 'תביעת_צד', 'cross_claim']):
        return "🏛️ תביעה צדדית"
    elif any(word in filename_lower for word in ['תביעה', 'תובע', 'כתב_תביעה', 'כתב תביעה']) and not any(word in filename_lower for word in ['צדדית', 'צד']):
        return "🏛️ כתב תביעה"
    elif any(word in filename_lower for word in ['הגנה', 'נתבע', 'כתב_הגנה', 'כתב הגנה']) and not any(word in filename_lower for word in ['תגובה', 'תשובה']):
        return "🛡️ כתב הגנה"
    elif any(word in filename_lower for word in ['סיכומים', 'כתב_סיכומים', 'summation']):
        return "⚖️ כתב סיכומים"
    elif any(word in filename_lower for word in ['בקשה', 'צו_ביניים', 'ביניים', 'interim']):
        return "📑 בקשה לצווי ביניים"
    elif any(word in filename_lower for word in ['תגובה_לתצהיר', 'תשובה_לתצהיר', 'תגובה לתצהיר']):
        return "📋 תגובה לתצהיר"
    elif any(word in filename_lower for word in ['תמלול', 'שיחה', 'הקלטה', 'telephone', 'recording']):
        return "📞 תמלול שיחה/הקלטה"
    elif any(word in filename_lower for word in ['בגץ', 'בג"צ', 'עליון', 'bagatz', 'supreme']):
        return "⚖️ בג\"צ ונספחים"
    elif any(word in filename_lower for word in ['תצהיר', 'עדות', 'עד', 'affidavit']):
        return "📋 תצהיר/עדות"
    elif any(word in filename_lower for word in ['חקירה', 'משטרה', 'חוקר', 'police']):
        return "🔍 חקירת משטרה"
    else:
        return "📄 מסמך אחר"


def save_document_metadata(file_path: Path, doc_type: str):
    """שמור מטא-דטה של המסמך כולל סוג"""
    try:
        metadata_file = file_path.parent / f"{file_path.stem}_metadata.json"
        metadata = {
            "document_type": doc_type,
            "original_filename": file_path.name,
            "upload_timestamp": pd.Timestamp.now().isoformat(),
            "file_size": file_path.stat().st_size
        }
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        st.warning(f"⚠️ לא הצלחתי לשמור מטא-דטה עבור {file_path.name}: {e}")


def show_smart_document_uploader():
    """ממשק העלאה חכם עם תיוג סוגי מסמכים משפטיים מקיף"""
    st.subheader("📁 העלאת מסמכים חכמה - עם תיוג מקיף")
    
    st.info("""
🧠 **מערכת חכמה עם תיוג מקיף:**
- ✅ זיהוי אוטומטי של קבצים כפולים
- 🔄 החלפה אוטומטי של גרסאות ישנות
- 🏷️ **תיוג 11 סוגי מסמכים משפטיים**
- 🧹 ניקוי של כל הקבצים הקשורים
- 🎯 ניתוח מותאם לכל סוג מסמך
""")
    
    smart_manager = SmartFileManager()
    
    uploaded_files = st.file_uploader(
        "בחר קבצי PDF",
        type=['pdf'],
        accept_multiple_files=True,
        help="העלה קבצי PDF - המערכת תזהה אוטומטית את סוג המסמך ותחליף קבצים עם אותו שם"
    )
    
    if uploaded_files:
        st.write(f"📄 נבחרו {len(uploaded_files)} קבצים:")
        
        # אפשרויות תיוג מקיפות
        doc_types = [
            "🏛️ כתב תביעה",
            "🛡️ כתב הגנה", 
            "📝 תגובה לכתב הגנה",
            "🔄 דופן (תגובה לתגובה)",
            "⚖️ כתב סיכומים",
            "📑 בקשה לצווי ביניים",
            "🏛️ תביעה צדדית",
            "📋 תצהיר/עדות",
            "📋 תגובה לתצהיר",
            "📞 תמלול שיחה/הקלטה",
            "🔍 חקירת משטרה",
            "⚖️ בג\"צ ונספחים",
            "📄 מסמך אחר"
        ]
        
        # מילון לשמירת התיוגים
        if 'file_tags' not in st.session_state:
            st.session_state.file_tags = {}
        
        # הצג תצוגה מקדימה עם תיוג
        st.write("### 🏷️ תייג את הקבצים לפי סוג:")
        st.write("*תיוג נכון ואיספית מקצועית ישפרו משמעותית את איכות הניתוח המשפטי*")
        
        # הצג מדריך מהיר
        with st.expander("📖 מדריך סוגי המסמכים"):
            st.markdown("""
**📋 מסמכי התובע:**
- 🏛️ כתב תביעה - המסמך הפותח של התובע
- 📝 תגובה לכתב הגנה - תשובת התובע להגנה
- 🏛️ תביעה צדדית - תביעה נוספת/צדדית

**📋 מסמכי הנתבע:**
- 🛡️ כתב הגנה - תשובת הנתבע לתביעה
- 🔄 דופן - תשובת הנתבע לתגובה

**📋 מסמכי סגירה:**
- ⚖️ כתב סיכומים - טיעונים סופיים לפני פסק דין
- 📑 בקשה לצווי ביניים - בקשות דחופות במהלך המשפט

**📋 עדויות וחקירות:**
- 📋 תצהיר/עדות - עדויות של עדים
- 📋 תגובה לתצהיר - תגובה לעדות
- 📞 תמלול שיחה/הקלטה - הקלטות וממלולים
- 🔍 חקירת משטרה - פרוטוקולי חקירה

**📋 מסמכים מיוחדים:**
- ⚖️ בג"צ ונספחים - עליונים ובג"צ
- 📄 מסמך אחר - כל מסמך שלא בקטגוריות האחרות
""")
        
        preview_data = []
        
        # יצור מזהה ייחודי לכל קובץ
        for file_index, uploaded_file in enumerate(uploaded_files):
            clean_name = smart_manager.clean_filename(uploaded_file.name)
            base_name = smart_manager.get_base_name(clean_name)
            existing_files = smart_manager.find_related_files(base_name)
            
            action = "🆕 חדש" if not any(existing_files.values()) else "🔄 החלפה"
            existing_count = sum(len(files) for files in existing_files.values())
            
            # תיוג לכל קובץ - עם מזהה ייחודי
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.write(f"📄 **{uploaded_file.name}**")
                st.caption(f"שם מנוקה: {clean_name}")
            
            with col2:
                # ניחוש אוטומטי לפי שם הקובץ
                auto_guess = guess_document_type(uploaded_file.name)
                default_index = doc_types.index(auto_guess) if auto_guess in doc_types else 0
                
                # יצור key ייחודי עם אינדקס
                unique_key = f"type_{file_index}_{uploaded_file.name}_{hash(uploaded_file.name + str(file_index))}"
                
                selected_type = st.selectbox(
                    f"סוג מסמך:",
                    doc_types,
                    index=default_index,
                    key=unique_key,  # key ייחודי
                    help="בחר את סוג המסמך לניתוח מיטבי. המערכת מנחשת אוטומטית לפי שם הקובץ."
                )
                
                # הצג אם זיהה אוטומטית
                if auto_guess == selected_type and auto_guess != "📄 מסמך אחר":
                    st.caption("🤖 זוהה אוטומטית")
                
                # שמור בסשן עם שם הקובץ המלא כמפתח
                file_key = f"{uploaded_file.name}_{file_index}"
                st.session_state.file_tags[file_key] = selected_type
            
            with col3:
                st.metric("פעולה", action)
                if existing_count > 0:
                    st.caption(f"{existing_count} קבצים קיימים")
            
            preview_data.append({
                "מס'": file_index + 1,
                "קובץ מקורי": uploaded_file.name,
                "שם מנוקה": clean_name,
                "סוג מסמך": selected_type,
                "פעולה": action,
                "גודל": f"{len(uploaded_file.getvalue())/1024:.1f} KB"
            })
        
        st.divider()
        
        # הצג טבלת סיכום
        st.write("### 📊 סיכום העלאה:")
        df = pd.DataFrame(preview_data)
        st.dataframe(df, use_container_width=True)
        
        # הצג סטטיסטיקה מהירה
        type_counts = df['סוג מסמך'].value_counts()
        if len(type_counts) > 1:
            st.write("**📈 פילוח לפי סוגים:**")
            cols = st.columns(min(4, len(type_counts)))
            for i, (doc_type, count) in enumerate(type_counts.items()):
                with cols[i % 4]:
                    st.metric(doc_type.replace("🏛️ ", "").replace("🛡️ ", "").replace("📝 ", "")[:15], count)
        
        if st.button("💾 שמור קבצים עם תיוג מקיף (עם החלפה חכמה)", key="smart_save_tagged_files"):
            results = []
            
            for file_index, uploaded_file in enumerate(uploaded_files):
                # שחזר את סוג הקובץ עם המפתח המתאים
                file_key = f"{uploaded_file.name}_{file_index}"
                file_type = st.session_state.file_tags.get(file_key, "📄 מסמך אחר")
                
                with st.spinner(f"מעבד {uploaded_file.name} כ-{file_type}..."):
                    result = smart_manager.save_uploaded_file_smart(uploaded_file)
                    
                    # הוסף מידע על סוג המסמך
                    result['document_type'] = file_type
                    
                    # שמור מטא-דטה עם סוג המסמך
                    if result['success']:
                        save_document_metadata(result['file_path'], file_type)
                    
                    results.append(result)
            
            # הצג תוצאות
            st.subheader("📊 תוצאות השמירה:")
            
            # סיכום לפי סוגים
            type_summary = {}
            for result in results:
                if result['success']:
                    doc_type = result['document_type']
                    if doc_type not in type_summary:
                        type_summary[doc_type] = 0
                    type_summary[doc_type] += 1
            
            if type_summary:
                st.write("📈 **סיכום לפי סוגי מסמכים:**")
                for doc_type, count in type_summary.items():
                    st.write(f"• {doc_type}: **{count}** קבצים")
            
            # הצג תוצאה לכל קובץ
            st.write("**📋 פירוט תוצאות:**")
            for result in results:
                if result['success']:
                    action_icon = "🆕" if result['action'] == 'new' else "🔄"
                    doc_type = result['document_type']
                    st.success(f"{action_icon} **{result['clean_name']}** → {doc_type}")
                    
                    if result['removed_files']:
                        with st.expander(f"🗑️ קבצים שנמחקו ({len(result['removed_files'])})"):
                            for removed in result['removed_files']:
                                st.write(f"  • {removed}")
                    
                    st.caption(f"📏 גודל: {result['size']/1024:.1f} KB")
                    
                else:
                    st.error(f"❌ **{result['original_name']}** - {result.get('error', 'שגיאה לא ידועה')}")
            
            # הצג סיכום
            successful = len([r for r in results if r['success']])
            if successful > 0:
                st.success(f"✅ {successful} קבצים נשמרו עם תיוג מקיף בהצלחה!")
                st.info("🔄 עכשיו לחץ על 'עבד מסמכים חדשים' כדי לעבד אותם עם התיוגים המותאמים")
                
                # נקה את ה-cache של המערכת
                if 'chatbot' in st.session_state:
                    st.session_state.chatbot.clear_search_cache()
                    st.info("🔄 Cache של המערכת נוקה")
                
                # נקה את התיוגים מהסשן אחרי שמירה מוצלחת
                if 'file_tags' in st.session_state:
                    st.session_state.file_tags = {}


# שאר הפונקציות נשארות ללא שינוי...
def show_document_processing():
    """הצג ממשק עיבוד מסמכים"""
    if st.button("🔄 עבד מסמכים חדשים (עם ניתוח מותאם)", key="smart_process_docs"):
        with st.spinner("⚙️ מעבד מסמכים בחכמה עם ניתוח מותאם לכל סוג... יכול לקחת כמה דקות..."):
            success, stdout, stderr = process_documents_function()
            
            if success:
                st.success("✅ המסמכים עובדו בהצלחה עם ניתוח מותאם!")
                if stdout:
                    st.text_area("פלט העיבוד:", stdout, height=150)
                # נקה cache גם כאן
                if 'chatbot' in st.session_state:
                    st.session_state.chatbot.clear_search_cache()
                st.rerun()
            else:
                st.error("❌ שגיאה בעיבוד המסמכים:")
                if stderr:
                    st.error(stderr)
                if stdout:
                    st.text_area("פלט נוסף:", stdout, height=100)


def show_files_status(file_manager: SmartFileManager):
    """הצג סטטוס הקבצים במערכת עם פירוט לפי סוגים"""
    st.subheader("📊 סטטוס הקבצים במערכת")
    
    status = file_manager.get_files_status()
    
    # קבצים שהועלו
    if status['uploaded']:
        st.write("**📁 קבצים שהועלו:**")
        for file_info in status['uploaded']:
            size_mb = file_info['size'] / (1024 * 1024)
            
            # נסה לקרוא סוג המסמך
            try:
                metadata_file = Path("data/uploaded_documents") / f"{file_info['base_name']}_metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        doc_type = metadata.get('document_type', '📄')
                else:
                    doc_type = '📄'
            except:
                doc_type = '📄'
            
            st.write(f"• {doc_type} {file_info['name']} ({size_mb:.1f} MB)")
    else:
        st.write("📁 **קבצים שהועלו:** אין קבצים")
    
    # קבצים מעובדים
    if status['processed']:
        st.write("**⚙️ קבצים מעובדים:**")
        total_chunks = 0
        for file_info in status['processed']:
            chunks = file_info['chunks']
            total_chunks += chunks
            st.write(f"📖 {file_info['base_name']}: {chunks} קטעים")
        st.metric("📊 סה\"כ קטעי טקסט", total_chunks)
    else:
        st.write("⚙️ **קבצים מעובדים:** אין קבצים")
    
    # סיכומים משפטיים
    if status['summaries']:
        st.write("**📋 סיכומים משפטיים:**")
        completed = 0
        for file_info in status['summaries']:
            status_icon = "✅" if file_info['status'] == 'completed' else "❌"
            st.write(f"{status_icon} {file_info['name'].replace('_legal_summary.json', '')}")
            if file_info['status'] == 'completed':
                completed += 1
        st.metric("✅ סיכומים מושלמים", completed)
    else:
        st.write("📋 **סיכומים משפטיים:** אין סיכומים")


def show_debug_info():
    """הצג מידע debug מפורט"""
    with st.expander("🔍 מידע טכני מפורט"):
        from core.file_manager import SmartFileManager
        file_manager = SmartFileManager()
        status = file_manager.get_files_status()
        
        st.json({
            "uploaded_count": len(status['uploaded']),
            "processed_count": len(status['processed']),
            "summaries_count": len(status['summaries']),
            "total_chunks": sum(f['chunks'] for f in status['processed']),
            "total_size_mb": sum(f['size'] for f in status['uploaded']) / (1024 * 1024) if status['uploaded'] else 0
        })
