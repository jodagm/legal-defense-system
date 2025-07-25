"""
מערכת הגנה משפטית חכמה - גרסה מתקדמת 2.2.0
עם ניתוח מסמכים משפטיים, AI מתקדם, וכלי ניהול מקצועיים
"""
import streamlit as st
import sys
import os
import time
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# הוסף את התיקייה הראשית ל-path
sys.path.append(str(Path(__file__).parent))

# ייבוא המודולים עם טיפול שגיאות מתקדם
def import_with_fallback():
    """ייבוא חכם עם fallbacks ודיווח מפורט"""
    chatbot_class = None
    import_errors = []
    
    # נסה לייבא את הצ'אטבוט
    chatbot_attempts = [
        ("core.chatbot", "LegalChatBot"),
        ("core.chatbot", "LegalChatbot"),
        ("core.chatbot", "ChatBot"),
        ("chatbot", "LegalChatBot")
    ]
    
    for module, class_name in chatbot_attempts:
        try:
            imported_module = __import__(module, fromlist=[class_name])
            chatbot_class = getattr(imported_module, class_name)
            print(f"✅ Successfully imported {class_name} from {module}")
            break
        except (ImportError, AttributeError) as e:
            import_errors.append(f"{module}.{class_name}: {e}")
    
    if not chatbot_class:
        st.error("❌ לא הצלחתי לייבא את הצ'אטבוט מאף מקום:")
        for error in import_errors:
            st.error(f"  - {error}")
        st.info("💡 ודא שהקובץ core/chatbot.py קיים ומכיל את הקלאס LegalChatBot")
        st.stop()
    
    return chatbot_class

# ייבא את הצ'אטבוט
LegalChatBot = import_with_fallback()

# ייבואים נוספים עם fallbacks
try:
    from ui.sidebar import show_sidebar, show_system_status_summary
    UI_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ UI modules not available: {e}")
    UI_AVAILABLE = False

try:
    from processors.legal_summary import LegalSummaryProcessor
    SUMMARY_PROCESSOR_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Summary processor not available: {e}")
    SUMMARY_PROCESSOR_AVAILABLE = False

try:
    from config.settings import (
        UI_MESSAGES, CLAUDE_MODEL, QUICK_QUESTIONS,
        DOCUMENT_TYPES, STREAMLIT_CONFIG
    )
    SETTINGS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Settings not fully available: {e}")
    SETTINGS_AVAILABLE = False
    # ברירות מחדל
    UI_MESSAGES = {
        'welcome': "🏛️ מערכת הגנה משפטית חכמה מוכנה לשימוש!",
        'no_documents': "❌ לא נמצאו מסמכים מעובדים"
    }
    CLAUDE_MODEL = "claude-3-haiku-20240307"
    QUICK_QUESTIONS = []
    DOCUMENT_TYPES = {}
    STREAMLIT_CONFIG = {
        'page_title': 'מערכת הגנה משפטית',
        'page_icon': '🏛️', 
        'layout': 'wide'
    }


