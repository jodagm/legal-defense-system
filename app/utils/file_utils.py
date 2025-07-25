"""
File utilities - helper functions for file operations
"""
from pathlib import Path
from typing import List, Optional, Iterator
import json
import shutil
from datetime import datetime


def ensure_directories_exist(directories: List[Path]) -> None:
    """Ensure all directories exist, create if they don't"""
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def count_files_in_directory(directory: Path, pattern: str = "*") -> int:
    """Count files matching pattern in directory"""
    if not directory.exists():
        return 0
    
    try:
        return len(list(directory.glob(pattern)))
    except Exception:
        return 0


def get_directory_size(directory: Path) -> float:
    """Get directory size in MB"""
    if not directory.exists():
        return 0.0
    
    try:
        total_size = sum(
            f.stat().st_size 
            for f in directory.rglob('*') 
            if f.is_file()
        )
        return total_size / (1024 * 1024)  # Convert to MB
    except Exception:
        return 0.0


def safe_read_json(file_path: Path) -> Optional[dict]:
    """Safely read JSON file, return None if failed"""
    if not file_path.exists():
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def safe_write_json(file_path: Path, data: dict) -> bool:
    """Safely write JSON file, return success status"""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception:
        return False
