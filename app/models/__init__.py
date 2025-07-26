"""
Data models for legal defense system
"""
from .conversation_models import (
    ResponseRating,
    ConversationContext,
    ConversationEntry,
    ConversationSession
)
from .evidence_models import (
    LegalDNA,
    EvidenceItem,
    EvidenceReport,
    DocumentClassification
)

__all__ = [
    'ResponseRating',
    'ConversationContext', 
    'ConversationEntry',
    'ConversationSession',
    'LegalDNA',
    'EvidenceItem',
    'EvidenceReport',
    'DocumentClassification'
] 