class SystemManager:
    """מנהל מערכת מתקדם עם כלי ניהול וניטור"""
    
    def __init__(self):
        self.start_time = time.time()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.operation_log = []
    
    def log_operation(self, operation: str, status: str = "success", details: str = ""):
        """רשום פעולה ביומן המערכת"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'status': status,
            'details': details,
            'session_id': self.session_id
        }
        self.operation_log.append(entry)
        
        # שמור ביומן קבוע
        try:
            log_file = Path("data/logs/system.log")
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"{entry['timestamp']} - {operation} - {status} - {details}\n")
        except Exception as e:
            print(f"Warning: Could not write to log file: {e}")
    
    def get_system_health(self) -> Dict:
        """קבל מצב בריאות המערכת"""
        try:
            data_dirs = ["data/uploaded_documents", "data/processed", "data/summaries"]
            health = {
                'uptime': time.time() - self.start_time,
                'session_id': self.session_id,
                'operation_count': len(self.operation_log),
                'directories_status': {},
                'total_files': 0,
                'total_size_mb': 0
            }
            
            for dir_path in data_dirs:
                path = Path(dir_path)
                if path.exists():
                    files = list(path.glob("**/*"))
                    file_count = len([f for f in files if f.is_file()])
                    health['directories_status'][dir_path] = {
                        'exists': True,
                        'file_count': file_count
                    }
                    health['total_files'] += file_count
                else:
                    health['directories_status'][dir_path] = {
                        'exists': False,
                        'file_count': 0
                    }
            
            # חשב גודל כולל
            data_path = Path("data")
            if data_path.exists():
                total_size = sum(f.stat().st_size for f in data_path.rglob("*") if f.is_file())
                health['total_size_mb'] = total_size / (1024 * 1024)
            
            return health
            
        except Exception as e:
            self.log_operation("get_system_health", "error", str(e))
            return {'error': str(e)}

    def cleanup_old_files(self, days: int = 30) -> Dict:
        """נקה קבצים ישנים"""
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            cleanup_stats = {'deleted_files': 0, 'freed_space_mb': 0}
            
            for log_file in Path("data/logs").glob("*.log"):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    size_mb = log_file.stat().st_size / (1024 * 1024)
                    log_file.unlink()
                    cleanup_stats['deleted_files'] += 1
                    cleanup_stats['freed_space_mb'] += size_mb
            
            self.log_operation("cleanup_old_files", "success", 
                             f"Deleted {cleanup_stats['deleted_files']} files, freed {cleanup_stats['freed_space_mb']:.1f}MB")
            return cleanup_stats
            
        except Exception as e:
            self.log_operation("cleanup_old_files", "error", str(e))
            return {'error': str(e)}


# יצירת מנהל מערכת גלובלי
if 'system_manager' not in st.session_state:
    st.session_state.system_manager = SystemManager()

system_manager = st.session_state.system_manager


def initialize_chatbot():
    """אתחל את הצ'אטבוט המשפטי עם ניטור מתקדם"""
    if 'chatbot' not in st.session_state:
        with st.spinner("🔄 מאתחל מערכת AI משפטית מתקדמת..."):
            try:
                start_time = time.time()
                st.session_state.chatbot = LegalChatBot()
                init_time = time.time() - start_time
                
                # רשום אתחול מוצלח
                system_manager.log_operation("chatbot_initialization", "success", 
                                           f"Initialized in {init_time:.2f}s")
                
                # הצג מידע על החיבור
                if hasattr(st.session_state.chatbot, 'claude_client') and st.session_state.chatbot.claude_client:
                    st.success(f"✅ AI מתחבר - אתחול הושלם ב-{init_time:.1f} שניות")
                else:
                    st.warning("⚠️ AI אותחל אבל ללא חיבור לClaude - בדוק API key")
                    
            except Exception as e:
                system_manager.log_operation("chatbot_initialization", "error", str(e))
                st.error(f"❌ שגיאה באתחול AI: {e}")
                raise
    
    return st.session_state.chatbot


def check_system_requirements():
    """בדוק דרישות מערכת וזמינות רכיבים"""
    requirements = {
        'python_version': sys.version_info >= (3, 7),
        'required_directories': True,
        'chatbot_available': 'chatbot' in st.session_state,
        'ui_components': UI_AVAILABLE,
        'summary_processor': SUMMARY_PROCESSOR_AVAILABLE,
        'settings_loaded': SETTINGS_AVAILABLE
    }
    
    # יצר תיקיות נדרשות
    essential_dirs = [
        "data", "data/uploaded_documents", "data/processed", 
        "data/summaries", "data/metadata", "data/logs"
    ]
    
    try:
        for dir_path in essential_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        requirements['required_directories'] = False
        system_manager.log_operation("create_directories", "error", str(e))
    
    return requirements


def enhanced_document_check(chatbot):
    """בדיקה מתקדמת של מצב המסמכים"""
    try:
        # בדיקות מרובות לוודא דיוק
        checks = {
            'chatbot_method': False,
            'file_system': False,
            'vectorizer': False,
            'document_chunks': False
        }
        
        # בדיקה 1: מתוד הצ'אטבוט
        if hasattr(chatbot, 'has_documents'):
            checks['chatbot_method'] = chatbot.has_documents()
        
        # בדיקה 2: מערכת קבצים
        processed_path = Path("data/processed")
        if processed_path.exists():
            json_files = list(processed_path.glob("*.json"))
            checks['file_system'] = len(json_files) > 0
        
        # בדיקה 3: vectorizer
        if hasattr(chatbot, 'vectorizer') and chatbot.vectorizer:
            checks['vectorizer'] = True
        
        # בדיקה 4: document chunks
        if hasattr(chatbot, 'document_chunks') and chatbot.document_chunks:
            checks['document_chunks'] = True
        
        # החלטה מבוססת רוב
        positive_checks = sum(checks.values())
        has_documents = positive_checks >= 2  # רוב הבדיקות חיוביות
        
        # רשום תוצאות
        system_manager.log_operation("document_check", "success", 
                                   f"Checks: {checks}, Result: {has_documents}")
        
        return {
            'has_documents': has_documents,
            'checks': checks,
            'confidence': positive_checks / len(checks)
        }
        
    except Exception as e:
        system_manager.log_operation("document_check", "error", str(e))
        return {'has_documents': False, 'error': str(e)}


