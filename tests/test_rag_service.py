import pytest
import pandas as pd
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from services.rag_service import RAGService

class TestRAGService:
    """Test cases for RAG service."""
    
    @pytest.fixture
    def rag_service(self):
        """Create a mock RAG service."""
        with patch('services.rag_service.chromadb.PersistentClient') as mock_client, \
             patch('services.rag_service.SentenceTransformer') as mock_transformer, \
             patch('services.rag_service.get_db_context') as mock_db_context:
            
            # Mock ChromaDB client
            mock_collection = Mock()
            mock_client.return_value.get_or_create_collection.return_value = mock_collection
            
            # Mock sentence transformer
            mock_transformer.return_value = Mock()
            
            # Mock database context
            mock_db_context.return_value.__enter__.return_value = Mock()
            
            service = RAGService()
            service.collection = mock_collection
            
            yield service
    
    def test_initialization(self):
        """Test RAG service initialization."""
        with patch('services.rag_service.chromadb.PersistentClient') as mock_client, \
             patch('services.rag_service.SentenceTransformer') as mock_transformer:
            
            mock_collection = Mock()
            mock_client.return_value.get_or_create_collection.return_value = mock_collection
            mock_transformer.return_value = Mock()
            
            service = RAGService()
            
            assert service.chroma_client is not None
            assert service.collection is not None
            assert service.embedding_model is not None
    
    def test_split_text(self, rag_service):
        """Test text splitting functionality."""
        text = "This is a test document. " * 100  # Create long text
        
        chunks = rag_service._split_text(text)
        
        assert len(chunks) > 1
        assert all(isinstance(chunk, str) for chunk in chunks)
    
    def test_split_text_short(self, rag_service):
        """Test text splitting with short text."""
        text = "Short text"
        
        chunks = rag_service._split_text(text)
        
        assert len(chunks) == 1
        assert chunks[0] == text
    
    def test_create_property_description(self, rag_service):
        """Test property description creation."""
        # Create a mock pandas Series
        property_data = pd.Series({
            'Property Address': '123 Main St',
            'Floor': 'E3',
            'Suite': '300',
            'Size (SF)': 1500,
            'Rent/SF/Year': '$85.00',
            'Annual Rent': '$127,500',
            'Monthly Rent': '$10,625',
            'Associate 1': 'John Doe',
            'BROKER Email ID': 'john@example.com',
            'Associate 2': 'Jane Smith'
        })
        
        description = rag_service._create_property_description(property_data)
        
        assert '123 Main St' in description
        assert 'E3' in description
        assert '300' in description
        assert '1500' in description
        assert 'John Doe' in description
        assert 'john@example.com' in description.lower()
        assert 'Jane Smith' in description
    
    def test_process_document(self, rag_service):
        """Test document processing."""
        content = "This is a test document content."
        filename = "test.txt"
        content_type = "text/plain"
        
        with patch('services.rag_service.get_db_context') as mock_context:
            mock_db = Mock()
            mock_context.return_value.__enter__.return_value = mock_db
            
            doc_id = rag_service.process_document(content, filename, content_type)
            
            # Check that collection.add was called
            assert rag_service.collection.add.called
            
            # Check that document was added to database
            assert mock_db.add.called
            assert mock_db.commit.called
    
    def test_process_csv_data(self, rag_service):
        """Test CSV data processing."""
        csv_content = """Property Address,Floor,Suite,Size (SF),Rent/SF/Year
123 Main St,E3,300,1500,$85.00
456 Oak Ave,E5,500,2000,$90.00"""
        
        filename = "test.csv"
        
        with patch('services.rag_service.get_db_context') as mock_context:
            mock_db = Mock()
            mock_context.return_value.__enter__.return_value = mock_db
            
            doc_id = rag_service.process_csv_data(csv_content, filename)
            
            # Check that collection.add was called
            assert rag_service.collection.add.called
            
            # Check that document was added to database
            assert mock_db.add.called
            assert mock_db.commit.called
    
    def test_retrieve_documents(self, rag_service):
        """Test document retrieval."""
        query = "office space"
        
        # Mock the collection query response
        mock_results = {
            'documents': [['Document content 1', 'Document content 2']],
            'metadatas': [[{'filename': 'doc1.txt'}, {'filename': 'doc2.txt'}]],
            'distances': [[0.1, 0.2]]
        }
        
        rag_service.collection.query.return_value = mock_results
        
        results = rag_service.retrieve_documents(query)
        
        assert len(results) == 2
        assert results[0]['content'] == 'Document content 1'
        assert results[0]['metadata']['filename'] == 'doc1.txt'
        assert results[0]['similarity_score'] == 0.9  # 1 - 0.1
        
        # Check that collection.query was called with correct parameters
        rag_service.collection.query.assert_called_once_with(
            query_texts=[query],
            n_results=5,  # default max_retrieval_docs
            include=["documents", "metadatas", "distances"]
        )
    
    def test_retrieve_documents_no_results(self, rag_service):
        """Test document retrieval with no results."""
        query = "non-existent query"
        
        # Mock empty results
        mock_results = {
            'documents': [[]],
            'metadatas': [[]],
            'distances': [[]]
        }
        
        rag_service.collection.query.return_value = mock_results
        
        results = rag_service.retrieve_documents(query)
        
        assert len(results) == 0
    
    def test_get_collection_stats(self, rag_service):
        """Test getting collection statistics."""
        rag_service.collection.count.return_value = 100
        
        # Mock the database context and query
        with patch('services.rag_service.get_db_context') as mock_db_context:
            mock_db = MagicMock()
            mock_db_context.return_value.__enter__.return_value = mock_db
            
            # Mock document count
            mock_db.query.return_value.filter.return_value.count.return_value = 5
            
            # Mock collection size
            mock_db.query.return_value.scalar.return_value = 1024
            
            # Mock last updated
            mock_document = MagicMock()
            mock_document.indexed_at.isoformat.return_value = '2024-01-01T00:00:00'
            mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_document
            
            stats = rag_service.get_collection_stats()
            
            assert stats['total_documents'] == 5
            assert stats['total_chunks'] == 100
            assert stats['collection_size'] == 1024
            assert stats['last_updated'] == '2024-01-01T00:00:00'
            assert stats['collection_name'] == 'knowledge_base'
            assert 'embedding_model' in stats
    
    def test_clear_collection(self, rag_service):
        """Test clearing the collection."""
        # Mock the database context and query
        with patch('services.rag_service.get_db_context') as mock_db_context:
            mock_db = MagicMock()
            mock_db_context.return_value.__enter__.return_value = mock_db
            
            rag_service.clear_collection()
            
            # Check that delete_collection was called
            assert rag_service.chroma_client.delete_collection.called
            
            # Check that get_or_create_collection was called to recreate
            assert rag_service.chroma_client.get_or_create_collection.called
            
            # Check that database was updated
            assert mock_db.query.called
            assert mock_db.commit.called
    
    def test_remove_document_by_filename(self, rag_service):
        """Test removing a document by filename."""
        # Mock the database context and query
        with patch('services.rag_service.get_db_context') as mock_db_context:
            mock_db = MagicMock()
            mock_db_context.return_value.__enter__.return_value = mock_db
            
            # Mock existing document
            mock_document = MagicMock()
            mock_document.is_active = True
            mock_db.query.return_value.filter.return_value.first.return_value = mock_document
            
            # Mock ChromaDB get method
            rag_service.collection.get.return_value = {
                'ids': ['doc1_chunk_0', 'doc2_chunk_0'],
                'metadatas': [
                    {'filename': 'test.txt'},
                    {'filename': 'other.txt'}
                ]
            }
            
            # Test removal
            result = rag_service.remove_document_by_filename('test.txt')
            
            # Verify document was marked inactive
            assert mock_document.is_active == False
            
            # Verify ChromaDB delete was called
            rag_service.collection.delete.assert_called_once_with(ids=['doc1_chunk_0'])
            
            # Verify database commit
            mock_db.commit.assert_called_once()
            
            assert result == True
    
    def test_process_document_replacement(self, rag_service):
        """Test that process_document replaces existing documents."""
        # Mock the remove_document_by_filename method
        with patch.object(rag_service, 'remove_document_by_filename') as mock_remove:
            with patch('services.rag_service.get_db_context') as mock_db_context:
                mock_db = MagicMock()
                mock_db_context.return_value.__enter__.return_value = mock_db
                
                # Mock document creation
                mock_document = MagicMock()
                mock_document.id = 'test_doc_id'
                mock_db.add.return_value = None
                mock_db.commit.return_value = None
                
                # Test document processing
                result = rag_service.process_document(
                    content="Test content",
                    filename="test.txt",
                    content_type="text/plain"
                )
                
                # Verify remove was called first
                mock_remove.assert_called_once_with("test.txt")
                
                # Verify document was added to database
                mock_db.add.assert_called_once()
                mock_db.commit.assert_called_once()
                
                # Verify ChromaDB add was called
                rag_service.collection.add.assert_called_once()
        assert rag_service.chroma_client.get_or_create_collection.called
    
    def test_process_document_with_metadata(self, rag_service):
        """Test document processing with metadata."""
        content = "Test document with metadata"
        filename = "test_meta.txt"
        content_type = "text/plain"
        metadata = {"source": "test", "category": "documentation"}
        
        with patch('services.rag_service.get_db_context') as mock_context:
            mock_db = Mock()
            mock_context.return_value.__enter__.return_value = mock_db
            
            doc_id = rag_service.process_document(content, filename, content_type, metadata)
            
            # Check that metadata was included
            call_args = rag_service.collection.add.call_args
            assert call_args is not None
            metadatas = call_args[1]['metadatas']
            assert any('source' in meta for meta in metadatas)
            assert any('category' in meta for meta in metadatas)
    
    def test_retrieve_documents_with_custom_limit(self, rag_service):
        """Test document retrieval with custom result limit."""
        query = "test query"
        n_results = 3
        
        # Mock the collection query response
        mock_results = {
            'documents': [['Doc 1', 'Doc 2', 'Doc 3']],
            'metadatas': [[{}, {}, {}]],
            'distances': [[0.1, 0.2, 0.3]]
        }
        
        rag_service.collection.query.return_value = mock_results
        
        results = rag_service.retrieve_documents(query, n_results)
        
        assert len(results) == 3
        rag_service.collection.query.assert_called_once_with(
            query_texts=[query],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
    
    def test_error_handling_in_process_document(self, rag_service):
        """Test error handling in document processing."""
        content = "Test content"
        filename = "test.txt"
        content_type = "text/plain"
        
        # Mock an exception during processing
        rag_service.collection.add.side_effect = Exception("ChromaDB error")
        
        with pytest.raises(Exception):
            rag_service.process_document(content, filename, content_type)
    
    def test_error_handling_in_retrieve_documents(self, rag_service):
        """Test error handling in document retrieval."""
        query = "test query"
        
        # Mock an exception during retrieval
        rag_service.collection.query.side_effect = Exception("Query error")
        
        results = rag_service.retrieve_documents(query)
        
        # Should return empty list on error
        assert results == []

if __name__ == "__main__":
    pytest.main([__file__]) 