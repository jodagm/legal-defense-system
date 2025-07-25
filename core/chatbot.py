"""
צ'אטבוט משפטי מתקדם למערכת הגנה משפטית
גרסה מתוקנת עם חיפוש חכם, טיפול שגיאות וכל הפונקציות הנדרשות
"""
from dotenv import load_dotenv
import anthropic
import os
from pathlib import Path
import streamlit as st
from typing import Dict, List, Optional, Tuple
import json
import re
import time
from datetime import datetime

# ייבואים אופציונליים עם fallback
try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    print("⚠️ sklearn not available - using simple text search")
    SKLEARN_AVAILABLE = False

# ייבוא ההגדרות
try:
    from config.settings import (
        CLAUDE_MODEL, CLAUDE_FALLBACK_MODELS, 
        LEGAL_KEYWORDS, LEGAL_CONTEXT_HEADER,
        MIN_SIMILARITY_THRESHOLD, MAX_SEARCH_RESULTS,
        TEMPERATURE_PRECISE, TEMPERATURE_NORMAL,
        PROCESSED_DIR, SUMMARIES_DIR, METADATA_DIR
    )
except ImportError:
    # fallback להגדרות בסיסיות
    CLAUDE_MODEL = "claude-3-haiku-20240307"
    CLAUDE_FALLBACK_MODELS = ["claude-3-haiku-20240307"]
    LEGAL_KEYWORDS = ['תביעה', 'טענה', 'הגנה', 'ראיה', 'עד', 'חוק', 'משפט']
    MIN_SIMILARITY_THRESHOLD = 0.1
    MAX_SEARCH_RESULTS = 15
    TEMPERATURE_PRECISE = 0.2
    TEMPERATURE_NORMAL = 0.3
    PROCESSED_DIR = Path("data/processed")
    SUMMARIES_DIR = Path("data/summaries")
    METADATA_DIR = Path("data/metadata")


