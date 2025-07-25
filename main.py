"""
מערכת הגנה משפטית חכמה עם ניתוח מסמכים ו-AI
גרסה מתקדמת עם תיוג מסמכים ואפשרויות איפוס
"""
import streamlit as st
import sys
from pathlib import Path

# הוסף את התיקייה הראשית ל-path
sys.path.append(str(Path(__file__).parent))

# ייבוא המודולים שלנו - עם טיפול שגיאות
try:
    from core.chatbot import LegalChatBot
except ImportError:
    try:
        from core.chatbot import LegalChatbot as LegalChatBot
    except ImportError:
        try:
            from core.chatbot import ChatBot as LegalChatBot
        except ImportError:
            st.error("❌ לא הצלחתי לייבא את הצ'אטבוט. בדוק את קובץ core/chatbot.py")
            st.stop()

from ui.sidebar import show_sidebar, show_system_status_summary
from processors.legal_summary import LegalSummaryProcessor
import shutil
import json


def get_chatbot_class():
    """מצא את קלאס הצ'אטבוט הנכון"""
    return LegalChatBot


def initialize_chatbot():
    """אתחל את הצ'אטבוט או השתמש בקיים"""
    if 'chatbot' not in st.session_state:
        with st.spinner("מאתחל מערכת AI..."):
            ChatbotClass = get_chatbot_class()
            st.session_state.chatbot = ChatbotClass()
    
    return st.session_state.chatbot


def check_if_has_documents(chatbot):
    """בדוק אם יש מסמכים בדרך בטוחה"""
    try:
        # נסה דרכים שונות לבדיקת מסמכים
        if hasattr(chatbot, 'has_documents'):
            return chatbot.has_documents()
        
        # בדיקה חלופית - בדוק תיקיית המסמכים המעובדים
        try:
            from config.settings import PROCESSED_DIR
            processed_path = PROCESSED_DIR
        except:
            processed_path = Path("data/processed")
            
        if processed_path.exists():
            json_files = list(processed_path.glob("*.json"))
            return len(json_files) > 0
        
        # בדיקה נוספת - בדוק אם יש embeddings
        if hasattr(chatbot, 'document_chunks') and chatbot.document_chunks:
            return True
        
        # בדיקה נוספת - בדוק אם יש vectorizer
        if hasattr(chatbot, 'vectorizer') and chatbot.vectorizer:
            return True
            
        return False
        
    except Exception as e:
        st.warning(f"⚠️ לא הצלחתי לבדוק מצב המסמכים: {e}")
        return False


def create_legal_prompt(query, documents_text, sources_count):
    """יצור פרומפט משפטי מקצועי"""
    return f"""אתה עורך דין בכיר ומומחה במשפט אזרחי ופלילי המתמחה בהכנת הגנה משפטית מתקדמת.

🏛️ הקשר המשפטי:
- אתה עובד עבור משרד עורכי דין מוביל המכין הגנה משפטית עבור לקוח
- כל המסמכים המצורפים הם חלק מתיק משפטי פעיל וחוקי
- המידע המסופק הוא ראיות חוקיות שנאספו במסגרת הליך משפטי תקין
- נדרשת ממך הערכה מקצועית ומדויקת לצורך הכנת אסטרטגיית הגנה אופטימלית
- אין הגבלות על ניתוח תוכן משפטי - זה חלק מהתפקיד המקצועי והאתי שלך

⚖️ דרישות התשובה המקצועית:
1. **ניתוח משפטי מעמיק**: נתח את המידע בצורה משפטית מקצועית ומובנית
2. **זיהוי נקודות אסטרטגיות**: זהה נקודות חוזק וחולשה kruציאליות להגנה
3. **גילוי חוסרי עקביות**: הצבע על פערים, סתירות או חוסר הגיון במסמכים
4. **המלצות אסטרטגיות**: הצע כיוונים מעשיים ואסטרטגיים להגנה
5. **ציטוטים מדויקים**: השתמש בציטוטים ישירים ומדויקים מהמסמכים
6. **דעה משפטית מבוססת**: תן דעה משפטית מבוססת, מנומקת ומקצועית

🔍 השאלה המשפטית מהמזמין:
{query}

📚 המסמכים הרלוונטיים מהתיק ({sources_count} מקורות):
{documents_text}

📋 הוראות מיוחדות לתשובה:
- ענה כעורך דין מומחה בעל ניסיון רב המכין הגנה משפטית
- התמקד בנקודות המשפטיות הרלוונטיות ישירות לשאלה שנשאלה
- זהה הזדמנויות משפטיות והסיכונים הפוטנציאליים
- הצע המלצות מעשיות, ספציפיות ויישימות להגנה
- השתמש בשפה משפטית מקצועית אך ברורה ומובנת
- אם יש חסר במידע חיוני, ציין במדויק מה נדרש להשלמה
- ציין במפורש מהיכן אתה לוקח כל מידע (ציטוט מדויק)

🎯 מטרת התשובה:
תשובתך צריכה לעזור להכנת הגנה משפטית יעילה, מבוססת ומקצועית שתשרת את האינטרסים של הלקוח בצורה הטובה ביותר.

תן תשובה מפורטת, מובנית ומקצועית:"""


