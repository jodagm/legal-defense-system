# 🏛️ מערכת הגנה משפטית חכמה

מערכת AI מתקדמת לניתוח מסמכים משפטיים והכנת הגנה אסטרטגית

## ✨ תכונות עיקריות

- **📄 ניתוח מסמכים משפטיים**: העלאה ועיבוד אוטומטי של קבצי PDF
- **🏷️ תיוג מתקדם**: זיהוי וסיווג סוגי מסמכים (תביעות, הגנות, תצהירים וכו')
- **🤖 AI משפטי**: בוט Claude מתמחה בניתוח משפטי ומתן עצות אסטרטגיות
- **📋 סיכומים אוטומטיים**: יצירת סיכומים משפטיים מפורטים ומובנים
- **🔍 חיפוש חכם**: מנוע חיפוש היברידי semantic + keyword
- **⚖️ ניתוח אסטרטגי**: זיהוי נקודות חוזק, חולשה וסתירות

## 🚀 התקנה מהירה

```bash
# שכפול הריפוזיטורי
git clone https://github.com/YOUR_USERNAME/legal_defense_system.git
cd legal_defense_system

# יצירת סביבה וירטואלית
python -m venv legal_env
source legal_env/bin/activate  # Linux/Mac
# או legal_env\Scripts\activate  # Windows

# התקנת תלותיות
pip install -r requirements.txt

# הגדרת API key
echo "CLAUDE_API_KEY=your_api_key_here" > .env

# הרצת המערכת
streamlit run main.py

cat > CHANGELOG.md << 'EOF'
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Initial release of Legal Defense System
- Document upload and processing
- Legal document tagging system
- Claude AI integration for legal analysis
- Automatic legal summary generation
- Hybrid search (semantic + keyword)
- Advanced legal prompting system
- Developer tools and system management
- Protected system reset functionality

### Features
- 📄 PDF document processing
- 🏷️ Legal document type classification
- 🤖 AI-powered legal analysis
- 📋 Automated legal summaries
- 🔍 Smart document search
- ⚖️ Strategic analysis and recommendations

## [2.1.0] - 2024-01-XX

### Added
- Advanced legal prompting system
- Strategic analysis capabilities
- Enhanced document type recognition
- Protected system management tools

### Improved
- Better error handling
- More robust document processing
- Enhanced search algorithms

### Fixed
- Import issues with sklearn
- Session state management
- Document loading reliability

## [2.0.0] - 2024-01-XX

### Added
- Complete system rewrite
- Legal document tagging
- Advanced AI integration
- Professional legal context prompting

### Changed
- Modernized codebase
- Improved user interface
- Better system architecture

## [1.0.0] - 2024-01-XX

### Added
- Initial version
- Basic document processing
- Simple AI chat functionality
