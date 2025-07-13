import pytest
import json
import tempfile
import os
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

from main import app
from database import get_db_context
from models.crm_models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class TestIntegration:
    """Integration tests for the API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)
    
    @pytest.fixture
    def test_db(self):
        """Create a test database."""
        # Create temporary database
        db_fd, db_path = tempfile.mkstemp()
        engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(engine)
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        yield SessionLocal, db_path
        
        # Clean up
        os.close(db_fd)
        os.unlink(db_path)
    
    def test_root_endpoint(self, client):
        """Test the root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "Multi-Agent Conversational AI System API" in data["message"]
        assert "endpoints" in data["data"]
    
    def test_health_check(self, client):
        """Test the health check endpoint."""
        with patch('main.get_db_context') as mock_context, \
             patch('main.rag_service.get_collection_stats') as mock_stats:
            
            mock_context.return_value.__enter__.return_value.execute.return_value = True
            mock_stats.return_value = {"total_documents": 100}
            
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "database" in data
            assert "vector_store" in data
            assert "openai" in data
    
    def test_chat_endpoint(self, client):
        """Test the chat endpoint."""
        with patch('main.chat_agent.process_message') as mock_process:
            mock_process.return_value = {
                "response": "Hello! How can I help you?",
                "user_id": "test-user-123",
                "session_id": "test-session-123",
                "conversation_id": "test-conv-123",
                "sources": [],
                "metadata": {"agent_used": "general_agent"},
                "processing_time": 0.5
            }
            
            chat_data = {
                "message": "Hello",
                "user_id": "test-user-123",
                "session_id": "test-session-123"
            }
            
            response = client.post("/chat", json=chat_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["response"] == "Hello! How can I help you?"
            assert data["user_id"] == "test-user-123"
            assert data["session_id"] == "test-session-123"
    
    def test_upload_documents_text(self, client):
        """Test document upload with text file."""
        with patch('main.rag_service.process_document') as mock_process:
            mock_process.return_value = "doc-123"
            
            # Create a test file
            test_content = "This is a test document."
            
            response = client.post(
                "/upload_docs",
                files={"files": ("test.txt", test_content, "text/plain")}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert "uploaded_documents" in data["data"]
            assert len(data["data"]["uploaded_documents"]) == 1
    
    def test_upload_documents_csv(self, client):
        """Test document upload with CSV file."""
        with patch('main.rag_service.process_csv_data') as mock_process:
            mock_process.return_value = "doc-123"
            
            # Create a test CSV
            csv_content = "Property Address,Floor,Suite\n123 Main St,E3,300"
            
            response = client.post(
                "/upload_docs",
                files={"files": ("test.csv", csv_content, "text/csv")}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert "uploaded_documents" in data["data"]
    
    def test_create_user(self, client):
        """Test user creation."""
        with patch('main.crm_service.create_user') as mock_create:
            mock_user = Mock()
            mock_user.to_dict.return_value = {
                "id": "user-123",
                "name": "John Doe",
                "email": "john@example.com"
            }
            mock_create.return_value = mock_user
            
            user_data = {
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "123-456-7890"
            }
            
            response = client.post("/crm/create_user", json=user_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert data["data"]["name"] == "John Doe"
    
    def test_update_user(self, client):
        """Test user update."""
        with patch('main.crm_service.update_user') as mock_update:
            mock_user = Mock()
            mock_user.to_dict.return_value = {
                "id": "user-123",
                "name": "John Updated",
                "email": "john@example.com"
            }
            mock_update.return_value = mock_user
            
            user_data = {
                "name": "John Updated"
            }
            
            response = client.put("/crm/update_user/user-123", json=user_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert data["data"]["name"] == "John Updated"
    
    def test_update_user_not_found(self, client):
        """Test updating non-existent user."""
        with patch('main.crm_service.update_user') as mock_update:
            mock_update.return_value = None
            
            user_data = {
                "name": "John Updated"
            }
            
            response = client.put("/crm/update_user/non-existent", json=user_data)
            
            assert response.status_code == 404
            data = response.json()
            assert "User not found" in data["detail"]
    
    def test_get_user(self, client):
        """Test getting a user."""
        with patch('main.crm_service.get_user') as mock_get:
            mock_user = Mock()
            mock_user.to_dict.return_value = {
                "id": "user-123",
                "name": "John Doe",
                "email": "john@example.com"
            }
            mock_get.return_value = mock_user
            
            response = client.get("/crm/users/user-123")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert data["data"]["name"] == "John Doe"
    
    def test_get_user_not_found(self, client):
        """Test getting non-existent user."""
        with patch('main.crm_service.get_user') as mock_get:
            mock_get.return_value = None
            
            response = client.get("/crm/users/non-existent")
            
            assert response.status_code == 404
            data = response.json()
            assert "User not found" in data["detail"]
    
    def test_list_users(self, client):
        """Test listing users."""
        with patch('main.crm_service.list_users') as mock_list:
            mock_users = [Mock(), Mock()]
            mock_users[0].to_dict.return_value = {"id": "user-1", "name": "User 1"}
            mock_users[1].to_dict.return_value = {"id": "user-2", "name": "User 2"}
            
            mock_list.return_value = {
                "users": mock_users,
                "total": 2,
                "page": 1,
                "per_page": 10,
                "pages": 1
            }
            
            response = client.get("/crm/users")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert len(data["data"]) == 2
            assert data["total"] == 2
    
    def test_delete_user(self, client):
        """Test deleting a user."""
        with patch('main.crm_service.delete_user') as mock_delete:
            mock_delete.return_value = True
            
            response = client.delete("/crm/users/user-123")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert "deleted successfully" in data["message"]
    
    def test_delete_user_not_found(self, client):
        """Test deleting non-existent user."""
        with patch('main.crm_service.delete_user') as mock_delete:
            mock_delete.return_value = False
            
            response = client.delete("/crm/users/non-existent")
            
            assert response.status_code == 404
            data = response.json()
            assert "User not found" in data["detail"]
    
    def test_get_user_conversations(self, client):
        """Test getting user conversations."""
        with patch('main.crm_service.get_user') as mock_get_user, \
             patch('main.crm_service.get_user_conversations') as mock_get_conversations:
            
            mock_get_user.return_value = Mock()
            mock_conversations = [Mock(), Mock()]
            mock_conversations[0].to_dict.return_value = {"id": "conv-1", "title": "Chat 1"}
            mock_conversations[1].to_dict.return_value = {"id": "conv-2", "title": "Chat 2"}
            
            mock_get_conversations.return_value = {
                "conversations": mock_conversations,
                "total": 2,
                "page": 1,
                "per_page": 10,
                "pages": 1
            }
            
            response = client.get("/crm/conversations/user-123")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert len(data["data"]) == 2
    
    def test_get_conversation_details(self, client):
        """Test getting conversation details."""
        with patch('main.crm_service.get_conversation_with_messages') as mock_get:
            mock_conversation = Mock()
            mock_conversation.user_id = "user-123"
            mock_conversation.to_dict.return_value = {
                "id": "conv-123",
                "title": "Test Conversation"
            }
            mock_conversation.messages = [Mock(), Mock()]
            mock_conversation.messages[0].to_dict.return_value = {
                "id": "msg-1",
                "content": "Hello",
                "role": "user"
            }
            mock_conversation.messages[1].to_dict.return_value = {
                "id": "msg-2",
                "content": "Hi there!",
                "role": "assistant"
            }
            
            mock_get.return_value = mock_conversation
            
            response = client.get("/crm/conversations/user-123/conv-123")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert data["data"]["id"] == "conv-123"
            assert len(data["data"]["messages"]) == 2
    
    def test_reset_conversation(self, client):
        """Test resetting conversation."""
        with patch('main.crm_service.clear_user_conversations') as mock_clear:
            mock_clear.return_value = 3
            
            reset_data = {
                "user_id": "user-123",
                "reset_type": "conversation"
            }
            
            response = client.post("/reset", json=reset_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["reset_type"] == "conversation"
            assert data["affected_records"] == 3
    
    def test_get_analytics(self, client):
        """Test getting analytics."""
        with patch('main.crm_service.get_conversation_analytics') as mock_analytics:
            mock_analytics.return_value = {
                "total_conversations": 10,
                "status_breakdown": {"active": 5, "resolved": 5},
                "category_breakdown": {"real_estate": 8, "general": 2}
            }
            
            response = client.get("/crm/analytics")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert data["data"]["total_conversations"] == 10
    
    def test_get_user_stats(self, client):
        """Test getting user statistics."""
        with patch('main.crm_service.get_user_stats') as mock_stats:
            mock_stats.return_value = {
                "user": {"id": "user-123", "name": "John Doe"},
                "conversation_count": 5,
                "message_count": 25
            }
            
            response = client.get("/crm/users/user-123/stats")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert data["data"]["conversation_count"] == 5
            assert data["data"]["message_count"] == 25
    
    def test_search_conversations(self, client):
        """Test searching conversations."""
        with patch('main.crm_service.search_conversations') as mock_search:
            mock_conversations = [Mock()]
            mock_conversations[0].to_dict.return_value = {
                "id": "conv-1",
                "title": "Property Search"
            }
            
            mock_search.return_value = {
                "conversations": mock_conversations,
                "total": 1,
                "page": 1,
                "per_page": 10,
                "pages": 1
            }
            
            response = client.get("/crm/search?q=property")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert len(data["data"]) == 1
    
    def test_get_rag_stats(self, client):
        """Test getting RAG statistics."""
        with patch('main.rag_service.get_collection_stats') as mock_stats:
            mock_stats.return_value = {
                "total_documents": 100,
                "collection_name": "knowledge_base"
            }
            
            response = client.get("/rag/stats")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert data["data"]["total_documents"] == 100
    
    def test_clear_rag_collection(self, client):
        """Test clearing RAG collection."""
        with patch('main.rag_service.clear_collection') as mock_clear:
            mock_clear.return_value = None
            
            response = client.delete("/rag/clear")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert "cleared successfully" in data["message"]
    
    def test_invalid_endpoint(self, client):
        """Test accessing invalid endpoint."""
        response = client.get("/invalid-endpoint")
        
        assert response.status_code == 404
    
    def test_chat_without_message(self, client):
        """Test chat endpoint without message."""
        response = client.post("/chat", json={})
        
        assert response.status_code == 422  # Validation error
    
    def test_create_user_invalid_data(self, client):
        """Test creating user with invalid data."""
        # Test with very long name
        user_data = {
            "name": "A" * 200,  # Exceeds max length
            "email": "invalid-email"  # Invalid email format
        }
        
        response = client.post("/crm/create_user", json=user_data)
        
        # Should still process but with validation constraints
        assert response.status_code in [200, 422]
    
    def test_pagination_parameters(self, client):
        """Test pagination parameters validation."""
        with patch('main.crm_service.list_users') as mock_list:
            mock_list.return_value = {
                "users": [],
                "total": 0,
                "page": 1,
                "per_page": 10,
                "pages": 0
            }
            
            # Test with invalid page (should default to 1)
            response = client.get("/crm/users?page=0")
            assert response.status_code == 422
            
            # Test with invalid per_page (should default to constraints)
            response = client.get("/crm/users?per_page=200")
            assert response.status_code == 422
    
    def test_error_handling(self, client):
        """Test error handling in endpoints."""
        with patch('main.crm_service.get_user') as mock_get:
            mock_get.side_effect = Exception("Database error")
            
            response = client.get("/crm/users/user-123")
            
            assert response.status_code == 500
            data = response.json()
            assert "Database error" in data["detail"]

if __name__ == "__main__":
    pytest.main([__file__]) 