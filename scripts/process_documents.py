#!/usr/bin/env python
"""
סקריפט לעיבוד מסמכים PDF לחלקים עם OCR המותאם למערכת החדשה
"""
import sys
import argparse
from pathlib import Path
import json
import PyPDF2
import os

# הוסף את התיקייה הראשית ל-PATH
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import MAX_CHUNK_SIZE

class LegalDocumentProcessor:
    """מעבד מסמכים משפטיים - גרסה חדשה"""
    
    def __init__(self, chunk_size=MAX_CHUNK_SIZE):
        self.chunk_size = chunk_size
    
    def extract_text_from_pdf(self, pdf_path):
        """חלץ טקסט מ-PDF"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
                
                return text.strip()
        except Exception as e:
            print(f"❌ שגיאה בחילוץ טקסט מ-{pdf_path}: {e}")
            return ""
    
    def split_text_into_chunks(self, text):
        """חלק טקסט לחלקים"""
        if not text:
            return []
        
        chunks = []
        words = text.split()
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_length = len(word) + 1  # +1 for space
            
            if current_length + word_length > self.chunk_size and current_chunk:
                # הוסף את החלק הנוכחי
                chunk_text = " ".join(current_chunk)
                chunks.append({
                    "text": chunk_text,
                    "metadata": {
                        "chunk_index": len(chunks),
                        "word_count": len(current_chunk)
                    }
                })
                
                # התחל חלק חדש
                current_chunk = [word]
                current_length = word_length
            else:
                current_chunk.append(word)
                current_length += word_length
        
        # הוסף את החלק האחרון
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append({
                "text": chunk_text,
                "metadata": {
                    "chunk_index": len(chunks),
                    "word_count": len(current_chunk)
                }
            })
        
        return chunks
    
    def process_pdf_file(self, pdf_path, output_dir):
        """עבד קובץ PDF אחד"""
        try:
            print(f"🔄 מעבד: {pdf_path}")
            
            # חלץ טקסט
            text = self.extract_text_from_pdf(pdf_path)
            if not text:
                print(f"⚠️ לא נמצא טקסט ב-{pdf_path}")
                return False
            
            # חלק לחלקים
            chunks = self.split_text_into_chunks(text)
            
            # הכן נתונים לשמירה
            output_data = {
                "source_file": str(pdf_path),
                "total_text_length": len(text),
                "chunks_count": len(chunks),
                "chunks": chunks,
                "processing_info": {
                    "chunk_size": self.chunk_size,
                    "total_words": len(text.split())
                }
            }
            
            # שמור לקובץ JSON
            output_file = output_dir / f"{pdf_path.stem}_processed.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ הושלם: {output_file.name} - {len(chunks)} חלקים")
            return True
            
        except Exception as e:
            print(f"❌ שגיאה בעיבוד {pdf_path}: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='עיבוד מסמכים משפטיים')
    parser.add_argument('--source', type=str, required=True, help='תיקיית קבצי PDF')
    parser.add_argument('--output', type=str, required=True, help='תיקיית פלט JSON')
    
    args = parser.parse_args()
    
    source_dir = Path(args.source)
    output_dir = Path(args.output)
    
    # וודא שהתיקיות קיימות
    if not source_dir.exists():
        print(f"❌ תיקיית המקור לא קיימת: {source_dir}")
        return 1
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # מצא קבצי PDF
    pdf_files = list(source_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"📄 לא נמצאו קבצי PDF ב-{source_dir}")
        return 0
    
    print(f"📁 נמצאו {len(pdf_files)} קבצי PDF")
    
    # עבד קבצים
    processor = LegalDocumentProcessor()
    successful = 0
    
    for pdf_file in pdf_files:
        # בדוק אם הקובץ כבר עובד
        output_file = output_dir / f"{pdf_file.stem}_processed.json"
        if output_file.exists():
            print(f"⏭️ דלג (כבר קיים): {pdf_file.name}")
            continue
        
        if processor.process_pdf_file(pdf_file, output_dir):
            successful += 1
    
    print(f"\n✅ הסתיים! עובדו {successful} קבצים חדשים")
    return 0

if __name__ == "__main__":
    sys.exit(main())