def manual_document_search(query):
    """חיפוש ידני במסמכים עם פרומפט משפטי מקצועי"""
    try:
        st.info("🔍 מבצע חיפוש משפטי מתקדם במסמכים...")
        
        # נסה לקרוא מסמכים מעובדים
        processed_path = Path("data/processed")
        summaries_path = Path("data/summaries")
        
        documents_text = ""
        sources_found = []
        
        # קרא מסמכים מעובדים
        if processed_path.exists():
            st.info(f"🔍 סורק {len(list(processed_path.glob('*.json')))} מסמכים מעובדים...")
            
            for json_file in processed_path.glob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                    # קבל את סוג המסמך
                    doc_name = json_file.stem.replace('_processed', '')
                    doc_type = get_document_type_from_metadata(doc_name)
                    
                    for i, chunk in enumerate(data.get('chunks', [])):
                        chunk_text = chunk.get('text', '')
                        
                        # חיפוש מתקדם יותר
                        if is_relevant_text(query, chunk_text):
                            documents_text += f"\n\n📄 מתוך {doc_name} ({doc_type}) - חלק {i+1}:\n{chunk_text}\n"
                            sources_found.append({
                                'file': f"{doc_name} ({doc_type})",
                                'content': chunk_text[:500] + "..." if len(chunk_text) > 500 else chunk_text,
                                'similarity': calculate_relevance_score(query, chunk_text),
                                'chunk': i+1
                            })
                            
                except Exception as e:
                    st.warning(f"⚠️ לא הצלחתי לקרוא {json_file.name}: {e}")
        
        # קרא גם סיכומים משפטיים אם יש
        if summaries_path.exists():
            st.info(f"🔍 סורק {len(list(summaries_path.glob('*.json')))} סיכומים משפטיים...")
            
            for summary_file in summaries_path.glob("*.json"):
                try:
                    with open(summary_file, 'r', encoding='utf-8') as f:
                        summary_data = json.load(f)
                        
                    if summary_data.get('status') == 'completed':
                        summary_text = summary_data.get('legal_summary', '')
                        doc_name = summary_data.get('document_name', 'מסמך לא ידוע')
                        doc_type = summary_data.get('document_type', 'לא ידוע')
                        
                        if is_relevant_text(query, summary_text):
                            documents_text += f"\n\n📋 סיכום משפטי של {doc_name} ({doc_type}):\n{summary_text}\n"
                            
                            sources_found.append({
                                'file': f"סיכום משפטי: {doc_name} ({doc_type})",
                                'content': summary_text[:500] + "..." if len(summary_text) > 500 else summary_text,
                                'similarity': calculate_relevance_score(query, summary_text) + 0.1,  # עדיפות לסיכומים
                                'type': 'summary'
                            })
                        
                except Exception as e:
                    st.warning(f"⚠️ לא הצלחתי לקרוא סיכום {summary_file.name}: {e}")
        
        if documents_text:
            # מיין לפי רלוונטיות
            sources_found.sort(key=lambda x: x['similarity'], reverse=True)
            st.success(f"✅ נמצאו {len(sources_found)} מקורות רלוונטיים, ממוינים לפי רלוונטיות")
            
            # יצור פרומפט משפטי מקצועי
            legal_prompt = create_legal_prompt(query, documents_text, len(sources_found))
            
            # קבל תשובה מקלוד עם הפרומפט המשפטי
            if 'chatbot' in st.session_state and hasattr(st.session_state.chatbot, 'claude_client'):
                chatbot = st.session_state.chatbot
                
                try:
                    st.info("🤖 מעבד במערכת AI משפטית מתקדמת...")
                    
                    message = chatbot.claude_client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=4000,
                        temperature=0.2,  # מדויק ומקצועי יותר
                        messages=[{"role": "user", "content": legal_prompt}]
                    )
                    
                    # הוסף context על התהליך
                    answer_with_context = f"""## 🏛️ תשובה משפטית מקצועית

{message.content[0].text}

---
📊 **פרטי החיפוש והניתוח:**
- 🔍 נסרקו מסמכים מכל סוגי התיק
- 📋 נמצאו {len(sources_found)} מקורות רלוונטיים
- ⚖️ ניתוח בוצע ברמה משפטית מקצועית
- 🎯 התמקדות באסטרטגיית הגנה אופטימלית"""
                    
                    return {
                        'answer': answer_with_context,
                        'sources': sources_found,
                        'search_method': '🔍 חיפוש משפטי מתקדם עם AI',
                        'legal_context': True,
                        'sources_count': len(sources_found)
                    }
                    
                except Exception as e:
                    st.error(f"❌ שגיאה במערכת AI: {e}")
                    return {
                        'answer': f"⚠️ נמצאו מסמכים רלוונטיים אך המערכת לא הצליחה לעבד אותם. הנה המידע הגולמי:\n\n{documents_text[:2000]}...",
                        'sources': sources_found
                    }
            else:
                return {
                    'answer': f"📚 נמצאו מסמכים רלוונטיים (ללא עיבוד AI):\n\n{documents_text[:2000]}...",
                    'sources': sources_found
                }
        else:
            return {
                'answer': "❌ לא נמצאו מסמכים רלוונטיים לשאלה המשפטית. וודא שהעלת וערבדת מסמכים שמכילים מידע משפטי רלוונטי, או נסח את השאלה בצורה שונה.",
                'sources': []
            }
            
    except Exception as e:
        return {
            'answer': f"❌ שגיאה במערכת החיפוש המשפטי: {e}",
            'sources': []
        }


