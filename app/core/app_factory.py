"""
Application factory - enhanced dependency injection with Phase 1 features
"""
from typing import Dict, Any
from pathlib import Path

from app.core.legal_app import LegalApp
from app.core.conversation_manager import ConversationManager
from app.services.chatbot_service import ChatbotService
from app.services.document_service import DocumentService  
from app.services.search_service import SearchService
from app.services.evidence_service import EvidenceService
from app.components.chatbot_component import ChatbotComponent
from app.components.document_component import DocumentComponent
from app.components.search_component import SearchComponent
from app.components.status_component import StatusComponent


def create_legal_app(dependencies: Dict[str, Any]) -> LegalApp:
    """Create application with enhanced dependency injection for Phase 1"""
    
    # Initialize conversation manager
    conversation_db_path = Path(dependencies['data_paths']['conversations'] / 'conversations.db')
    conversation_manager = ConversationManager(conversation_db_path)
    
    # Create evidence service (new in Phase 1)
    evidence_service = EvidenceService(dependencies['data_paths'])
    
    # Create enhanced services layer
    chatbot_service = ChatbotService(
        claude_client=dependencies['claude_client'],
        settings=dependencies['settings'],
        conversation_manager=conversation_manager
    )
    
    document_service = DocumentService(
        data_paths=dependencies['data_paths'],
        evidence_service=evidence_service  # Integration with evidence processing
    )
    
    search_service = SearchService(
        chatbot_service=chatbot_service,
        document_service=document_service
    )
    
    # Create components layer
    chatbot_component = ChatbotComponent(chatbot_service)
    document_component = DocumentComponent(document_service)
    search_component = SearchComponent(search_service)
    status_component = StatusComponent(
        chatbot_service=chatbot_service, 
        document_service=document_service,
        evidence_service=evidence_service,  # Enhanced status monitoring
        conversation_manager=conversation_manager
    )
    
    # Create and return application
    return LegalApp(
        chatbot_component=chatbot_component,
        document_component=document_component,
        search_component=search_component,
        status_component=status_component
    )
