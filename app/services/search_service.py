"""
Search service - comprehensive search logic with multiple strategies
"""
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.services.chatbot_service import ChatbotService
from app.services.document_service import DocumentService
from app.config.constants import DEFAULT_SIMILARITY_THRESHOLD, MAX_SEARCH_RESULTS
from app.core.error_handler import SearchError


class SearchService:
    """Service for search operations - handles all search strategies"""
    
    def __init__(self, chatbot_service: ChatbotService, document_service: DocumentService):
        self.chatbot = chatbot_service
        self.documents = document_service
        self.search_history: List[Dict] = []
    
    def execute_comprehensive_search(
        self, 
        query: str,
        max_results: int = MAX_SEARCH_RESULTS,
        min_similarity: float = DEFAULT_SIMILARITY_THRESHOLD
    ) -> Dict[str, Any]:
        """Execute comprehensive search with multiple fallback strategies"""
        
        self._log_search_attempt(query)
        
        # Check prerequisites
        has_documents = self.documents.has_documents()
        has_api = self.chatbot.is_available()
        
        # Strategy selection based on available resources
        if has_documents and has_api:
            return self._execute_full_search(query, max_results, min_similarity)
        elif has_documents and not has_api:
            return self._execute_document_only_search(query, max_results)
        elif not has_documents and has_api:
            return self._execute_general_ai_search(query)
        else:
            return self._execute_fallback_search(query)
    
    def execute_quick_search(self, query: str) -> Dict[str, Any]:
        """Execute quick search for immediate results"""
        if not self.documents.has_documents():
            return self._execute_general_ai_search(query)
        
        # Quick document search without AI processing
        sources = self._perform_document_search(query, max_results=5)
        
        if sources and self.chatbot.is_available():
            # Quick AI response with limited context
            context = self._build_compact_context(sources)
            return self.chatbot.generate_response(query, context, sources)
        elif sources:
            return self._format_document_results(query, sources)
        else:
            return self._execute_general_ai_search(query)
    
    def get_search_suggestions(self, partial_query: str) -> List[str]:
        """Get search suggestions based on document content"""
        if not partial_query.strip():
            return self._get_popular_queries()
        
        # Generate suggestions based on document content
        suggestions = []
        processed_docs = self.documents.get_processed_documents()
        
        for doc in processed_docs:
            doc_type = doc.get('document_type', '')
            if doc_type:
                suggestions.extend(self._get_type_based_suggestions(doc_type))
        
        # Remove duplicates and return relevant ones
        unique_suggestions = list(dict.fromkeys(suggestions))
        return [s for s in unique_suggestions if partial_query.lower() in s.lower()][:5]
    
    def _execute_full_search(
        self, 
        query: str, 
        max_results: int, 
        min_similarity: float
    ) -> Dict[str, Any]:
        """Execute full search with documents and AI"""
        try:
            # Search documents
            sources = self._perform_document_search(
                query, 
                max_results=max_results,
                min_similarity=min_similarity
            )
            
            if sources:
                # Build comprehensive context
                context = self._build_comprehensive_context(sources)
                
                # Generate AI response
                response = self.chatbot.generate_response(query, context, sources)
                response['search_strategy'] = 'comprehensive_with_documents'
                
                self._log_search_success(query, len(sources), 'full_search')
                return response
            else:
                # No relevant documents found, try AI-only
                return self._execute_general_ai_search(query)
                
        except Exception as e:
            self._log_search_error(query, str(e))
            raise SearchError(f"שגיאה בחיפוש מקיף: {e}")
    
    def _execute_document_only_search(self, query: str, max_results: int) -> Dict[str, Any]:
        """Execute search using only documents (no AI)"""
        try:
            sources = self._perform_document_search(query, max_results)
            
            if sources:
                # Format results without AI processing
                result = self._format_document_results(query, sources)
                result['search_strategy'] = 'document_only'
                
                self._log_search_success(query, len(sources), 'document_only')
                return result
            else:
                return {
                    'answer': "❌ לא נמצאו תוצאות רלוונטיות במסמכים. נסה לנסח את השאלה אחרת.",
                    'sources': [],
                    'search_strategy': 'document_only_no_results'
                }
                
        except Exception as e:
            self._log_search_error(query, str(e))
            raise SearchError(f"שגיאה בחיפוש במסמכים: {e}")
    
    def _execute_general_ai_search(self, query: str) -> Dict[str, Any]:
        """Execute general AI search without documents"""
        try:
            response = self.chatbot.generate_simple_response(query)
            response['search_strategy'] = 'general_ai_only'
            
            self._log_search_success(query, 0, 'general_ai')
            return response
            
        except Exception as e:
            self._log_search_error(query, str(e))
            raise SearchError(f"שגיאה בתשובה כללית: {e}")
    
    def _execute_fallback_search(self, query: str) -> Dict[str, Any]:
        """Execute fallback search when no resources available"""
        self._log_search_success(query, 0, 'fallback')
        
        return {
            'answer': """❌ המערכת לא זמינה במלואה כרגע.
            
**מה נדרש:**
- הוסף מסמכים משפטיים לניתוח
- הגדר Claude API key
            
**בינתיים תוכל:**
- להעלות מסמכים דרך הסרגל הצדדי
- לבדוק הגדרות API במדריך המערכת""",
            'sources': [],
            'search_strategy': 'fallback_unavailable',
            'note': 'מערכת לא זמינה - העלה מסמכים והגדר API'
        }
    
    def _perform_document_search(
        self, 
        query: str, 
        max_results: int = MAX_SEARCH_RESULTS,
        min_similarity: float = DEFAULT_SIMILARITY_THRESHOLD
    ) -> List[Dict[str, Any]]:
        """Perform actual document search"""
        # Use document service search
        all_results = self.documents.search_documents(query)
        
        # Filter by similarity threshold
        filtered_results = [
            result for result in all_results 
            if result.get('relevance_score', 0) >= min_similarity
        ]
        
        # Return top results
        return filtered_results[:max_results]
    
    def _build_comprehensive_context(self, sources: List[Dict]) -> str:
        """Build comprehensive context from search results"""
        context_parts = []
        
        # Group by document type
        by_type: Dict[str, List[Dict]] = {}
        for source in sources:
            doc_type = source.get('document_type', 'מסמך')
            if doc_type not in by_type:
                by_type[doc_type] = []
            by_type[doc_type].append(source)
        
        # Build context by type
        for doc_type, type_sources in by_type.items():
            type_content = f"\n\n=== {doc_type} ===\n"
            for source in type_sources[:3]:  # Max 3 per type
                content = source.get('content', '')
                file_name = source.get('file', '')
                type_content += f"\nמתוך {file_name}:\n{content}\n"
            
            context_parts.append(type_content)
        
        return "\n".join(context_parts)
    
    def _build_compact_context(self, sources: List[Dict]) -> str:
        """Build compact context for quick searches"""
        return "\n\n".join([
            f"מתוך {source.get('file', 'מסמך')}: {source.get('content', '')[:300]}..."
            for source in sources[:3]
        ])
    
    def _format_document_results(self, query: str, sources: List[Dict]) -> Dict[str, Any]:
        """Format document search results without AI processing"""
        answer_parts = [
            f"## תוצאות חיפוש עבור: {query}\n",
            f"נמצאו **{len(sources)} תוצאות רלוונטיות**:\n"
        ]
        
        for i, source in enumerate(sources[:5], 1):
            file_name = source.get('file', 'מסמך לא ידוע')
            doc_type = source.get('document_type', 'מסמך')
            content = source.get('content', '')
            relevance = source.get('relevance_score', 0)
            
            answer_parts.append(
                f"**{i}. {file_name}** ({doc_type}) - רלוונטיות: {relevance:.2%}\n"
                f"{content}\n"
            )
        
        if len(sources) > 5:
            answer_parts.append(f"\n*ועוד {len(sources) - 5} תוצאות נוספות...*")
        
        answer_parts.append(
            "\n---\n*הערה: תוצאות ללא עיבוד AI - להגדר API key לניתוח מתקדם*"
        )
        
        return {
            'answer': "\n".join(answer_parts),
            'sources': sources,
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_popular_queries(self) -> List[str]:
        """Get popular/suggested queries"""
        return [
            "מהן הטענות המרכזיות בכתב התביעה?",
            "מה הראיות העיקריות בתיק?",
            "אילו סתירות יש במסמכים?",
            "מה נקודות החולשה בטענות התובע?",
            "אילו זכויות יש לנתבע?",
            "מהן האסטרטגיות אפשריות להגנה?",
            "אילו חוקים רלוונטיים לתיק?",
            "מה הפסיקה הרלוונטית?"
        ]
    
    def _get_type_based_suggestions(self, doc_type: str) -> List[str]:
        """Get suggestions based on document type"""
        suggestions_map = {
            'כתב תביעה': [
                "מהן הטענות בכתב התביעה?",
                "מה הסכום הנתבע?",
                "על מה מבוססת התביעה?",
                "מהן העובדות שנטענו?"
            ],
            'כתב הגנה': [
                "מהן טענות ההגנה?",
                "איך מתמודדים עם הטענות?",
                "מה החריגות שנטענו?",
                "האם יש תביעה שכנגד?"
            ],
            'חוזה': [
                "מהן חובות הצדדים?",
                "האם יש הפרת חוזה?",
                "מה התנאים המיוחדים?",
                "איך מחושב הפיצוי?"
            ],
            'עדות': [
                "מה עיקר העדות?",
                "האם יש סתירות בעדות?",
                "מה המהימנות של העד?",
                "איך העדות תומכת בטענות?"
            ]
        }
        
        return suggestions_map.get(doc_type, [])
    
    def _log_search_attempt(self, query: str) -> None:
        """Log search attempt"""
        self.search_history.append({
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'status': 'started'
        })
    
    def _log_search_success(self, query: str, results_count: int, strategy: str) -> None:
        """Log successful search"""
        if self.search_history:
            self.search_history[-1].update({
                'status': 'success',
                'results_count': results_count,
                'strategy': strategy
            })
    
    def _log_search_error(self, query: str, error: str) -> None:
        """Log search error"""
        if self.search_history:
            self.search_history[-1].update({
                'status': 'error',
                'error': error
            })
    
    def get_search_statistics(self) -> Dict[str, Any]:
        """Get search usage statistics"""
        if not self.search_history:
            return {'total_searches': 0}
        
        total = len(self.search_history)
        successful = len([h for h in self.search_history if h.get('status') == 'success'])
        
        strategies = {}
        for entry in self.search_history:
            strategy = entry.get('strategy', 'unknown')
            strategies[strategy] = strategies.get(strategy, 0) + 1
        
        return {
            'total_searches': total,
            'successful_searches': successful,
            'success_rate': successful / total if total > 0 else 0,
            'strategies_used': strategies,
            'last_search': self.search_history[-1].get('timestamp') if self.search_history else None
        }