def get_document_type_from_metadata(doc_name):
    """קבל סוג מסמך מהמטא-דטה"""
    try:
        metadata_file = Path("data/uploaded_documents") / f"{doc_name}_metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                return metadata.get('document_type', '📄 מסמך')
    except:
        pass
    return "📄 מסמך"


def is_relevant_text(query, text):
    """בדוק אם טקסט רלוונטי לשאלה"""
    query_lower = query.lower()
    text_lower = text.lower()
    
    # מילות מפתח משפטיות כלליות
    legal_keywords = [
        'תביעה', 'טענה', 'סעד', 'הגנה', 'ראיה', 'עד', 'חוק', 'משפט', 'בית משפט',
        'חוזה', 'נזק', 'פיצוי', 'אחריות', 'הפרה', 'התחייבות', 'זכות', 'חובה',
        'תקנה', 'פסיקה', 'החלטה', 'כתב', 'תצהיר', 'חקירה', 'תמלול', 'עדות'
    ]
    
    # חפש מילות מפתח מהשאלה או מילות מפתח משפטיות
    query_words = [word for word in query_lower.split() if len(word) > 2]
    
    # בדוק אם יש התאמה עם מילות השאלה או מילות מפתח משפטיות
    return (
        any(word in text_lower for word in query_words if len(word) > 3) or
        any(keyword in text_lower for keyword in legal_keywords) or
        len(text) > 100  # טקסטים ארוכים בדרך כלל יותר רלוונטיים
    )


def calculate_relevance_score(query, text):
    """חשב ציון רלוונטיות"""
    query_lower = query.lower()
    text_lower = text.lower()
    
    score = 0.1  # בסיס
    
    # מילות השאלה
    query_words = [word for word in query_lower.split() if len(word) > 2]
    for word in query_words:
        if word in text_lower:
            score += 0.2
    
    # מילות מפתח משפטיות חשובות
    important_legal_terms = [
        'תביעה', 'טענה', 'הגנה', 'ראיה', 'עד', 'חוק', 'פסיקה', 'החלטה'
    ]
    
    for term in important_legal_terms:
        if term in text_lower:
            score += 0.15
    
    return min(score, 1.0)  # מקסימום 1.0