def smart_search_and_respond(chatbot, question: str, **kwargs) -> Dict:
    """מערכת חיפוש חכמה עם fallbacks מרובים"""
    
    system_manager.log_operation("search_request", "started", f"Query: {question[:50]}...")
    
    try:
        # בדוק מצב מסמכים
        doc_status = enhanced_document_check(chatbot)
        has_docs = doc_status.get('has_documents', False)
        
        if not has_docs:
            st.info("ℹ️ לא נמצאו מסמכים מעובדים - מתן תשובה כללית")
        
        # רצף של ניסיונות חיפוש
        search_attempts = [
            ("search_and_respond", "המערכת המתקדמת"),
            ("hybrid_search_response", "חיפוש היברידי"),
            ("semantic_search_response", "חיפוש סמנטי"),
            ("simple_search_response", "חיפוש פשוט"),
            ("manual_document_search", "חיפוש ידני"),
            ("general_ai_response", "תשובה כללית")
        ]
        
        last_error = None
        
        for method_name, description in search_attempts:
            try:
                st.info(f"🔍 מנסה {description}...")
                
                if method_name == "search_and_respond" and hasattr(chatbot, 'search_and_respond'):
                    response = chatbot.search_and_respond(question, **kwargs)
                    if response and response.get('answer'):
                        system_manager.log_operation("search_request", "success", f"Method: {description}")
                        return enhance_response(response, method_name)
                
                elif method_name == "manual_document_search":
                    response = perform_manual_search(question)
                    if response and response.get('answer'):
                        system_manager.log_operation("search_request", "success", f"Method: {description}")
                        return enhance_response(response, method_name)
                
                elif method_name == "general_ai_response":
                    response = get_general_legal_response(chatbot, question)
                    system_manager.log_operation("search_request", "success", f"Method: {description}")
                    return enhance_response(response, method_name)
                    
            except Exception as e:
                last_error = e
                st.warning(f"⚠️ {description} נכשל: {e}")
                continue
        
        # אם כל השיטות נכשלו
        system_manager.log_operation("search_request", "failed", f"All methods failed. Last error: {last_error}")
        return {
            'answer': f"❌ כל שיטות החיפוש נכשלו. שגיאה אחרונה: {last_error}",
            'sources': [],
            'error': str(last_error) if last_error else "Unknown error"
        }
        
    except Exception as e:
        system_manager.log_operation("search_request", "error", str(e))
        return {
            'answer': f"❌ שגיאה כללית במערכת החיפוש: {e}",
            'sources': [],
            'error': str(e)
        }


def enhance_response(response: Dict, method: str) -> Dict:
    """שפר תשובה עם metadata נוספת"""
    if not isinstance(response, dict):
        response = {'answer': str(response), 'sources': []}
    
    response.update({
        'search_method_used': method,
        'timestamp': datetime.now().isoformat(),
        'enhanced': True
    })
    
    return response


def perform_manual_search(query: str) -> Dict:
    """חיפוש ידני מתקדם במסמכים"""
    try:
        st.info("🔍 מבצע חיפוש ידני מתקדם...")
        
        processed_path = Path("data/processed")
        summaries_path = Path("data/summaries")
        
        all_content = []
        sources_found = []
        
        # חפש במסמכים מעובדים
        if processed_path.exists():
            for json_file in processed_path.glob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    doc_name = json_file.stem.replace('_processed', '')
                    doc_type = data.get('document_type', 'מסמך')
                    
                    for i, chunk in enumerate(data.get('chunks', [])):
                        chunk_text = chunk.get('text', '')
                        if is_relevant_to_query(query, chunk_text):
                            all_content.append(chunk_text)
                            sources_found.append({
                                'file': f"{doc_name} ({doc_type})",
                                'content': chunk_text[:400] + "...",
                                'similarity': calculate_simple_relevance(query, chunk_text),
                                'chunk': i + 1,
                                'type': 'document'
                            })
                except Exception as e:
                    st.warning(f"⚠️ שגיאה בקריאת {json_file.name}: {e}")
        
        # חפש בסיכומים
        if summaries_path.exists():
            for summary_file in summaries_path.glob("*.json"):
                try:
                    with open(summary_file, 'r', encoding='utf-8') as f:
                        summary_data = json.load(f)
                    
                    if summary_data.get('status') == 'completed':
                        summary_text = summary_data.get('legal_summary', '')
                        doc_name = summary_data.get('document_name', 'מסמך')
                        
                        if is_relevant_to_query(query, summary_text):
                            all_content.append(f"סיכום של {doc_name}:\n{summary_text}")
                            sources_found.append({
                                'file': f"סיכום: {doc_name}",
                                'content': summary_text[:400] + "...",
                                'similarity': calculate_simple_relevance(query, summary_text) + 0.2,
                                'type': 'summary'
                            })
                except Exception as e:
                    st.warning(f"⚠️ שגיאה בקריאת סיכום: {e}")
        
        if all_content:
            # מיין לפי רלוונטיות
            sources_found.sort(key=lambda x: x['similarity'], reverse=True)
            
            # יצור תשובה עם AI אם אפשר
            combined_text = "\n\n".join(all_content[:5])  # הגבל לכמות מטופלת
            
            if 'chatbot' in st.session_state and hasattr(st.session_state.chatbot, 'claude_client'):
                ai_response = generate_ai_response_from_content(query, combined_text, sources_found)
                return ai_response
            else:
                return {
                    'answer': f"נמצאו {len(sources_found)} מקורות רלוונטיים:\n\n{combined_text[:1000]}...",
                    'sources': sources_found[:10]
                }
        else:
            return {
                'answer': "❌ לא נמצאו מסמכים רלוונטיים לשאלה. נסה לנסח את השאלה אחרת או העלה מסמכים נוספים.",
                'sources': []
            }
            
    except Exception as e:
        return {
            'answer': f"❌ שגיאה בחיפוש ידני: {e}",
            'sources': []
        }


