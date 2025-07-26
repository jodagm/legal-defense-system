"""
Conversation management data models
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import json


class ResponseRating(Enum):
    """User rating for AI response quality"""
    HIGH_QUALITY = "high_quality"      # ✅ Add to context verbatim
    SUMMARIZE = "summarize"            # 📝 Create focused summary  
    REJECT = "reject"                  # ❌ Exclude from future context
    PENDING = "pending"                # ⏳ Not yet rated


@dataclass
class ConversationEntry:
    """Single conversation exchange with quality control"""
    id: str
    query: str
    ai_response: str
    rating: ResponseRating = ResponseRating.PENDING
    sources: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    context_used: str = ""
    model_used: str = ""
    processing_time: float = 0.0
    user_feedback: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'id': self.id,
            'query': self.query,
            'ai_response': self.ai_response,
            'rating': self.rating.value,
            'sources': self.sources,
            'timestamp': self.timestamp.isoformat(),
            'context_used': self.context_used,
            'model_used': self.model_used,
            'processing_time': self.processing_time,
            'user_feedback': self.user_feedback
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationEntry':
        """Create from dictionary"""
        return cls(
            id=data['id'],
            query=data['query'],
            ai_response=data['ai_response'],
            rating=ResponseRating(data['rating']),
            sources=data.get('sources', []),
            timestamp=datetime.fromisoformat(data['timestamp']),
            context_used=data.get('context_used', ''),
            model_used=data.get('model_used', ''),
            processing_time=data.get('processing_time', 0.0),
            user_feedback=data.get('user_feedback')
        )


@dataclass
class ConversationContext:
    """Accumulated conversation context with quality filtering"""
    high_quality_responses: List[str] = field(default_factory=list)
    summarized_insights: List[str] = field(default_factory=list)
    key_findings: List[str] = field(default_factory=list)
    legal_precedents: List[str] = field(default_factory=list)
    evidence_references: List[str] = field(default_factory=list)
    total_token_estimate: int = 0
    last_updated: datetime = field(default_factory=datetime.now)
    
    def add_high_quality_response(self, response: str, query: str):
        """Add high-quality response to context"""
        context_entry = f"Q: {query}\nA: {response}"
        self.high_quality_responses.append(context_entry)
        self.total_token_estimate += len(context_entry.split())
        self.last_updated = datetime.now()
    
    def add_summary(self, summary: str):
        """Add summarized insight to context"""
        self.summarized_insights.append(summary)
        self.total_token_estimate += len(summary.split())
        self.last_updated = datetime.now()
    
    def get_context_string(self, max_tokens: int = 3000) -> str:
        """Get formatted context string within token limit"""
        context_parts = []
        current_tokens = 0
        
        # Add key findings first (highest priority)
        for finding in self.key_findings:
            tokens = len(finding.split())
            if current_tokens + tokens > max_tokens:
                break
            context_parts.append(f"📋 Key Finding: {finding}")
            current_tokens += tokens
        
        # Add high-quality responses
        for response in reversed(self.high_quality_responses):  # Most recent first
            tokens = len(response.split())
            if current_tokens + tokens > max_tokens:
                break
            context_parts.append(f"💡 Previous Analysis:\n{response}")
            current_tokens += tokens
        
        # Add summarized insights
        for insight in reversed(self.summarized_insights):
            tokens = len(insight.split())
            if current_tokens + tokens > max_tokens:
                break
            context_parts.append(f"📝 Summary: {insight}")
            current_tokens += tokens
        
        return "\n\n".join(context_parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'high_quality_responses': self.high_quality_responses,
            'summarized_insights': self.summarized_insights,
            'key_findings': self.key_findings,
            'legal_precedents': self.legal_precedents,
            'evidence_references': self.evidence_references,
            'total_token_estimate': self.total_token_estimate,
            'last_updated': self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationContext':
        """Create from dictionary"""
        context = cls()
        context.high_quality_responses = data.get('high_quality_responses', [])
        context.summarized_insights = data.get('summarized_insights', [])
        context.key_findings = data.get('key_findings', [])
        context.legal_precedents = data.get('legal_precedents', [])
        context.evidence_references = data.get('evidence_references', [])
        context.total_token_estimate = data.get('total_token_estimate', 0)
        context.last_updated = datetime.fromisoformat(data['last_updated'])
        return context


@dataclass
class ConversationSession:
    """Complete conversation session with metadata"""
    session_id: str
    case_name: str = ""
    legal_domain: str = "defamation_defense"
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    conversation_entries: List[ConversationEntry] = field(default_factory=list)
    context: ConversationContext = field(default_factory=ConversationContext)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_entry(self, entry: ConversationEntry):
        """Add conversation entry and update metadata"""
        self.conversation_entries.append(entry)
        self.last_activity = datetime.now()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get session statistics"""
        total_entries = len(self.conversation_entries)
        rated_entries = [e for e in self.conversation_entries if e.rating != ResponseRating.PENDING]
        
        rating_counts = {}
        for rating in ResponseRating:
            rating_counts[rating.value] = sum(1 for e in self.conversation_entries if e.rating == rating)
        
        return {
            'total_exchanges': total_entries,
            'rated_exchanges': len(rated_entries),
            'rating_distribution': rating_counts,
            'avg_processing_time': sum(e.processing_time for e in self.conversation_entries) / max(total_entries, 1),
            'context_token_estimate': self.context.total_token_estimate,
            'session_duration_hours': (self.last_activity - self.created_at).total_seconds() / 3600
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'session_id': self.session_id,
            'case_name': self.case_name,
            'legal_domain': self.legal_domain,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'conversation_entries': [entry.to_dict() for entry in self.conversation_entries],
            'context': self.context.to_dict(),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationSession':
        """Create from dictionary"""
        session = cls(
            session_id=data['session_id'],
            case_name=data.get('case_name', ''),
            legal_domain=data.get('legal_domain', 'defamation_defense'),
            created_at=datetime.fromisoformat(data['created_at']),
            last_activity=datetime.fromisoformat(data['last_activity']),
            metadata=data.get('metadata', {})
        )
        
        session.conversation_entries = [
            ConversationEntry.from_dict(entry_data) 
            for entry_data in data.get('conversation_entries', [])
        ]
        
        session.context = ConversationContext.from_dict(data.get('context', {}))
        return session 