def safe_search_and_respond(chatbot, question, **kwargs):
    """חיפוש בטוח שתומך בגרסאות שונות של הצ'אטבוט"""
    try:
        # בדוק קודם אם יש מסמכים
        has_docs = check_if_has_documents(chatbot)
        
        if not has_docs:
            st.warning("⚠️ לא נמצאו מסמכים מעובדים. תשובה תהיה כללית.")
        else:
            st.info("✅ מחפש במסמכים המעובדים...")
        
        # נסה את הפונקציה המתקדמת
        if hasattr(chatbot, 'search_and_respond'):
            st.info("🔍 משתמש בחיפוש המתקדם של המערכת...")
            return chatbot.search_and_respond(question, **kwargs)
        
        # נסה פונקציה פשוטה יותר
        elif hasattr(chatbot, 'get_response'):
            st.info("🔍 משתמש בתשובה פשוטה...")
            response_text = chatbot.get_response(question)
            return {
                'answer': response_text,
                'sources': []
            }
        
        # נסה פונקציה בסיסית
        elif hasattr(chatbot, 'respond'):
            st.info("🔍 משתמש בתשובה בסיסית...")
            response_text = chatbot.respond(question)
            return {
                'answer': response_text,
                'sources': []
            }
        
        # אם אין מסמכים או שום פונקציה לא עובדת - נסה חיפוש ידני
        elif has_docs:
            st.info("🔍 מתחיל חיפוש ידני מתקדם במסמכים...")
            return manual_document_search(question)
        
        else:
            # אם אין מסמכים, שלח לקלוד ישירות עם פרומפט משפטי כללי
            st.warning("⚠️ אין מסמכים מעובדים - מתן תשובה משפטية כללית")
            
            general_legal_prompt = f"""אתה עורך דין מומחה במשפט אזרחי ופלילי.

הקשר: אני עובד עם מערכת הגנה משפטית וכרגע אין לי גישה למסמכים הספציפיים של התיק.

השאלה שלי: {question}

אנא תן תשובה משפטית מקצועית שכוללת:
1. הסבר כללי על הנושא המשפטי
2. איך לזהות ולנתח את המידע הרלוונטי במסמכים
3. נקודות מפתח שצריך לחפש בתיק
4. שיקולים אסטרטגיים להגנה משפטית
5. המלצות למשך הטיפול בנושא
6. סוגי מסמכים שכדאי לאסוף

השתמש בידע המשפטי המקצועי שלך ותן עצות מעשיות להכנת הגנה."""
            
            # נסה שמות מודלים שונים
            if hasattr(chatbot, 'claude_client') and chatbot.claude_client:
                model_names = [
                    "claude-3-5-sonnet-20241022",
                    "claude-3-5-sonnet-20240620",
                    "claude-3-sonnet-20240229",
                    "claude-3-haiku-20240307"
                ]
                
                for model_name in model_names:
                    try:
                        st.info(f"🔄 מנסה מודל: {model_name}")
                        
                        message = chatbot.claude_client.messages.create(
                            model=model_name,
                            max_tokens=3000,
                            temperature=0.3,
                            messages=[{"role": "user", "content": general_legal_prompt}]
                        )
                        
                        st.success(f"✅ הצלחה עם מודל: {model_name}")
                        
                        return {
                            'answer': f"## 🏛️ תשובה משפטית כללית\n\n{message.content[0].text}\n\n---\n📝 **הערה:** תשובה זו ניתנה ללא גישה למסמכים ספציפיים. להכנת הגנה מדויקת יותר, יש צורך לנתח את המסמכים הספציפיים של התיק.",
                            'sources': [],
                            'model_used': model_name,
                            'note': 'תשובה כללית ללא מסמכים ספציפיים'
                        }
                        
                    except Exception as model_error:
                        st.warning(f"❌ מודל {model_name} נכשל: {model_error}")
                        continue
                
                # אם כל המודלים נכשלו
                return {
                    'answer': "❌ לא הצלחתי להתחבר לאף מודל Claude. בדוק את ה-API key והחיבור לאינטרנט.",
                    'sources': []
                }
            else:
                return {
                    'answer': "❌ לא הצלחתי להתחבר לשירות AI. בדוק את הגדרות ה-API.",
                    'sources': []
                }
                
    except Exception as e:
        st.error(f"שגיאה כללית בחיפוש: {e}")
        return {
            'answer': f"❌ שגיאה טכנית: {e}",
            'sources': []
        }


