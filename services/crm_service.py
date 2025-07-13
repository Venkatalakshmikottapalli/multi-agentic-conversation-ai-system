import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime
from models.crm_models import User, Conversation, Message
from database import get_db_context
from schemas.api_schemas import UserCreate, UserUpdate

logger = logging.getLogger(__name__)

class CRMService:
    """Service class for CRM operations."""
    
    def __init__(self):
        pass
    
    def create_user(self, user_data: UserCreate) -> Dict[str, Any]:
        """Create a new user."""
        try:
            with get_db_context() as db:
                user = User(
                    name=user_data.name,
                    email=user_data.email,
                    phone=user_data.phone,
                    company=user_data.company,
                    role=user_data.role,
                    preferences=user_data.preferences
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                
                # Convert to dict before session closes
                user_dict = user.to_dict()
                logger.info(f"User created successfully: {user.id}")
                return user_dict
                
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID."""
        try:
            with get_db_context() as db:
                user = db.query(User).filter(User.id == user_id).first()
                return user
                
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    def get_user_with_session(self, user_id: str, db: Session) -> Optional[User]:
        """Get a user by ID using an existing database session."""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            return user
                
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    def update_user(self, user_id: str, user_data: UserUpdate) -> Optional[Dict[str, Any]]:
        """Update a user."""
        try:
            with get_db_context() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    return None
                
                # Update fields if provided
                if user_data.name is not None:
                    user.name = user_data.name
                if user_data.email is not None:
                    user.email = user_data.email
                if user_data.phone is not None:
                    user.phone = user_data.phone
                if user_data.company is not None:
                    user.company = user_data.company
                if user_data.role is not None:
                    user.role = user_data.role
                if user_data.preferences is not None:
                    user.preferences = user_data.preferences
                
                user.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(user)
                
                # Convert to dict before session closes
                user_dict = user.to_dict()
                logger.info(f"User updated successfully: {user.id}")
                return user_dict
                
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            raise
    
    def delete_user(self, user_id: str) -> bool:
        """Delete a user (soft delete)."""
        try:
            with get_db_context() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    return False
                
                user.is_active = False
                user.updated_at = datetime.utcnow()
                db.commit()
                
                logger.info(f"User soft deleted: {user.id}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            return False
    
    def list_users(self, page: int = 1, per_page: int = 10, active_only: bool = True) -> Dict[str, Any]:
        """List users with pagination."""
        try:
            with get_db_context() as db:
                query = db.query(User)
                
                if active_only:
                    query = query.filter(User.is_active == True)
                
                total = query.count()
                users = query.offset((page - 1) * per_page).limit(per_page).all()
                
                # Convert to dicts before session closes
                users_dict = [user.to_dict() for user in users]
                
                return {
                    "users": users_dict,
                    "total": total,
                    "page": page,
                    "per_page": per_page,
                    "pages": (total + per_page - 1) // per_page
                }
                
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return {"users": [], "total": 0, "page": page, "per_page": per_page, "pages": 0}
    
    def get_user_conversations(self, user_id: str, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """Get conversations for a user."""
        try:
            with get_db_context() as db:
                query = db.query(Conversation).filter(Conversation.user_id == user_id)
                query = query.order_by(desc(Conversation.updated_at))
                
                total = query.count()
                conversations = query.offset((page - 1) * per_page).limit(per_page).all()
                
                # Convert to dicts before session closes
                conversations_dict = [conv.to_dict() for conv in conversations]
                
                return {
                    "conversations": conversations_dict,
                    "total": total,
                    "page": page,
                    "per_page": per_page,
                    "pages": (total + per_page - 1) // per_page
                }
                
        except Exception as e:
            logger.error(f"Error getting conversations for user {user_id}: {e}")
            return {"conversations": [], "total": 0, "page": page, "per_page": per_page, "pages": 0}
    
    def get_conversation_with_messages(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation with its messages."""
        try:
            with get_db_context() as db:
                conversation = db.query(Conversation).filter(
                    Conversation.id == conversation_id
                ).first()
                
                if conversation:
                    # Load messages
                    messages = db.query(Message).filter(
                        Message.conversation_id == conversation_id
                    ).order_by(Message.timestamp).all()
                    
                    # Add messages to conversation object
                    conversation.messages = messages
                
                return conversation
                
        except Exception as e:
            logger.error(f"Error getting conversation {conversation_id}: {e}")
            return None
    
    def update_conversation_status(self, conversation_id: str, status: str) -> bool:
        """Update conversation status."""
        try:
            with get_db_context() as db:
                conversation = db.query(Conversation).filter(
                    Conversation.id == conversation_id
                ).first()
                
                if not conversation:
                    return False
                
                conversation.status = status
                conversation.updated_at = datetime.utcnow()
                db.commit()
                
                logger.info(f"Conversation status updated: {conversation_id} -> {status}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating conversation status: {e}")
            return False
    
    def get_conversation_analytics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get conversation analytics."""
        try:
            with get_db_context() as db:
                query = db.query(Conversation)
                
                if user_id:
                    query = query.filter(Conversation.user_id == user_id)
                
                total_conversations = query.count()
                
                # Count by status
                status_counts = db.query(
                    Conversation.status,
                    func.count(Conversation.id).label('count')
                ).group_by(Conversation.status)
                
                if user_id:
                    status_counts = status_counts.filter(Conversation.user_id == user_id)
                
                status_data = {row.status: row.count for row in status_counts.all()}
                
                # Count by category
                category_counts = db.query(
                    Conversation.category,
                    func.count(Conversation.id).label('count')
                ).group_by(Conversation.category)
                
                if user_id:
                    category_counts = category_counts.filter(Conversation.user_id == user_id)
                
                category_data = {row.category: row.count for row in category_counts.all()}
                
                # Get recent conversations
                recent_conversations = query.order_by(
                    desc(Conversation.updated_at)
                ).limit(10).all()
                
                return {
                    "total_conversations": total_conversations,
                    "status_breakdown": status_data,
                    "category_breakdown": category_data,
                    "recent_conversations": [conv.to_dict() for conv in recent_conversations]
                }
                
        except Exception as e:
            logger.error(f"Error getting conversation analytics: {e}")
            return {}
    
    def search_conversations(self, search_term: str, user_id: Optional[str] = None, 
                           page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """Search conversations by content."""
        try:
            with get_db_context() as db:
                # Search in messages
                query = db.query(Conversation).join(Message).filter(
                    Message.content.ilike(f"%{search_term}%")
                )
                
                if user_id:
                    query = query.filter(Conversation.user_id == user_id)
                
                query = query.order_by(desc(Conversation.updated_at)).distinct()
                
                total = query.count()
                conversations = query.offset((page - 1) * per_page).limit(per_page).all()
                
                return {
                    "conversations": conversations,
                    "total": total,
                    "page": page,
                    "per_page": per_page,
                    "pages": (total + per_page - 1) // per_page,
                    "search_term": search_term
                }
                
        except Exception as e:
            logger.error(f"Error searching conversations: {e}")
            return {"conversations": [], "total": 0, "page": page, "per_page": per_page, "pages": 0}
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        try:
            with get_db_context() as db:
                user = db.query(User).filter(User.email == email).first()
                return user
                
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None
    
    def clear_user_conversations(self, user_id: str) -> int:
        """Clear all conversations for a user."""
        try:
            with get_db_context() as db:
                # Get all conversations for the user
                conversations = db.query(Conversation).filter(
                    Conversation.user_id == user_id
                ).all()
                
                count = 0
                for conversation in conversations:
                    # Delete all messages in the conversation
                    db.query(Message).filter(
                        Message.conversation_id == conversation.id
                    ).delete()
                    
                    # Delete the conversation
                    db.delete(conversation)
                    count += 1
                
                db.commit()
                logger.info(f"Cleared {count} conversations for user {user_id}")
                return count
                
        except Exception as e:
            logger.error(f"Error clearing conversations for user {user_id}: {e}")
            return 0
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics for a specific user."""
        try:
            with get_db_context() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    return {}
                
                # Get conversation count
                conversation_count = db.query(Conversation).filter(
                    Conversation.user_id == user_id
                ).count()
                
                # Get message count
                message_count = db.query(Message).join(Conversation).filter(
                    Conversation.user_id == user_id
                ).count()
                
                # Get last conversation
                last_conversation = db.query(Conversation).filter(
                    Conversation.user_id == user_id
                ).order_by(desc(Conversation.updated_at)).first()
                
                return {
                    "user": user.to_dict(),
                    "conversation_count": conversation_count,
                    "message_count": message_count,
                    "last_conversation": last_conversation.to_dict() if last_conversation else None
                }
                
        except Exception as e:
            logger.error(f"Error getting user stats for {user_id}: {e}")
            return {}

# Global CRM service instance
crm_service = CRMService() 