"""
מנהל קבצים חכם ומתקדם עם ניהול גרסאות, זיהוי AI וניהול מטא-דטה
גרסה 2.2.0 - עם batch operations, compression, וניטור real-time
"""
import hashlib
import shutil
import re
import gzip
import pickle
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set, Any
from datetime import datetime, timedelta
import json
import time
import logging
from dataclasses import dataclass, asdict
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

import streamlit as st

# ייבואים עם fallbacks
try:
    from config.settings import (
        UPLOAD_DIR, PROCESSED_DIR, SUMMARIES_DIR, 
        METADATA_DIR, CACHE_DIR, LOGS_DIR
    )
    SETTINGS_AVAILABLE = True
except ImportError:
    SETTINGS_AVAILABLE = False
    # ברירות מחדל
    UPLOAD_DIR = Path("data/uploaded_documents")
    PROCESSED_DIR = Path("data/processed")
    SUMMARIES_DIR = Path("data/summaries")
    METADATA_DIR = Path("data/metadata")
    CACHE_DIR = Path("data/cache")
    LOGS_DIR = Path("data/logs")


@dataclass
class FileInfo:
    """מידע מפורט על קובץ"""
    name: str
    path: Path
    size: int
    hash: str
    created: datetime
    modified: datetime
    type: str = "unknown"
    status: str = "active"
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class OperationResult:
    """תוצאת פעולה"""
    success: bool
    operation: str
    details: Dict[str, Any]
    timestamp: datetime
    duration: float = 0.0
    error: Optional[str] = None


