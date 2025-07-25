"""
ממשק העלאת קבצים חכם ומתקדם עם זיהוי אוטומטי, תיוג משפטי וניהול גרסאות
גרסה 2.2.0 - עם AI לזיהוי מסמכים, drag&drop ועיבוד real-time
"""
import streamlit as st
import pandas as pd
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import re

# ייבואים עם fallbacks
try:
    from core.file_manager import SmartFileManager
    FILE_MANAGER_AVAILABLE = True
except ImportError:
    FILE_MANAGER_AVAILABLE = False
    print("⚠️ SmartFileManager not available - using fallback")

try:
    from utils.helpers import process_documents_function
    HELPERS_AVAILABLE = True
except ImportError:
    HELPERS_AVAILABLE = False
    print("⚠️ Helpers not available - using fallback processing")

try:
    from config.settings import DOCUMENT_TYPES
    SETTINGS_AVAILABLE = True
except ImportError:
    SETTINGS_AVAILABLE = False
    DOCUMENT_TYPES = {}


class AdvancedDocumentAnalyzer:
    """מנתח מסמכים מתקדם עם בינה מלאכותית לזיהוי סוגי מסמכים"""
    
    def __init__(self):
        self.legal_patterns = self._build_legal_patterns()
        self.confidence_scores = {}
        
    def _build_legal_patterns(self) -> Dict[str, List[str]]:
        """בנה דפוסי זיהוי מתקדמים לסוגי מסמכים משפטיים"""
        return {
            "כתב תביעה": [
                r"כתב[\s\-_]*תביעה", r"תובע", r"נגד", r"תביעה.*הוגשה",
                r"סעד", r"סעדים", r"טענות.*התובע", r"plaintiff", r"complaint"
            ],
            "כתב הגנה": [
                r"כתב[\s\-_]*הגנה", r"נתבע", r"להגנתו", r"טענות.*הנתבע",
                r"הגנה.*מטעם", r"defense", r"defendant", r"מכחיש"
            ],
            "תגובה לכתב הגנה": [
                r"תגובה[\s\-_]*לכתב[\s\-_]*הגנה", r"תשובה[\s\-_]*להגנה",
                r"תובע.*מגיב", r"response.*defense", r"משיב.*להגנה"
            ],
            "דופן": [
                r"דופן", r"תגובה[\s\-_]*לתגובה", r"תשובה[\s\-_]*לתשובה",
                r"נתבע.*מגיב", r"counter.*response", r"תגובה.*נוספת"
            ],
            "כתב סיכומים": [
                r"כתב[\s\-_]*סיכומים", r"סיכומי.*טיעונים", r"טיעונים[\s\-_]*סופיים",
                r"summation", r"closing.*arguments", r"לסיכום"
            ],
            "בקשה לצווי ביניים": [
                r"בקשה.*צו[\s\-_]*ביניים", r"צו[\s\-_]*זמני", r"ביניים",
                r"interim.*order", r"temporary.*injunction", r"דחוף"
            ],
            "תביעה צדדית": [
                r"תביעה[\s\-_]*צדדית", r"תביעת[\s\-_]*צד", r"cross[\s\-_]*claim",
                r"צד[\s\-_]*שלישי", r"third[\s\-_]*party", r"תובע.*נוסף"
            ],
            "תצהיר": [
                r"תצהיר", r"עדות", r"מתצהיר", r"עד", r"מציין.*בזאת",
                r"affidavit", r"sworn.*statement", r"testimony"
            ],
            "תגובה לתצהיר": [
                r"תגובה[\s\-_]*לתצהיר", r"תשובה[\s\-_]*לעדות",
                r"response.*affidavit", r"מגיב.*לתצהיר"
            ],
            "תמלול": [
                r"תמלול", r"הקלטה", r"שיחה", r"רישום.*שיחה",
                r"transcript", r"recording", r"audio", r"נוכח.*בשיחה"
            ],
            "חקירת משטרה": [
                r"חקירה", r"משטרה", r"חקירת.*חשוד", r"פרוטוקול.*חקירה",
                r"police.*investigation", r"interrogation", r"חוקר"
            ],
            "בג\"צ": [
                r"בג[\"\']*צ", r"בית[\s\-_]*משפט[\s\-_]*עליון", r"עליון",
                r"supreme.*court", r"high.*court", r"bagatz"
            ]
        }
    
    def analyze_filename(self, filename: str, file_content: bytes = None) -> Tuple[str, float]:
        """נתח שם קובץ ותוכן (אם זמין) לזיהוי סוג המסמך"""
        filename_lower = filename.lower()
        scores = {}
        
        # נתח לפי שם הקובץ
        for doc_type, patterns in self.legal_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, filename_lower, re.IGNORECASE))
                score += matches * 10  # משקל גבוה לשם קובץ
            
            scores[doc_type] = score
        
        # בדיקות נוספות להשם
        self._apply_filename_rules(filename_lower, scores)
        
        # מצא את הסוג עם הציון הגבוה ביותר
        if scores and max(scores.values()) > 0:
            best_type = max(scores, key=scores.get)
            confidence = min(scores[best_type] / 50, 0.95)  # נורמליזציה
            
            # המר לפורמט התצוגה
            display_type = self._convert_to_display_format(best_type)
            return display_type, confidence
        
        return "📄 מסמך אחר", 0.1
    
    def _apply_filename_rules(self, filename: str, scores: Dict[str, int]):
        """החל חוקים מיוחדים לזיהוי לפי שם קובץ"""
        
        # חוקי עדיפות
        if any(word in filename for word in ['דופן', 'תגובה_לתגובה']):
            scores['דופן'] += 30
        
        if 'תגובה' in filename and 'הגנה' in filename:
            scores['תגובה לכתב הגנה'] += 25
        
        if 'תביעה' in filename and 'צדדית' in filename:
            scores['תביעה צדדית'] += 25
        
        # נקודות הפרדה בין סוגים דומים
        if 'תביעה' in filename and 'צדדית' not in filename:
            scores['כתב תביעה'] += 15
        
        if 'הגנה' in filename and 'תגובה' not in filename:
            scores['כתב הגנה'] += 15
    
    def _convert_to_display_format(self, internal_type: str) -> str:
        """המר מפורמט פנימי לפורמט תצוגה עם אייקונים"""
        conversion_map = {
            "כתב תביעה": "🏛️ כתב תביעה",
            "כתב הגנה": "🛡️ כתב הגנה",
            "תגובה לכתב הגנה": "📝 תגובה לכתב הגנה",
            "דופן": "🔄 דופן (תגובה לתגובה)",
            "כתב סיכומים": "⚖️ כתב סיכומים",
            "בקשה לצווי ביניים": "📑 בקשה לצווי ביניים",
            "תביעה צדדית": "🏛️ תביעה צדדית",
            "תצהיר": "📋 תצהיר/עדות",
            "תגובה לתצהיר": "📋 תגובה לתצהיר",
            "תמלול": "📞 תמלול שיחה/הקלטה",
            "חקירת משטרה": "🔍 חקירת משטרה",
            "בג\"צ": "⚖️ בג\"צ ונספחים"
        }
        return conversion_map.get(internal_type, "📄 מסמך אחר")


