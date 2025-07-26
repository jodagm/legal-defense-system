"""
Conversation Manager - Context-aware conversation with quality control
"""
import sqlite3
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from app.models.conversation_models import (
    ConversationSession,
    ConversationEntry,
    ConversationContext,
    ResponseRating
)
from app.core.error_handler import ApplicationError


class ConversationManager:
    """Manages goal-driven conversation with quality control
    
    Core Innovation: User rates each AI response:
    ✅ High Quality → Add to context verbatim  
    📝 Summarize → Create focused summary
    ❌ Reject → Exclude from future context
    
    Result: Only quality information builds context
    """
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.current_session: Optional[ConversationSession] = None
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for conversation storage"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversation_sessions (
                    session_id TEXT PRIMARY KEY,
                    case_name TEXT,
                    legal_domain TEXT,
                    created_at TEXT,
                    last_activity TEXT,
                    context_data TEXT,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversation_entries (
                    entry_id TEXT PRIMARY KEY,
                    session_id TEXT,
                    query TEXT,
                    ai_response TEXT,
                    rating TEXT,
                    sources TEXT,
                    timestamp TEXT,
                    context_used TEXT,
                    model_used TEXT,
                    processing_time REAL,
                    user_feedback TEXT,
                    FOREIGN KEY (session_id) REFERENCES conversation_sessions (session_id)
                )
            """)
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_session_activity ON conversation_sessions(last_activity)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_entries_session ON conversation_entries(session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_entries_rating ON conversation_entries(rating)")
    
    def start_session(self, case_name: str = "", legal_domain: str = "defamation_defense") -> str:
        """Start new conversation session"""
        session_id = str(uuid.uuid4())
        
        self.current_session = ConversationSession(
            session_id=session_id,
            case_name=case_name,
            legal_domain=legal_domain
        )
        
        self._save_session()
        return session_id
    
    def load_session(self, session_id: str) -> bool:
        """Load existing conversation session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT case_name, legal_domain, created_at, last_activity, context_data, metadata
                    FROM conversation_sessions WHERE session_id = ?
                """, (session_id,))
                
                row = cursor.fetchone()
                if not row:
                    return False
                
                # Load session data
                case_name, legal_domain, created_at, last_activity, context_data, metadata = row
                
                self.current_session = ConversationSession(
                    session_id=session_id,
                    case_name=case_name,
                    legal_domain=legal_domain,
                    created_at=datetime.fromisoformat(created_at),
                    last_activity=datetime.fromisoformat(last_activity),
                    context=ConversationContext.from_dict(json.loads(context_data or "{}")),
                    metadata=json.loads(metadata or "{}")
                )
                
                # Load conversation entries
                cursor = conn.execute("""
                    SELECT entry_id, query, ai_response, rating, sources, timestamp,
                           context_used, model_used, processing_time, user_feedback
                    FROM conversation_entries WHERE session_id = ? ORDER BY timestamp
                """, (session_id,))
                
                for row in cursor.fetchall():
                    entry_data = {
                        'id': row[0],
                        'query': row[1],
                        'ai_response': row[2],
                        'rating': row[3],
                        'sources': json.loads(row[4] or "[]"),
                        'timestamp': row[5],
                        'context_used': row[6] or "",
                        'model_used': row[7] or "",
                        'processing_time': row[8] or 0.0,
                        'user_feedback': row[9]
                    }
                    entry = ConversationEntry.from_dict(entry_data)
                    self.current_session.conversation_entries.append(entry)
                
                return True
                
        except Exception as e:
            raise ApplicationError(f"Failed to load session {session_id}: {e}")
    
    def add_conversation_entry(
        self,
        query: str,
        ai_response: str,
        sources: List[Dict[str, Any]] = None,
        context_used: str = "",
        model_used: str = "",
        processing_time: float = 0.0
    ) -> str:
        """Add new conversation entry"""
        if not self.current_session:
            raise ApplicationError("No active session. Start a session first.")
        
        entry_id = str(uuid.uuid4())
        entry = ConversationEntry(
            id=entry_id,
            query=query,
            ai_response=ai_response,
            sources=sources or [],
            context_used=context_used,
            model_used=model_used,
            processing_time=processing_time
        )
        
        self.current_session.add_entry(entry)
        self._save_entry(entry)
        return entry_id
    
    def rate_response(self, entry_id: str, rating: ResponseRating, user_feedback: str = "") -> bool:
        """Rate AI response and update context accordingly"""
        if not self.current_session:
            return False
        
        # Find the entry
        entry = None
        for e in self.current_session.conversation_entries:
            if e.id == entry_id:
                entry = e
                break
        
        if not entry:
            return False
        
        # Update rating
        entry.rating = rating
        entry.user_feedback = user_feedback
        
        # Update context based on rating
        if rating == ResponseRating.HIGH_QUALITY:
            self.current_session.context.add_high_quality_response(
                entry.ai_response, entry.query
            )
        elif rating == ResponseRating.SUMMARIZE:
            # For now, add as-is; later implement AI summarization
            self.current_session.context.add_summary(
                f"Query: {entry.query}\nKey insight: {entry.ai_response[:500]}..."
            )
        # REJECT and PENDING don't add to context
        
        # Save updates
        self._save_entry(entry)
        self._save_session()
        
        return True
    
    def get_current_context(self, max_tokens: int = 3000) -> str:
        """Get current conversation context for AI prompts"""
        if not self.current_session:
            return ""
        
        return self.current_session.context.get_context_string(max_tokens)
    
    def get_conversation_statistics(self) -> Dict[str, Any]:
        """Get comprehensive conversation statistics"""
        if not self.current_session:
            return {}
        
        stats = self.current_session.get_statistics()
        
        # Add context quality metrics
        context = self.current_session.context
        stats.update({
            'context_quality_items': len(context.high_quality_responses),
            'context_summaries': len(context.summarized_insights),
            'context_key_findings': len(context.key_findings),
            'estimated_context_tokens': context.total_token_estimate
        })
        
        return stats
    
    def get_unrated_entries(self) -> List[ConversationEntry]:
        """Get all unrated conversation entries"""
        if not self.current_session:
            return []
        
        return [
            entry for entry in self.current_session.conversation_entries
            if entry.rating == ResponseRating.PENDING
        ]
    
    def list_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List recent conversation sessions"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT session_id, case_name, legal_domain, last_activity,
                           (SELECT COUNT(*) FROM conversation_entries ce WHERE ce.session_id = cs.session_id) as entry_count
                    FROM conversation_sessions cs
                    ORDER BY last_activity DESC
                    LIMIT ?
                """, (limit,))
                
                sessions = []
                for row in cursor.fetchall():
                    sessions.append({
                        'session_id': row[0],
                        'case_name': row[1] or 'Unnamed Case',
                        'legal_domain': row[2],
                        'last_activity': row[3],
                        'entry_count': row[4]
                    })
                
                return sessions
                
        except Exception as e:
            raise ApplicationError(f"Failed to list sessions: {e}")
    
    def export_session(self, session_id: str = None) -> Dict[str, Any]:
        """Export complete session data for backup or analysis"""
        if session_id:
            if not self.load_session(session_id):
                raise ApplicationError(f"Session {session_id} not found")
        
        if not self.current_session:
            raise ApplicationError("No session to export")
        
        return self.current_session.to_dict()
    
    def _save_session(self):
        """Save current session to database"""
        if not self.current_session:
            return
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO conversation_sessions
                (session_id, case_name, legal_domain, created_at, last_activity, context_data, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                self.current_session.session_id,
                self.current_session.case_name,
                self.current_session.legal_domain,
                self.current_session.created_at.isoformat(),
                self.current_session.last_activity.isoformat(),
                json.dumps(self.current_session.context.to_dict()),
                json.dumps(self.current_session.metadata)
            ))
    
    def _save_entry(self, entry: ConversationEntry):
        """Save conversation entry to database"""
        if not self.current_session:
            return
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO conversation_entries
                (entry_id, session_id, query, ai_response, rating, sources, timestamp,
                 context_used, model_used, processing_time, user_feedback)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.id,
                self.current_session.session_id,
                entry.query,
                entry.ai_response,
                entry.rating.value,
                json.dumps(entry.sources),
                entry.timestamp.isoformat(),
                entry.context_used,
                entry.model_used,
                entry.processing_time,
                entry.user_feedback
            ))
    
    def clear_all_conversations(self) -> Dict[str, Any]:
        """Clear all conversation data and reset database"""
        results = {
            'sessions_deleted': 0,
            'entries_deleted': 0,
            'errors': []
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Count existing data
                cursor = conn.execute("SELECT COUNT(*) FROM conversation_sessions")
                results['sessions_deleted'] = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM conversation_entries") 
                results['entries_deleted'] = cursor.fetchone()[0]
                
                # Clear all data
                conn.execute("DELETE FROM conversation_entries")
                conn.execute("DELETE FROM conversation_sessions")
                conn.commit()
            
            # Reset current session
            self.current_session = None
            
        except Exception as e:
            results['errors'].append(f"Database error during conversation clearing: {e}")
        
        return results 