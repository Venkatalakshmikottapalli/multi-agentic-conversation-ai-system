import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from models.crm_models import User, Conversation, Message, UserSession
from database import get_db_context
from schemas.api_schemas import UserCreate, UserUpdate
import secrets

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

    def get_system_analytics(self) -> Dict[str, Any]:
        """Get comprehensive system analytics for admin use."""
        try:
            with get_db_context() as db:
                # Basic counts
                total_users = db.query(User).count()
                active_users = db.query(User).filter(User.is_active == True).count()
                total_conversations = db.query(Conversation).count()
                total_messages = db.query(Message).count()
                
                # Average messages per conversation
                avg_messages = total_messages / total_conversations if total_conversations > 0 else 0
                
                # Conversations by status
                status_counts = db.query(
                    Conversation.status,
                    func.count(Conversation.id).label('count')
                ).group_by(Conversation.status).all()
                conversations_by_status = {row.status: row.count for row in status_counts}
                
                # Conversations by category
                category_counts = db.query(
                    Conversation.category,
                    func.count(Conversation.id).label('count')
                ).group_by(Conversation.category).all()
                conversations_by_category = {row.category or 'uncategorized': row.count for row in category_counts}
                
                # Users by role
                role_counts = db.query(
                    User.role,
                    func.count(User.id).label('count')
                ).group_by(User.role).all()
                users_by_role = {row.role or 'unspecified': row.count for row in role_counts}
                
                # Recent activity (last 10 conversations)
                recent_conversations = db.query(Conversation).order_by(
                    desc(Conversation.updated_at)
                ).limit(10).all()
                recent_activity = [
                    {
                        "id": conv.id,
                        "user_id": conv.user_id,
                        "category": conv.category,
                        "status": conv.status,
                        "updated_at": conv.updated_at.isoformat() if conv.updated_at else None
                    }
                    for conv in recent_conversations
                ]
                
                # Top users by conversation count
                top_users_query = db.query(
                    User.id,
                    User.name,
                    User.email,
                    func.count(Conversation.id).label('conversation_count')
                ).join(Conversation).group_by(User.id).order_by(
                    desc(func.count(Conversation.id))
                ).limit(10).all()
                
                top_users = [
                    {
                        "user_id": row.id,
                        "name": row.name,
                        "email": row.email,
                        "conversation_count": row.conversation_count
                    }
                    for row in top_users_query
                ]
                
                # Agent usage stats (from message metadata)
                agent_usage = {}
                messages_with_metadata = db.query(Message).filter(
                    Message.metadata.isnot(None)
                ).all()
                
                for msg in messages_with_metadata:
                    if msg.metadata and isinstance(msg.metadata, dict):
                        agent = msg.metadata.get('agent_used', 'unknown')
                        agent_usage[agent] = agent_usage.get(agent, 0) + 1
                
                # System performance metrics
                system_performance = {
                    "total_storage_mb": self._calculate_database_size(),
                    "average_response_time": self._calculate_average_response_time(),
                    "error_rate": self._calculate_error_rate()
                }
                
                return {
                    "total_users": total_users,
                    "active_users": active_users,
                    "total_conversations": total_conversations,
                    "total_messages": total_messages,
                    "average_messages_per_conversation": round(avg_messages, 2),
                    "conversations_by_status": conversations_by_status,
                    "conversations_by_category": conversations_by_category,
                    "users_by_role": users_by_role,
                    "recent_activity": recent_activity,
                    "top_users": top_users,
                    "agent_usage_stats": agent_usage,
                    "system_performance": system_performance
                }
                
        except Exception as e:
            logger.error(f"Error getting system analytics: {e}")
            return {}

    def get_detailed_user_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get detailed analytics for a specific user."""
        try:
            with get_db_context() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    return {}
                
                # Basic user stats
                conversations = db.query(Conversation).filter(
                    Conversation.user_id == user_id
                ).all()
                
                total_conversations = len(conversations)
                total_messages = db.query(Message).join(Conversation).filter(
                    Conversation.user_id == user_id
                ).count()
                
                avg_messages = total_messages / total_conversations if total_conversations > 0 else 0
                
                # Most used agent
                agent_usage = {}
                messages_with_metadata = db.query(Message).join(Conversation).filter(
                    Conversation.user_id == user_id,
                    Message.metadata.isnot(None)
                ).all()
                
                for msg in messages_with_metadata:
                    if msg.metadata and isinstance(msg.metadata, dict):
                        agent = msg.metadata.get('agent_used', 'unknown')
                        agent_usage[agent] = agent_usage.get(agent, 0) + 1
                
                most_used_agent = max(agent_usage.items(), key=lambda x: x[1])[0] if agent_usage else None
                
                # Conversation categories and statuses
                conversation_categories = {}
                conversation_statuses = {}
                
                for conv in conversations:
                    category = conv.category or 'uncategorized'
                    status = conv.status
                    conversation_categories[category] = conversation_categories.get(category, 0) + 1
                    conversation_statuses[status] = conversation_statuses.get(status, 0) + 1
                
                # First and last conversation dates
                first_conversation = min(conv.created_at for conv in conversations) if conversations else None
                last_conversation = max(conv.updated_at for conv in conversations) if conversations else None
                
                # User activity trend (conversations per day for last 30 days)
                activity_trend = []
                if conversations:
                    # Simple activity trend - count conversations per day
                    activity_trend = self._get_user_activity_trend(user_id, db)
                
                return {
                    "user_id": user_id,
                    "user_name": user.name,
                    "user_email": user.email,
                    "total_conversations": total_conversations,
                    "total_messages": total_messages,
                    "average_messages_per_conversation": round(avg_messages, 2),
                    "most_used_agent": most_used_agent,
                    "conversation_categories": conversation_categories,
                    "conversation_statuses": conversation_statuses,
                    "first_conversation": first_conversation.isoformat() if first_conversation else None,
                    "last_conversation": last_conversation.isoformat() if last_conversation else None,
                    "user_activity_trend": activity_trend
                }
                
        except Exception as e:
            logger.error(f"Error getting detailed user analytics for {user_id}: {e}")
            return {}

    def _calculate_database_size(self) -> float:
        """Calculate approximate database size in MB."""
        try:
            # This is a simplified calculation
            # In a real implementation, you'd query the database system tables
            return 10.5  # Placeholder
        except Exception:
            return 0.0

    def _calculate_average_response_time(self) -> float:
        """Calculate average response time from message metadata."""
        try:
            with get_db_context() as db:
                messages_with_metadata = db.query(Message).filter(
                    Message.metadata.isnot(None)
                ).limit(100).all()
                
                response_times = []
                for msg in messages_with_metadata:
                    if msg.metadata and isinstance(msg.metadata, dict):
                        response_time = msg.metadata.get('processing_time')
                        if response_time and isinstance(response_time, (int, float)):
                            response_times.append(response_time)
                
                return sum(response_times) / len(response_times) if response_times else 0.0
                
        except Exception:
            return 0.0

    def _calculate_error_rate(self) -> float:
        """Calculate error rate from system logs."""
        try:
            # This would ideally read from a logging system
            # For now, return a placeholder
            return 0.02  # 2% error rate
        except Exception:
            return 0.0

    def _get_user_activity_trend(self, user_id: str, db: Session) -> List[Dict[str, Any]]:
        """Get user activity trend for the last 30 days."""
        try:
            from datetime import datetime, timedelta
            
            # Get conversations from last 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            conversations = db.query(Conversation).filter(
                Conversation.user_id == user_id,
                Conversation.created_at >= thirty_days_ago
            ).all()
            
            # Group by date
            activity_by_date = {}
            for conv in conversations:
                date_str = conv.created_at.strftime('%Y-%m-%d')
                activity_by_date[date_str] = activity_by_date.get(date_str, 0) + 1
            
            # Create trend data
            trend_data = []
            for i in range(30):
                date = (datetime.utcnow() - timedelta(days=i)).strftime('%Y-%m-%d')
                trend_data.append({
                    "date": date,
                    "conversations": activity_by_date.get(date, 0)
                })
            
            return sorted(trend_data, key=lambda x: x['date'])
            
        except Exception as e:
            logger.error(f"Error getting user activity trend: {e}")
            return []

    def create_user_session(self, user_id: str, expires_in_hours: int = 24) -> Dict[str, Any]:
        """Create a new user session with token."""
        try:
            with get_db_context() as db:
                # Check if user exists
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    raise ValueError(f"User {user_id} not found")
                
                # Deactivate existing sessions for this user
                existing_sessions = db.query(UserSession).filter(
                    UserSession.user_id == user_id,
                    UserSession.is_active == True
                ).all()
                
                for session in existing_sessions:
                    session.is_active = False
                
                # Create new session
                session_token = secrets.token_urlsafe(32)
                expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
                
                user_session = UserSession(
                    user_id=user_id,
                    session_token=session_token,
                    expires_at=expires_at,
                    is_active=True
                )
                
                db.add(user_session)
                db.commit()
                db.refresh(user_session)
                
                logger.info(f"Created session for user {user_id}: {user_session.id}")
                
                return {
                    "session_id": user_session.id,
                    "session_token": session_token,
                    "user_id": user_id,
                    "expires_at": expires_at.isoformat(),
                    "created_at": user_session.created_at.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error creating user session: {e}")
            raise
    
    def get_user_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Get user session by token."""
        try:
            with get_db_context() as db:
                user_session = db.query(UserSession).filter(
                    UserSession.session_token == session_token,
                    UserSession.is_active == True,
                    UserSession.expires_at > datetime.utcnow()
                ).first()
                
                if user_session:
                    return {
                        "session_id": user_session.id,
                        "user_id": user_session.user_id,
                        "session_token": user_session.session_token,
                        "expires_at": user_session.expires_at.isoformat(),
                        "created_at": user_session.created_at.isoformat()
                    }
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting user session: {e}")
            return None
    
    def validate_session(self, session_token: str) -> Optional[User]:
        """Validate session token and return user if valid."""
        try:
            with get_db_context() as db:
                user_session = db.query(UserSession).filter(
                    UserSession.session_token == session_token,
                    UserSession.is_active == True,
                    UserSession.expires_at > datetime.utcnow()
                ).first()
                
                if user_session:
                    user = db.query(User).filter(User.id == user_session.user_id).first()
                    return user
                
                return None
                
        except Exception as e:
            logger.error(f"Error validating session: {e}")
            return None
    
    def extend_session(self, session_token: str, extend_hours: int = 24) -> bool:
        """Extend session expiration time."""
        try:
            with get_db_context() as db:
                user_session = db.query(UserSession).filter(
                    UserSession.session_token == session_token,
                    UserSession.is_active == True
                ).first()
                
                if user_session:
                    user_session.expires_at = datetime.utcnow() + timedelta(hours=extend_hours)
                    db.commit()
                    logger.info(f"Extended session {user_session.id} by {extend_hours} hours")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error extending session: {e}")
            return False
    
    def revoke_session(self, session_token: str) -> bool:
        """Revoke/deactivate a session."""
        try:
            with get_db_context() as db:
                user_session = db.query(UserSession).filter(
                    UserSession.session_token == session_token,
                    UserSession.is_active == True
                ).first()
                
                if user_session:
                    user_session.is_active = False
                    db.commit()
                    logger.info(f"Revoked session {user_session.id}")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error revoking session: {e}")
            return False
    
    def get_user_sessions(self, user_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all sessions for a user."""
        try:
            with get_db_context() as db:
                query = db.query(UserSession).filter(UserSession.user_id == user_id)
                
                if active_only:
                    query = query.filter(
                        UserSession.is_active == True,
                        UserSession.expires_at > datetime.utcnow()
                    )
                
                sessions = query.order_by(desc(UserSession.created_at)).all()
                
                return [session.to_dict() for session in sessions]
                
        except Exception as e:
            logger.error(f"Error getting user sessions: {e}")
            return []
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        try:
            with get_db_context() as db:
                expired_sessions = db.query(UserSession).filter(
                    UserSession.expires_at < datetime.utcnow(),
                    UserSession.is_active == True
                ).all()
                
                count = len(expired_sessions)
                
                for session in expired_sessions:
                    session.is_active = False
                
                db.commit()
                logger.info(f"Cleaned up {count} expired sessions")
                return count
                
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
            return 0

# Global CRM service instance
crm_service = CRMService() 