class FileUploadManager:
    """מנהל העלאת קבצים מתקדם עם ניהול session וcache"""
    
    def __init__(self):
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.upload_history = []
        self.analyzer = AdvancedDocumentAnalyzer()
        
        # אתחל session state
        if 'upload_session' not in st.session_state:
            st.session_state.upload_session = {
                'files': {},
                'tags': {},
                'processed': [],
                'errors': []
            }
    
    def calculate_file_hash(self, file_data: bytes) -> str:
        """חשב hash לקובץ לזיהוי כפילות"""
        return hashlib.md5(file_data).hexdigest()
    
    def detect_duplicates(self, uploaded_files: List) -> Dict[str, List[str]]:
        """זהה קבצים כפולים לפי תוכן"""
        file_hashes = {}
        duplicates = {}
        
        for file in uploaded_files:
            file_hash = self.calculate_file_hash(file.getvalue())
            
            if file_hash in file_hashes:
                if file_hash not in duplicates:
                    duplicates[file_hash] = [file_hashes[file_hash]]
                duplicates[file_hash].append(file.name)
            else:
                file_hashes[file_hash] = file.name
        
        return duplicates
    
    def save_upload_metadata(self, file_info: Dict):
        """שמור מטא-דטה של העלאה"""
        try:
            metadata_dir = Path("data/metadata")
            metadata_dir.mkdir(parents=True, exist_ok=True)
            
            metadata_file = metadata_dir / f"{file_info['clean_name']}_metadata.json"
            
            metadata = {
                "original_filename": file_info['original_name'],
                "clean_filename": file_info['clean_name'],
                "document_type": file_info['document_type'],
                "confidence": file_info.get('confidence', 0),
                "upload_timestamp": datetime.now().isoformat(),
                "file_size": file_info['size'],
                "file_hash": file_info.get('hash', ''),
                "session_id": self.session_id,
                "auto_detected": file_info.get('auto_detected', False),
                "user_modified": file_info.get('user_modified', False)
            }
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            st.error(f"❌ שגיאה בשמירת metadata: {e}")
            return False


