"""
Tests for System Clear functionality
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from app.services.document_service import DocumentService
from app.services.evidence_service import EvidenceService
from app.core.conversation_manager import ConversationManager


class TestSystemClear:
    """Test system clear/reset functionality"""
    
    @pytest.fixture
    def temp_data_paths(self):
        """Create temporary data paths for testing"""
        temp_dir = Path(tempfile.mkdtemp())
        
        data_paths = {
            'upload': temp_dir / 'uploaded_documents',
            'processed': temp_dir / 'processed',
            'summaries': temp_dir / 'summaries',
            'metadata': temp_dir / 'metadata',
            'evidence': temp_dir / 'evidence_items',
            'conversations': temp_dir / 'conversations'
        }
        
        # Create directories
        for path in data_paths.values():
            path.mkdir(parents=True, exist_ok=True)
        
        yield data_paths
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def document_service(self, temp_data_paths):
        """Create document service instance"""
        return DocumentService(temp_data_paths)
    
    @pytest.fixture
    def evidence_service(self, temp_data_paths):
        """Create evidence service instance"""
        return EvidenceService(temp_data_paths)
    
    @pytest.fixture
    def conversation_manager(self, temp_data_paths):
        """Create conversation manager instance"""
        db_path = temp_data_paths['conversations'] / 'test_conversations.db'
        return ConversationManager(db_path)
    
    def test_clear_documents(self, document_service, temp_data_paths):
        """Test clearing uploaded and processed documents"""
        # Create test files
        upload_path = temp_data_paths['upload']
        processed_path = temp_data_paths['processed']
        
        test_upload = upload_path / 'test.pdf'
        test_processed = processed_path / 'test_processed.json'
        
        test_upload.write_text('test pdf content')
        test_processed.write_text('{"test": "data"}')
        
        # Clear documents
        results = document_service.clear_all_documents()
        
        # Verify results
        assert results['uploaded_files_deleted'] == 1
        assert results['processed_files_deleted'] == 1
        assert len(results['errors']) == 0
        
        # Verify files are deleted
        assert not test_upload.exists()
        assert not test_processed.exists()
    
    def test_clear_evidence(self, evidence_service, temp_data_paths):
        """Test clearing evidence files"""
        # Create test evidence file
        evidence_path = temp_data_paths['evidence']
        test_evidence = evidence_path / 'test_evidence.json'
        test_evidence.write_text('{"evidence": "data"}')
        
        # Clear evidence
        results = evidence_service.clear_all_evidence()
        
        # Verify results
        assert results['evidence_files_deleted'] == 1
        assert len(results['errors']) == 0
        
        # Verify file is deleted
        assert not test_evidence.exists()
    
    def test_clear_conversations(self, conversation_manager):
        """Test clearing conversation database"""
        # Create test conversation
        session_id = conversation_manager.start_session("Test Case")
        entry_id = conversation_manager.add_conversation_entry(
            "Test query", 
            "Test response"
        )
        
        # Verify data exists
        assert conversation_manager.current_session is not None
        assert len(conversation_manager.current_session.conversation_entries) == 1
        
        # Clear conversations
        results = conversation_manager.clear_all_conversations()
        
        # Verify results
        assert results['sessions_deleted'] == 1
        assert results['entries_deleted'] == 1
        assert len(results['errors']) == 0
        
        # Verify data is cleared
        assert conversation_manager.current_session is None
    
    def test_error_handling_in_clear_operations(self, temp_data_paths):
        """Test error handling during clear operations"""
        # Create document service with invalid paths
        invalid_paths = {
            'upload': Path('/invalid/path'),
            'processed': Path('/invalid/path'),
            'summaries': Path('/invalid/path'),
            'metadata': Path('/invalid/path')
        }
        
        document_service = DocumentService(invalid_paths)
        
        # This should not raise an exception, but should report errors
        results = document_service.clear_all_documents()
        
        # Should complete without crashing
        assert 'uploaded_files_deleted' in results
        assert 'processed_files_deleted' in results
        assert 'errors' in results
    
    def test_empty_directories_clear(self, document_service, evidence_service, conversation_manager):
        """Test clearing when directories are already empty"""
        # Clear empty systems
        doc_results = document_service.clear_all_documents()
        ev_results = evidence_service.clear_all_evidence()
        conv_results = conversation_manager.clear_all_conversations()
        
        # Should complete successfully with zero deletions
        assert doc_results['uploaded_files_deleted'] == 0
        assert doc_results['processed_files_deleted'] == 0
        assert ev_results['evidence_files_deleted'] == 0
        assert conv_results['sessions_deleted'] == 0
        assert conv_results['entries_deleted'] == 0
        
        # Should have no errors
        assert len(doc_results['errors']) == 0
        assert len(ev_results['errors']) == 0
        assert len(conv_results['errors']) == 0


if __name__ == "__main__":
    pytest.main([__file__]) 