# החלף את app/core/app_factory.py עם זה:
"""
Application factory - clean dependency injection
"""
from typing import Dict, Any

from app.core.legal_app import LegalApp
from app.services.chatbot_service import ChatbotService
from app.services.document_service import DocumentService  
from app.services.search_service import SearchService
from app.components.chatbot_component import ChatbotComponent
from app.components.document_component import DocumentComponent
from app.components.search_component import SearchComponent
from app.components.status_component import StatusComponent


def create_legal_app(dependencies: Dict[str, Any]) -> LegalApp:
    """Create application with clean dependency injection"""
    
    # Create services layer
    chatbot_service = ChatbotService(
        claude_client=dependencies['claude_client'],
        settings=dependencies['settings']
    )
    
    document_service = DocumentService(
        data_paths=dependencies['data_paths']
    )
    
    search_service = SearchService(
        chatbot_service=chatbot_service,
        document_service=document_service
    )
    
    # Create components layer
    chatbot_component = ChatbotComponent(chatbot_service)
    document_component = DocumentComponent(document_service)
    search_component = SearchComponent(search_service)
    status_component = StatusComponent(chatbot_service, document_service)
    
    # Create and return application
    return LegalApp(
        chatbot_component=chatbot_component,
        document_component=document_component,
        search_component=search_component,
        status_component=status_component
    )