def is_relevant_to_query(query: str, text: str) -> bool:
    """בדק רלוונטיות טקסט לשאלה עם אלגוריתם משופר"""
    query_lower = query.lower()
    text_lower = text.lower()
    
    # מילות מפתח משפטיות מורחבות
    legal_terms = [
        'תביעה', 'טענה', 'סעד', 'הגנה', 'ראיה', 'עד', 'חוק', 'משפט', 
        'בית משפט', 'שופט', 'פסק דין', 'החלטה', 'תצהיר', 'עדות',
        'חוזה', 'הסכם', 'נזק', 'פיצוי', 'אחריות', 'הפרה', 'זכות', 'חובה'
    ]
    
    # ציון בסיס
    score = 0
    
    # מילות השאלה
    query_words = [word for word in query_lower.split() if len(word) > 2]
    for word in query_words:
        if word in text_lower:
            score += 1
    
    # מילות מפתח משפטיות
    for term in legal_terms:
        if term in text_lower:
            score += 0.5
    
    # אורך טקסט מינימלי
    if len(text) < 50:
        score *= 0.5
    
    return score > 0.5


def calculate_simple_relevance(query: str, text: str) -> float:
    """חשב רלוונטיות פשוטה"""
    query_words = set(query.lower().split())
    text_words = set(text.lower().split())
    
    if not query_words:
        return 0.0
    
    intersection = query_words.intersection(text_words)
    return len(intersection) / len(query_words)


def generate_ai_response_from_content(query: str, content: str, sources: List[Dict]) -> Dict:
    """יצור תשובת AI מתוכן שנמצא"""
    try:
        chatbot = st.session_state.chatbot
        
        legal_prompt = f"""אתה עורך דין מומחה במשפט אזרחי ופלילי.

הוראה: נתח את התוכן הבא מתיק משפטי וענה על השאלה בצורה מקצועית.

השאלה: {query}

תוכן מהתיק ({len(sources)} מקורות):
{content}

הוראות לתשובה:
1. נתח את המידע מהתיק בצורה משפטית מקצועית
2. זהה נקודות חוזק וחולשה רלוונטיות
3. הצע המלצות אסטרטגיות להגנה
4. השתמש בציטוטים ישירים מהמסמכים
5. תן דעה משפטית מבוססת ומנומקת

תן תשובה מפורטה ומקצועית:"""

        # נסה מודלים שונים
        models_to_try = ["claude-3-haiku-20240307", "claude-3-sonnet-20240229"]
        
        for model in models_to_try:
            try:
                message = chatbot.claude_client.messages.create(
                    model=model,
                    max_tokens=3000,
                    temperature=0.2,
                    messages=[{"role": "user", "content": legal_prompt}]
                )
                
                return {
                    'answer': f"## תשובה משפטית מבוססת מסמכים\n\n{message.content[0].text}",
                    'sources': sources[:10],
                    'model_used': model,
                    'search_method': 'Manual search + AI analysis'
                }
                
            except Exception as e:
                st.warning(f"מודל {model} נכשל: {e}")
                continue
        
        # אם כל המודלים נכשלו
        return {
            'answer': f"נמצא תוכן רלוונטי אך לא ניתן לעבד אותו עם AI:\n\n{content[:800]}...",
            'sources': sources[:10]
        }
        
    except Exception as e:
        return {
            'answer': f"שגיאה ביצירת תשובת AI: {e}\n\nתוכן גולמי:\n{content[:500]}...",
            'sources': sources[:5]
        }


