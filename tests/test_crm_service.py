import pytest
import sqlite3
import tempfile
import os
from unittest.mock import Mock, patch
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.crm_models import Base, User, Conversation, Message
from services.crm_service import CRMService
from schemas.api_schemas import UserCreate, UserUpdate

class TestCRMService:
    """Test cases for CRM service."""
    
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
    
    @pytest.fixture
    def crm_service(self, test_db):
        """Create CRM service with test database."""
        SessionLocal, db_path = test_db
        
        service = CRMService()
        
        # Mock the database context
        with patch('services.crm_service.get_db_context') as mock_context:
            mock_context.return_value.__enter__.return_value = SessionLocal()
            yield service
    
    def test_create_user(self, crm_service):
        """Test user creation."""
        user_data = UserCreate(
            name="John Doe",
            email="john@example.com",
            phone="123-456-7890",
            company="Test Corp",
            role="Manager"
        )
        
        with patch('services.crm_service.get_db_context') as mock_context:
            mock_db = Mock()
            mock_context.return_value.__enter__.return_value = mock_db
            
            user = crm_service.create_user(user_data)
            
            assert mock_db.add.called
            assert mock_db.commit.called
            assert user.name == "John Doe"
            assert user.email == "john@example.com"
    
    def test_get_user(self, crm_service):
        """Test getting a user by ID."""
        user_id = "test-user-id"
        
        with patch('services.crm_service.get_db_context') as mock_context:
            mock_db = Mock()
            mock_user = Mock()
            mock_user.id = user_id
            mock_db.query.return_value.filter.return_value.first.return_value = mock_user
            mock_context.return_value.__enter__.return_value = mock_db
            
            user = crm_service.get_user(user_id)
            
            assert user.id == user_id
            assert mock_db.query.called
    
    def test_update_user(self, crm_service):
        """Test updating a user."""
        user_id = "test-user-id"
        user_data = UserUpdate(name="Updated Name")
        
        with patch('services.crm_service.get_db_context') as mock_context:
            mock_db = Mock()
            mock_user = Mock()
            mock_user.id = user_id
            mock_user.name = "Old Name"
            mock_db.query.return_value.filter.return_value.first.return_value = mock_user
            mock_context.return_value.__enter__.return_value = mock_db
            
            updated_user = crm_service.update_user(user_id, user_data)
            
            assert updated_user.name == "Updated Name"
            assert mock_db.commit.called
    
    def test_delete_user(self, crm_service):
        """Test soft deleting a user."""
        user_id = "test-user-id"
        
        with patch('services.crm_service.get_db_context') as mock_context:
            mock_db = Mock()
            mock_user = Mock()
            mock_user.id = user_id
            mock_user.is_active = True
            mock_db.query.return_value.filter.return_value.first.return_value = mock_user
            mock_context.return_value.__enter__.return_value = mock_db
            
            result = crm_service.delete_user(user_id)
            
            assert result == True
            assert mock_user.is_active == False
            assert mock_db.commit.called
    
    def test_list_users(self, crm_service):
        """Test listing users with pagination."""
        with patch('services.crm_service.get_db_context') as mock_context:
            mock_db = Mock()
            mock_users = [Mock(), Mock()]
            mock_db.query.return_value.filter.return_value.count.return_value = 2
            mock_db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = mock_users
            mock_context.return_value.__enter__.return_value = mock_db
            
            result = crm_service.list_users(page=1, per_page=10)
            
            assert result["total"] == 2
            assert len(result["users"]) == 2
            assert result["page"] == 1
            assert result["per_page"] == 10
    
    def test_get_user_conversations(self, crm_service):
        """Test getting conversations for a user."""
        user_id = "test-user-id"
        
        with patch('services.crm_service.get_db_context') as mock_context:
            mock_db = Mock()
            mock_conversations = [Mock(), Mock()]
            mock_db.query.return_value.filter.return_value.order_by.return_value.count.return_value = 2
            mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_conversations
            mock_context.return_value.__enter__.return_value = mock_db
            
            result = crm_service.get_user_conversations(user_id)
            
            assert result["total"] == 2
            assert len(result["conversations"]) == 2
    
    def test_get_conversation_analytics(self, crm_service):
        """Test getting conversation analytics."""
        with patch('services.crm_service.get_db_context') as mock_context:
            mock_db = Mock()
            
            # Mock the main conversation query
            mock_query = Mock()
            mock_query.count.return_value = 5
            
            # Mock status counts query
            mock_status_query = Mock()
            mock_status_row1 = Mock()
            mock_status_row1.status = "active"
            mock_status_row1.count = 3
            mock_status_row2 = Mock()
            mock_status_row2.status = "resolved"
            mock_status_row2.count = 2
            
            mock_status_query.group_by.return_value = mock_status_query
            mock_status_query.all.return_value = [mock_status_row1, mock_status_row2]
            
            # Mock category counts query
            mock_category_query = Mock()
            mock_category_row1 = Mock()
            mock_category_row1.category = "support"
            mock_category_row1.count = 4
            mock_category_row2 = Mock()
            mock_category_row2.category = "sales"
            mock_category_row2.count = 1
            
            mock_category_query.group_by.return_value = mock_category_query
            mock_category_query.all.return_value = [mock_category_row1, mock_category_row2]
            
            # Mock recent conversations query
            mock_recent_convs = [Mock(), Mock()]
            for conv in mock_recent_convs:
                conv.to_dict.return_value = {"id": "test-id", "status": "active"}
            mock_query.order_by.return_value.limit.return_value.all.return_value = mock_recent_convs
            
            # Set up the db.query return values based on the query being made
            def mock_query_side_effect(*args):
                if len(args) == 1:  # Single model query - main conversation query
                    return mock_query
                elif len(args) == 2:  # Multiple args - status/category count queries
                    # Check if it's a status or category query by examining the attributes
                    if hasattr(args[0], 'status') or 'status' in str(args[0]):
                        return mock_status_query
                    elif hasattr(args[0], 'category') or 'category' in str(args[0]):
                        return mock_category_query
                    else:
                        return mock_query
                else:
                    return mock_query
            
            mock_db.query.side_effect = mock_query_side_effect
            mock_context.return_value.__enter__.return_value = mock_db
            
            result = crm_service.get_conversation_analytics()
            
            assert result["total_conversations"] == 5
            assert "status_breakdown" in result
            assert "category_breakdown" in result
            assert result["status_breakdown"]["active"] == 3
            assert result["status_breakdown"]["resolved"] == 2
            assert result["category_breakdown"]["support"] == 4
            assert result["category_breakdown"]["sales"] == 1
    
    def test_search_conversations(self, crm_service):
        """Test searching conversations."""
        search_term = "test query"
        
        with patch('services.crm_service.get_db_context') as mock_context:
            mock_db = Mock()
            mock_conversations = [Mock()]
            mock_db.query.return_value.join.return_value.filter.return_value.order_by.return_value.distinct.return_value.count.return_value = 1
            mock_db.query.return_value.join.return_value.filter.return_value.order_by.return_value.distinct.return_value.offset.return_value.limit.return_value.all.return_value = mock_conversations
            mock_context.return_value.__enter__.return_value = mock_db
            
            result = crm_service.search_conversations(search_term)
            
            assert result["total"] == 1
            assert len(result["conversations"]) == 1
            assert result["search_term"] == search_term
    
    def test_clear_user_conversations(self, crm_service):
        """Test clearing conversations for a user."""
        user_id = "test-user-id"
        
        with patch('services.crm_service.get_db_context') as mock_context:
            mock_db = Mock()
            mock_conversations = [Mock(id="conv1"), Mock(id="conv2")]
            mock_db.query.return_value.filter.return_value.all.return_value = mock_conversations
            mock_context.return_value.__enter__.return_value = mock_db
            
            count = crm_service.clear_user_conversations(user_id)
            
            assert count == 2
            assert mock_db.commit.called
    
    def test_get_user_stats(self, crm_service):
        """Test getting user statistics."""
        user_id = "test-user-id"
        
        with patch('services.crm_service.get_db_context') as mock_context:
            mock_db = Mock()
            mock_user = Mock()
            mock_user.to_dict.return_value = {"id": user_id, "name": "Test User"}
            mock_db.query.return_value.filter.return_value.first.return_value = mock_user
            mock_db.query.return_value.filter.return_value.count.return_value = 5
            mock_db.query.return_value.join.return_value.filter.return_value.count.return_value = 25
            mock_context.return_value.__enter__.return_value = mock_db
            
            stats = crm_service.get_user_stats(user_id)
            
            assert stats["user"]["id"] == user_id
            assert stats["conversation_count"] == 5
            assert stats["message_count"] == 25

if __name__ == "__main__":
    pytest.main([__file__]) 