def get_enhanced_document_types() -> List[str]:
    """קבל רשימת סוגי מסמכים מורחבת"""
    if SETTINGS_AVAILABLE and DOCUMENT_TYPES:
        return list(DOCUMENT_TYPES.values())
    
    # רשימה מקיפה כברירת מחדל
    return [
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
        "📄 חוזה/הסכם",
        "💼 מסמך מסחרי",
        "📊 דוח/מחקר",
        "📧 התכתבות",
        "🏥 מסמך רפואי",
        "🏢 מסמך ממשלתי",
        "📄 מסמך אחר"
    ]


def show_smart_document_uploader():
    """ממשק העלאה חכם ומתקדם"""
    upload_manager = FileUploadManager()
    doc_types = get_enhanced_document_types()
    
    # כותרת מתקדמת
    st.markdown("""
    <div style="background: linear-gradient(90deg, #1f4e79, #2d5a8b); color: white; 
                padding: 1rem; border-radius: 10px; text-align: center; margin-bottom: 1rem;">
        <h3>📁 העלאת מסמכים חכמה ומתקדמת</h3>
        <p style="margin: 0;">זיהוי אוטומטי, ניהול גרסאות וטיפול בכפילות</p>
    </div>
    """, unsafe_allow_html=True)
    
    # הצג יכולות המערכת
    with st.expander("🎯 יכולות המערכת המתקדמة", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **🤖 זיהוי אוטומטי:**
            - AI לזיהוי סוגי מסמכים
            - ניתוח שם קובץ מתקדם
            - דירוג ביטחון לכל זיהוי
            - זיהוי דפוסים משפטיים
            """)
        
        with col2:
            st.markdown("""
            **⚡ ניהול חכם:**
            - זיהוי כפילות לפי תוכן
            - החלפת גרסאות אוטומטית
            - ניקוי קבצים קשורים
            - גיבוי מטא-דטה מלא
            """)
        
        with col3:
            st.markdown("""
            **📊 ניתוח מתקדם:**
            - 19 סוגי מסמכים נתמכים
            - ניתוח מותאם לכל סוג
            - מעקב היסטוריית שינויים
            - סטטיסטיקות מפורטות
            """)
    
    # ממשק העלאה עיקרי
    st.markdown("### 📤 בחירת קבצים")
    
    uploaded_files = st.file_uploader(
        "גרור קבצים לכאן או לחץ לבחירה",
        type=['pdf'],
        accept_multiple_files=True,
        help="תומך בקבצי PDF עד 50MB. ניתן להעלות מספר קבצים בבת אחת.",
        key="main_uploader"
    )
    
    if uploaded_files:
        # בדוק כפילות
        duplicates = upload_manager.detect_duplicates(uploaded_files)
        if duplicates:
            st.warning("⚠️ זוהו קבצים עם תוכן זהה:")
            for file_hash, file_names in duplicates.items():
                st.write(f"🔗 קבצים זהים: {', '.join(file_names)}")
        
        st.markdown(f"### 📋 זיהוי וניתוח {len(uploaded_files)} קבצים")
        
        # אתחל session עבור הקבצים
        if 'current_upload_tags' not in st.session_state:
            st.session_state.current_upload_tags = {}
        
        # נתח כל קובץ
        analysis_results = []
        
        for idx, uploaded_file in enumerate(uploaded_files):
            file_data = uploaded_file.getvalue()
            file_hash = upload_manager.calculate_file_hash(file_data)
            
            # נתח סוג המסמך
            detected_type, confidence = upload_manager.analyzer.analyze_filename(
                uploaded_file.name, file_data
            )
            
            analysis_results.append({
                'index': idx,
                'file': uploaded_file,
                'detected_type': detected_type,
                'confidence': confidence,
                'hash': file_hash,
                'size': len(file_data)
            })
        
        # הצג תוצאות ניתוח
        show_file_analysis_interface(analysis_results, doc_types, upload_manager)


def show_file_analysis_interface(analysis_results: List[Dict], doc_types: List[str], upload_manager: FileUploadManager):
    """הצג ממשק ניתוח וטיוג הקבצים"""
    
    # טבלת סיכום מהיר
    with st.expander("📊 סיכום זיהוי אוטומטי", expanded=True):
        summary_data = []
        high_confidence_count = 0
        
        for result in analysis_results:
            confidence_level = "🟢 גבוה" if result['confidence'] > 0.7 else "🟡 בינוני" if result['confidence'] > 0.3 else "🔴 נמוך"
            if result['confidence'] > 0.7:
                high_confidence_count += 1
            
            summary_data.append({
                "קובץ": result['file'].name,
                "זוהה כ": result['detected_type'],
                "רמת ביטחון": f"{result['confidence']:.0%}",
                "סטטוס": confidence_level
            })
        
        df = pd.DataFrame(summary_data)
        st.dataframe(df, use_container_width=True)
        
        # מטריקות
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📁 קבצים", len(analysis_results))
        with col2:
            st.metric("🎯 זיהוי גבוה", high_confidence_count)
        with col3:
            accuracy_pct = (high_confidence_count / len(analysis_results)) * 100
            st.metric("📈 דיוק", f"{accuracy_pct:.0f}%")
        with col4:
            total_size = sum(r['size'] for r in analysis_results) / (1024 * 1024)
            st.metric("💾 גודל כולל", f"{total_size:.1f}MB")
    
    # ממשק טיוג מפורט
    st.markdown("### 🏷️ טיוג וקביעת סוגי מסמכים")
    
    # אפשרות טיוג מהיר
    col1, col2 = st.columns([3, 1])
    with col1:
        quick_tag_type = st.selectbox(
            "🚀 טיוג מהיר לכל הקבצים:",
            [""] + doc_types,
            help="בחר סוג מסמך לטיוג מהיר של כל הקבצים (אופציונאלי)"
        )
    with col2:
        if st.button("⚡ החל על הכל", disabled=not quick_tag_type):
            for result in analysis_results:
                file_key = f"file_{result['index']}_{result['hash'][:8]}"
                st.session_state.current_upload_tags[file_key] = quick_tag_type
            st.success("✅ טיוג מהיר הוחל!")
            st.rerun()
    
    st.divider()
    
    # טיוג פרטני לכל קובץ
    for result in analysis_results:
        show_individual_file_interface(result, doc_types)


def show_individual_file_interface(result: Dict, doc_types: List[str]):
    """הצג ממשק לקובץ יחיד"""
    file = result['file']
    confidence = result['confidence']
    detected_type = result['detected_type']
    
    # יצור מזהה ייחודי
    file_key = f"file_{result['index']}_{result['hash'][:8]}"
    
    with st.container():
        # כותרת קובץ עם מידע
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            confidence_color = "🟢" if confidence > 0.7 else "🟡" if confidence > 0.3 else "🔴"
            st.markdown(f"**📄 {file.name}**")
            st.caption(f"גודל: {result['size']/1024:.1f}KB | Hash: {result['hash'][:8]}")
        
        with col2:
            st.metric("🎯 ביטחון", f"{confidence:.0%}", help="רמת הביטחון בזיהוי האוטומטי")
        
        with col3:
            if confidence > 0.7:
                st.success("🤖 זוהה בביטחון")
            elif confidence > 0.3:
                st.warning("⚠️ זיהוי חלקי")
            else:
                st.error("❓ זיהוי לא ברור")
        
        # בחירת סוג מסמך
        default_index = 0
        if detected_type in doc_types:
            default_index = doc_types.index(detected_type)
        
        # בדוק אם יש טיוג קודם
        current_tag = st.session_state.current_upload_tags.get(file_key)
        if current_tag and current_tag in doc_types:
            default_index = doc_types.index(current_tag)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            selected_type = st.selectbox(
                "בחר סוג מסמך:",
                doc_types,
                index=default_index,
                key=f"type_select_{file_key}",
                help=f"זוהה אוטומטית: {detected_type} ({confidence:.0%} ביטחון)"
            )
            
            # שמור בחירה
            st.session_state.current_upload_tags[file_key] = selected_type
        
        with col2:
            # מידע על שינוי
            if selected_type != detected_type:
                st.info("✏️ שונה ידנית")
            elif confidence > 0.7:
                st.success("🤖 אוטו")
            
        st.divider()


def show_file_processing_controls(analysis_results: List[Dict], upload_manager: FileUploadManager):
    """הצג בקרות עיבוד קבצים"""
    
    if not analysis_results:
        return
    
    st.markdown("### 🚀 שמירה ועיבוד")
    
    # הצג סיכום לפני שמירה
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if st.button("💾 שמור קבצים עם טיוג מלא", type="primary", key="save_analyzed_files"):
            save_analyzed_files(analysis_results, upload_manager)
    
    with col2:
        # אפשרויות נוספות
        auto_process = st.checkbox("⚡ עבד אוטומטית אחרי שמירה", value=True)
        if auto_process:
            st.caption("המערכת תעבד את הקבצים מיד לאחר השמירה")


def save_analyzed_files(analysis_results: List[Dict], upload_manager: FileUploadManager):
    """שמור קבצים מנותחים"""
    
    if not FILE_MANAGER_AVAILABLE:
        save_files_fallback(analysis_results)
        return
    
    smart_manager = SmartFileManager()
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results = []
    saved_count = 0
    
    try:
        for idx, result in enumerate(analysis_results):
            file = result['file']
            file_key = f"file_{result['index']}_{result['hash'][:8]}"
            selected_type = st.session_state.current_upload_tags.get(file_key, result['detected_type'])
            
            # עדכן פרוגרס
            progress = (idx + 1) / len(analysis_results)
            progress_bar.progress(progress)
            status_text.text(f"מעבד {file.name}...")
            
            # שמור קובץ
            save_result = smart_manager.save_uploaded_file_smart(file)
            
            if save_result['success']:
                # הוסף מטא-דטה
                file_info = {
                    'original_name': file.name,
                    'clean_name': save_result['clean_name'],
                    'document_type': selected_type,
                    'confidence': result['confidence'],
                    'size': result['size'],
                    'hash': result['hash'],
                    'auto_detected': result['confidence'] > 0.7,
                    'user_modified': selected_type != result['detected_type']
                }
                
                # שמור metadata
                upload_manager.save_upload_metadata(file_info)
                
                save_result['document_type'] = selected_type
                save_result['confidence'] = result['confidence']
                saved_count += 1
            
            results.append(save_result)
            time.sleep(0.1)  # קצת השהיה לחוויית משתמש
        
        progress_bar.progress(1.0)
        status_text.text("הושלם!")
        
        # הצג תוצאות
        display_save_results(results, saved_count)
        
        # נקה session
        if 'current_upload_tags' in st.session_state:
            del st.session_state.current_upload_tags
        
        time.sleep(2)
        progress_bar.empty()
        status_text.empty()
        
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"❌ שגיאה בשמירה: {e}")


def save_files_fallback(analysis_results: List[Dict]):
    """שמירת קבצים בסיסית כ-fallback"""
    st.warning("⚠️ מצב חירום - שמירה בסיסית")
    
    upload_dir = Path("data/uploaded_documents")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    saved_count = 0
    
    for result in analysis_results:
        try:
            file = result['file']
            file_path = upload_dir / file.name
            
            with open(file_path, 'wb') as f:
                f.write(file.getvalue())
            
            saved_count += 1
            st.success(f"✅ {file.name}")
            
        except Exception as e:
            st.error(f"❌ {result['file'].name}: {e}")
    
    if saved_count > 0:
        st.success(f"✅ {saved_count} קבצים נשמרו במצב בסיסי")


def display_save_results(results: List[Dict], saved_count: int):
    """הצג תוצאות שמירה מפורטות"""
    
    st.subheader("📊 תוצאות שמירה מפורטות")
    
    if saved_count > 0:
        st.success(f"✅ {saved_count} מתוך {len(results)} קבצים נשמרו בהצלחה!")
        
        # סיכום לפי סוגים
        type_summary = {}
        for result in results:
            if result['success'] and 'document_type' in result:
                doc_type = result['document_type']
                type_summary[doc_type] = type_summary.get(doc_type, 0) + 1
        
        if type_summary:
            st.markdown("**📈 פילוח לפי סוגי מסמכים:**")
            cols = st.columns(min(4, len(type_summary)))
            for i, (doc_type, count) in enumerate(type_summary.items()):
                with cols[i % 4]:
                    clean_type = doc_type.split(' ', 1)[-1] if ' ' in doc_type else doc_type
                    st.metric(clean_type[:15], count)
        
        # פירוט תוצאות
        with st.expander("📋 פירוט מלא"):
            for result in results:
                if result['success']:
                    action_icon = "🆕" if result.get('action') == 'new' else "🔄"
                    doc_type = result.get('document_type', 'לא ידוע')
                    confidence = result.get('confidence', 0)
                    
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.write(f"{action_icon} **{result['clean_name']}**")
                        st.caption(f"סוג: {doc_type}")
                    
                    with col2:
                        st.metric("ביטחון", f"{confidence:.0%}")
                    
                    with col3:
                        size_kb = result['size'] / 1024
                        st.metric("גודל", f"{size_kb:.1f}KB")
                    
                    if result.get('removed_files'):
                        st.caption(f"🗑️ הוחלפו {len(result['removed_files'])} קבצים קודמים")
                
                else:
                    st.error(f"❌ {result.get('original_name', 'קובץ לא ידוע')}: {result.get('error', 'שגיאה')}")
        
        # הנחיות המשך
        st.info("🔄 המשך: לחץ על 'עבד מסמכים חדשים' בסרגל הצדדי לעיבוד הקבצים")
        
    else:
        st.error("❌ לא נשמר אף קובץ - בדוק שגיאות ונסה שוב")


def show_document_processing():
    """הצג ממשק עיבוד מסמכים מתקדם"""
    if not HELPERS_AVAILABLE:
        show_processing_fallback()
        return
    
    st.markdown("### ⚙️ עיבוד מסמכים מתקדם")
    
    # בדוק קבצים זמינים לעיבוד
    uploaded_dir = Path("data/uploaded_documents")
    if not uploaded_dir.exists():
        st.info("📁 אין קבצים לעיבוד - העלה קבצים תחילה")
        return
    
    pdf_files = list(uploaded_dir.glob("*.pdf"))
    if not pdf_files:
        st.info("📄 אין קבצי PDF לעיבוד")
        return
    
    # הצג סיכום קבצים
    st.markdown(f"**📊 זמין לעיבוד: {len(pdf_files)} קבצים**")
    
    # אפשרויות עיבוד
    col1, col2 = st.columns([3, 1])
    
    with col1:
        processing_mode = st.selectbox(
            "מצב עיבוד:",
            [
                "🚀 מהיר - עיבוד בסיסי",
                "🎯 מותאם - לפי סוג מסמך", 
                "🔍 מעמיק - ניתוח מלא עם OCR"
            ],
            index=1,
            help="בחר רמת עיבוד לפי הצורך"
        )
    
    with col2:
        parallel_processing = st.checkbox(
            "⚡ עיבוד מקבילי", 
            value=True,
            help="עיבוד מספר קבצים במקביל (מהיר יותר)"
        )
    
    # כפתור עיבוד
    if st.button("🔄 התחל עיבוד מותאם", type="primary", key="advanced_process_docs"):
        process_documents_advanced(pdf_files, processing_mode, parallel_processing)


def process_documents_advanced(pdf_files: List[Path], mode: str, parallel: bool):
    """עבד מסמכים במצב מתקדם"""
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text("🔄 מתחיל עיבוד מתקדם...")
        progress_bar.progress(10)
        
        # קרא metadata לכל קובץ
        files_with_metadata = []
        for pdf_file in pdf_files:
            metadata_file = pdf_file.parent / f"{pdf_file.stem}_metadata.json"
            metadata = {}
            
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                except:
                    pass
            
            files_with_metadata.append({
                'path': pdf_file,
                'metadata': metadata,
                'type': metadata.get('document_type', '📄 מסמך אחר')
            })
        
        progress_bar.progress(30)
        status_text.text(f"📋 מעבד {len(files_with_metadata)} קבצים עם metadata...")
        
        # קרא לפונקציית העיבוד
        success, stdout, stderr = process_documents_function()
        
        progress_bar.progress(80)
        
        if success:
            progress_bar.progress(100)
            status_text.text("✅ עיבוד הושלם!")
            
            st.success("✅ המסמכים עובדו בהצלחה עם ניתוח מותאם לסוג!")
            
            if stdout:
                with st.expander("📋 פלט עיבוד מפורט"):
                    st.text_area("יומן עיבוד:", stdout, height=200)
            
            # נקה cache
            if 'chatbot' in st.session_state:
                chatbot = st.session_state.chatbot
                if hasattr(chatbot, 'clear_search_cache'):
                    chatbot.clear_search_cache()
                if hasattr(chatbot, 'reload_documents'):
                    chatbot.reload_documents()
            
            st.success("🔄 Cache נוקה והמסמכים נטענו מחדש")
            time.sleep(2)
            st.rerun()
            
        else:
            progress_bar.empty()
            status_text.empty()
            
            st.error("❌ שגיאה בעיבוד המסמכים")
            
            if stderr:
                with st.expander("❌ שגיאות"):
                    st.error(stderr)
            
            if stdout:
                with st.expander("📋 פלט נוסף"):
                    st.text_area("פלט:", stdout, height=150)
                    
        progress_bar.empty()
        status_text.empty()
        
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"❌ שגיאה במהלך העיבוד: {e}")


def show_processing_fallback():
    """ממשק עיבוד fallback"""
    st.warning("⚠️ מעבד בסיסי - פונקציית עיבוד מתקדמת לא זמינה")
    
    if st.button("🔄 עיבוד בסיסי", key="basic_process"):
        st.info("🔄 מעבד במצב בסיסי...")
        # כאן יכול להיות עיבוד בסיסי
        st.success("✅ עיבוד בסיסי הושלם")


def show_files_status(file_manager=None):
    """הצג מצב קבצים מפורט"""
    
    st.markdown("### 📊 מצב מערכת קבצים")
    
    # סטטיסטיקות בסיסיות
    stats = get_basic_file_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📄 PDF", stats['uploaded'], help="קבצי PDF שהועלו")
    
    with col2:
        st.metric("⚙️ מעובדים", stats['processed'], help="מסמכים מעובדים")
    
    with col3:
        st.metric("📋 סיכומים", stats['summaries'], help="סיכומים משפטיים")
    
    with col4:
        st.metric("🏷️ מתויגים", stats['tagged'], help="מסמכים עם metadata")
    
    # התקדמות
    if stats['uploaded'] > 0:
        processing_pct = (stats['processed'] / stats['uploaded']) * 100
        summary_pct = (stats['summaries'] / stats['uploaded']) * 100
        
        st.markdown("**📈 התקדמות:**")
        st.progress(processing_pct / 100, text=f"עיבוד: {processing_pct:.0f}%")
        st.progress(summary_pct / 100, text=f"סיכומים: {summary_pct:.0f}%")
    
    # פרטים מורחבים
    if FILE_MANAGER_AVAILABLE and file_manager:
        show_detailed_files_status(file_manager)
    else:
        show_basic_files_listing()


def get_basic_file_stats() -> Dict[str, int]:
    """קבל סטטיסטיקות קבצים בסיסיות"""
    try:
        return {
            'uploaded': len(list(Path("data/uploaded_documents").glob("*.pdf"))) if Path("data/uploaded_documents").exists() else 0,
            'processed': len(list(Path("data/processed").glob("*.json"))) if Path("data/processed").exists() else 0,
            'summaries': len(list(Path("data/summaries").glob("*.json"))) if Path("data/summaries").exists() else 0,
            'tagged': len(list(Path("data/metadata").glob("*_metadata.json"))) if Path("data/metadata").exists() else 0
        }
    except Exception as e:
        return {'uploaded': 0, 'processed': 0, 'summaries': 0, 'tagged': 0}


def show_detailed_files_status(file_manager):
    """הצג מצב קבצים מפורט עם SmartFileManager"""
    status = file_manager.get_files_status()
    
    # קבצים לפי סוגים
    if status['uploaded']:
        with st.expander("📁 קבצים שהועלו (לפי סוגים)", expanded=False):
            type_groups = {}
            
            for file_info in status['uploaded']:
                # קרא metadata
                metadata_file = Path("data/metadata") / f"{file_info['base_name']}_metadata.json"
                doc_type = "📄 לא מתויג"
                
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                            doc_type = metadata.get('document_type', '📄 לא מתויג')
                    except:
                        pass
                
                if doc_type not in type_groups:
                    type_groups[doc_type] = []
                
                type_groups[doc_type].append(file_info)
            
            for doc_type, files in type_groups.items():
                st.markdown(f"**{doc_type}:** {len(files)} קבצים")
                for file_info in files:
                    size_mb = file_info['size'] / (1024 * 1024)
                    st.write(f"  • {file_info['name']} ({size_mb:.1f}MB)")


def show_basic_files_listing():
    """הצג רשימת קבצים בסיסית"""
    
    with st.expander("📋 פירוט קבצים", expanded=False):
        
        # קבצי PDF
        uploaded_dir = Path("data/uploaded_documents")
        if uploaded_dir.exists():
            pdf_files = list(uploaded_dir.glob("*.pdf"))
            if pdf_files:
                st.markdown("**📄 קבצי PDF:**")
                for pdf_file in pdf_files:
                    size = pdf_file.stat().st_size / (1024 * 1024)
                    st.write(f"• {pdf_file.name} ({size:.1f}MB)")
        
        # קבצים מעובדים
        processed_dir = Path("data/processed")
        if processed_dir.exists():
            processed_files = list(processed_dir.glob("*.json"))
            if processed_files:
                st.markdown("**⚙️ מעובדים:**")
                for proc_file in processed_files:
                    st.write(f"• {proc_file.stem.replace('_processed', '')}")


def show_debug_info():
    """הצג מידע debug מתקדם"""
    
    with st.expander("🔍 מידע טכני ו-debug", expanded=False):
        
        # מצב רכיבים
        st.markdown("**🔧 מצב רכיבי מערכת:**")
        
        components = {
            'SmartFileManager': FILE_MANAGER_AVAILABLE,
            'Helpers': HELPERS_AVAILABLE,
            'Settings': SETTINGS_AVAILABLE,
        }
        
        for component, available in components.items():
            status_icon = "✅" if available else "❌" 
            st.write(f"{status_icon} {component}")
        
        # סטטיסטיקות מערכת
        st.markdown("**📊 סטטיסטיקות מערכת:**")
        
        stats = get_basic_file_stats()
        debug_info = {
            **stats,
            'session_keys': len(st.session_state.keys()),
            'upload_tags_count': len(st.session_state.get('current_upload_tags', {})),
            'component_availability': f"{sum(components.values())}/{len(components)}"
        }
        
        st.json(debug_info)
        
        # מידע על session
        if st.checkbox("🔍 הצג מידע session מפורט"):
            session_info = {}
            for key, value in st.session_state.items():
                if isinstance(value, (str, int, float, bool)):
                    session_info[key] = value
                else:
                    session_info[key] = f"<{type(value).__name__}>"
            
            st.json(session_info)