def show_main_interface(chatbot):
    """הצג את הממשק הראשי"""
    st.title("🏛️ מערכת הגנה משפטית חכמה")
    st.markdown("### ⚖️ בוט AI מתקדם למתן תשובות משפטיות מבוססות מסמכים")
    
    # הצג מצב המערכת
    show_system_status_summary(chatbot)
    
    st.markdown("---")
    
    # ממשק השיחה
    st.subheader("💬 שאל שאלות משפטיות על המסמכים")
    
    # בדוק אם יש מסמכים טעונים - בדרך בטוחה
    has_docs = check_if_has_documents(chatbot)
    
    if has_docs:
        doc_count = count_files_in_directory("data/processed", "*.json")
        summary_count = count_files_in_directory("data/summaries", "*.json")
        st.success(f"✅ המערכת מוכנה לשאלות - {doc_count} מסמכים מעובדים, {summary_count} סיכומים משפטיים")
    else:
        st.warning("⚠️ לא נמצאו מסמכים מעובדים. העלה וערבד מסמכים תחילה בסרגל הצדדי.")
        
    if has_docs or st.checkbox("🔄 אפשר שאלות משפטיות כלליות", help="שאלות כלליות ללא חיפוש במסמכים ספציפיים"):
        
        # דוגמאות שאלות
        st.markdown("""
        **💡 דוגמאות לשאלות משפטיות:**
        - מהן הטענות העיקריות בכתב התביעה?
        - סכם את הראיות שהוצגו בתמלול החקירה
        - מה נקודות החוזק והחולשה של ההגנה?
        - אילו סתירות יש בעדויות?
        - מה האסטרטגיה המומלצת להגנה?
        """)
        
        # שדה השאלה
        user_question = st.text_area(
            "🔍 שאל את השאלה המשפטית שלך:",
            height=120,
            placeholder="לדוגמה: מהן הטענות העיקריות בכתב התביעה ומה נקודות החולשה שבהן?",
            help="שאל שאלות ספציפיות ומפורטות על המסמכים המשפטיים שלך"
        )
        
        # אפשרויות מתקדמות
        with st.expander("⚙️ הגדרות חיפוש משפטי מתקדמות"):
            col1, col2 = st.columns(2)
            
            with col1:
                search_method = st.selectbox(
                    "שיטת חיפוש:",
                    ["hybrid", "semantic", "keyword"],
                    index=0,
                    help="Hybrid = שילוב של סמנטי וחיפוש מילות מפתח משפטיות"
                )
                
                max_results = st.slider(
                    "מספר תוצאות מקסימלי:",
                    5, 25, 15,
                    help="כמה קטעי טקסט להביא מהמסמכים המשפטיים"
                )
            
            with col2:
                min_similarity = st.slider(
                    "דרגת דמיון מינימלית:",
                    0.1, 0.9, 0.25,
                    help="0.1 = חיפוש רחב יותר, 0.9 = מדויק ומצומצם יותר"
                )
                
                use_summaries = st.checkbox(
                    "כלול סיכומים משפטיים בחיפוש",
                    value=True,
                    help="חפש גם בסיכומים המשפטיים המתקדמים"
                )
        
        # כפתור שליחת שאלה
        if st.button("🏛️ חפש תשובה משפטית", key="search_answer", type="primary"):
            if user_question.strip():
                with st.spinner("🔍 מחפש תשובה במסמכים המשפטיים..."):
                    try:
                        # חיפוש עם הפרמטרים שנבחרו - בדרך בטוחה
                        response = safe_search_and_respond(
                            chatbot,
                            user_question,
                            method=search_method,
                            max_results=max_results,
                            min_similarity=min_similarity,
                            include_summaries=use_summaries
                        )
                        
                        # הצג את התשובה
                        if response:
                            st.markdown("### 📝 תשובה משפטית:")
                            st.markdown(response['answer'])
                            
                            # הצג את המודל שנעשה בו שימוש
                            if 'model_used' in response:
                                st.caption(f"🤖 מודל AI: {response['model_used']}")
                            
                            # הצג שיטת חיפוש
                            if 'search_method' in response:
                                st.caption(f"🔍 שיטת חיפוש: {response['search_method']}")
                            
                            # הצג הערה אם יש
                            if 'note' in response:
                                st.info(f"📝 הערה: {response['note']}")
                            
                            # הצג מקורות אם יש
                            if response.get('sources'):
                                with st.expander(f"📚 מקורות משפטיים ({len(response['sources'])} נמצאו)"):
                                    for i, source in enumerate(response['sources'], 1):
                                        col1, col2 = st.columns([3, 1])
                                        with col1:
                                            st.markdown(f"**מקור {i}:** {source.get('file', 'לא ידוע')}")
                                        with col2:
                                            st.metric("דמיון", f"{source.get('similarity', 0):.2f}")
                                        
                                        content = source.get('content', '')
                                        with st.container():
                                            st.text(content[:600] + "..." if len(content) > 600 else content)
                                        st.markdown("---")
                            
                            # שמור בהיסטוריה
                            if 'question_history' not in st.session_state:
                                st.session_state.question_history = []
                            
                            st.session_state.question_history.append((user_question, response['answer'][:200]))
                            
                        else:
                            st.error("❌ לא הצלחתי לקבל תשובה. נסה שאלה אחרת או בדוק את החיבור.")
                            
                    except Exception as e:
                        st.error(f"❌ שגיאה בחיפוש משפטי: {e}")
            else:
                st.warning("⚠️ אנא כתוב שאלה משפטית")
    
    # הצג היסטוריית שאלות אם יש
    if hasattr(st.session_state, 'question_history') and st.session_state.question_history:
        with st.expander(f"📋 היסטוריית שאלות משפטיות ({len(st.session_state.question_history)} שאלות)"):
            for i, (question, answer) in enumerate(reversed(st.session_state.question_history[-5:]), 1):
                st.markdown(f"**{i}. {question}**")
                st.text(answer[:300] + "..." if len(answer) > 300 else answer)
                st.markdown("---")


