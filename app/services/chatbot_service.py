"""
Chatbot service - business logic for AI interactions
"""
from typing import Optional, Dict, Any, List
import json
from datetime import datetime

from app.config.constants import CLAUDE_MODEL, CLAUDE_FALLBACK_MODELS
from app.core.error_handler import APIError


class ChatbotService:
    """Service for chatbot operations - single responsibility for AI logic"""
    
    def __init__(self, claude_client: Optional[Any], settings: Dict[str, Any]):
        self.claude_client = claude_client
        self.settings = settings
        self.conversation_history: List[Dict] = []
    
    def is_available(self) -> bool:
        """Check if chatbot service is available"""
        return self.claude_client is not None
    
    def generate_response(
        self, 
        query: str, 
        context: str = "", 
        sources: List[Dict] = None
    ) -> Dict[str, Any]:
        """Generate AI response with context and sources"""
        if not self.is_available():
            raise APIError("Claude API לא זמין")
        
        prompt = self._build_legal_prompt(query, context, sources or [])
        
        try:
            response = self._call_claude_api(prompt)
            
            result = {
                'answer': response,
                'sources': sources or [],
                'timestamp': datetime.now().isoformat(),
                'model_used': self.settings.get('claude_model', CLAUDE_MODEL),
                'query': query,
                'has_context': bool(context)
            }
            
            self._add_to_history(query, result)
            return result
            
        except Exception as e:
            raise APIError(f"שגיאה ביצירת תשובה: {e}")
    
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
