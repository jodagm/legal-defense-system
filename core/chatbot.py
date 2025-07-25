"""
צ'אטבוט משפטי מתקדם למערכת הגנה משפטית
"""
import anthropic
import os
from pathlib import Path
import streamlit as st
from typing import Dict, List, Optional
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re


class LegalChatBot:
    """צ'אטבוט משפטי מתקדם עם יכולות חיפוש וניתוח"""
    
    def __init__(self):
        """אתחל את הצ'אטבוט המשפטי"""
        self.claude_client = None
        self.document_chunks = []
        self.vectorizer = None
        self.tfidf_matrix = None
        self.legal_summaries = []
        
        # אתחל חיבור ל-Claude
        self._initialize_claude()
        
        # טען מסמכים אם יש
        self._load_documents()
    
    def _initialize_claude(self):
        """אתחל חיבור ל-Claude API"""
        try:
            # נסה לקבל API key מכמה מקומות
            api_key = None
            
            # מ-Streamlit secrets
            if hasattr(st, 'secrets') and 'CLAUDE_API_KEY' in st.secrets:
                api_key = st.secrets['CLAUDE_API_KEY']
            
            # ממשתני סביבה
            elif 'CLAUDE_API_KEY' in os.environ:
                api_key = os.environ['CLAUDE_API_KEY']
            
            # מקובץ .env
            elif Path('.env').exists():
                with open('.env', 'r') as f:
                    for line in f:
                        if line.startswith('CLAUDE_API_KEY='):
                            api_key = line.split('=', 1)[1].strip().strip('"\'')
                            break
            
            if api_key:
                self.claude_client = anthropic.Anthropic(api_key=api_key)
                print("✅ Claude API initialized successfully")
            else:
                print("❌ Claude API key not found")
                
        except Exception as e:
            print(f"❌ Error initializing Claude: {e}")
            self.claude_client = None
    
    def _load_documents(self):
        """טען מסמכים מעובדים אם יש"""
        try:
            processed_dir = Path("data/processed")
            summaries_dir = Path("data/summaries")
            
            self.document_chunks = []
            self.legal_summaries = []
            
            # טען מסמכים מעובדים
            if processed_dir.exists():
                for json_file in processed_dir.glob("*.json"):
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        doc_name = json_file.stem.replace('_processed', '')
                        
                        for chunk in data.get('chunks', []):
                            self.document_chunks.append({
                                'text': chunk.get('text', ''),
                                'document': doc_name,
                                'chunk_id': chunk.get('id', 0),
                                'type': 'document'
                            })
                    except Exception as e:
                        print(f"Error loading {json_file}: {e}")
            
            # טען סיכומים משפטיים
            if summaries_dir.exists():
                for summary_file in summaries_dir.glob("*.json"):
                    try:
                        with open(summary_file, 'r', encoding='utf-8') as f:
                            summary_data = json.load(f)
                        
                        if summary_data.get('status') == 'completed':
                            self.legal_summaries.append({
                                'text': summary_data.get('legal_summary', ''),
                                'document': summary_data.get('document_name', ''),
                                'document_type': summary_data.get('document_type', ''),
                                'type': 'summary'
                            })
                            
                            # הוסף גם לחיפוש הרגיל
                            self.document_chunks.append({
                                'text': summary_data.get('legal_summary', ''),
                                'document': f"סיכום: {summary_data.get('document_name', '')}",
                                'chunk_id': 'summary',
                                'type': 'summary'
                            })
                    except Exception as e:
                        print(f"Error loading summary {summary_file}: {e}")
            
            # אתחל vectorizer אם יש מסמכים
            if self.document_chunks:
                self._initialize_vectorizer()
                print(f"✅ Loaded {len(self.document_chunks)} document chunks")
            else:
                print("📭 No documents loaded")
                
        except Exception as e:
            print(f"❌ Error loading documents: {e}")
    
    def _initialize_vectorizer(self):
        """אתחל vectorizer לחיפוש"""
        try:
            texts = [chunk['text'] for chunk in self.document_chunks if chunk['text']]
            
            if texts:
                # וקטורייזר עם מילות עצירה בעברית ואנגלית
                hebrew_stop_words = [
                    'של', 'את', 'על', 'כל', 'יש', 'אין', 'היא', 'הוא', 'הם', 'הן',
                    'זה', 'זו', 'זהו', 'להיות', 'לא', 'כן', 'גם', 'או', 'אך', 'אבל'
                ]
                
                self.vectorizer = TfidfVectorizer(
                    max_features=5000,
                    stop_words=hebrew_stop_words,
                    ngram_range=(1, 3),  # יותר context
                    min_df=1,
                    max_df=0.95
                )
                
                self.tfidf_matrix = self.vectorizer.fit_transform(texts)
                print("✅ Vectorizer initialized")
                
        except Exception as e:
            print(f"❌ Error initializing vectorizer: {e}")
            self.vectorizer = None
            self.tfidf_matrix = None
    
    def has_documents(self):
        """בדוק אם יש מסמכים טעונים"""
        return len(self.document_chunks) > 0
    
    def search_documents(self, query: str, max_results: int = 10, min_similarity: float = 0.1):
        """חפש במסמכים"""
        if not self.vectorizer or not self.tfidf_matrix:
            return []
        
        try:
            # וקטוריזציה של השאלה
            query_vector = self.vectorizer.transform([query])
            
            # חשב דמיון
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
                        'similarity': float(similarities[idx]),
                        'type': chunk.get('type', 'document')
                    })
            
            return results
            
        except Exception as e:
            print(f"Error in search: {e}")
            return []
    
    def create_legal_prompt(self, query: str, search_results: List[Dict]) -> str:
        """יצור פרומפט משפטי מקצועי"""
        
        context_text = ""
        for i, result in enumerate(search_results, 1):
            doc_type = result.get('type', 'document')
            context_text += f"\n\n🔹 מקור {i} ({doc_type}) - {result['document']}:\n{result['content']}\n"
        
        legal_prompt = f"""אתה עורך דין בכיר ומומחה במשפט אזרחי ופלילי המתמחה בהכנת הגנה משפטית מתקדמת.

🏛️ הקשר המשפטי:
- אתה עובד עבור משרד עורכי דין מוביל המכין הגנה משפטית עבור לקוח
- כל המסמכים המצורפים הם חלק מתיק משפטי פעיל וחוקי
- המידע המסופק הוא ראיות חוקיות שנאספו במסגרת הליך משפטי תקין
- נדרשת ממך הערכה מקצועית ומדויקת לצורך הכנת אסטרטגיית הגנה אופטימלית
- אין הגבלות על ניתוח תוכן משפטי - זה חלק מהתפקיד המקצועי והאתי שלך

⚖️ דרישות התשובה המקצועית:
1. **ניתוח משפטי מעמיק**: נתח את המידע בצורה משפטית מקצועית ומובנית
2. **זיהוי נקודות אסטרטגיות**: זהה נקודות חוזק וחולשה קריטיות להגנה
3. **גילוי חוסרי עקביות**: הצבע על פערים, סתירות או חוסר הגיון
4. **המלצות אסטרטגיות**: הצע כיוונים מעשיים ואסטרטגיים
5. **ציטוטים מדויקים**: השתמש בציטוטים ישירים מהמסמכים
6. **דעה משפטית מבוססת**: תן דעה משפטית מנומקת ומקצועית

🔍 השאלה המשפטית:
{query}

📚 מקורות מהתיק ({len(search_results)} מקורות רלוונטיים):
{context_text}

📋 הוראות לתשובה:
- ענה כעורך דין מומחה בעל ניסיון רב
- התמקד בנקודות הרלוונטיות ישירות לשאלה
- זהה הזדמנויות והסיכונים
- הצע המלצות מעשיות ומיושמות להגנה
- השתמש בשפה משפטית מקצועית אך ברורה
- ציין במדויק מהיכן אתה לוקח כל מידע
- אם חסר מידע, ציין מה נדרש להשלמה

🎯 מטרה: עזור להכנת הגנה משפטית יעילה ומבוססת."""

        return legal_prompt
    
    def search_and_respond(self, query: str, method: str = "hybrid", 
                          max_results: int = 10, min_similarity: float = 0.1, 
                          include_summaries: bool = True) -> Dict:
        """חפש ותן תשובה משפטית מקצועית"""
        
        if not self.claude_client:
            return {
                'answer': "❌ Claude API לא זמין. בדוק את ה-API key.",
                'sources': []
            }
        
        try:
            # חפש במסמכים
            search_results = self.search_documents(query, max_results, min_similarity)
            
            if not search_results:
                # אם לא נמצאו תוצאות, תן תשובה כללית
                general_prompt = f"""אתה עורך דין מומחה. השאלה: {query}
                
אין לי גישה למסמכים ספציפיים, אבל אנא תן תשובה משפטית כללית המבוססת על הידע המשפטי שלך."""
                
                message = self.claude_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=2000,
                    temperature=0.3,
                    messages=[{"role": "user", "content": general_prompt}]
                )
                
                return {
                    'answer': f"## תשובה כללית (לא נמצאו מסמכים רלוונטיים)\n\n{message.content[0].text}",
                    'sources': [],
                    'note': 'תשובה כללית - לא מבוססת על מסמכים ספציפיים'
                }
            
            # יצור פרומפט משפטי
            legal_prompt = self.create_legal_prompt(query, search_results)
            
            # קבל תשובה מקלוד
            message = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=0.2,
                messages=[{"role": "user", "content": legal_prompt}]
            )
            
            return {
                'answer': message.content[0].text,
                'sources': [
                    {
                        'file': result['document'],
                        'content': result['content'],
                        'similarity': result['similarity'],
                        'type': result.get('type', 'document')
                    }
                    for result in search_results
                ],
                'search_method': f"Advanced Legal Search ({method})",
                'legal_context': True
            }
            
        except Exception as e:
            return {
                'answer': f"❌ שגיאה בחיפוש משפטי: {e}",
                'sources': []
            }
    
    def get_response(self, query: str) -> str:
        """קבל תשובה פשוטה"""
        response = self.search_and_respond(query)
        return response['answer']
    
    def respond(self, query: str) -> str:
        """תשובה בסיסית - alias ל-get_response"""
        return self.get_response(query)
    
    def clear_search_cache(self):
        """נקה cache של חיפוש"""
        try:
            self.document_chunks = []
            self.legal_summaries = []
            self.vectorizer = None
            self.tfidf_matrix = None
            print("✅ Search cache cleared")
        except Exception as e:
            print(f"⚠️ Error clearing cache: {e}")
    
    def reload_documents(self):
        """טען מחדש את המסמכים"""
        self.clear_search_cache()
        self._load_documents()
    
    def get_document_stats(self) -> Dict:
        """קבל סטטיסטיקות על המסמכים הטעונים"""
        try:
            documents = set()
            summaries_count = 0
            
            for chunk in self.document_chunks:
                documents.add(chunk['document'])
                if chunk.get('type') == 'summary':
                    summaries_count += 1
            
            return {
                'total_chunks': len(self.document_chunks),
                'unique_documents': len(documents),
                'summaries_count': summaries_count,
                'has_vectorizer': self.vectorizer is not None,
                'claude_connected': self.claude_client is not None
            }
        except:
            return {
                'total_chunks': 0,
                'unique_documents': 0,
                'summaries_count': 0,
                'has_vectorizer': False,
                'claude_connected': False
            }