def count_files_in_directory(directory_path, pattern="*"):
    """ספור קבצים בתיקייה"""
    try:
        path = Path(directory_path)
        if path.exists():
            return len(list(path.glob(pattern)))
        return 0
    except:
        return 0


def calculate_total_data_size():
    """חשב גודל כולל של הנתונים"""
    try:
        total_size = 0
        data_path = Path("data")
        
        if data_path.exists():
            for file_path in data_path.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        
        return total_size / (1024 * 1024)  # המרה ל-MB
    except:
        return 0.0


def show_file_statistics():
    """הצג סטטיסטיקות קבצים"""
    try:
        st.write("### 📊 סטטיסטיקות מסמכים משפטיים:")
        
        # ספירת קבצים בתיקיות שונות
        stats = {
            "📁 קבצי PDF": count_files_in_directory("data/uploaded_documents", "*.pdf"),
            "⚙️ מעובדים": count_files_in_directory("data/processed", "*.json"),
            "📋 סיכומים": count_files_in_directory("data/summaries", "*.json"),
            "🏷️ מטא-דטה": count_files_in_directory("data/metadata", "*.json")
        }
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📁 PDF", stats["📁 קבצי PDF"])
        with col2:
            st.metric("⚙️ מעובדים", stats["⚙️ מעובדים"])
        with col3:
            st.metric("📋 סיכומים", stats["📋 סיכומים"])
        with col4:
            st.metric("🏷️ מטא-דטה", stats["🏷️ מטא-דטה"])
        
        # גודל כולל
        total_size = calculate_total_data_size()
        st.write(f"💾 **גודל כולל:** {total_size:.1f} MB")
        
        # אחוזי השלמה
        if stats["📁 קבצי PDF"] > 0:
            processing_percentage = (stats["⚙️ מעובדים"] / stats["📁 קבצי PDF"]) * 100
            summary_percentage = (stats["📋 סיכומים"] / stats["📁 קבצי PDF"]) * 100 if stats["📁 קבצי PDF"] > 0 else 0
            
            st.write(f"📊 **עיבוד:** {processing_percentage:.0f}% מהקבצים מעובדים")
            st.write(f"📋 **סיכומים:** {summary_percentage:.0f}% מהקבצים מסוכמים")
        
    except Exception as e:
        st.write(f"⚠️ לא הצלחתי להציג סטטיסטיקות: {e}")


def verify_claude_connection():
    """בדוק חיבור ל-Claude"""
    if 'chatbot' in st.session_state:
        chatbot = st.session_state.chatbot
        
        if hasattr(chatbot, 'claude_client') and chatbot.claude_client:
            try:
                # בדיקה מהירה עם המודל החדש
                response = chatbot.claude_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=50,
                    messages=[{"role": "user", "content": "בדיקת חיבור"}]
                )
                return True, "✅ החיבור ל-Claude תקין"
            except Exception as e:
                # נסה מודל אחר
                try:
                    response = chatbot.claude_client.messages.create(
                        model="claude-3-5-sonnet-20240620",
                        max_tokens=50,
                        messages=[{"role": "user", "content": "בדיקת חיבור"}]
                    )
                    return True, "✅ החיבור ל-Claude תקין (מודל חלופי)"
                except Exception as e2:
                    return False, f"❌ שגיאה בחיבור: {e2}"
        else:
            return False, "❌ Claude client לא אותחל"
    else:
        return False, "❌ הצ'אטבוט לא אותחל"


