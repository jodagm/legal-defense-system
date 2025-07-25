"""
Application constants - centralized configuration
"""
from pathlib import Path

# Application metadata
APP_TITLE = "מערכת הגנה משפטית חכמה"
APP_VERSION = "3.0.0"
APP_ICON = "🏛️"

# API configuration
CLAUDE_MODEL = "claude-3-haiku-20240307"
CLAUDE_FALLBACK_MODELS = ["claude-3-sonnet-20240229"]

# File system
DATA_DIR = Path("data")
REQUIRED_DIRECTORIES = [
    DATA_DIR / "uploaded_documents",
    DATA_DIR / "processed", 
    DATA_DIR / "summaries",
    DATA_DIR / "metadata",
    DATA_DIR / "logs"
]

# UI constants
MAX_DISPLAY_ITEMS = 10
MAX_FILE_SIZE_MB = 50
QUERY_HISTORY_LIMIT = 20

# Search configuration
DEFAULT_SIMILARITY_THRESHOLD = 0.2
MAX_SEARCH_RESULTS = 15
SEARCH_TIMEOUT_SECONDS = 30

# Messages
MESSAGES = {
    'no_documents': "📁 לא נמצאו מסמכים מעובדים",
    'upload_success': "✅ קבצים הועלו בהצלחה",
    'processing_error': "❌ שגיאה בעיבוד הקובץ",
    'api_unavailable': "❌ שירות AI לא זמין כרגע"
}

# File patterns
SUPPORTED_FILE_TYPES = ['pdf']
PROCESSED_FILE_PATTERN = "*_processed.json"
SUMMARY_FILE_PATTERN = "*_summary.json"