def get_general_legal_response(chatbot, query: str) -> Dict:
    """קבל תשובה משפטית כללית"""
    try:
        general_prompt = f"""אתה עורך דין מומחה במשפט ישראלי.

אין לי גישה למסמכים ספציפיים, אבל אנא תן תשובה משפטית כללית לשאלה הבאה:

{query}

כלול בתשובה:
1. הסבר כללי על הנושא המשפטי
2. עקרונות משפטיים רלוונטיים
3. הליכים טיפוסיים בנושא
4. נקודות מפתח לבדיקה
5. המלצות כלליות

תן תשובה מקצועית וברורה המבוססת על הידע המשפטי הכללי."""

        if hasattr(chatbot, 'claude_client') and chatbot.claude_client:
            message = chatbot.claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2000,
                temperature=0.3,
                messages=[{"role": "user", "content": general_prompt}]
            )
            
            return {
                'answer': f"## תשובה משפטית כללית\n\n{message.content[0].text}\n\n---\n**הערה:** תשובה כללית ללא מסמכים ספציפיים",
                'sources': [],
                'note': 'תשובה כללית ללא מסמכים ספציפיים'
            }
        else:
            return {
                'answer': "❌ שירות AI לא זמין. לא ניתן לספק תשובה כללית.",
                'sources': [],
                'error': 'claude_unavailable'
            }
            
    except Exception as e:
        return {
            'answer': f"❌ שגיאה בקבלת תשובה כללית: {e}",
            'sources': [],
            'error': str(e)
        }


def show_enhanced_main_interface(chatbot):
    """ממשק ראשי משופר עם תכונות מתקדמות"""
    
    # כותרת ראשית מתקדמת
    st.title("🏛️ מערכת הגנה משפטית חכמה")
    st.markdown("### ⚖️ מערכת AI מתקדמת לניתוח משפטי ואסטרטגיית הגנה")
    
    # תצוגת מצב מערכת מתקדמת
    show_advanced_system_status(chatbot)
    
    st.markdown("---")
    
    # הצג הודעת ברכה אם מוגדרת
    if SETTINGS_AVAILABLE and 'welcome' in UI_MESSAGES:
        with st.expander("📋 מדריך המערכת", expanded=False):
            st.markdown(UI_MESSAGES['welcome'])
    
    # בדיקת מסמכים מתקדמת
    doc_status = enhanced_document_check(chatbot)
    has_docs = doc_status.get('has_documents', False)
    confidence = doc_status.get('confidence', 0)
    
    # הצג מצב המסמכים
    if has_docs:
        file_stats = get_comprehensive_file_stats()
        st.success(f"✅ המערכת מוכנה - {file_stats['processed']} מסמכים מעובדים, {file_stats['summaries']} סיכומים (דיוק: {confidence:.0%})")
    else:
        st.warning("⚠️ לא נמצאו מסמכים מעובדים. העלה מסמכים דרך הסרגל הצדדי.")
    
    # ממשק שאלות מתקדם
    show_advanced_query_interface(chatbot, has_docs)
    
    # היסטוריה והמלצות
    show_query_history_and_suggestions()


