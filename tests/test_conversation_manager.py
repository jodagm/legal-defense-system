"""
Tests for ConversationManager - Core Phase 1 functionality
"""
import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from app.core.conversation_manager import ConversationManager
from app.models.conversation_models import ResponseRating


class TestConversationManager:
    """Test conversation management functionality"""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        yield db_path
        # Cleanup
        if db_path.exists():
            db_path.unlink()
    
    @pytest.fixture
    def conversation_manager(self, temp_db_path):
        """Create conversation manager instance"""
        return ConversationManager(temp_db_path)
    
    def test_session_creation(self, conversation_manager):
        """Test creating new conversation session"""
        session_id = conversation_manager.start_session("Test Case")
        
        assert session_id is not None
        assert len(session_id) > 0
        assert conversation_manager.current_session is not None
        assert conversation_manager.current_session.case_name == "Test Case"
    
    def test_conversation_entry_addition(self, conversation_manager):
        """Test adding conversation entries"""
        # Start session
        session_id = conversation_manager.start_session("Test Case")
        
        # Add entry
        entry_id = conversation_manager.add_conversation_entry(
            query="What is defamation law?",
            ai_response="Defamation law protects individuals from false statements...",
            sources=[{"title": "Legal Code", "content": "Article 123..."}]
        )
        
        assert entry_id is not None
        assert len(conversation_manager.current_session.conversation_entries) == 1
        
        entry = conversation_manager.current_session.conversation_entries[0]
        assert entry.query == "What is defamation law?"
        assert entry.rating == ResponseRating.PENDING
    
    def test_response_rating(self, conversation_manager):
        """Test response rating functionality"""
        # Setup
        session_id = conversation_manager.start_session("Test Case")
        entry_id = conversation_manager.add_conversation_entry(
            query="Test query",
            ai_response="Test response"
        )
        
        # Rate response as high quality
        success = conversation_manager.rate_response(
            entry_id, 
            ResponseRating.HIGH_QUALITY, 
            "Very helpful response"
        )
        
        assert success is True
        
        # Check context was updated
        context = conversation_manager.get_current_context()
        assert "Test query" in context
        assert "Test response" in context
    
    def test_context_building(self, conversation_manager):
        """Test conversation context building"""
        # Start session
        session_id = conversation_manager.start_session("Test Case")
        
        # Add high-quality response
        entry_id1 = conversation_manager.add_conversation_entry(
            query="What is truth defense?",
            ai_response="Truth defense requires proving factual accuracy..."
        )
        conversation_manager.rate_response(entry_id1, ResponseRating.HIGH_QUALITY)
        
        # Add response to summarize
        entry_id2 = conversation_manager.add_conversation_entry(
            query="How to gather evidence?",
            ai_response="Evidence gathering involves systematic collection of documents..."
        )
        conversation_manager.rate_response(entry_id2, ResponseRating.SUMMARIZE)
        
        # Add rejected response
        entry_id3 = conversation_manager.add_conversation_entry(
            query="Random question",
            ai_response="Not helpful response"
        )
        conversation_manager.rate_response(entry_id3, ResponseRating.REJECT)
        
        # Check context
        context = conversation_manager.get_current_context()
        
        # High quality should be included verbatim
        assert "Truth defense requires proving factual accuracy" in context
        
        # Summarized should be included as summary
        assert "Evidence gathering" in context
        
        # Rejected should not be included
        assert "Not helpful response" not in context
    
    def test_session_persistence(self, conversation_manager, temp_db_path):
        """Test session persistence across manager instances"""
        # Create session and add data
        session_id = conversation_manager.start_session("Persistent Test")
        entry_id = conversation_manager.add_conversation_entry(
            query="Persistent query",
            ai_response="Persistent response"
        )
        conversation_manager.rate_response(entry_id, ResponseRating.HIGH_QUALITY)
        
        # Create new manager instance
        new_manager = ConversationManager(temp_db_path)
        
        # Load the session
        success = new_manager.load_session(session_id)
        assert success is True
        
        assert new_manager.current_session.case_name == "Persistent Test"
        assert len(new_manager.current_session.conversation_entries) == 1
        
        # Check context persistence
        context = new_manager.get_current_context()
        assert "Persistent response" in context
    
    def test_conversation_statistics(self, conversation_manager):
        """Test conversation statistics generation"""
        # Setup session with multiple entries
        session_id = conversation_manager.start_session("Stats Test")
        
        # Add various rated responses
        for i in range(5):
            entry_id = conversation_manager.add_conversation_entry(
                query=f"Query {i}",
                ai_response=f"Response {i}"
            )
            if i < 2:
                conversation_manager.rate_response(entry_id, ResponseRating.HIGH_QUALITY)
            elif i < 4:
                conversation_manager.rate_response(entry_id, ResponseRating.SUMMARIZE)
            # Leave last one unrated
        
        stats = conversation_manager.get_conversation_statistics()
        
        assert stats['total_exchanges'] == 5
        assert stats['rated_exchanges'] == 4
        assert stats['rating_distribution']['high_quality'] == 2
        assert stats['rating_distribution']['summarize'] == 2
        assert stats['rating_distribution']['pending'] == 1
    
    def test_unrated_entries(self, conversation_manager):
        """Test retrieving unrated entries"""
        # Setup
        session_id = conversation_manager.start_session("Unrated Test")
        
        # Add rated and unrated entries
        rated_id = conversation_manager.add_conversation_entry("Rated query", "Rated response")
        unrated_id = conversation_manager.add_conversation_entry("Unrated query", "Unrated response")
        
        conversation_manager.rate_response(rated_id, ResponseRating.HIGH_QUALITY)
        
        # Get unrated entries
        unrated = conversation_manager.get_unrated_entries()
        
        assert len(unrated) == 1
        assert unrated[0].id == unrated_id
        assert unrated[0].query == "Unrated query"
    
    def test_session_listing(self, conversation_manager):
        """Test listing conversation sessions"""
        # Create multiple sessions
        session1_id = conversation_manager.start_session("Case 1")
        conversation_manager.add_conversation_entry("Query 1", "Response 1")
        
        session2_id = conversation_manager.start_session("Case 2") 
        conversation_manager.add_conversation_entry("Query 2", "Response 2")
        
        # List sessions
        sessions = conversation_manager.list_sessions()
        
        assert len(sessions) == 2
        assert any(s['session_id'] == session1_id for s in sessions)
        assert any(s['session_id'] == session2_id for s in sessions)
        assert any(s['case_name'] == "Case 1" for s in sessions)
        assert any(s['case_name'] == "Case 2" for s in sessions)


if __name__ == "__main__":
    pytest.main([__file__]) 