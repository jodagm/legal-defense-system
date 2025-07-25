"""
כלי עזר כלליים למערכת המשפטית
"""
import subprocess
import sys
from pathlib import Path
import streamlit as st
from typing import Tuple

from config.settings import UPLOAD_DIR, PROCESSED_DIR


def process_documents_function() -> Tuple[bool, str, str]:
    """פונקציה משופרת לעיבוד מסמכים עם דיווח מפורט"""
    try:
        st.info("🔄 מעבד מסמכים חדשים עם דיווח מפורט...")
        
        # בדוק כמה קבצים יעובדו
        if not UPLOAD_DIR.exists():
            return False, "", "📁 תיקיית המסמכים לא קיימת"
        
        uploaded_files = list(UPLOAD_DIR.glob("*.pdf"))
        if not uploaded_files:
            return False, "", "📄 לא נמצאו קבצי PDF לעיבוד"
        
        processed_files = set()
        if PROCESSED_DIR.exists():
            processed_files = {f.stem.replace('_processed', '') for f in PROCESSED_DIR.glob("*.json")}
        
        new_files = [f for f in uploaded_files if f.stem not in processed_files]
        
        st.write(f"📊 מצב לפני עיבוד:")
        st.write(f"  • קבצים שהועלו: {len(uploaded_files)}")
        st.write(f"  • כבר מעובדים: {len(processed_files)}")
        st.write(f"  • חדשים לעיבוד: {len(new_files)}")
        
        if new_files:
            st.write("🆕 קבצים חדשים שיעובדו:")
            for f in new_files:
                st.write(f"  • {f.name}")
        
        # הפעל את הסקריפט
        result = subprocess.run(
            [sys.executable, "scripts/process_documents.py", "--source", str(UPLOAD_DIR), "--output", str(PROCESSED_DIR)],
            capture_output=True,
            text=True,
            cwd=".",
            timeout=300
        )
        
        return result.returncode == 0, result.stdout, result.stderr
        
    except subprocess.TimeoutExpired:
        return False, "", "❌ העיבוד ארך יותר מידי (5 דקות)"
    except Exception as e:
        return False, "", f"❌ שגיאה כללית: {e}"


def format_file_size(size_bytes: int) -> str:
    """המר גודל קובץ לפורמט קריא"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"


def validate_pdf_file(file_path: Path) -> bool:
    """בדוק אם קובץ PDF תקין"""
    try:
        # בדיקה בסיסית - גודל ותוספת
        if not file_path.exists():
            return False
        
        if file_path.suffix.lower() != '.pdf':
            return False
        
        if file_path.stat().st_size == 0:
            return False
        
        # בדיקה מתקדמת יותר אם יש PyPDF2
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                # נסה לקרוא את העמוד הראשון
                if len(reader.pages) > 0:
                    reader.pages[0]
                return True
        except ImportError:
            # אם אין PyPDF2, העבר רק בדיקות בסיסיות
            return True
        except Exception:
            return False
            
    except Exception as e:
        st.warning(f"⚠️ שגיאה בבדיקת {file_path.name}: {e}")
        return False


def clean_text_for_display(text: str, max_length: int = 500) -> str:
    """נקה טקסט לתצוגה"""
    if not text:
        return ""
    
    # נקה תווים מיוחדים
    cleaned = text.strip()
    
    # קצר אם נדרש
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length] + "..."
    
    return cleaned


def get_system_info() -> dict:
    """קבל מידע על מצב המערכת"""
    import platform
    import os
    
    info = {
        "python_version": sys.version.split()[0],
        "platform": platform.system(),
        "working_directory": str(Path.cwd()),
        "upload_dir_exists": UPLOAD_DIR.exists(),
        "processed_dir_exists": PROCESSED_DIR.exists(),
        "upload_files_count": len(list(UPLOAD_DIR.glob("*.pdf"))) if UPLOAD_DIR.exists() else 0,
        "processed_files_count": len(list(PROCESSED_DIR.glob("*.json"))) if PROCESSED_DIR.exists() else 0
    }
    
    return info


def create_backup_name(original_name: str) -> str:
    """יצור שם גיבוי לקובץ"""
    from datetime import datetime
    
    path = Path(original_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{path.stem}_backup_{timestamp}{path.suffix}"


def safe_delete_file(file_path: Path) -> bool:
    """מחק קובץ בצורה בטוחה"""
    try:
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    except Exception as e:
        st.warning(f"⚠️ לא הצלחתי למחוק {file_path.name}: {e}")
        return False


def estimate_processing_time(file_size_mb: float) -> str:
    """הערך זמן עיבוד על בסיס גודל הקובץ"""
    # הערכה גסה: כ-1 דקה לכל 10MB
    estimated_minutes = max(1, int(file_size_mb / 10))
    
    if estimated_minutes == 1:
        return "כדקה"
    elif estimated_minutes < 5:
        return f"כ-{estimated_minutes} דקות"
    else:
        return f"{estimated_minutes} דקות"


def count_hebrew_words(text: str) -> int:
    """ספור מילים עבריות בטקסט"""
    import re
    
    # מצא מילים עבריות (תווים עבריים)
    hebrew_words = re.findall(r'[\u0590-\u05FF]+', text)
    return len(hebrew_words)


def extract_dates_from_text(text: str) -> list:
    """חלץ תאריכים מטקסט"""
    import re
    
    # תבניות תאריכים שונות
    date_patterns = [
        r'\d{1,2}/\d{1,2}/\d{2,4}',  # DD/MM/YYYY או DD/MM/YY
        r'\d{1,2}\.\d{1,2}\.\d{2,4}',  # DD.MM.YYYY או DD.MM.YY
        r'\d{1,2}-\d{1,2}-\d{2,4}',  # DD-MM-YYYY או DD-MM-YY
    ]
    
    dates = []
    for pattern in date_patterns:
        dates.extend(re.findall(pattern, text))
    
    return list(set(dates))  # הסר כפילויות


def highlight_search_terms(text: str, search_terms: list) -> str:
    """הדגש מונחי חיפוש בטקסט"""
    import re
    
    highlighted = text
    for term in search_terms:
        if term and len(term) > 2:
            # החלף עם הדגשה (markdown)
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            highlighted = pattern.sub(f"**{term}**", highlighted)
    
    return highlighted