def show_advanced_system_status(chatbot):
    """הצג מצב מערכת מתקדם"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # מצב AI
        ai_status = "🟢 מחובר" if (hasattr(chatbot, 'claude_client') and chatbot.claude_client) else "🔴 לא מחובר"
        st.metric("🤖 מצב AI", ai_status)
    
    with col2:
        # זמן פעילות
        uptime = system_manager.get_system_health().get('uptime', 0)
        st.metric("⏱️ זמן פעילות", f"{uptime/60:.1f}m")
    
    with col3:
        # פעולות
        operations = len(system_manager.operation_log)
        st.metric("📊 פעולות", operations)
    
    with col4:
        # גודל נתונים
        health = system_manager.get_system_health()
        size_mb = health.get('total_size_mb', 0)
        st.metric("💾 גודל נתונים", f"{size_mb:.1f}MB")


def get_comprehensive_file_stats() -> Dict:
    """קבל סטטיסטיקות קבצים מקיפות"""
    stats = {
        'uploaded': count_files_in_directory("data/uploaded_documents", "*.pdf"),
        'processed': count_files_in_directory("data/processed", "*.json"), 
        'summaries': count_files_in_directory("data/summaries", "*.json"),
        'metadata': count_files_in_directory("data/metadata", "*.json")
    }
    return stats


def show_advanced_query_interface(chatbot, has_docs: bool):
    """ממשק שאלות מתקדם"""
    st.subheader("💬 ממשק שאלות משפטיות מתקדם")
    
    # אפשר שאלות תמיד
    query_enabled = has_docs or st.checkbox(
        "🔄 אפשר שאלות כלליות ללא מסמכים",
        help="קבל תשובות משפטיות כלליות גם ללא מסמכים טעונים"
    )
    
    if query_enabled:
        # הצע שאלות מהירות אם מוגדרות
        if SETTINGS_AVAILABLE and QUICK_QUESTIONS:
            st.markdown("**💡 שאלות מהירות:**")
            cols = st.columns(min(len(QUICK_QUESTIONS), 3))
            for i, question in enumerate(QUICK_QUESTIONS[:3]):
                with cols[i % 3]:
                    if st.button(f"❓ {question[:30]}...", key=f"quick_q_{i}"):
                        st.session_state.user_query = question
        
        # שדה שאלה ראשי
        user_question = st.text_area(
            "🔍 שאל את השאלה המשפטית שלך:",
            value=st.session_state.get('user_query', ''),
            height=120,
            placeholder="דוגמה: מהן הטענות המרכזיות בתיק ומה נקודות החולשה שבהן?",
            help="שאל שאלות ספציפיות ומפורטות. המערכת תחפש במסמכים ותיתן ניתוח משפטי מקצועי."
        )
        
        # הגדרות מתקדמות
        with st.expander("⚙️ הגדרות חיפוש וניתוח מתקדמות"):
            col1, col2 = st.columns(2)
            
            with col1:
                search_method = st.selectbox(
                    "שיטת חיפוש:",
                    ["hybrid", "semantic", "keyword", "comprehensive"],
                    help="Hybrid = משלב סמנטי וחיפוש מילות מפתח\nComprehensive = חיפוש מקיף בכל השיטות"
                )
                
                analysis_type = st.selectbox(
                    "סוג ניתוח:",
                    ["standard", "precise", "comprehensive", "strategic"],
                    help="Standard = ניתוח רגיל\nPrecise = מדויק יותר\nComprehensive = מקיף ומפורט\nStrategic = התמקדות באסטרטגיה"
                )
            
            with col2:
                max_results = st.slider("מספר מקורות מקסימלי:", 5, 30, 15)
                include_summaries = st.checkbox("כלול סיכומים משפטיים", value=True)
                min_similarity = st.slider("דרגת דמיון מינימלית:", 0.1, 0.9, 0.2)
        
        # כפתור חיפוש מתקדם
        if st.button("🏛️ בצע חיפוש וניתוח משפטי", key="advanced_search", type="primary"):
            if user_question.strip():
                # נקה שאלה שמורה
                if 'user_query' in st.session_state:
                    del st.session_state.user_query
                
                # בצע חיפוש עם פרוגרס
                with st.spinner("🔍 מבצע חיפוש וניתוח משפטי מתקדם..."):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # עדכן פרוגרס
                    status_text.text("🔍 מחפש במסמכים...")
                    progress_bar.progress(25)
                    
                    try:
                        response = smart_search_and_respond(
                            chatbot, user_question,
                            method=search_method,
                            max_results=max_results,
                            min_similarity=min_similarity,
                            include_summaries=include_summaries,
                            analysis_type=analysis_type
                        )
                        
                        progress_bar.progress(75)
                        status_text.text("📝 מעבד תשובה...")
                        
                        # הצג תוצאות
                        display_advanced_response(response, user_question)
                        
                        progress_bar.progress(100)
                        status_text.text("✅ הושלם!")
                        time.sleep(1)
                        progress_bar.empty()
                        status_text.empty()
                        
                    except Exception as e:
                        progress_bar.empty()
                        status_text.empty()
                        st.error(f"❌ שגיאה: {e}")
            else:
                st.warning("⚠️ אנא כתוב שאלה")


def display_advanced_response(response: Dict, question: str):
    """הצג תשובה משפטית באופן מתקדם"""
    if not response:
        st.error("❌ לא התקבלה תשובה")
        return
    
    # כותרת תשובה
    st.markdown("## 📝 תשובה משפטית מתקדמת")
    
    # תוכן התשובה
    answer = response.get('answer', 'לא התקבלה תשובה')
    st.markdown(answer)
    
    # מידע טכני על התשובה
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'model_used' in response:
            st.caption(f"🤖 מודל: {response['model_used']}")
    
    with col2:
        if 'search_method_used' in response:
            st.caption(f"🔍 שיטה: {response['search_method_used']}")
    
    with col3:
        if 'processing_time' in response:
            st.caption(f"⏱️ זמן: {response['processing_time']}")
    
    # הצג הערות
    if 'note' in response:
        st.info(f"📝 הערה: {response['note']}")
    
    if 'error' in response:
        st.warning(f"⚠️ התרחשה שגיאה: {response['error']}")
    
    # מקורות משופרים
    sources = response.get('sources', [])
    if sources:
        with st.expander(f"📚 מקורות משפטיים ({len(sources)} נמצאו)", expanded=True):
            for i, source in enumerate(sources, 1):
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        file_name = source.get('file', 'לא ידוע')
                        doc_type = source.get('type', 'מסמך')
                        st.markdown(f"**מקור {i}: {file_name}**")
                        st.caption(f"סוג: {doc_type}")
                    
                    with col2:
                        similarity = source.get('similarity', 0)
                        st.metric("רלוונטיות", f"{similarity:.2f}")
                    
                    with col3:
                        if 'chunk' in source:
                            st.metric("חלק", source['chunk'])
                    
                    # תוכן המקור
                    content = source.get('content', '')
                    if content:
                        with st.expander(f"📄 תוכן מקור {i}", expanded=False):
                            st.text(content)
                    
                    st.divider()
    
    # שמור בהיסטוריה
    save_to_history(question, response)


def save_to_history(question: str, response: Dict):
    """שמור שאלה ותשובה בהיסטוריה"""
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    
    history_entry = {
        'timestamp': datetime.now().isoformat(),
        'question': question,
        'answer_preview': response.get('answer', '')[:200],
        'sources_count': len(response.get('sources', [])),
        'method': response.get('search_method_used', 'לא ידוע')
    }
    
    st.session_state.query_history.append(history_entry)
    
    # הגבל היסטוריה
    if len(st.session_state.query_history) > 20:
        st.session_state.query_history = st.session_state.query_history[-20:]


def show_query_history_and_suggestions():
    """הצג היסטוריית שאלות והצעות"""
    if hasattr(st.session_state, 'query_history') and st.session_state.query_history:
        with st.expander(f"📋 היסטוריית שאלות ({len(st.session_state.query_history)})", expanded=False):
            for i, entry in enumerate(reversed(st.session_state.query_history[-10:]), 1):
                timestamp = datetime.fromisoformat(entry['timestamp']).strftime("%H:%M")
                st.markdown(f"**{i}. [{timestamp}] {entry['question']}**")
                st.text(f"Method: {entry['method']} | Sources: {entry['sources_count']}")
                st.text(entry['answer_preview'] + "...")
                st.markdown("---")


def show_sidebar_fallback(chatbot):
    """sidebar fallback אם UI לא זמין"""
    st.sidebar.title("🏛️ ניהול מערכת")
    
    # מידע בסיסי
    st.sidebar.subheader("📊 מצב מערכת")
    
    # בדיקה בסיסית
    claude_connected = hasattr(chatbot, 'claude_client') and chatbot.claude_client
    st.sidebar.write(f"🤖 Claude: {'✅' if claude_connected else '❌'}")
    
    docs_available = bool(list(Path("data/processed").glob("*.json"))) if Path("data/processed").exists() else False
    st.sidebar.write(f"📄 מסמכים: {'✅' if docs_available else '❌'}")
    
    # כלי בסיסיים
    st.sidebar.subheader("🛠️ כלים")
    
    if st.sidebar.button("🔄 טען מחדש"):
        if hasattr(chatbot, 'reload_documents'):
            chatbot.reload_documents()
            st.sidebar.success("✅ נטען מחדש")
    
    if st.sidebar.button("🧹 נקה cache"):
        st.cache_data.clear()
        st.sidebar.success("✅ Cache נוקה")


def count_files_in_directory(directory_path: str, pattern: str = "*") -> int:
    """ספור קבצים בתיקייה"""
    try:
        path = Path(directory_path)
        return len(list(path.glob(pattern))) if path.exists() else 0
    except:
        return 0


def show_development_tools():
    """כלי פיתוח מתקדמים"""
    st.sidebar.divider()
    
    with st.sidebar.expander("⚡ כלי פיתוח מתקדמים", expanded=False):
        
        # מידע מערכת
        st.subheader("📊 מידע מערכת")
        health = system_manager.get_system_health()
        st.json(health)
        
        # לוג פעולות
        if st.button("📋 הצג לוג פעולות", key="show_log"):
            with st.expander("📋 לוג פעולות אחרונות"):
                for entry in system_manager.operation_log[-10:]:
                    st.text(f"{entry['timestamp']}: {entry['operation']} - {entry['status']}")
        
        # ניקוי קבצים ישנים
        if st.button("🧹 נקה קבצים ישנים", key="cleanup_old"):
            result = system_manager.cleanup_old_files()
            if 'error' in result:
                st.error(f"שגיאה: {result['error']}")
            else:
                st.success(f"נוקו {result['deleted_files']} קבצים, שוחרר {result['freed_space_mb']:.1f}MB")
        
        # איפוס מהיר
        st.subheader("🗑️ איפוס")
        if st.button("🚮 איפוס מלא", key="dev_reset"):
            perform_system_reset()
        
        # בדיקות מערכת
        st.subheader("🔧 בדיקות")
        if st.button("✅ בדוק דרישות", key="check_req"):
            requirements = check_system_requirements()
            for req, status in requirements.items():
                icon = "✅" if status else "❌"
                st.write(f"{icon} {req}: {status}")


def perform_system_reset():
    """בצע איפוס מערכת מלא"""
    try:
        data_path = Path("data")
        if data_path.exists():
            shutil.rmtree(data_path)
        
        # צור תיקיות חדשות
        essential_dirs = [
            "data", "data/uploaded_documents", "data/processed",
            "data/summaries", "data/metadata", "data/logs"
        ]
        
        for dir_path in essential_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        
        # נקה session state
        st.session_state.clear()
        
        # רשום פעולה
        system_manager.log_operation("full_system_reset", "success", "Complete reset performed")
        
        st.success("✅ איפוס מלא בוצע")
        
    except Exception as e:
        system_manager.log_operation("full_system_reset", "error", str(e))
        st.error(f"❌ שגיאה באיפוס: {e}")


def main():
    """פונקציה ראשית משופרת"""
    
    # הגדרת עמוד
    page_config = STREAMLIT_CONFIG if SETTINGS_AVAILABLE else {
        'page_title': 'מערכת הגנה משפטית',
        'page_icon': '🏛️',
        'layout': 'wide'
    }
    
    st.set_page_config(**page_config)
    
    # CSS מתקדם
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #1f4e79, #2d5a8b);
        color: white;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    .metric-container {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #007bff;
        margin: 0.5rem 0;
    }
    
    .success-alert {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .warning-alert {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .error-alert {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .source-container {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    try:
        # בדוק דרישות מערכת
        requirements = check_system_requirements()
        
        # הצג אזהרות אם נדרש
        failed_requirements = [req for req, status in requirements.items() if not status]
        if failed_requirements:
            st.warning(f"⚠️ דרישות מערכת לא הושלמו: {failed_requirements}")
        
        # אתחל צ'אטבוט
        chatbot = initialize_chatbot()
        
        # הצג sidebar - UI או fallback
        if UI_AVAILABLE:
            show_sidebar(chatbot)
            show_system_status_summary(chatbot)
        else:
            show_sidebar_fallback(chatbot)
        
        # כלי פיתוח
        show_development_tools()
        
        # ממשק ראשי
        show_enhanced_main_interface(chatbot)
        
        # מידע תחתון
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 💡 עצות שימוש מתקדם:
            - **תיוג מדויק** של מסמכים לפי סוגם המשפטי
            - **שאלות ספציפיות** מביאות תשובות טובות יותר  
            - **שימוש בסיכומים** לתובנות אסטרטגיות
            - **ניתוח הדרגתי** מהכללי לפרטי
            """)
        
        with col2:
            st.markdown("""
            ### 🔧 תכונות מתקדמות:
            - **חיפוש היברידי** - סמנטי + מילות מפתח
            - **ניתוח אסטרטגי** - זיהוי נקודות חוזק/חולשה
            - **מעקב פעולות** - לוג מפורט של השימוש
            - **איפוס מוגן** - עם אישורים כפולים
            """)
        
        # מידע טכני מתקדם
        with st.expander("🔍 מידע טכני מתקדם"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                **🛠️ מפרטים טכניים:**
                - **גרסה:** 2.2.0 (מתקדמת)
                - **מנוע AI:** Claude Haiku/Sonnet  
                - **חיפוש:** TF-IDF + Semantic
                - **אחסון:** מקומי מוצפן
                """)
            
            with col2:
                st.markdown("""
                **📊 רכיבי מערכת:**
                - **חיפוש:** Hybrid + Fallbacks
                - **UI:** Progressive Enhancement
                - **לוגים:** Structured Logging
                - **כלים:** Advanced Dev Tools
                """)
            
            # הצג מצב מערכת מפורט
            if 'chatbot' in st.session_state:
                stats = st.session_state.chatbot.get_document_stats() if hasattr(st.session_state.chatbot, 'get_document_stats') else {}
                health = system_manager.get_system_health()
                
                st.markdown("**📈 סטטיסטיקות נוכחיות:**")
                
                metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
                
                with metrics_col1:
                    st.metric("📄 מסמכים", stats.get('unique_documents', 0))
                
                with metrics_col2:
                    st.metric("🔍 חתיכות", stats.get('total_chunks', 0))
                
                with metrics_col3:
                    st.metric("📋 סיכומים", stats.get('summaries_count', 0))
                
                with metrics_col4:
                    st.metric("💾 גודל", f"{health.get('total_size_mb', 0):.1f}MB")
    
    except Exception as e:
        # טיפול שגיאות מתקדם
        system_manager.log_operation("main_function", "error", str(e))
        
        st.error("❌ שגיאה כללית במערכת")
        
        with st.expander("🔍 פרטי השגיאה"):
            st.code(str(e))
            
            # הצע פתרונות
            st.markdown("""
            **💡 פתרונות מוצעים:**
            1. רענן את הדף (F5)
            2. נקה cache בכלי הפיתוח
            3. בצע איפוס מלא אם הבעיה נמשכת
            4. בדוק שכל הקבצים קיימים בתיקיות הנכונות
            """)
        
        # אפשרות חירום
        if st.button("🚨 איפוס חירום מלא", key="emergency_reset"):
            perform_system_reset()
            st.success("✅ איפוס חירום בוצע - אנא רענן את הדף")


if __name__ == "__main__":
    main()