def show_development_tools():
    """כלי פיתוח מהירים"""
    st.sidebar.divider()
    
    with st.sidebar.expander("⚡ כלי פיתוח", expanded=False):
        st.write("**כלים למפתחים:**")
        
        # מחיקה מהירה
        st.subheader("🗑️ מחיקה מהירה")
        st.caption("לפיתוח בלבד - ללא הגנות")
        
        if st.button("🚮 מחק הכל", key="dev_quick_reset", help="מחיקה מהירה של כל הנתונים"):
            try:
                # מחק את כל תיקיית data לגמרי
                data_path = Path("data")
                
                if data_path.exists():
                    shutil.rmtree(data_path)
                    st.success("🗑️ כל תיקיית data נמחקה")
                
                # צור תיקיות ריקות מחדש
                essential_dirs = [
                    "data",
                    "data/uploaded_documents", 
                    "data/processed",
                    "data/summaries"
                ]
                
                for dir_path in essential_dirs:
                    Path(dir_path).mkdir(parents=True, exist_ok=True)
                    
                # נקה session state לגמרי
                st.session_state.clear()
                
                # נקה Streamlit cache
                st.cache_data.clear()
                st.cache_resource.clear()
                
                st.success("🗑️ מחיקה מהירה בוצעה - רענן את הדף!")
                
            except Exception as e:
                st.error(f"❌ שגיאה: {e}")
        
        # כלים נוספים
        st.divider()
        
        # בדיקת מצב המערכת - בטוח
        if st.button("🔍 בדיקת מערכת", key="system_check"):
            chatbot = st.session_state.get('chatbot')
            if chatbot:
                st.write("**מצב המערכת:**")
                st.write(f"✅ Claude API: {'מחובר' if hasattr(chatbot, 'claude_client') and chatbot.claude_client else 'לא מחובר'}")
                
                # בדיקת מסמכים בטוחה
                has_docs = check_if_has_documents(chatbot)
                st.write(f"📊 מסמכים טעונים: {'כן' if has_docs else 'לא'}")
                st.write(f"💾 Session keys: {len(st.session_state.keys())}")
                
                # בדוק תיקיות
                for name, path in [
                    ("Uploaded", "data/uploaded_documents"),
                    ("Processed", "data/processed"),
                    ("Summaries", "data/summaries")
                ]:
                    file_count = count_files_in_directory(path)
                    st.write(f"📁 {name}: {file_count} קבצים")
            else:
                st.write("❌ הבוט לא אותחל")
        
        # בדיקת חיבור Claude
        if st.button("🔗 בדוק חיבור Claude", key="test_claude"):
            success, message = verify_claude_connection()
            if success:
                st.success(message)
            else:
                st.error(message)
                st.info("💡 בדוק את ה-API key ב-.env או בהגדרות")
        
        # רענון מלא
        if st.button("🔄 רענון מלא", key="full_refresh"):
            # נקה הכל ורענן
            st.session_state.clear()
            st.rerun()


def show_protected_system_reset():
    """איפוס מלא מוגן של המערכת"""
    st.sidebar.divider()
    
    with st.sidebar.expander("🚨 איפוס מלא מוגן", expanded=False):
        st.warning("⚠️ איפוס מלא של כל הנתונים")
        
        # הצג סטטיסטיקות נוכחיות
        st.subheader("📊 מצב נוכחי:")
        
        # ספירת קבצים
        stats = {}
        paths = {
            "PDF files": Path("data/uploaded_documents"),
            "Processed": Path("data/processed"),
            "Summaries": Path("data/summaries")
        }
        
        total_files = 0
        for name, path in paths.items():
            if path.exists():
                count = len(list(path.glob("*.*")))
                stats[name] = count
                total_files += count
                st.write(f"• {name}: **{count}** קבצים")
            else:
                stats[name] = 0
                st.write(f"• {name}: **0** קבצים")
        
        if total_files == 0:
            st.info("📭 אין נתונים למחיקה")
            return
        
        st.write(f"**סה\"כ: {total_files} קבצים**")
        
        # אישורים כפולים
        st.subheader("✋ אישורים:")
        
        confirm1 = st.checkbox(
            f"☑️ אני מבין ש-{total_files} קבצים יימחקו",
            key="protected_confirm_1"
        )
        
        if confirm1:
            confirm_text = st.text_input(
                "✍️ כתוב 'מחק הכל' לאישור סופי:",
                key="protected_confirm_text",
                help="צריך לכתוב בדיוק: מחק הכל"
            )
            
            if confirm_text == "מחק הכל":
                if st.button(
                    "🗑️ מחק את כל הנתונים", 
                    key="protected_final_reset", 
                    type="primary"
                ):
                    return execute_protected_reset(stats)
    
    return False