class LegalChatBot:
    """צ'אטבוט משפטי מתקדם עם יכולות חיפוש וניתוח משופרות"""
    
    def __init__(self):
        """אתחל את הצ'אטבוט המשפטי"""
        self.claude_client = None
        self.document_chunks = []
        self.vectorizer = None
        self.tfidf_matrix = None
        self.legal_summaries = []
        self.document_metadata = {}
        self.last_search_results = []
        self.search_history = []
        
        # אתחל חיבור ל-Claude
        self._initialize_claude()
        
        # טען מסמכים אם יש
        self._load_documents()
        
        # טען metadata
        self._load_metadata()
    
    def _initialize_claude(self):
        """אתחל חיבור ל-Claude API עם fallback models"""
        try:
            # טען .env בתחילה
            load_dotenv()
            
            api_key = None
            
            print("🔍 Looking for Claude API key...")
            
            # 1. בדוק Streamlit session state
            if hasattr(st, 'session_state') and hasattr(st.session_state, 'claude_api_key'):
                api_key = st.session_state.claude_api_key
                print("📍 Found API key in session state")
            
            # 2. בדוק Streamlit secrets
            elif hasattr(st, 'secrets'):
                for key_name in ['CLAUDE_API_KEY', 'ANTHROPIC_API_KEY']:
                    if key_name in st.secrets:
                        api_key = st.secrets[key_name]
                        print(f"📍 Found API key in Streamlit secrets: {key_name}")
                        break
            
            # 3. בדוק משתני סביבה (אחרי load_dotenv)
            if not api_key:
                for key_name in ['CLAUDE_API_KEY', 'ANTHROPIC_API_KEY']:
                    if key_name in os.environ:
                        api_key = os.environ[key_name]
                        print(f"📍 Found API key in environment: {key_name}")
                        break
            
            # 4. בדוק קריאה ידנית מ-.env
            if not api_key and Path('.env').exists():
                print("📍 Reading .env file manually...")
                with open('.env', 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('CLAUDE_API_KEY=') or line.startswith('ANTHROPIC_API_KEY='):
                            api_key = line.split('=', 1)[1].strip().strip('"\'')
                            print(f"📍 Found API key in .env file")
                            break
            
            # בדיקת runtime validation
            if api_key:
                api_key = api_key.strip()
                print(f"🔍 API key found - Length: {len(api_key)}")
                print(f"🔍 API key starts with: {api_key[:15]}...")
                
                if api_key.startswith('sk-ant-'):
                    self.claude_client = anthropic.Anthropic(api_key=api_key)
                    
                    # בדוק חיבור
                    if self._test_claude_connection():
                        print("✅ Claude API initialized successfully")
                    else:
                        print("❌ Claude API key invalid or connection failed")
                        self.claude_client = None
                else:
                    print("❌ API key format invalid - should start with 'sk-ant-'")
                    self.claude_client = None
            else:
                print("❌ Claude API key not found in any location")
                self.claude_client = None
                
        except Exception as e:
            print(f"❌ Error initializing Claude: {e}")
            import traceback
            print(f"Full error: {traceback.format_exc()}")
            self.claude_client = None

            """אתחל חיבור ל-Claude API עם fallback models"""
            try:
                load_dotenv()
                # נסה לקבל API key מכמה מקומות
                api_key = None
                
                # מההגדרות
                if hasattr(st, 'session_state') and hasattr(st.session_state, 'claude_api_key'):
                    api_key = st.session_state.claude_api_key
                
                # מ-Streamlit secrets
                elif hasattr(st, 'secrets') and 'CLAUDE_API_KEY' in st.secrets:
                    api_key = st.secrets['CLAUDE_API_KEY']
                
                # ממשתני סביבה
                elif 'CLAUDE_API_KEY' in os.environ:
                    api_key = os.environ['CLAUDE_API_KEY']
                
                # מקובץ .env
                elif Path('.env').exists():
                    with open('.env', 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.startswith('CLAUDE_API_KEY='):
                                api_key = line.split('=', 1)[1].strip().strip('"\'')
                                break
                
                if api_key and api_key.strip():
                    self.claude_client = anthropic.Anthropic(api_key=api_key.strip())
                    
                    # בדוק חיבור עם מודל זמין
                    self._test_claude_connection()
                    print("✅ Claude API initialized successfully")
                else:
                    print("❌ Claude API key not found")
                    
            except Exception as e:
                print(f"❌ Error initializing Claude: {e}")
                self.claude_client = None
    
    def _test_claude_connection(self):
        """בדוק חיבור ל-Claude עם המודלים הזמינים"""
        if not self.claude_client:
            return False
        
        for model in CLAUDE_FALLBACK_MODELS:
            try:
                response = self.claude_client.messages.create(
                    model=model,
                    max_tokens=50,
                    messages=[{"role": "user", "content": "בדיקת חיבור"}]
                )
                print(f"✅ Claude model {model} is working")
                return True
            except Exception as e:
                print(f"⚠️ Model {model} failed: {e}")
                continue
        
        print("❌ No working Claude models found")
        return False
    
    def _load_documents(self):
        """טען מסמכים מעובדים עם שיפורים"""
        try:
            self.document_chunks = []
            self.legal_summaries = []
            
            # טען מסמכים מעובדים
            if PROCESSED_DIR.exists():
                for json_file in PROCESSED_DIR.glob("*.json"):
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        doc_name = json_file.stem.replace('_processed', '')
                        doc_type = data.get('document_type', 'מסמך')
                        
                        for i, chunk in enumerate(data.get('chunks', [])):
                            self.document_chunks.append({
                                'text': chunk.get('text', ''),
                                'document': doc_name,
                                'document_type': doc_type,
                                'chunk_id': chunk.get('id', i),
                                'type': 'document',
                                'page': chunk.get('page', 0),
                                'timestamp': data.get('processed_at', '')
                            })
                    except Exception as e:
                        print(f"Error loading {json_file}: {e}")
            
            # טען סיכומים משפטיים
            if SUMMARIES_DIR.exists():
                for summary_file in SUMMARIES_DIR.glob("*.json"):
                    try:
                        with open(summary_file, 'r', encoding='utf-8') as f:
                            summary_data = json.load(f)
                        
                        if summary_data.get('status') == 'completed':
                            summary_text = summary_data.get('legal_summary', '')
                            doc_name = summary_data.get('document_name', '')
                            doc_type = summary_data.get('document_type', '')
                            
                            # הוסף לסיכומים נפרדים
                            self.legal_summaries.append({
                                'text': summary_text,
                                'document': doc_name,
                                'document_type': doc_type,
                                'type': 'summary',
                                'created_at': summary_data.get('created_at', ''),
                                'key_points': summary_data.get('key_points', []),
                                'contradictions': summary_data.get('contradictions', []),
                                'recommendations': summary_data.get('recommendations', [])
                            })
                            
                            # הוסף גם לחיפוש הרגיל עם משקל גבוה יותר
                            self.document_chunks.append({
                                'text': summary_text,
                                'document': f"סיכום: {doc_name}",
                                'document_type': doc_type,
                                'chunk_id': 'summary',
                                'type': 'summary',
                                'priority_weight': 2.0  # משקל גבוה יותר לסיכומים
                            })
                    except Exception as e:
                        print(f"Error loading summary {summary_file}: {e}")
            
            # אתחל vectorizer אם יש מסמכים
            if self.document_chunks:
                self._initialize_vectorizer()
                print(f"✅ Loaded {len(self.document_chunks)} document chunks ({len(self.legal_summaries)} summaries)")
            else:
                print("📭 No documents loaded")
                
        except Exception as e:
            print(f"❌ Error loading documents: {e}")
    
    def _load_metadata(self):
        """טען metadata של מסמכים"""
        try:
            if METADATA_DIR.exists():
                for metadata_file in METADATA_DIR.glob("*.json"):
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                            doc_name = metadata_file.stem.replace('_metadata', '')
                            self.document_metadata[doc_name] = metadata
                    except Exception as e:
                        print(f"Error loading metadata {metadata_file}: {e}")
        except Exception as e:
            print(f"Error loading metadata: {e}")
    
    def _initialize_vectorizer(self):
        """אתחל vectorizer לחיפוש סמנטי (אם sklearn זמין)"""
        if not SKLEARN_AVAILABLE:
            print("⚠️ Using simple text search (sklearn not available)")
            return
        
        try:
            texts = [chunk['text'] for chunk in self.document_chunks if chunk['text']]
            
            if texts:
                # מילות עצירה מורחבות בעברית
                hebrew_stop_words = [
                    'של', 'את', 'על', 'כל', 'יש', 'אין', 'היא', 'הוא', 'הם', 'הן',
                    'זה', 'זו', 'זהו', 'להיות', 'לא', 'כן', 'גם', 'או', 'אך', 'אבל',
                    'עם', 'אל', 'מן', 'כי', 'אם', 'בין', 'לפי', 'דרך', 'תוך', 'אצל',
                    'לגבי', 'בעד', 'ללא', 'בלי', 'חוץ', 'פרט', 'אלא', 'רק', 'ביד',
                    'ביס', 'יכול', 'צריך', 'אפשר', 'נבון', 'נכון'
                ]
                
                self.vectorizer = TfidfVectorizer(
                    max_features=8000,  # יותר features
                    stop_words=hebrew_stop_words,
                    ngram_range=(1, 3),
                    min_df=1,
                    max_df=0.95,
                    analyzer='word',
                    token_pattern=r'\b[^\d\W]+\b'  # רק מילים (לא מספרים)
                )
                
                self.tfidf_matrix = self.vectorizer.fit_transform(texts)
                print("✅ TF-IDF Vectorizer initialized")
                
        except Exception as e:
            print(f"❌ Error initializing vectorizer: {e}")
            self.vectorizer = None
            self.tfidf_matrix = None
    
    def has_documents(self):
        """בדוק אם יש מסמכים טעונים"""
        return len(self.document_chunks) > 0
    
    def smart_text_search(self, query: str, max_results: int = 15) -> List[Dict]:
        """חיפוש טקסט חכם עם ניקוד משפטי"""
        if not self.document_chunks:
            return []
        
        try:
            query_lower = query.lower()
            results = []
            
            # מילות מפתח משפטיות מורחבות
            legal_keywords = LEGAL_KEYWORDS + [
                'חשוד', 'נאשם', 'קורבן', 'מתלונן', 'מאשים', 'ממונה', 'פרקליט',
                'תובע', 'נתבע', 'מועמד', 'מבקש', 'משיב', 'מערער', 'מעורר',
                'כתב', 'מסמך', 'תעודה', 'אישור', 'אישורים', 'העתק', 'העתקים',
                'חקירה', 'בירור', 'בדיקה', 'בחינה', 'דיון', 'דיונים', 'ישיבה'
            ]
            
            for chunk in self.document_chunks:
                text_lower = chunk['text'].lower()
                score = 0
                
                # חיפוש מילות השאלה (משקל בסיס)
                query_words = [word for word in query_lower.split() if len(word) > 2]
                word_matches = 0
                for word in query_words:
                    if word in text_lower:
                        word_matches += 1
                        score += 3
                
                # בונוס לביטויים מדויקים
                if len(query_words) > 1 and query_lower in text_lower:
                    score += 10
                
                # משקל מיוחד למילות מפתח משפטיות
                legal_matches = 0
                for keyword in legal_keywords:
                    if keyword.lower() in text_lower:
                        legal_matches += 1
                        score += 2
                
                # בונוס לסוג מסמך רלוונטי
                doc_type = chunk.get('document_type', '').lower()
                if any(word in doc_type for word in query_words):
                    score += 5
                
                # בונוס לסיכומים (עדיפות גבוהה)
                if chunk.get('type') == 'summary':
                    score *= 1.5
                
                # בונוס למסמכים עם priority_weight
                priority_weight = chunk.get('priority_weight', 1.0)
                score *= priority_weight
                
                # חשב רלוונטיות יחסית
                relevance = 0
                if word_matches > 0:
                    relevance = (word_matches / len(query_words)) * 0.7 + (legal_matches / max(len(legal_keywords), 10)) * 0.3
                
                # אם יש ציון מינימלי, הוסף לתוצאות
                if score > 0 and relevance > 0:
                    results.append({
                        'content': chunk['text'],
                        'document': chunk['document'],
                        'document_type': chunk.get('document_type', ''),
                        'similarity': min(score / 20, 1.0),
                        'relevance': relevance,
                        'type': chunk.get('type', 'document'),
                        'chunk_id': chunk.get('chunk_id', 0),
                        'word_matches': word_matches,
                        'legal_matches': legal_matches
                    })
            
            # מיין לפי ציון משולב
            results.sort(key=lambda x: (x['similarity'] * 0.6 + x['relevance'] * 0.4), reverse=True)
            
            return results[:max_results]
            
        except Exception as e:
            print(f"Error in smart text search: {e}")
            return []
    
    def semantic_search(self, query: str, max_results: int = 15, min_similarity: float = None) -> List[Dict]:
        """חיפוש סמנטי עם TF-IDF (אם sklearn זמין)"""
        if not SKLEARN_AVAILABLE or not self.vectorizer or not self.tfidf_matrix:
            # fallback לחיפוש טקסט חכם
            return self.smart_text_search(query, max_results)
        
        if min_similarity is None:
            min_similarity = MIN_SIMILARITY_THRESHOLD
        
        try:
            # וקטוריזציה של השאלה
            query_vector = self.vectorizer.transform([query])
            
            # חשב דמיון קוסינוס
            similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
            
            # קבל התוצאות הטובות ביותר
            top_indices = np.argsort(similarities)[::-1]
            
            results = []
            for idx in top_indices:
                if similarities[idx] >= min_similarity and len(results) < max_results:
                    chunk = self.document_chunks[idx]
                    results.append({
                        'content': chunk['text'],
                        'document': chunk['document'],
                        'document_type': chunk.get('document_type', ''),
                        'similarity': float(similarities[idx]),
                        'type': chunk.get('type', 'document'),
                        'chunk_id': chunk.get('chunk_id', 0),
                        'page': chunk.get('page', 0)
                    })
            
            return results
            
        except Exception as e:
            print(f"Error in semantic search: {e}")
            # fallback לחיפוש פשוט
            return self.smart_text_search(query, max_results)
    
    def hybrid_search(self, query: str, max_results: int = 15) -> List[Dict]:
        """חיפוש היברידי משולב (semantic + text + legal context)"""
        try:
            # קבל תוצאות מכל השיטות
            semantic_results = self.semantic_search(query, max_results // 2) if SKLEARN_AVAILABLE else []
            text_results = self.smart_text_search(query, max_results)
            
            # שלב התוצאות ומנע כפילות
            combined_results = {}
            
            # הוסף תוצאות semantic עם משקל גבוה
            for result in semantic_results:
                key = f"{result['document']}_{result['chunk_id']}"
                result['search_method'] = 'semantic'
                result['final_score'] = result['similarity'] * 1.2  # בונוס לחיפוש סמנטי
                combined_results[key] = result
            
            # הוסף תוצאות טקסט במקרים שלא נמצאו
            for result in text_results:
                key = f"{result['document']}_{result['chunk_id']}"
                if key not in combined_results:
                    result['search_method'] = 'text'
                    result['final_score'] = result['similarity']
                    combined_results[key] = result
                else:
                    # שלב ציונים עבור תוצאות חופפות
                    existing = combined_results[key]
                    existing['final_score'] = (existing['final_score'] + result['similarity']) / 2
                    existing['search_method'] = 'hybrid'
            
            # המר לרשימה וסדר לפי ציון סופי
            final_results = list(combined_results.values())
            final_results.sort(key=lambda x: x['final_score'], reverse=True)
            
            return final_results[:max_results]
            
        except Exception as e:
            print(f"Error in hybrid search: {e}")
            # fallback לחיפוש טקסט בלבד
            return self.smart_text_search(query, max_results)
    
    def search_documents(self, query: str, method: str = "hybrid", max_results: int = 15, 
                        min_similarity: float = None, include_summaries: bool = True) -> List[Dict]:
        """נקודת כניסה מרכזית לחיפוש במסמכים"""
        
        # שמור את החיפוש בהיסטוריה
        search_entry = {
            'query': query,
            'method': method,
            'timestamp': datetime.now().isoformat(),
            'max_results': max_results
        }
        self.search_history.append(search_entry)
        
        # הגבל היסטוריה ל-50 חיפושים אחרונים
        if len(self.search_history) > 50:
            self.search_history = self.search_history[-50:]
        
        try:
            if method == "semantic":
                results = self.semantic_search(query, max_results, min_similarity)
            elif method == "text" or method == "keyword":
                results = self.smart_text_search(query, max_results)
            else:  # hybrid (default)
                results = self.hybrid_search(query, max_results)
            
            # סנן סיכומים אם נדרש
            if not include_summaries:
                results = [r for r in results if r.get('type') != 'summary']
            
            # שמור תוצאות אחרונות
            self.last_search_results = results
            
            print(f"🔍 Search completed: {len(results)} results for '{query[:50]}...'")
            return results
            
        except Exception as e:
            print(f"❌ Error in search_documents: {e}")
            return []
    
    def create_legal_prompt(self, query: str, search_results: List[Dict], analysis_type: str = "standard") -> str:
        """יצור פרומפט משפטי מתודע והקשר"""
        
        if not search_results:
            return self._create_general_legal_prompt(query)
        
        # בנה הקשר מהמסמכים
        context_text = ""
        sources_summary = []
        
        for i, result in enumerate(search_results, 1):
            doc_type = result.get('document_type', result.get('type', 'מסמך'))
            doc_name = result['document']
            similarity = result.get('similarity', 0)
            
            context_text += f"\n\n📄 **מקור {i}** - {doc_name} ({doc_type}) [רלוונטיות: {similarity:.2f}]:\n"
            context_text += f"{result['content']}\n"
            context_text += "---"
            
            sources_summary.append(f"{doc_name} ({doc_type})")
        
        # בחר טמפרטורה לפי סוג הניתוח
        temperature_setting = TEMPERATURE_PRECISE if analysis_type == "precise" else TEMPERATURE_NORMAL
        
        # פרומפט משפטי מתקדם
        legal_prompt = f"""{LEGAL_CONTEXT_HEADER}

🎯 **סוג המשימה**: {analysis_type}
🔍 **השאלה המשפטי**: {query}

📚 **מסמכי התיק הרלוונטיים** ({len(search_results)} מקורות):
{sources_summary}

📄 **תוכן המסמכים**:
{context_text}

⚖️ **הוראות מיוחדות לתשובה**:
1. **נתח בקפידה** את כל המידע המשפטי המצורף
2. **זהה נקודות חוזק וחולשה** בתיק להגנה
3. **גלה סתירות ואי-עקביויות** במסמכים השונים
4. **הצע אסטרטגיות הגנה** מבוססות ומעשיות
5. **השתמש בציטוטים ישירים** מהמסמכים לתמיכה בניתוח
6. **התמקד בפתרונות** המתאימים לשאלה הספציפית
7. **ציין בבירור** מהיכן לקוח כל מידע או ציטוט
8. **אם חסר מידע** - ציין במדויק מה נדרש להשלמה

🏛️ **זכור**: אתה עוזר בהכנת הגנה משפטית חיונית. התשובה שלך צריכה להיות מקצועית, מדויקת ושלמה."""

        return legal_prompt
    
    def _create_general_legal_prompt(self, query: str) -> str:
        """פרומפט כללי כאשר אין מסמכים"""
        return f"""אתה עורך דין מומחה במשפט אזרחי ופלילי.

🔍 השאלה: {query}

אין לי גישה למסמכים ספציפיים של התיק, אבל אנא תן תשובה משפטית מקצועית וכללית המבוססת על הידע המשפטי שלך.

כלול בתשובה:
1. הסבר כללי על הנושא המשפטי
2. עקרונות משפטיים רלוונטיים  
3. נקודות מפתח לחיפוש או ניתוח
4. שיקולים אסטרטגיים כלליים
5. המלצות למשך הטיפול בנושא

תן תשובה מקצועית וברורה."""
    
    def _get_working_model(self) -> str:
        """קבל מודל Claude שעובד"""
        for model in [CLAUDE_MODEL] + CLAUDE_FALLBACK_MODELS:
            try:
                # בדיקה מהירה
                test_response = self.claude_client.messages.create(
                    model=model,
                    max_tokens=10,
                    messages=[{"role": "user", "content": "test"}]
                )
                return model
            except Exception:
                continue
        
        # אם כל המודלים נכשלו
        return CLAUDE_MODEL  # נסה את הברירת מחדל בכל זאת
    
    def search_and_respond(self, query: str, method: str = "hybrid", 
                          max_results: int = 15, min_similarity: float = None, 
                          include_summaries: bool = True, analysis_type: str = "standard") -> Dict:
        """חפש ותן תשובה משפטית מקצועית - הפונקציה המרכזית"""
        
        if not self.claude_client:
            return {
                'answer': "❌ Claude API לא זמין. בדוק את ה-API key ב-.env או בהגדרות Streamlit.",
                'sources': [],
                'error': 'claude_unavailable'
            }
        
        start_time = time.time()
        
        try:
            # חפש במסמכים
            search_results = self.search_documents(query, method, max_results, min_similarity, include_summaries)
            
            # יצור פרומפט משפטי
            legal_prompt = self.create_legal_prompt(query, search_results, analysis_type)
            
            # בחר מודל עובד
            working_model = self._get_working_model()
            
            # בחר הגדרות לפי סוג הניתוח
            max_tokens = 4000 if analysis_type == "comprehensive" else 3000
            temperature = TEMPERATURE_PRECISE if analysis_type == "precise" else TEMPERATURE_NORMAL
            
            # קבל תשובה מקלוד
            message = self.claude_client.messages.create(
                model=working_model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": legal_prompt}]
            )
            
            processing_time = time.time() - start_time
            
            # הכן תשובה מפורטת
            response = {
                'answer': message.content[0].text,
                'sources': [
                    {
                        'file': result['document'],
                        'content': result['content'][:500] + "..." if len(result['content']) > 500 else result['content'],
                        'similarity': result.get('similarity', result.get('final_score', 0)),
                        'type': result.get('type', 'document'),
                        'document_type': result.get('document_type', ''),
                        'search_method': result.get('search_method', method),
                        'chunk_id': result.get('chunk_id', 0)
                    }
                    for result in search_results
                ],
                'search_method': f"Legal AI Search ({method})",
                'legal_context': True,
                'model_used': working_model,
                'processing_time': f"{processing_time:.2f}s",
                'analysis_type': analysis_type,
                'num_sources': len(search_results),
                'query_timestamp': datetime.now().isoformat()
            }
            
            # הוסף הערה אם לא נמצאו מסמכים
            if not search_results:
                response['note'] = 'תשובה כללית - לא נמצאו מסמכים רלוונטיים בתיק'
            
            return response
            
        except Exception as e:
            print(f"❌ Error in search_and_respond: {e}")
            return {
                'answer': f"❌ שגיאה בחיפוש משפטי: {e}",
                'sources': [],
                'error': str(e),
                'search_method': method
            }
    
    # Alias methods for compatibility
    def get_response(self, query: str) -> str:
        """קבל תשובה פשוטה - תואמות לאחור"""
        response = self.search_and_respond(query)
        return response['answer']
    
    def respond(self, query: str) -> str:
        """תשובה בסיסית - alias ל-get_response"""
        return self.get_response(query)
    
    # Management and utility methods
    def clear_search_cache(self):
        """נקה cache של חיפוש"""
        try:
            self.document_chunks = []
            self.legal_summaries = []
            self.vectorizer = None
            self.tfidf_matrix = None
            self.last_search_results = []
            self.search_history = []
            print("✅ Search cache cleared")
        except Exception as e:
            print(f"⚠️ Error clearing cache: {e}")
    
    def reload_documents(self):
        """טען מחדש את המסמכים"""
        print("🔄 Reloading documents...")
        self.clear_search_cache()
        self._load_documents()
        self._load_metadata()
        print("✅ Documents reloaded")
    
    def get_document_stats(self) -> Dict:
        """קבל סטטיסטיקות מפורטות על המסמכים"""
        try:
            documents = set()
            summaries_count = 0
            doc_types = {}
            
            for chunk in self.document_chunks:
                documents.add(chunk['document'])
                if chunk.get('type') == 'summary':
                    summaries_count += 1
                
                doc_type = chunk.get('document_type', 'אחר')
                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            
            # חשב גם קבצים בתיקיות
            upload_count = len(list(Path("data/uploaded_documents").glob("*.pdf"))) if Path("data/uploaded_documents").exists() else 0
            processed_count = len(list(PROCESSED_DIR.glob("*.json"))) if PROCESSED_DIR.exists() else 0
            summary_files = len(list(SUMMARIES_DIR.glob("*.json"))) if SUMMARIES_DIR.exists() else 0
            
            return {
                'total_chunks': len(self.document_chunks),
                'unique_documents': len(documents),
                'summaries_count': summaries_count,
                'uploaded_files': upload_count,
                'processed_files': processed_count,
                'summary_files': summary_files,
                'document_types': doc_types,
                'has_vectorizer': self.vectorizer is not None,
                'has_sklearn': SKLEARN_AVAILABLE,
                'claude_connected': self.claude_client is not None,
                'search_history_count': len(self.search_history),
                'last_search_results_count': len(self.last_search_results),
                'documents_list': list(documents)
            }
        except Exception as e:
            print(f"Error getting document stats: {e}")
            return {
                'total_chunks': 0,
                'unique_documents': 0,
                'summaries_count': 0,
                'error': str(e)
            }
    
    def get_documents_info(self) -> Dict:
        """Alias ל-get_document_stats עבור תואמות לאחור"""
        return self.get_document_stats()
    
    def get_search_history(self, limit: int = 10) -> List[Dict]:
        """קבל היסטוריית חיפושים"""
        return self.search_history[-limit:] if self.search_history else []
    
    def get_legal_summaries(self) -> List[Dict]:
        """קבל רשימת סיכומים משפטיים"""
        return self.legal_summaries
    
    def get_document_metadata(self, document_name: str) -> Dict:
        """קבל metadata של מסמך ספציפי"""
        return self.document_metadata.get(document_name, {})
    
    def test_connection(self) -> Tuple[bool, str]:
        """בדיקת חיבור מפורטת"""
        try:
            if not self.claude_client:
                return False, "❌ Claude client לא אותחל"
            
            # נסה קריאה פשוטה
            response = self.claude_client.messages.create(
                model=self._get_working_model(),
                max_tokens=50,
                messages=[{"role": "user", "content": "שלום, זוהי בדיקת חיבור"}]
            )
            
            if response and response.content:
                return True, f"✅ חיבור תקין. מודל: {self._get_working_model()}"
            else:
                return False, "❌ תגובה ריקה מClaude"
                
        except Exception as e:
            return False, f"❌ שגיאה בבדיקת חיבור: {e}"
