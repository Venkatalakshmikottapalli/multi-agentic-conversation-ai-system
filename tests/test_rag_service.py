import pytest
import pandas as pd
import tempfile
import os
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from services.rag_service import RAGService

class TestRAGService:
    """Test cases for RAG service."""
    
    @pytest.fixture
    def rag_service(self):
        """Create a mock RAG service."""
        with patch('services.rag_service.faiss') as mock_faiss, \
             patch('services.rag_service.SentenceTransformer') as mock_transformer, \
             patch('services.rag_service.get_db_context') as mock_db_context:
            
            # Mock FAISS index
            mock_index = Mock()
            mock_index.ntotal = 0
            mock_faiss.IndexFlatIP.return_value = mock_index
            mock_faiss.read_index.return_value = mock_index
            
            # Mock sentence transformer
            mock_transformer_instance = Mock()
            mock_transformer_instance.get_sentence_embedding_dimension.return_value = 768
            mock_transformer_instance.encode.return_value = np.random.rand(1, 768)
            mock_transformer.return_value = mock_transformer_instance
            
            # Mock database context
            mock_db_context.return_value.__enter__.return_value = Mock()
            
            service = RAGService()
            service.faiss_index = mock_index
            service.documents = []
            service.metadatas = []
            
            yield service
    
    def test_initialization(self):
        """Test RAG service initialization."""
        with patch('services.rag_service.faiss') as mock_faiss, \
             patch('services.rag_service.SentenceTransformer') as mock_transformer, \
             patch('os.path.exists') as mock_exists:
            
            mock_index = Mock()
            mock_index.ntotal = 0
            mock_faiss.IndexFlatIP.return_value = mock_index
            mock_exists.return_value = False
            
            mock_transformer_instance = Mock()
            mock_transformer_instance.get_sentence_embedding_dimension.return_value = 768
            mock_transformer.return_value = mock_transformer_instance
            
            service = RAGService()
            
            assert service.faiss_index is not None
            assert service.embedding_model is not None
            assert service.documents == []
            assert service.metadatas == []
    
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
            'Property Type': 'Office Space',
            'Location': 'Downtown',
            'Price': '$150,000',
            'Size': '1500 sq ft',
            'Parking': 'Available'
        })
        
        description = rag_service._create_property_description(property_data)
        
        assert 'Office Space' in description
        assert 'Downtown' in description
        assert '$150,000' in description
        assert 'Size: 1500 sq ft' in description
        assert 'Parking: Available' in description
    
    def test_process_document(self, rag_service):
        """Test document processing."""
        content = "This is a test document content."
        filename = "test.txt"
        content_type = "text/plain"
        
        with patch('services.rag_service.get_db_context') as mock_context, \
             patch.object(rag_service, '_save_index') as mock_save:
            
            mock_db = Mock()
            mock_context.return_value.__enter__.return_value = mock_db
            
            doc_id = rag_service.process_document(content, filename, content_type)
            
            # Check that index was updated
            assert rag_service.faiss_index.add.called
            
            # Check that document was added to database
            assert mock_db.add.called
            assert mock_db.commit.called
            
            # Check that index was saved
            assert mock_save.called
    
    def test_process_csv_data(self, rag_service):
        """Test CSV data processing."""
        csv_content = """Property Type,Location,Price
Office Space,Downtown,$150000
Retail Space,Uptown,$200000"""
        
        filename = "test.csv"
        
        with patch('services.rag_service.get_db_context') as mock_context, \
             patch.object(rag_service, '_save_index') as mock_save:
            
            mock_db = Mock()
            mock_context.return_value.__enter__.return_value = mock_db
            
            doc_id = rag_service.process_csv_data(csv_content, filename)
            
            # Check that index was updated
            assert rag_service.faiss_index.add.called
            
            # Check that document was added to database
            assert mock_db.add.called
            assert mock_db.commit.called
    
    def test_retrieve_documents(self, rag_service):
        """Test document retrieval."""
        query = "office space"
        
        # Set up mock data
        rag_service.documents = ['Document content 1', 'Document content 2']
        rag_service.metadatas = [{'filename': 'doc1.txt'}, {'filename': 'doc2.txt'}]
        rag_service.faiss_index.ntotal = 2
        
        # Mock search results
        mock_scores = np.array([[0.9, 0.8]])
        mock_indices = np.array([[0, 1]])
        rag_service.faiss_index.search.return_value = (mock_scores, mock_indices)
        
        results = rag_service.retrieve_documents(query)
        
        assert len(results) == 2
        assert results[0]['content'] == 'Document content 1'
        assert results[0]['metadata']['filename'] == 'doc1.txt'
        assert results[0]['similarity_score'] == 0.9
        
        # Check that search was called
        assert rag_service.faiss_index.search.called
    
    def test_retrieve_documents_empty_index(self, rag_service):
        """Test document retrieval with empty index."""
        query = "test query"
        rag_service.faiss_index.ntotal = 0
        
        results = rag_service.retrieve_documents(query)
        
        assert len(results) == 0
    
    def test_get_collection_stats(self, rag_service):
        """Test getting collection statistics."""
        rag_service.documents = ['doc1', 'doc2', 'doc3']
        rag_service.faiss_index.ntotal = 3
        
        stats = rag_service.get_collection_stats()
        
        assert stats['total_documents'] == 3
        assert stats['total_vectors'] == 3
        assert stats['embedding_dimension'] == 768
        assert stats['index_type'] == 'FAISS IndexFlatIP'
    
    def test_clear_collection(self, rag_service):
        """Test clearing the collection."""
        with patch.object(rag_service, '_save_index') as mock_save:
            rag_service.clear_collection()
            
            # Check that documents and metadata were cleared
            assert len(rag_service.documents) == 0
            assert len(rag_service.metadatas) == 0
            
            # Check that index was saved
            assert mock_save.called
    
    def test_process_document_with_metadata(self, rag_service):
        """Test document processing with metadata."""
        content = "Test document with metadata"
        filename = "test_meta.txt"
        content_type = "text/plain"
        metadata = {"source": "test", "category": "documentation"}
        
        with patch('services.rag_service.get_db_context') as mock_context, \
             patch.object(rag_service, '_save_index') as mock_save:
            
            mock_db = Mock()
            mock_context.return_value.__enter__.return_value = mock_db
            
            doc_id = rag_service.process_document(content, filename, content_type, metadata)
            
            # Check that metadata was included in stored metadatas
            assert len(rag_service.metadatas) > 0
            assert any('source' in meta for meta in rag_service.metadatas)
            assert any('category' in meta for meta in rag_service.metadatas)
    
    def test_retrieve_documents_with_custom_limit(self, rag_service):
        """Test document retrieval with custom result limit."""
        query = "test query"
        n_results = 3
        
        # Set up mock data
        rag_service.documents = ['Doc 1', 'Doc 2', 'Doc 3', 'Doc 4']
        rag_service.metadatas = [{}, {}, {}, {}]
        rag_service.faiss_index.ntotal = 4
        
        # Mock search results
        mock_scores = np.array([[0.9, 0.8, 0.7]])
        mock_indices = np.array([[0, 1, 2]])
        rag_service.faiss_index.search.return_value = (mock_scores, mock_indices)
        
        results = rag_service.retrieve_documents(query, n_results)
        
        assert len(results) == 3
        # Check that search was called with correct n_results
        rag_service.faiss_index.search.assert_called_once()
        args = rag_service.faiss_index.search.call_args[0]
        assert args[1] == n_results  # Second argument should be n_results
    
    def test_error_handling_in_process_document(self, rag_service):
        """Test error handling in document processing."""
        content = "Test content"
        filename = "test.txt"
        content_type = "text/plain"
        
        # Mock an exception during processing
        rag_service.faiss_index.add.side_effect = Exception("FAISS error")
        
        with pytest.raises(Exception):
            rag_service.process_document(content, filename, content_type)
    
    def test_error_handling_in_retrieve_documents(self, rag_service):
        """Test error handling in document retrieval."""
        query = "test query"
        
        # Mock an exception during search
        rag_service.faiss_index.search.side_effect = Exception("Search error")
        
        results = rag_service.retrieve_documents(query)
        
        # Should return empty list on error
        assert results == []
    
    def test_save_and_load_index(self, rag_service):
        """Test saving and loading index."""
        with patch('services.rag_service.faiss.write_index') as mock_write, \
             patch('services.rag_service.pickle.dump') as mock_dump, \
             patch('builtins.open', mock_open=True):
            
            rag_service._save_index()
            
            # Check that faiss index was written
            assert mock_write.called
            
            # Check that metadata was pickled
            assert mock_dump.called 