def execute_protected_reset(stats):
    """בצע איפוס מוגן של המערכת"""
    try:
        with st.spinner("🔄 מבצע איפוס מלא..."):
            
            # מחק תיקיות
            directories_to_clean = [
                ("📁 קבצי PDF", Path("data/uploaded_documents")),
                ("⚙️ מסמכים מעובדים", Path("data/processed")),
                ("📋 סיכומים משפטיים", Path("data/summaries")),
                ("📊 מטא-דטה", Path("data/metadata")),
            ]
            
            deleted_total = 0
            
            for desc, directory in directories_to_clean:
                if directory.exists():
                    try:
                        shutil.rmtree(directory)
                        st.success(f"✅ {desc}: תיקייה נמחקה")
                        deleted_total += 1
                        directory.mkdir(parents=True, exist_ok=True)
                    except Exception as e:
                        st.error(f"❌ שגיאה במחיקת {desc}: {e}")
                else:
                    st.info(f"⏭️ {desc}: תיקייה לא קיימת")
            
            # נקה session state
            keys_to_preserve = ['chatbot']
            keys_to_delete = [k for k in st.session_state.keys() if k not in keys_to_preserve]
            for key in keys_to_delete:
                del st.session_state[key]
            
            # נקה cache
            try:
                st.cache_data.clear()
                st.cache_resource.clear()
            except:
                pass
            
            st.success(f"🎉 איפוס הושלם! {deleted_total} תיקיות נמחקו")
            
            if st.button("🔄 רענן את הדף", key="refresh_after_reset"):
                st.rerun()
                
            return True
            
    except Exception as e:
        st.error(f"❌ שגיאה באיפוס: {e}")
        return False


def main():
    """פונקציה ראשית"""
    # הגדרות עמוד
    st.set_page_config(
        page_title="מערכת הגנה משפטית חכמה",
        page_icon="🏛️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # CSS מותאם
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        color: #1f4e79;
    }
    
    .status-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    
    .success-box {
        background-color: #d4edda;
        border-left: 5px solid #28a745;
    }
    
    .warning-box {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
    }
    
    .error-box {
        background-color: #f8d7da;
        border-left: 5px solid #dc3545;
    }
    </style>
    """, unsafe_allow_html=True)
    
    try:
        # אתחל צ'אטבוט
        chatbot = initialize_chatbot()
        
        # סרגל צדדי
        show_sidebar(chatbot)
        
        # כלי פיתוח
        show_development_tools()
        
        # איפוס מוגן
        show_protected_system_reset()
        
        # ממשק ראשי
        show_main_interface(chatbot)
        
        # מידע נוסף בתחתית
        st.markdown("---")
        st.markdown("""
        ### 💡 עצות שימוש משפטי:
        - **העלה מסמכים משפטיים** דרך הסרגל הצדדי
        - **תייג כל מסמך** לפי סוגו המשפטי לניתוח מיטבי  
        - **עבד את המסמכים** לפני שאילת שאלות
        - **צור סיכומים משפטיים** לניתוח מעמיק ואסטרטגי
        - **השתמש בשאלות ספציפיות ומפורטות** לתשובות משפטיות מדויקות
        - **נתח נקודות חוזק וחולשה** בראיות ובטענות
        """)
        
        # פרטים טכניים בתחתית
        with st.expander("🔍 מידע טכני"):
            st.write("**גרסת המערכת:** 2.1 - עם פרומפט משפטי מתקדם")
            st.write("**מנוע AI:** Claude-3.5-Sonnet (מיטבי למשפט)")
            st.write("**חיפוש:** Semantic + Keyword Hybrid עם מילות מפתח משפטיות")
            st.write("**סוגי מסמכים נתמכים:** PDF (כל סוגי המסמכים המשפטיים)")
            st.write("**אחסון:** מקומי מוצפן")
            
            # בדיקת מצב המערכת
            if 'chatbot' in st.session_state:
                chatbot = st.session_state.chatbot
                
                # בדיקת Claude
                claude_status = "🔴 לא מחובר"
                if hasattr(chatbot, 'claude_client') and chatbot.claude_client:
                    claude_status = "🟢 מחובר"
                st.write(f"**מצב Claude:** {claude_status}")
                
                # בדיקת מסמכים
                docs_status = "🔴 לא"
                if check_if_has_documents(chatbot):
                    docs_status = "🟢 כן"
                st.write(f"**מסמכים טעונים:** {docs_status}")
                
                # סטטיסטיקות
                show_file_statistics()
            else:
                st.write("**מצב Claude:** 🔴 הבוט לא אותחל")
    
    except Exception as e:
        st.error(f"❌ שגיאה כללית: {e}")
        st.write("**פרטי השגיאה:**")
        import traceback
        st.code(traceback.format_exc())
        
        # אפשרות לאיפוס במקרה של שגיאה חמורה
        st.subheader("🚨 אפשרות חירום")
        if st.button("🔄 איפוס חירום", key="emergency_reset"):
            st.session_state.clear()
            st.rerun()


if __name__ == "__main__":
    main()
