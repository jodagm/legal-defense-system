"""
מנהל קבצים חכם עם יכולת החלפה ומניעת כפילויות
"""
import hashlib
import shutil
import re
from pathlib import Path
from typing import Dict, List
import streamlit as st
import json
from datetime import datetime

from config.settings import UPLOAD_DIR, PROCESSED_DIR, SUMMARIES_DIR


class SmartFileManager:
    """מנהל קבצים חכם עם יכולת החלפה ומניעת כפילויות"""
    
    def __init__(self):
        self.upload_path = UPLOAD_DIR
        self.processed_path = PROCESSED_DIR
        self.summaries_path = SUMMARIES_DIR
    
    def get_file_hash(self, file_content: bytes) -> str:
        """חזור hash של תוכן הקובץ לזיהוי שינויים"""
        return hashlib.md5(file_content).hexdigest()[:8]
    
    def clean_filename(self, filename: str) -> str:
        """נקה שם קובץ מתווים בעייתיים"""
        # החלף תווים בעייתיים
        cleaned = filename.replace(" ", "_").replace("-", "_").replace(":", "_")
        # הסר תווים מיוחדים נוספים
        cleaned = re.sub(r'[^\w\u0590-\u05FF._]', '_', cleaned)
        return cleaned
    
    def get_base_name(self, filename: str) -> str:
        """קבל שם בסיסי של קובץ (ללא סיומת)"""
        return Path(filename).stem
    
    def find_related_files(self, base_name: str) -> Dict[str, List[Path]]:
        """מצא את כל הקבצים הקשורים לשם בסיס מסוים"""
        related_files = {
            'uploaded': [],
            'processed': [],
            'summaries': []
        }
        
        # חפש בקבצים שהועלו
        for file_path in self.upload_path.glob("*.pdf"):
            if self.get_base_name(file_path.name) == base_name:
                related_files['uploaded'].append(file_path)
        
        # חפש בקבצים מעובדים
        for file_path in self.processed_path.glob("*.json"):
            if file_path.stem.replace('_processed', '') == base_name:
                related_files['processed'].append(file_path)
        
        # חפש בסיכומים
        for file_path in self.summaries_path.glob("*.json"):
            if base_name in file_path.stem:
                related_files['summaries'].append(file_path)
        
        return related_files
    
    def clean_old_versions(self, base_name: str):
        """נקה את כל הגרסאות הישנות של קובץ"""
        related_files = self.find_related_files(base_name)
        
        removed_files = []
        
        # מחק קבצים ישנים מכל התיקיות
        for category, files in related_files.items():
            for file_path in files:
                try:
                    file_path.unlink()
                    removed_files.append(f"{category}: {file_path.name}")
                except Exception as e:
                    st.warning(f"⚠️ לא הצלחתי למחוק {file_path.name}: {e}")
        
        return removed_files
    
    def save_uploaded_file_smart(self, uploaded_file) -> Dict:
        """שמור קובץ עם ניקוי אוטומטי של גרסאות ישנות"""
        try:
            # נקה שם הקובץ
            original_name = uploaded_file.name
            clean_name = self.clean_filename(original_name)
            base_name = self.get_base_name(clean_name)
            
            # קבל תוכן הקובץ
            file_content = uploaded_file.getvalue()
            file_hash = self.get_file_hash(file_content)
            
            # בדוק אם יש כבר קובץ עם אותו שם בסיס
            existing_files = self.find_related_files(base_name)
            
            result = {
                'original_name': original_name,
                'clean_name': clean_name,
                'base_name': base_name,
                'file_hash': file_hash,
                'action': 'new',
                'removed_files': [],
                'file_path': None,
                'size': len(file_content)
            }
            
            # אם יש קבצים קיימים - נקה אותם
            if any(existing_files.values()):
                st.info(f"🔄 מזהה קובץ קיים בשם '{base_name}' - מנקה גרסאות ישנות...")
                result['removed_files'] = self.clean_old_versions(base_name)
                result['action'] = 'replaced'
            
            # שמור את הקובץ החדש
            file_path = self.upload_path / clean_name
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            result['file_path'] = file_path
            result['success'] = True
            
            return result
            
        except Exception as e:
            return {
                'original_name': uploaded_file.name,
                'success': False,
                'error': str(e),
                'action': 'failed'
            }
    
    def get_files_status(self) -> Dict:
        """קבל סטטוס של כל הקבצים במערכת"""
        status = {
            'uploaded': [],
            'processed': [],
            'summaries': []
        }
        
        # קבצים שהועלו
        if self.upload_path.exists():
            for file_path in self.upload_path.glob("*.pdf"):
                status['uploaded'].append({
                    'name': file_path.name,
                    'size': file_path.stat().st_size,
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime)
                })
        
        # קבצים מעובדים
        if self.processed_path.exists():
            for file_path in self.processed_path.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        chunks = len(data.get('chunks', []))
                except:
                    chunks = 0
                
                status['processed'].append({
                    'name': file_path.name,
                    'base_name': file_path.stem.replace('_processed', ''),
                    'chunks': chunks,
                    'size': file_path.stat().st_size,
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime)
                })
        
        # סיכומים
        if self.summaries_path.exists():
            for file_path in self.summaries_path.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        summary_status = data.get('status', 'unknown')
                except:
                    summary_status = 'error'
                
                status['summaries'].append({
                    'name': file_path.name,
                    'status': summary_status,
                    'size': file_path.stat().st_size,
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime)
                })
        
        return status
    
    def clean_vectorstore_cache(self):
        """נקה את cache של מאגר הווקטורים"""
        from config.settings import VECTORSTORE_DIR
        if VECTORSTORE_DIR.exists():
            try:
                shutil.rmtree(VECTORSTORE_DIR)
                VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)
                return True
            except Exception as e:
                st.warning(f"⚠️ לא הצלחתי לנקות cache: {e}")
                return False
        return True
