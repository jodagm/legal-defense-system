"""
מנוע חיפוש מתקדם במסמכים משפטיים
"""
import json
from pathlib import Path
from typing import List, Dict, Any
import streamlit as st
import re

from config.settings import PROCESSED_DIR


class AdvancedDocumentSearch:
    """מנוע חיפוש מתקדם עם ניקוד רלוונטיות"""
    
    def __init__(self):
        self.documents = []
        self.processed_path = PROCESSED_DIR
    
    def load_documents(self) -> bool:
        """טען מסמכים מעובדים לזיכרון"""
        try:
            self.documents = []
            
            if not self.processed_path.exists():
                st.warning("📁 תיקיית המסמכים המעובדים לא קיימת")
                return False
            
            # טען כל המסמכים המעובדים
            total_chunks = 0
            for json_file in self.processed_path.glob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if 'chunks' in data and data['chunks']:
                            for i, chunk in enumerate(data['chunks']):
                                chunk['source_file'] = json_file.stem
                                chunk['global_index'] = total_chunks + i
                                self.documents.append(chunk)
                            total_chunks += len(data['chunks'])
                            st.write(f"📖 נטען: {json_file.name} - {len(data['chunks'])} קטעים")
                except Exception as e:
                    st.warning(f"⚠️ שגיאה בטעינת {json_file.name}: {e}")
                    continue
            
            if not self.documents:
                st.warning("📄 לא נמצאו מסמכים לטעינה")
                return False
            
            # הודעת סיכום
            st.success(f"✅ טעינה הושלמה! {len(self.documents)} קטעי טקסט מוכנים לחיפוש מתקדם")
            return True
            
        except Exception as e:
            st.error(f"❌ שגיאה בטעינת מסמכים: {e}")
            return False
    
    def calculate_relevance_score(self, text: str, query: str) -> int:
        """חשב ניקוד רלוונטיות מתקדם"""
        text_lower = text.lower()
        query_lower = query.lower()
        query_words = query_lower.split()
        score = 0
        
        # ניקוד בסיסי - מילים בטקסט
        for word in query_words:
            if len(word) > 2:  # התעלם ממילים קצרות
                count = text_lower.count(word)
                score += count * 2
        
        # ניקוד מתקדם - ביטויים שלמים
        if query_lower in text_lower:
            score += 15
        
        # ניקוד משוקלל לפי אורך המילים
        for word in query_words:
            if len(word) > 4 and word in text_lower:
                score += len(word)
        
        # ניקוד עבור מילים עבריות חשובות
        important_hebrew_words = [
            'משטרה', 'חקירה', 'עדות', 'תצהיר', 'הקלטה', 
            'אוירבאך', 'רביבנוביץ', 'שהם', 'עדה', 'קהילה',
            'איום', 'פחד', 'לחץ', 'הכרח', 'סכנה', 'גילוי עריות',
            'הודאה', 'הכחשה', 'סתירה', 'ראיה', 'עד'
        ]
        
        for important_word in important_hebrew_words:
            if important_word in query_lower and important_word in text_lower:
                score += 20
        
        # ניקוד נוסף לקרבה בין מילים
        if len(query_words) > 1:
            for i in range(len(query_words) - 1):
                word1, word2 = query_words[i], query_words[i + 1]
                if word1 in text_lower and word2 in text_lower:
                    pos1 = text_lower.find(word1)
                    pos2 = text_lower.find(word2)
                    if abs(pos1 - pos2) < 100:  # קרובים זה לזה
                        score += 10
        
        return score
    
    def search_documents(self, query: str, n_results: int = 8) -> List[Dict]:
        """חיפוש מתקדם בטקסט עם ניקוד רלוונטיות"""
        try:
            if not self.documents:
                return []
            
            results = []
            
            for doc in self.documents:
                score = self.calculate_relevance_score(doc['text'], query)
                
                if score > 0:
                    results.append({
                        'text': doc['text'],
                        'metadata': doc.get('metadata', {}),
                        'source_file': doc.get('source_file', 'unknown'),
                        'relevance_score': score,
                        'global_index': doc.get('global_index', 0)
                    })
            
            # מיין לפי רלוונטיות ואז לפי מיקום במסמך
            results.sort(key=lambda x: (-x['relevance_score'], x['global_index']))
            
            return results[:n_results]
            
        except Exception as e:
            st.error(f"❌ שגיאה בחיפוש: {e}")
            return []
    
    def get_documents_summary(self) -> Dict:
        """קבל סיכום של המסמכים הטעונים"""
        if not self.documents:
            return {"total_chunks": 0, "sources": []}
        
        sources = {}
        for doc in self.documents:
            source = doc.get('source_file', 'unknown')
            clean_source = source.replace('_processed', '')
            if clean_source not in sources:
                sources[clean_source] = 0
            sources[clean_source] += 1
        
        return {
            "total_chunks": len(self.documents),
            "sources": sources
        }
    
    def clear_documents(self):
        """נקה את המסמכים מהזיכרון"""
        self.documents = []
        st.info("🔄 מסמכים נוקו מהזיכרון")
