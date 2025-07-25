"""
Document service - business logic for document operations
"""
from typing import Dict, List, Any, Optional
import json
from pathlib import Path
from datetime import datetime

from app.config.constants import SUPPORTED_FILE_TYPES, PROCESSED_FILE_PATTERN
from app.core.error_handler import DocumentProcessingError


class DocumentService:
    """Service for document operations - handles all document logic"""
    
    def __init__(self, data_paths: Dict[str, Path]):
        self.upload_path = data_paths['upload']
        self.processed_path = data_paths['processed']
        self.summaries_path = data_paths['summaries']
        self.metadata_path = data_paths['metadata']
    
    def has_documents(self) -> bool:
        """Check if any processed documents exist"""
        return len(self.get_processed_documents()) > 0
    
    def get_uploaded_files(self) -> List[Path]:
        """Get list of uploaded PDF files"""
        return list(self.upload_path.glob("*.pdf"))
    
    def get_processed_documents(self) -> List[Dict[str, Any]]:
        """Get all processed documents with metadata"""
        documents = []
        
        for json_file in self.processed_path.glob(PROCESSED_FILE_PATTERN):
            try:
                document_data = self._load_document(json_file)
                if document_data:
                    documents.append(document_data)
            except Exception as e:
                print(f"Warning: Could not load {json_file}: {e}")
        
        return documents
    
    def save_uploaded_file(self, file_content: bytes, filename: str) -> Path:
        """Save uploaded file to upload directory"""
        if not self._is_supported_file(filename):
            raise DocumentProcessingError(f"סוג קובץ לא נתמך: {filename}")
        
        file_path = self.upload_path / filename
        
        try:
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            self._log_operation("file_upload", filename, "success")
            return file_path
            
        except Exception as e:
            self._log_operation("file_upload", filename, "error", str(e))
            raise DocumentProcessingError(f"שגיאה בשמירת קובץ: {e}")
    
    def process_uploaded_file(self, file_path: Path) -> Dict[str, Any]:
        """Process uploaded PDF file and extract real content"""
        if not file_path.exists():
            raise DocumentProcessingError(f"קובץ לא נמצא: {file_path}")
        
        try:
            import streamlit as st
            
            # חילוץ תוכן PDF אמיתי
            chunks = self._extract_pdf_content(file_path)
            
            processed_data = {
                'filename': file_path.name,
                'file_path': str(file_path),
                'processed_at': datetime.now().isoformat(),
                'status': 'completed',
                'document_type': self._detect_document_type(file_path.name),
                'file_size_mb': file_path.stat().st_size / (1024 * 1024),
                'chunks': chunks,
                'chunk_count': len(chunks),
                'extraction_method': 'PyPDF2' if chunks else 'fallback'
            }
            
            # Save processed data
            output_file = self.processed_path / f"{file_path.stem}_processed.json"
            self._save_processed_document(output_file, processed_data)
            
            st.success(f"✅ עובד בהצלחה: {len(chunks)} קטעי טקסט נחלצו")
            
            self._log_operation("file_processing", file_path.name, "success")
            return processed_data
            
        except Exception as e:
            self._log_operation("file_processing", file_path.name, "error", str(e))
            raise DocumentProcessingError(f"שגיאה בעיבוד קובץ: {e}")

    

    def _extract_pdf_content(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract actual content from PDF file"""
        chunks = []
        
        try:
            # נסה PyPDF2 קודם
            import PyPDF2
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    text = page.extract_text()
                    
                    if text.strip():  # רק אם יש טקסט אמיתי
                        # חלק לקטעים של ~500 מילים
                        text_chunks = self._split_text_into_chunks(text, max_words=500)
                        
                        for i, chunk_text in enumerate(text_chunks):
                            if len(chunk_text.strip()) > 50:  # רק טקסט משמעותי
                                chunks.append({
                                    'id': len(chunks) + 1,
                                    'text': chunk_text.strip(),
                                    'page': page_num,
                                    'chunk_in_page': i + 1,
                                    'metadata': {
                                        'source_file': file_path.name,
                                        'chunk_index': len(chunks) + 1,
                                        'processing_method': 'PyPDF2',
                                        'page_number': page_num
                                    }
                                })
            
            return chunks
            
        except ImportError:
            import streamlit as st
            st.warning("⚠️ PyPDF2 לא מותקן - מתחילן להתקנה אוטומטית")
            
            try:
                import subprocess
                subprocess.check_call(['pip', 'install', 'PyPDF2'])
                st.success("✅ PyPDF2 הותקן - נסה שוב")
                return self._extract_pdf_content(file_path)  # נסה שוב
            except:
                st.error("❌ לא ניתן להתקין PyPDF2 - משתמש בפתרון חלופי")
                return self._create_fallback_chunks(file_path)
        
        except Exception as e:
            import streamlit as st
            st.warning(f"⚠️ שגיאה בחילוץ PDF: {e} - משתמש בפתרון חלופי")
            return self._create_fallback_chunks(file_path)



    def _split_text_into_chunks(self, text: str, max_words: int = 500) -> List[str]:
        """Split text into manageable chunks"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), max_words):
            chunk = ' '.join(words[i:i + max_words])
            chunks.append(chunk)
        
        return chunks

    def _create_fallback_chunks(self, file_path: Path) -> List[Dict[str, Any]]:
        """Create basic chunks when PDF extraction fails"""
        return [{
            'id': 1,
            'text': f'מסמך PDF: {file_path.name} - לא ניתן היה לחלץ טקסט אוטומטית. ייתכן שהקובץ סרוק או מוגן.',
            'page': 1,
            'metadata': {
                'source_file': file_path.name,
                'chunk_index': 1,
                'processing_method': 'fallback',
                'note': 'failed_pdf_extraction'
            }
        }]



    
    def get_document_statistics(self) -> Dict[str, Any]:
        """Get comprehensive document statistics"""
        uploaded_files = self.get_uploaded_files()
        processed_docs = self.get_processed_documents()
        
        stats = {
            'uploaded_count': len(uploaded_files),
            'processed_count': len(processed_docs),
            'processing_rate': 0,
            'total_chunks': 0,
            'total_size_mb': 0,
            'document_types': {},
            'last_upload': None,
            'last_processing': None
        }
        
        # Calculate processing rate
        if stats['uploaded_count'] > 0:
            stats['processing_rate'] = stats['processed_count'] / stats['uploaded_count']
        
        # Calculate total chunks and categorize by type
        for doc in processed_docs:
            chunks = doc.get('chunks', [])
            stats['total_chunks'] += len(chunks)
            stats['total_size_mb'] += doc.get('file_size_mb', 0)
            
            doc_type = doc.get('document_type', 'לא ידוע')
            stats['document_types'][doc_type] = stats['document_types'].get(doc_type, 0) + 1
        
        # Get last upload/processing times
        if uploaded_files:
            latest_upload = max(uploaded_files, key=lambda f: f.stat().st_mtime)
            stats['last_upload'] = datetime.fromtimestamp(latest_upload.stat().st_mtime).isoformat()
        
        if processed_docs:
            latest_processed = max(processed_docs, key=lambda d: d.get('processed_at', ''))
            stats['last_processing'] = latest_processed.get('processed_at')
        
        return stats
    
    def search_documents(self, query: str) -> List[Dict[str, Any]]:
        """Search through processed documents"""
        results = []
        processed_docs = self.get_processed_documents()
        
        query_lower = query.lower()
        
        for doc in processed_docs:
            for chunk in doc.get('chunks', []):
                chunk_text = chunk.get('text', '').lower()
                
                if self._is_relevant_chunk(query_lower, chunk_text):
                    relevance_score = self._calculate_relevance(query_lower, chunk_text)
                    
                    results.append({
                        'file': doc.get('filename', 'לא ידוע'),
                        'document_type': doc.get('document_type', 'מסמך'),
                        'chunk_index': chunk.get('id', 0),
                        'content': chunk.get('text', '')[:500] + "...",
                        'relevance_score': relevance_score,
                        'source_metadata': {
                            'processed_at': doc.get('processed_at'),
                            'file_size_mb': doc.get('file_size_mb', 0)
                        }
                    })
        
        # Sort by relevance
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        return results
    
    def get_all_document_content(self) -> str:
        """Get all document content as single string for AI processing"""
        all_content = []
        processed_docs = self.get_processed_documents()
        
        for doc in processed_docs:
            doc_name = doc.get('filename', 'מסמך')
            doc_content = f"\n\n=== מתוך {doc_name} ===\n"
            
            for chunk in doc.get('chunks', []):
                chunk_text = chunk.get('text', '')
                if chunk_text.strip():
                    doc_content += chunk_text + "\n"
            
            all_content.append(doc_content)
        
        return "\n".join(all_content)
    
    def _load_document(self, json_file: Path) -> Optional[Dict[str, Any]]:
        """Load document from JSON file"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    
    def _save_processed_document(self, output_file: Path, data: Dict[str, Any]) -> None:
        """Save processed document data"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _is_supported_file(self, filename: str) -> bool:
        """Check if file type is supported"""
        return any(filename.lower().endswith(f'.{ext}') for ext in SUPPORTED_FILE_TYPES)
    
    def _detect_document_type(self, filename: str) -> str:
        """Detect document type from filename - basic implementation"""
        filename_lower = filename.lower()
        
        if any(term in filename_lower for term in ['תביעה', 'lawsuit', 'claim']):
            return 'כתב תביעה'
        elif any(term in filename_lower for term in ['הגנה', 'defense', 'response']):
            return 'כתב הגנה'
        elif any(term in filename_lower for term in ['חוזה', 'contract', 'agreement']):
            return 'חוזה'
        elif any(term in filename_lower for term in ['עדות', 'witness', 'testimony']):
            return 'עדות'
        else:
            return 'מסמך משפטי'
    
    def _create_dummy_chunks(self, file_path: Path) -> List[Dict[str, Any]]:
        """Create dummy chunks - placeholder for real PDF processing"""
        return [
            {
                'id': 1,
                'text': f'תוכן מעובד מהמסמך {file_path.name}. זהו תוכן דמה שיוחלף בעיבוד PDF אמיתי.',
                'page': 1,
                'metadata': {
                    'source_file': file_path.name,
                    'chunk_index': 1,
                    'processing_method': 'dummy'
                }
            }
        ]
    
    def _is_relevant_chunk(self, query: str, chunk_text: str) -> bool:
        """Check if chunk is relevant to query"""
        # Basic keyword matching
        query_words = query.split()
        return any(word in chunk_text for word in query_words if len(word) > 2)
    
    def _calculate_relevance(self, query: str, chunk_text: str) -> float:
        """Calculate relevance score"""
        query_words = set(query.split())
        text_words = set(chunk_text.split())
        
        if not query_words:
            return 0.0
        
        intersection = query_words.intersection(text_words)
        return len(intersection) / len(query_words)
    
    def _log_operation(self, operation: str, filename: str, status: str, details: str = "") -> None:
        """Log operation to metadata"""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'operation': operation,
                'filename': filename,
                'status': status,
                'details': details
            }
            
            log_file = self.metadata_path / f"operations_{datetime.now().strftime('%Y%m%d')}.json"
            
            # Append to daily log file
            logs = []
            if log_file.exists():
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        logs = json.load(f)
                except Exception:
                    logs = []
            
            logs.append(log_entry)
            
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Warning: Could not log operation: {e}")