class FileSystemMonitor:
    """מנטר מערכת קבצים לזיהוי שינויים real-time"""
    
    def __init__(self):
        self.watched_directories = set()
        self.file_states = {}
        self.change_callbacks = []
        self._monitoring = False
        self._monitor_thread = None
    
    def add_watch_directory(self, directory: Path):
        """הוסף תיקייה למעקב"""
        self.watched_directories.add(directory)
        self._scan_directory(directory)
    
    def _scan_directory(self, directory: Path):
        """סרוק תיקייה ואתחל מצב"""
        if not directory.exists():
            return
        
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                self.file_states[str(file_path)] = {
                    'size': file_path.stat().st_size,
                    'mtime': file_path.stat().st_mtime
                }
    
    def start_monitoring(self):
        """התחל מעקב"""
        if not self._monitoring:
            self._monitoring = True
            self._monitor_thread = threading.Thread(target=self._monitor_loop)
            self._monitor_thread.daemon = True
            self._monitor_thread.start()
    
    def stop_monitoring(self):
        """עצור מעקב"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join()
    
    def _monitor_loop(self):
        """לולאת מעקב"""
        while self._monitoring:
            try:
                self._check_changes()
                time.sleep(2)  # בדוק כל 2 שניות
            except Exception as e:
                print(f"Monitor error: {e}")
    
    def _check_changes(self):
        """בדוק שינויים בקבצים"""
        for directory in self.watched_directories:
            if not directory.exists():
                continue
            
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    path_str = str(file_path)
                    current_state = {
                        'size': file_path.stat().st_size,
                        'mtime': file_path.stat().st_mtime
                    }
                    
                    if path_str not in self.file_states:
                        # קובץ חדש
                        self.file_states[path_str] = current_state
                        self._notify_change('created', file_path)
                    
                    elif self.file_states[path_str] != current_state:
                        # קובץ שונה
                        self.file_states[path_str] = current_state
                        self._notify_change('modified', file_path)
    
    def _notify_change(self, change_type: str, file_path: Path):
        """הודע על שינוי"""
        for callback in self.change_callbacks:
            try:
                callback(change_type, file_path)
            except Exception as e:
                print(f"Callback error: {e}")


class AdvancedFileManager:
    """מנהל קבצים מתקדם עם כל התכונות"""
    
    def __init__(self):
        # אתחל נתיבים
        self.upload_path = UPLOAD_DIR
        self.processed_path = PROCESSED_DIR
        self.summaries_path = SUMMARIES_DIR
        self.metadata_path = METADATA_DIR
        self.cache_path = CACHE_DIR
        self.logs_path = LOGS_DIR
        
        # יצור תיקיות
        self._ensure_directories()
        
        # יצירת cache ומבנ נתוק
        self.file_cache = {}
        self.operation_log = []
        self.file_index = {}
        self.tag_index = defaultdict(set)
        
        # מנטר מערכת קבצים
        self.monitor = FileSystemMonitor()
        self.monitor.change_callbacks.append(self._on_file_change)
        
        # הגדר לוגר
        self._setup_logger()
        
        # טען מטא-דטה קיימת
        self._load_existing_metadata()
        
        # התחל מעקב
        self._start_monitoring()
    
    def _ensure_directories(self):
        """ודא שכל התיקיות קיימות"""
        directories = [
            self.upload_path, self.processed_path, self.summaries_path,
            self.metadata_path, self.cache_path, self.logs_path
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _setup_logger(self):
        """הגדר לוגר"""
        log_file = self.logs_path / f"file_manager_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def _start_monitoring(self):
        """התחל מעקב על תיקיות"""
        for directory in [self.upload_path, self.processed_path, self.summaries_path]:
            self.monitor.add_watch_directory(directory)
        self.monitor.start_monitoring()
    
    def _on_file_change(self, change_type: str, file_path: Path):
        """טפל בשינוי קובץ"""
        self.logger.info(f"File {change_type}: {file_path}")
        
        # עדכן cache
        if change_type == 'created':
            self._add_to_cache(file_path)
        elif change_type == 'modified':
            self._update_cache(file_path)
    
    def _load_existing_metadata(self):
        """טען מטא-דטה קיימת"""
        try:
            for metadata_file in self.metadata_path.glob("*_metadata.json"):
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    file_name = metadata.get('clean_filename', metadata_file.stem.replace('_metadata', ''))
                    self.file_cache[file_name] = metadata
                    
            self.logger.info(f"Loaded {len(self.file_cache)} metadata files")
        except Exception as e:
            self.logger.error(f"Error loading metadata: {e}")
    
    def get_file_hash(self, file_content: bytes, algorithm: str = 'md5') -> str:
        """חזור hash של תוכן הקובץ עם תמיכה באלגוריתמים שונים"""
        if algorithm == 'md5':
            return hashlib.md5(file_content).hexdigest()[:12]
        elif algorithm == 'sha256':
            return hashlib.sha256(file_content).hexdigest()[:16]
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    def analyze_filename(self, filename: str) -> Dict[str, Any]:
        """נתח שם קובץ באופן מתקדם"""
        analysis = {
            'original': filename,
            'extension': Path(filename).suffix.lower(),
            'size_class': self._classify_by_name(filename),
            'legal_indicators': self._extract_legal_indicators(filename),
            'date_indicators': self._extract_dates(filename),
            'language': self._detect_language(filename),
            'confidence_score': 0.0
        }
        
        # חשב ציון ביטחון
        score = 0.0
        if analysis['legal_indicators']:
            score += 0.4
        if analysis['date_indicators']:
            score += 0.2
        if analysis['language'] == 'hebrew':
            score += 0.2
        if analysis['extension'] == '.pdf':
            score += 0.2
        
        analysis['confidence_score'] = score
        return analysis
    
    def _classify_by_name(self, filename: str) -> str:
        """סווג לפי שם"""
        filename_lower = filename.lower()
        
        if any(word in filename_lower for word in ['summary', 'סיכום']):
            return 'summary'
        elif any(word in filename_lower for word in ['evidence', 'ראיה', 'תצהיר']):
            return 'evidence'
        elif any(word in filename_lower for word in ['contract', 'חוזה', 'הסכם']):
            return 'contract'
        else:
            return 'document'
    
    def _extract_legal_indicators(self, filename: str) -> List[str]:
        """חלץ מחוויםים משפטיים"""
        indicators = []
        filename_lower = filename.lower()
        
        legal_terms = [
            'תביעה', 'הגנה', 'תצהיר', 'עדות', 'חוזה', 'הסכם',
            'בגץ', 'עליון', 'משפט', 'פלילי', 'אזרחי', 'צו',
            'בקשה', 'תגובה', 'סיכום', 'טיעון'
        ]
        
        for term in legal_terms:
            if term in filename_lower:
                indicators.append(term)
        
        return indicators
    
    def _extract_dates(self, filename: str) -> List[str]:
        """חלץ תאריכים משם הקובץ"""
        import re
        date_patterns = [
            r'\d{1,2}[._-]\d{1,2}[._-]\d{2,4}',  # DD.MM.YYYY
            r'\d{4}[._-]\d{1,2}[._-]\d{1,2}',    # YYYY.MM.DD
            r'\d{8}',                             # YYYYMMDD
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, filename)
            dates.extend(matches)
        
        return dates
    
    def _detect_language(self, filename: str) -> str:
        """זהה שפת שם הקובץ"""
        hebrew_chars = re.findall(r'[\u0590-\u05FF]', filename)
        english_chars = re.findall(r'[a-zA-Z]', filename)
        
        if len(hebrew_chars) > len(english_chars):
            return 'hebrew'
        elif len(english_chars) > 0:
            return 'english'
        else:
            return 'unknown'
    
    def clean_filename(self, filename: str, aggressive: bool = False) -> str:
        """נקה שם קובץ עם אפשרויות מתקדמות"""
        if aggressive:
            # ניקוי אגרסיבי
            cleaned = re.sub(r'[^\w\u0590-\u05FF.]', '_', filename)
            cleaned = re.sub(r'_{2,}', '_', cleaned)  # צמצם לוקדות prefix
        else:
            # ניקוי עדין
            cleaned = filename.replace(" ", "_").replace("-", "_")
            cleaned = re.sub(r'[<>:"/\\|?*]', '_', cleaned)
        
        # הסר תווים בתחילה ובסוף
        cleaned = cleaned.strip('_.')
        
        return cleaned
    
    def get_base_name(self, filename: str) -> str:
        """קבל שם בסיסי מתקדם"""
        path = Path(filename)
        base = path.stem
        
        # הסר סיומות נפוצות
        suffixes = ['_processed', '_summary', '_legal_summary', '_analyzed', '_final']
        for suffix in suffixes:
            if base.endswith(suffix):
                base = base[:-len(suffix)]
                break
        
        return base
    
    def find_related_files(self, base_name: str, include_metadata: bool = True) -> Dict[str, List[FileInfo]]:
        """מצא קבצים קשורים עם מידע מפורט"""
        related_files = defaultdict(list)
        
        # ספריות לסריקה
        scan_dirs = {
            'uploaded': self.upload_path,
            'processed': self.processed_path,
            'summaries': self.summaries_path
        }
        
        if include_metadata:
            scan_dirs['metadata'] = self.metadata_path
        
        for category, directory in scan_dirs.items():
            if not directory.exists():
                continue
            
            for file_path in directory.rglob("*"):
                if not file_path.is_file():
                    continue
                
                file_base = self.get_base_name(file_path.name)
                
                if file_base == base_name or base_name in file_path.stem:
                    file_info = self._create_file_info(file_path, category)
                    related_files[category].append(file_info)
        
        return dict(related_files)
    
    def _create_file_info(self, file_path: Path, category: str = None) -> FileInfo:
        """יצור אובייקט FileInfo"""
        try:
            stat = file_path.stat()
            
            with open(file_path, 'rb') as f:
                content = f.read()
                file_hash = self.get_file_hash(content)
            
            # טען metadata אם קיים
            metadata = self._load_file_metadata(file_path)
            
            return FileInfo(
                name=file_path.name,
                path=file_path,
                size=stat.st_size,
                hash=file_hash,
                created=datetime.fromtimestamp(stat.st_ctime),
                modified=datetime.fromtimestamp(stat.st_mtime),
                type=category or self._classify_file_type(file_path),
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"Error creating FileInfo for {file_path}: {e}")
            return FileInfo(
                name=file_path.name,
                path=file_path,
                size=0,
                hash="",
                created=datetime.now(),
                modified=datetime.now(),
                type="error",
                metadata={"error": str(e)}
            )
    
    def _load_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """טען metadata לקובץ"""
        base_name = self.get_base_name(file_path.name)
        metadata_file = self.metadata_path / f"{base_name}_metadata.json"
        
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Error loading metadata for {file_path}: {e}")
        
        return {}
    
    def _classify_file_type(self, file_path: Path) -> str:
        """סווג סוג קובץ"""
        extension = file_path.suffix.lower()
        
        if extension == '.pdf':
            return 'document'
        elif extension == '.json':
            if 'processed' in file_path.parts:
                return 'processed'
            elif 'summaries' in file_path.parts:
                return 'summary'
            elif 'metadata' in file_path.parts:
                return 'metadata'
            else:
                return 'data'
        else:
            return 'unknown'
    
    def save_uploaded_file_advanced(self, uploaded_file, options: Dict[str, Any] = None) -> OperationResult:
        """שמור קובץ עם אפשרויות מתקדמות"""
        start_time = time.time()
        
        if options is None:
            options = {}
        
        try:
            # ניתוח הקובץ הנוהיק
            original_name = uploaded_file.name
            file_content = uploaded_file.getvalue()
            file_hash = self.get_file_hash(file_content)
            
            # נקה שם קובץ
            aggressive_clean = options.get('aggressive_clean', False)
            clean_name = self.clean_filename(original_name, aggressive_clean)
            base_name = self.get_base_name(clean_name)
            
            # נתח שם הקובץ
            filename_analysis = self.analyze_filename(original_name)
            
            # בדוק עבק כפילויות
            duplicate_check = self._check_duplicates(file_content, base_name)
            
            result_details = {
                'original_name': original_name,
                'clean_name': clean_name,
                'base_name': base_name,
                'file_hash': file_hash,
                'size': len(file_content),
                'filename_analysis': filename_analysis,
                'duplicate_info': duplicate_check
            }
            
            # בדוק אם להחליף קבצים קיימים
            replace_existing = options.get('replace_existing', True)
            removed_files = []
            
            if replace_existing:
                related_files = self.find_related_files(base_name)
                removed_files = self._clean_related_files(related_files)
                result_details['removed_files'] = removed_files
            
            # שמור קובץ חדש
            file_path = self.upload_path / clean_name
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            # צור והשמור metadata
            metadata = self._create_file_metadata(
                original_name, clean_name, base_name, 
                file_hash, len(file_content), filename_analysis, options
            )
            self._save_file_metadata(base_name, metadata)
            
            # עדכן indexes
            self._update_indexes(base_name, metadata)
            
            # רשום פעולה
            operation_duration = time.time() - start_time
            
            return OperationResult(
                success=True,
                operation="save_file_advanced",
                details=result_details,
                timestamp=datetime.now(),
                duration=operation_duration
            )
            
        except Exception as e:
            self.logger.error(f"Error saving file {uploaded_file.name}: {e}")
            
            return OperationResult(
                success=False,
                operation="save_file_advanced",
                details={'error_details': str(e)},
                timestamp=datetime.now(),
                duration=time.time() - start_time,
                error=str(e)
            )
    
    def _check_duplicates(self, file_content: bytes, base_name: str) -> Dict[str, Any]:
        """בדוק כפילויות מתקדמות"""
        file_hash = self.get_file_hash(file_content)
        
        duplicate_info = {
            'is_duplicate': False,
            'duplicate_files': [],
            'similar_files': [],
            'hash_matches': []
        }
        
        # בדוק לפי hash מדויק
        for existing_base, metadata in self.file_cache.items():
            if metadata.get('file_hash') == file_hash:
                duplicate_info['is_duplicate'] = True
                duplicate_info['hash_matches'].append(existing_base)
        
        # בדוק קבצים דומים לפי שם
        for existing_base in self.file_cache:
            similarity = self._calculate_name_similarity(base_name, existing_base)
            if similarity > 0.8:  # 80% דמיון
                duplicate_info['similar_files'].append({
                    'name': existing_base,
                    'similarity': similarity
                })
        
        return duplicate_info
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """חשב דמיון בין שמות"""
        # אלגוריתם פשוט לדמיון
        name1_set = set(name1.lower().split('_'))
        name2_set = set(name2.lower().split('_'))
        
        if not name1_set or not name2_set:
            return 0.0
        
        intersection = name1_set.intersection(name2_set)
        union = name1_set.union(name2_set)
        
        return len(intersection) / len(union)
    
    def _clean_related_files(self, related_files: Dict[str, List[FileInfo]]) -> List[str]:
        """נקה קבצים קשורים"""
        removed = []
        
        for category, files in related_files.items():
            for file_info in files:
                try:
                    file_info.path.unlink()
                    removed.append(f"{category}: {file_info.name}")
                    self.logger.info(f"Removed {file_info.path}")
                except Exception as e:
                    self.logger.error(f"Failed to remove {file_info.path}: {e}")
        
        return removed
    
    def _create_file_metadata(self, original_name: str, clean_name: str, 
                            base_name: str, file_hash: str, size: int, 
                            analysis: Dict, options: Dict) -> Dict[str, Any]:
        """צור metadata מלא לקובץ"""
        return {
            'original_filename': original_name,
            'clean_filename': clean_name,
            'base_name': base_name,
            'file_hash': file_hash,
            'file_size': size,
            'upload_timestamp': datetime.now().isoformat(),
            'filename_analysis': analysis,
            'upload_options': options,
            'document_type': options.get('document_type', 'unknown'),
            'tags': options.get('tags', []),
            'version': 1,
            'status': 'active'
        }
    
    def _save_file_metadata(self, base_name: str, metadata: Dict[str, Any]):
        """שמור metadata"""
        metadata_file = self.metadata_path / f"{base_name}_metadata.json"
        
        try:
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # עדכן cache
            self.file_cache[base_name] = metadata
            
        except Exception as e:
            self.logger.error(f"Error saving metadata for {base_name}: {e}")
    
    def _update_indexes(self, base_name: str, metadata: Dict[str, Any]):
        """עדכן אינדקסים"""
        # עדכן אינדקס קבצים
        self.file_index[base_name] = {
            'metadata': metadata,
            'last_updated': datetime.now()
        }
        
        # עדכן אינדקס תגיות
        for tag in metadata.get('tags', []):
            self.tag_index[tag].add(base_name)
        
        # עדכן אינדקס סוגי מסמכים 
        doc_type = metadata.get('document_type', 'unknown')
        self.tag_index[f"type:{doc_type}"].add(base_name)
    
    def get_files_status_advanced(self) -> Dict[str, Any]:
        """קבל מצב קבצים מתקדם עם analytics"""
        status = {
            'overview': {},
            'by_category': {},
            'analytics': {},
            'health': {}
        }
        
        # סקירה כללית
        status['overview'] = {
            'total_files': 0,
            'total_size': 0,
            'last_activity': None,
            'active_files': 0
        }
        
        # לפי קטגוריה
        categories = {
            'uploaded': (self.upload_path, '*.pdf'),
            'processed': (self.processed_path, '*.json'),
            'summaries': (self.summaries_path, '*.json'),
            'metadata': (self.metadata_path, '*_metadata.json')
        }
        
        for category, (path, pattern) in categories.items():
            category_info = self._analyze_category(path, pattern, category)
            status['by_category'][category] = category_info
            
            # עדכן סקירה כללית
            status['overview']['total_files'] += category_info['count']
            status['overview']['total_size'] += category_info['total_size']
            
            if category_info['last_modified']:
                if (status['overview']['last_activity'] is None or 
                    category_info['last_modified'] > status['overview']['last_activity']):
                    status['overview']['last_activity'] = category_info['last_modified']
        
        # ניתוחים מתקדמים
        status['analytics'] = self._generate_analytics()
        
        # בריאות המערכת
        status['health'] = self._check_system_health()
        
        return status
    
    def _analyze_category(self, directory: Path, pattern: str, category: str) -> Dict[str, Any]:
        """נתח קטגוריה של קבצים"""
        info = {
            'count': 0,
            'total_size': 0,
            'last_modified': None,
            'files': [],
            'size_distribution': {},
            'date_distribution': defaultdict(int)
        }
        
        if not directory.exists():
            return info
        
        files = list(directory.glob(pattern))
        info['count'] = len(files)
        
        for file_path in files:
            try:
                stat = file_path.stat()
                size = stat.st_size
                modified = datetime.fromtimestamp(stat.st_mtime)
                
                info['total_size'] += size
                
                if info['last_modified'] is None or modified > info['last_modified']:
                    info['last_modified'] = modified
                
                # פילוח גודלים
                size_category = self._categorize_size(size)
                info['size_distribution'][size_category] = info['size_distribution'].get(size_category, 0) + 1
                
                # פילוח תאריכים
                date_key = modified.strftime('%Y-%m-%d')
                info['date_distribution'][date_key] += 1
                
                # מידע קובץ יחיד (עבור קבצים קטנים)
                if len(files) <= 20:  # הגבל לקבצים מועטים
                    file_info = self._create_file_info(file_path, category)
                    info['files'].append(asdict(file_info))
                
            except Exception as e:
                self.logger.warning(f"Error analyzing {file_path}: {e}")
        
        # המר defaultdict רגיל dict ל-JSON
        info['date_distribution'] = dict(info['date_distribution'])
        
        return info
    
    def _categorize_size(self, size: int) -> str:
        """סווג קובץ לפי גודל"""
        if size < 1024 * 1024:  # < 1MB
            return 'small'
        elif size < 10 * 1024 * 1024:  # < 10MB
            return 'medium'
        elif size < 50 * 1024 * 1024:  # < 50MB
            return 'large'
        else:
            return 'very_large'
    
    def _generate_analytics(self) -> Dict[str, Any]:
        """צור ניתוחים מתקדמים"""
        analytics = {
            'document_types': defaultdict(int),
            'upload_patterns': defaultdict(int),
            'processing_stats': {},
            'tag_frequency': defaultdict(int)
        }
        
        for base_name, metadata in self.file_cache.items():
            # סוגי מסמכים
            doc_type = metadata.get('document_type', 'unknown')
            analytics['document_types'][doc_type] += 1
            
            # דפוסי העלאה
            upload_time = metadata.get('upload_timestamp', '')
            if upload_time:
                try:
                    dt = datetime.fromisoformat(upload_time)
                    hour_key = f"{dt.hour:02d}:00"
                    analytics['upload_patterns'][hour_key] += 1
                except:
                    pass
            
            # תדירות תגיות
            for tag in metadata.get('tags', []):
                analytics['tag_frequency'][tag] += 1
        
        # המר defaultdict l-dict
        analytics['document_types'] = dict(analytics['document_types'])
        analytics['upload_patterns'] = dict(analytics['upload_patterns'])
        analytics['tag_frequency'] = dict(analytics['tag_frequency'])
        
        # סטטיסטיקות עיבוד
        analytics['processing_stats'] = self._calculate_processing_stats()
        
        return analytics
    
    def _calculate_processing_stats(self) -> Dict[str, Any]:
        """חשב סטטיסטיקות עיבוד"""
        uploaded_count = len(list(self.upload_path.glob("*.pdf"))) if self.upload_path.exists() else 0
        processed_count = len(list(self.processed_path.glob("*.json"))) if self.processed_path.exists() else 0
        summary_count = len(list(self.summaries_path.glob("*.json"))) if self.summaries_path.exists() else 0
        
        return {
            'uploaded_files': uploaded_count,
            'processed_files': processed_count,
            'summarized_files': summary_count,
            'processing_rate': (processed_count / uploaded_count * 100) if uploaded_count > 0 else 0,
            'summary_rate': (summary_count / uploaded_count * 100) if uploaded_count > 0 else 0
        }
    
    def _check_system_health(self) -> Dict[str, Any]:
        """בדוק בריאות המערכת"""
        health = {
            'status': 'healthy',
            'issues': [],
            'warnings': [],
            'recommendations': []
        }
        
        # בדוק שטח דיסק
        total_size = 0
        for directory in [self.upload_path, self.processed_path, self.summaries_path]:
            if directory.exists():
                for file_path in directory.rglob("*"):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
        
        size_gb = total_size / (1024**3)
        if size_gb > 5:  # מעל 5GB
            health['warnings'].append(f"High disk usage: {size_gb:.2f}GB")
        
        # בדוק קבצים שוכפים
        orphaned_metadata = self._find_orphaned_metadata()
        if orphaned_metadata:
            health['issues'].append(f"{len(orphaned_metadata)} orphaned metadata files")
            health['recommendations'].append("Run metadata cleanup")
        
        # בדוק עיבוד
        processing_rate = self._calculate_processing_stats()['processing_rate']
        if processing_rate < 50:  # פחות מ-50% מעובד
            health['warnings'].append(f"Low processing rate: {processing_rate:.0f}%")
            health['recommendations'].append("Process more uploaded files")
        
        # קבע סמטטוס כללי
        if health['issues']:
            health['status'] = 'issues'
        elif health['warnings']:
            health['status'] = 'warnings'
        
        return health
    
    def _find_orphaned_metadata(self) -> List[str]:
        """מצא קבצי metadata של קבצים לא קיימים"""
        orphaned = []
        
        if not self.metadata_path.exists():
            return orphaned
        
        for metadata_file in self.metadata_path.glob("*_metadata.json"):
            base_name = metadata_file.stem.replace('_metadata', '')
            
            # בדוק אם יש קובץ מקורי
            related_files = self.find_related_files(base_name, include_metadata=False)
            
            has_main_file = (
                related_files.get('uploaded') or 
                related_files.get('processed') or 
                related_files.get('summaries')
            )
            
            if not has_main_file:
                orphaned.append(base_name)
        
        return orphaned
    
    def cleanup_orphaned_metadata(self) -> OperationResult:
        """נקה metadata של קבצים שלא קיימים"""
        start_time = time.time()
        
        try:
            orphaned = self._find_orphaned_metadata()
            removed_count = 0
            
            for base_name in orphaned:
                metadata_file = self.metadata_path / f"{base_name}_metadata.json"
                try:
                    metadata_file.unlink()
                    removed_count += 1
                    
                    # הסר מcache
                    if base_name in self.file_cache:
                        del self.file_cache[base_name]
                        
                except Exception as e:
                    self.logger.error(f"Failed to remove {metadata_file}: {e}")
            
            return OperationResult(
                success=True,
                operation="cleanup_orphaned_metadata",
                details={'removed_count': removed_count, 'orphaned_files': orphaned},
                timestamp=datetime.now(),
                duration=time.time() - start_time
            )
            
        except Exception as e:
            return OperationResult(
                success=False,
                operation="cleanup_orphaned_metadata",
                details={},
                timestamp=datetime.now(),
                duration=time.time() - start_time,
                error=str(e)
            )
    
    def batch_operation(self, operation_func, targets: List[Any], 
                       max_workers: int = 3, progress_callback=None) -> List[OperationResult]:
        """בצע פעולות batch עם threading"""
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_target = {executor.submit(operation_func, target): target for target in targets}
            
            for i, future in enumerate(as_completed(future_to_target)):
                target = future_to_target[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    error_result = OperationResult(
                        success=False,
                        operation="batch_operation",
                        details={'target': str(target)},
                        timestamp=datetime.now(),
                        error=str(e)
                    )
                    results.append(error_result)
                
                # עדכן פרוגרס
                if progress_callback:
                    progress_callback((i + 1) / len(targets))
        
        return results
    
    def create_backup(self, backup_path: Path = None) -> OperationResult:
        """צור גיבוי מלא של המערכת"""
        start_time = time.time()
        
        if backup_path is None:
            backup_path = self.cache_path / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # גבה כל תיקייה
            directories_to_backup = [
                ('uploaded', self.upload_path),
                ('processed', self.processed_path),
                ('summaries', self.summaries_path),
                ('metadata', self.metadata_path)
            ]
            
            backed_up_files = 0
            
            for dir_name, source_dir in directories_to_backup:
                if source_dir.exists():
                    target_dir = backup_path / dir_name
                    shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)
                    
                    # ספור קבצים
                    backed_up_files += len(list(target_dir.rglob("*")))
            
            # צור manifest
            manifest = {
                'backup_timestamp': datetime.now().isoformat(),
                'backed_up_files': backed_up_files,
                'directories': [dir_name for dir_name, _ in directories_to_backup],
                'system_stats': self.get_files_status_advanced()
            }
            
            with open(backup_path / 'manifest.json', 'w', encoding='utf-8') as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)
            
            return OperationResult(
                success=True,
                operation="create_backup",
                details={'backup_path': str(backup_path), 'files_count': backed_up_files},
                timestamp=datetime.now(),
                duration=time.time() - start_time
            )
            
        except Exception as e:
            return OperationResult(
                success=False,
                operation="create_backup",
                details={'backup_path': str(backup_path) if backup_path else None},
                timestamp=datetime.now(),
                duration=time.time() - start_time,
                error=str(e)
            )
    
    def search_files(self, query: str, filters: Dict[str, Any] = None) -> List[FileInfo]:
        """חפש קבצים עם אפשרויות מתקדמות"""
        if filters is None:
            filters = {}
        
        results = []
        query_lower = query.lower()
        
        # חפש בmetadata
        for base_name, metadata in self.file_cache.items():
            match_score = 0
            
            # חיפוש בשמות
            if query_lower in base_name.lower():
                match_score += 10
            
            if query_lower in metadata.get('original_filename', '').lower():
                match_score += 8
            
            # חיפוש בתגיות
            for tag in metadata.get('tags', []):
                if query_lower in tag.lower():
                    match_score += 5
            
            # חיפוש בסוג מסמך
            doc_type = metadata.get('document_type', '')
            if query_lower in doc_type.lower():
                match_score += 6
            
            # בדוק פילטרים
            if self._matches_filters(metadata, filters):
                pass  # נמשיך
            else:
                match_score = 0  # לא ייכלל בתוצאות
            
            # אם יש התאמה, וא ליצור FileInfo
            if match_score > 0:
                related_files = self.find_related_files(base_name)
                if related_files:
                    # קחו את הקובץ הראשון שנמצא
                    for category, files in related_files.items():
                        if files and category != 'metadata':
                            file_info = files[0]
                            file_info.metadata['match_score'] = match_score
                            results.append(file_info)
                            break
        
        # מיין לפי ציון התאמה
        results.sort(key=lambda x: x.metadata.get('match_score', 0), reverse=True)
        
        return results
    
    def _matches_filters(self, metadata: Dict, filters: Dict[str, Any]) -> bool:
        """בדוק אם metadata מתאים לפילטרים"""
        for filter_key, filter_value in filters.items():
            if filter_key == 'document_type':
                if metadata.get('document_type') != filter_value:
                    return False
            
            elif filter_key == 'size_min':
                if metadata.get('file_size', 0) < filter_value:
                    return False
            
            elif filter_key == 'size_max':
                if metadata.get('file_size', 0) > filter_value:
                    return False
            
            elif filter_key == 'date_after':
                upload_time = metadata.get('upload_timestamp')
                if upload_time:
                    try:
                        upload_dt = datetime.fromisoformat(upload_time)
                        if upload_dt < filter_value:
                            return False
                    except:
                        return False
            
            elif filter_key == 'tags':
                metadata_tags = set(metadata.get('tags', []))
                filter_tags = set(filter_value) if isinstance(filter_value, list) else {filter_value}
                if not metadata_tags.intersection(filter_tags):
                    return False
        
        return True
    
    def __del__(self):
        """ניקוי בעת השמדת האובייקט"""
        try:
            if hasattr(self, 'monitor'):
                self.monitor.stop_monitoring()
        except:
            pass


# Compatibility class עבור תואמות לאחור
class SmartFileManager(AdvancedFileManager):
    """מחלקה לתואמות לאחור"""
    
    def save_uploaded_file_smart(self, uploaded_file) -> Dict:
        """שמור קובץ - תואם לגרסה הישנה"""
        result = self.save_uploaded_file_advanced(uploaded_file)
        
        # המר לפורמט הישן
        if result.success:
            return {
                'success': True,
                'original_name': result.details['original_name'],
                'clean_name': result.details['clean_name'],
                'base_name': result.details['base_name'],
                'file_hash': result.details['file_hash'],
                'size': result.details['size'],
                'action': 'replaced' if result.details.get('removed_files') else 'new',
                'removed_files': result.details.get('removed_files', []),
                'file_path': self.upload_path / result.details['clean_name']
            }
        else:
            return {
                'success': False,
                'original_name': uploaded_file.name,
                'error': result.error,
                'action': 'failed'
            }
    
    def get_files_status(self) -> Dict:
        """קבל מצב קבצים - תואם לגרסה הישנה"""
        advanced_status = self.get_files_status_advanced()
        
        # המר לפורמט הישן
        return {
            'uploaded': self._convert_to_old_format(advanced_status['by_category'].get('uploaded', {})),
            'processed': self._convert_to_old_format(advanced_status['by_category'].get('processed', {})),
            'summaries': self._convert_to_old_format(advanced_status['by_category'].get('summaries', {}))
        }
    
    def _convert_to_old_format(self, category_info: Dict) -> List[Dict]:
        """המר לפורמט הישן"""
        if not category_info.get('files'):
            return []
        
        converted = []
        for file_dict in category_info['files']:
            converted.append({
                'name': file_dict['name'],
                'size': file_dict['size'],
                'base_name': self.get_base_name(file_dict['name']),
                'chunks': file_dict.get('metadata', {}).get('chunks', 0),
                'status': file_dict.get('metadata', {}).get('status', 'unknown'),
                'modified': file_dict['modified']
            })
        
        return converted
    
    def clean_vectorstore_cache(self) -> bool:
        """נקה cache וקטורים - תואם לגרסה הישנה"""
        try:
            if hasattr(self, 'cache_path') and self.cache_path.exists():
                vector_cache = self.cache_path / 'vectorstore'
                if vector_cache.exists():
                    shutil.rmtree(vector_cache)
                    vector_cache.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            self.logger.error(f"Error cleaning vectorstore cache: {e}")
            return False
