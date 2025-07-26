"""
Chatbot service - business logic for AI interactions with conversation management
"""
from typing import Optional, Dict, Any, List
import json
import time
from datetime import datetime
from pathlib import Path

from app.config.constants import CLAUDE_MODEL, CLAUDE_FALLBACK_MODELS
from app.core.error_handler import APIError
from app.core.conversation_manager import ConversationManager
from app.models.conversation_models import ResponseRating


class ChatbotService:
    """Service for chatbot operations with context-aware conversation management"""
    
    def __init__(
        self, 
        claude_client: Optional[Any], 
        settings: Dict[str, Any],
        conversation_manager: Optional[ConversationManager] = None
    ):
        self.claude_client = claude_client
        self.settings = settings
        self.conversation_history: List[Dict] = []  # Legacy support
        
        # Initialize conversation manager
        if conversation_manager:
            self.conversation_manager = conversation_manager
        else:
            # Create default conversation manager
            db_path = Path(settings.get('conversation_db_path', 'data/conversations/conversations.db'))
            self.conversation_manager = ConversationManager(db_path)
    
    def is_available(self) -> bool:
        """Check if chatbot service is available"""
        return self.claude_client is not None
    
    def generate_contextual_response(
        self, 
        query: str, 
        document_context: str = "", 
        sources: List[Dict] = None,
        use_conversation_context: bool = True
    ) -> Dict[str, Any]:
        """Generate context-aware AI response with conversation management"""
        if not self.is_available():
            raise APIError("Claude API לא זמין")
        
        start_time = time.time()
        
        # Get conversation context if enabled
        conversation_context = ""
        if use_conversation_context:
            conversation_context = self.conversation_manager.get_current_context()
        
        # Build comprehensive prompt
        prompt = self._build_enhanced_legal_prompt(
            query, 
            document_context, 
            conversation_context,
            sources or []
        )
        
        try:
            response = self._call_claude_api(prompt)
            processing_time = time.time() - start_time
            
            # Ensure we have an active session (auto-start if needed)
            if not self.conversation_manager.current_session:
                self.conversation_manager.start_session("Auto-started Session")
            
            # Add to conversation manager
            entry_id = self.conversation_manager.add_conversation_entry(
                query=query,
                ai_response=response,
                sources=sources or [],
                context_used=f"Doc context: {len(document_context)} chars, Conv context: {len(conversation_context)} chars",
                model_used=self.settings.get('claude_model', CLAUDE_MODEL),
                processing_time=processing_time
            )
            
            result = {
                'answer': response,
                'sources': sources or [],
                'timestamp': datetime.now().isoformat(),
                'model_used': self.settings.get('claude_model', CLAUDE_MODEL),
                'query': query,
                'has_context': bool(document_context or conversation_context),
                'entry_id': entry_id,
                'processing_time': processing_time,
                'conversation_context_used': bool(conversation_context)
            }
            
            # Legacy support
            self._add_to_history(query, result)
            return result
            
        except Exception as e:
            raise APIError(f"שגיאה ביצירת תשובה: {e}")
    
    def generate_response(
        self, 
        query: str, 
        context: str = "", 
        sources: List[Dict] = None
    ) -> Dict[str, Any]:
        """Backward compatibility wrapper for generate_contextual_response"""
        return self.generate_contextual_response(
            query=query,
            document_context=context,
            sources=sources,
            use_conversation_context=True
        )
    
    def generate_simple_response(self, query: str) -> Dict[str, Any]:
        """Generate simple response without document context"""
        if not self.is_available():
            return {
                'answer': "❌ שירות AI לא זמין כרגע. אנא הגדר Claude API key.",
                'sources': [],
                'error': 'api_unavailable'
            }
        
        general_prompt = f"""אתה עורך דין מומחה במשפט ישראלי.

תן תשובה משפטית מקצועית לשאלה הבאה (ללא מסמכים ספציפיים):

{query}

כלול בתשובה:
1. הסבר כללי על הנושא המשפטי
2. עקרונות משפטיים רלוונטיים  
3. נקודות מפתח לבדיקה
4. המלצות כלליות

תן תשובה מקצועית וברורה."""

        try:
            response = self._call_claude_api(general_prompt)
            
            return {
                'answer': f"## תשובה משפטית כללית\n\n{response}\n\n---\n*הערה: תשובה כללית ללא מסמכים ספציפיים*",
                'sources': [],
                'timestamp': datetime.now().isoformat(),
                'model_used': self.settings.get('claude_model', CLAUDE_MODEL),
                'type': 'general_response'
            }
            
        except Exception as e:
            return {
                'answer': f"❌ שגיאה בקבלת תשובה: {e}",
                'sources': [],
                'error': str(e)
            }
    
    def get_conversation_history(self) -> List[Dict]:
        """Get conversation history"""
        return self.conversation_history.copy()
    
    def clear_history(self) -> None:
        """Clear conversation history"""
        self.conversation_history.clear()
        
        # Also clear conversation manager if available
        if hasattr(self, 'conversation_manager') and self.conversation_manager:
            return self.conversation_manager.clear_all_conversations()
        return {'sessions_deleted': 0, 'entries_deleted': 0, 'errors': []}
    
    def rate_response(self, entry_id: str, rating: ResponseRating, feedback: str = "") -> bool:
        """Rate AI response for conversation context building"""
        return self.conversation_manager.rate_response(entry_id, rating, feedback)
    
    def get_conversation_statistics(self) -> Dict[str, Any]:
        """Get conversation quality and usage statistics"""
        return self.conversation_manager.get_conversation_statistics()
    
    def get_unrated_responses(self) -> List[Dict[str, Any]]:
        """Get responses that need user rating"""
        unrated_entries = self.conversation_manager.get_unrated_entries()
        return [
            {
                'entry_id': entry.id,
                'query': entry.query,
                'response_preview': entry.ai_response[:200] + "..." if len(entry.ai_response) > 200 else entry.ai_response,
                'timestamp': entry.timestamp.isoformat(),
                'processing_time': entry.processing_time
            }
            for entry in unrated_entries
        ]
    
    def start_conversation_session(self, case_name: str = "") -> str:
        """Start new conversation session"""
        return self.conversation_manager.start_session(case_name)
    
    def load_conversation_session(self, session_id: str) -> bool:
        """Load existing conversation session"""
        return self.conversation_manager.load_session(session_id)
    
    def list_conversation_sessions(self) -> List[Dict[str, Any]]:
        """List available conversation sessions"""
        return self.conversation_manager.list_sessions()
    
    def _build_enhanced_legal_prompt(
        self, 
        query: str, 
        document_context: str = "",
        conversation_context: str = "",
        sources: List[Dict] = None
    ) -> str:
        """Build enhanced legal prompt with multiple context types"""
        
        # Base legal expertise prompt
        prompt = """אתה יועץ משפטי מומחה בדיני לשון הרע והגנה על זכויות אדם בישראל.
        
התמחויותיך כוללות:
• הגנת אמת - הוכחת נכונות עובדתית של הצהרות
• הגנת תום לב - הוכחת כוונה טובה בסיוע לנפגעי אלימות
• הגנה פרוצדורלית - זיהוי פגמי הליך משפטי

"""
        
        # Add conversation context if available
        if conversation_context.strip():
            prompt += f"""
## הקשר השיחה הקודם:
{conversation_context}

---
"""
        
        # Add document context if available
        if document_context.strip():
            prompt += f"""
## תוכן המסמכים הרלוונטיים:
{document_context}

"""
        
        # Add sources if available
        if sources:
            prompt += "## מקורות תומכים:\n"
            for i, source in enumerate(sources, 1):
                prompt += f"{i}. {source.get('title', 'מסמך')} - {source.get('content', '')[:200]}...\n"
            prompt += "\n"
        
        # Add the user query
        prompt += f"""
## השאלה המשפטית:
{query}

## הנחיות למענה:
1. ספק ניתוח משפטי מקצועי ומדויק
2. התייחס לכל ההקשרים הקיימים (שיחות קודמות ומסמכים)
3. הדגש ראיות חזקות לכל אסטרטגיית הגנה
4. ציין מקורות ספציפיים מהמסמכים
5. הצע צעדים מעשיים והמלצות

תן תשובה מקצועית, מפורטת וברורה:"""
        
        return prompt
    
    def _build_legal_prompt(self, query: str, context: str, sources: List[Dict]) -> str:
        """Build comprehensive legal analysis prompt"""
        sources_text = ""
        if sources:
            sources_text = "\n\nמקורות מהתיק:\n"
            for i, source in enumerate(sources, 1):
                content = source.get('content', '')[:500]
                file_name = source.get('file', 'מקור לא ידוע')
                sources_text += f"\n{i}. מתוך {file_name}:\n{content}\n"
        
        return f"""אתה עורך דין מומחה במשפט אזרחי ופלילי דובר עברית רהוטה.

הוראה: נתח את התוכן הבא מתיק משפטי וענה על השאלה בצורה מקצועית.

השאלה: {query}

תוכן מהתיק:
{context}
{sources_text}

הוראות לתשובה:
1. נתח את המידע מהתיק בצורה משפטית מקצועית
2. זהה נקודות חוזק וחולשה רלוונטיות  
3. הצע המלצות אסטרטגיות להגנה
4. השתמש בציטוטים ישירים מהמסמכים כשרלוונטי
5. תן דעה משפטית מבוססת ומנומקת
6. ציין אם יש מידע חסר או צורך בבירור נוסף

תן תשובה מפורטה, מקצועית ומובנת."""
    
    def _call_claude_api(self, prompt: str) -> str:
        """Call Claude API with fallback models"""
        models_to_try = [self.settings.get('claude_model', CLAUDE_MODEL)] + CLAUDE_FALLBACK_MODELS
        
        last_error = None
        
        for model in models_to_try:
            try:
                message = self.claude_client.messages.create(
                    model=model,
                    max_tokens=4000,
                    temperature=0.2,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                return message.content[0].text
                
            except Exception as e:
                last_error = e
                continue
        
        raise APIError(f"כל המודלים נכשלו. שגיאה אחרונה: {last_error}")
    
    def _add_to_history(self, query: str, response: Dict[str, Any]) -> None:
        """Add interaction to conversation history"""
        self.conversation_history.append({
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'response_preview': response.get('answer', '')[:200] + "...",
            'sources_count': len(response.get('sources', [])),
            'model_used': response.get('model_used', 'unknown')
        })
        
        # Limit history size
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]
