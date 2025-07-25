# Legal Defense System - Development Context for Cursor AI

## 🎯 Project Overview
מערכת הגנה משפטית מתקדמת עם AI לניתוח מסמכים משפטיים והכנת אסטרטגיית הגנה.

## 🐛 Current Bugs & Issues

### 1. Import Issues (RESOLVED)
- **Problem**: `ModuleNotFoundError: No module named 'sklearn'`
- **Solution**: Created simplified version of chatbot without sklearn dependency
- **Status**: ✅ FIXED
- **Files Affected**: `core/chatbot.py`

### 2. Missing Methods (RESOLVED) 
- **Problem**: `'LegalChatBot' object has no attribute 'has_documents'`
- **Solution**: Added `has_documents()` method and safe checking functions
- **Status**: ✅ FIXED
- **Files Affected**: `main.py`, `core/chatbot.py`

### 3. Claude API Model Issues (RESOLVED)
- **Problem**: Error 404 with model `claude-3-sonnet-20240229`
- **Solution**: Updated to `claude-3-5-sonnet-20241022` with fallback models
- **Status**: ✅ FIXED
- **Files Affected**: `main.py`, `core/chatbot.py`

### 4. Legal Prompt Context Missing (RESOLVED)
- **Problem**: AI responses were generic instead of legal-focused
- **Solution**: Added comprehensive legal prompting system with professional context
- **Status**: ✅ FIXED
- **Files Affected**: `main.py`, `core/chatbot.py`

### 5. REMAINING BUGS TO FIX:
🔴 **Bug Status: ACTIVE - NEEDS FIXING**

#### A. Document Reset Issues
- **Problem**: Reset functions don't completely clear document count display
- **Symptoms**: After reset, main page still shows "12 documents" even after deletion
- **Files**: `main.py` - functions `execute_protected_reset()`, `show_main_interface()`

#### B. Session State Persistence
- **Problem**: Streamlit session state not properly clearing cached document info
- **Files**: `main.py` - session management functions

#### C. Search Function Not Finding Documents
- **Problem**: When asking "מהן הטענות העיקריות בכתב התביעה" gets generic Claude response instead of searching uploaded documents
- **Symptoms**: System responds "אני לא יכול לדעת מהן הטענות העיקריות בכתב התביעה מכיוון שלא הוצג בפני כתב תביעה ספציפי"
- **Root Cause**: Search function not properly connecting to uploaded/processed documents
- **Files**: `main.py` - `safe_search_and_respond()`, `manual_document_search()`

## 🏗️ System Architecture

### File Structure

legal_defense_system/ ├── main.py # Main Streamlit app - CONTAINS MOST LOGIC ├── core/ │ ├── init.py │ └── chatbot.py # LegalChatBot class - simplified version without sklearn ├── ui/ │ ├── init.py │ └── sidebar.py # UI components (may have import issues) ├── processors/ │ ├── init.py │ ├── document_processor.py │ └── legal_summary.py # Legal document summarization ├── config/ │ ├── init.py │ └── settings.py # System configuration (cleaned from secrets) ├── data/ # Auto-created directories │ ├── uploaded_documents/ │ ├── processed/ │ ├── summaries/ │ └── metadata/


### Key Components Status
- ✅ `main.py` - Working but has reset & search bugs
- ✅ `core/chatbot.py` - Simplified working version
- ❓ `ui/sidebar.py` - May have import issues
- ❓ `processors/` - Need to verify functionality
- ✅ `config/settings.py` - Clean from secrets

## 🔧 Technical Implementation Details

### Current Working Features
1. **Document Upload** - Users can upload PDF files
2. **Document Tagging** - Legal document type classification
3. **Claude AI Integration** - Working with proper legal context prompts
4. **Basic Search** - Simple text search (not sklearn-dependent)
5. **Legal Prompting** - Professional legal context for AI responses
6. **System Management** - File statistics, cleanup tools

### Legal Prompting System
The system includes a sophisticated legal prompting mechanism:
```python
def create_legal_prompt(query, documents_text, sources_count):
    """Professional legal prompting with proper context"""
    # Defines lawyer persona
    # Sets legal context (preparing defense)
    # Specifies analysis requirements
    # Requests strategic recommendations

    Search Mechanism
Currently using simple text search instead of semantic search:

Basic keyword matching
Legal terminology weighting
Document type awareness
Relevance scoring
🎯 Development Priorities
Immediate Fixes Needed
Fix Document Search Integration 🔴 HIGH PRIORITY

Problem: Search not finding uploaded documents
Expected: When user asks about document content, system should find and analyze uploaded files
Files to check: main.py functions safe_search_and_respond(), manual_document_search()
Fix Reset Functionality 🟡 MEDIUM PRIORITY

Problem: Document count persists after reset
Files: main.py functions in reset section
Verify Document Processing Pipeline 🟡 MEDIUM PRIORITY

Ensure uploaded documents are properly processed and stored
Check processors/ modules
Enhancement Opportunities
Add proper error logging
Implement semantic search (optional sklearn integration)
Add document preview functionality
Improve UI/UX feedback
💡 Development Guidelines
Code Style
Hebrew comments for user-facing features
Professional legal terminology
Error handling with user-friendly messages
Security-first approach (no hardcoded secrets)
Legal Context
All AI responses must include legal professional context
Focus on defense strategy
Identify contradictions and weaknesses
Provide strategic recommendations
Use proper legal citation format
Security
API keys only in .env files
Local document storage only
Input validation for file uploads
Session management security