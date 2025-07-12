import logging
import time
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from openai import OpenAI
from sqlalchemy.orm import Session
from config import settings
from models.crm_models import User, Conversation, Message
from database import get_db_context
from services.rag_service import rag_service

logger = logging.getLogger(__name__)

class Agent:
    """Base agent class for the multi-agent system."""
    
    def __init__(self, name: str, role: str, instructions: str):
        self.name = name
        self.role = role
        self.instructions = instructions
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        return f"""You are {self.name}, a {self.role}.

Instructions: {self.instructions}

Always maintain a professional and helpful tone. Use the provided context to give accurate and relevant responses."""

class ConversationManager:
    """Manages conversation state and memory."""
    
    def __init__(self):
        self.active_conversations: Dict[str, List[Dict]] = {}
        self.max_history = settings.max_conversation_history
    
    def get_conversation_history(self, session_id: str, user_id: str) -> List[Dict]:
        """Get conversation history for a session."""
        try:
            with get_db_context() as db:
                # Get or create conversation
                conversation = db.query(Conversation).filter(
                    Conversation.session_id == session_id,
                    Conversation.user_id == user_id
                ).first()
                
                if not conversation:
                    return []
                
                # Get recent messages
                messages = db.query(Message).filter(
                    Message.conversation_id == conversation.id
                ).order_by(Message.timestamp.desc()).limit(self.max_history).all()
                
                # Convert to chat format
                history = []
                for msg in reversed(messages):
                    history.append({
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
                    })
                
                return history
                
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    def save_message(self, session_id: str, user_id: str, role: str, content: str, 
                    metadata: Optional[Dict] = None) -> str:
        """Save a message to the conversation."""
        try:
            with get_db_context() as db:
                # Get or create conversation
                conversation = db.query(Conversation).filter(
                    Conversation.session_id == session_id,
                    Conversation.user_id == user_id
                ).first()
                
                if not conversation:
                    conversation = Conversation(
                        user_id=user_id,
                        session_id=session_id,
                        title=f"Chat Session {session_id[:8]}",
                        category="general",
                        status="active"
                    )
                    db.add(conversation)
                    db.flush()
                
                # Create message
                message = Message(
                    conversation_id=conversation.id,
                    role=role,
                    content=content,
                    metadata=metadata
                )
                db.add(message)
                db.commit()
                
                return message.id
                
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            raise

class ChatAgent:
    """Main chat agent that coordinates the multi-agent system."""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.conversation_manager = ConversationManager()
        self.agents = self._initialize_agents()
    
    def _initialize_agents(self) -> Dict[str, Agent]:
        """Initialize the different agents in the system."""
        agents = {
            "real_estate_agent": Agent(
                name="Real Estate Specialist",
                role="Real Estate Expert",
                instructions="""You are a knowledgeable real estate specialist with expertise in commercial and residential properties. 
                You help clients find properties, understand market conditions, and provide detailed information about available listings.
                Use the retrieved property data to provide accurate information about specific properties, including pricing, size, location, and broker contacts.
                Always be professional and focus on the client's needs."""
            ),
            "crm_agent": Agent(
                name="CRM Assistant",
                role="Customer Relationship Manager",
                instructions="""You are a CRM assistant that helps capture and organize customer information during conversations.
                You naturally extract user details like name, email, phone, company, and preferences from conversations.
                You help categorize conversations and maintain customer relationships.
                Be subtle when collecting information - don't make it feel like an interrogation."""
            ),
            "general_agent": Agent(
                name="General Assistant",
                role="General Purpose Assistant",
                instructions="""You are a helpful general assistant that can answer questions and provide information on various topics.
                You work with other specialized agents to provide comprehensive responses.
                Be friendly, professional, and always try to be helpful."""
            )
        }
        return agents
    
    def process_message(self, message: str, user_id: str = None, session_id: str = None, 
                       context: Optional[Dict] = None) -> Dict[str, Any]:
        """Process a user message and return a response."""
        start_time = time.time()
        
        try:
            # Generate user_id and session_id if not provided
            if not user_id:
                user_id = str(uuid.uuid4())
            if not session_id:
                session_id = str(uuid.uuid4())
            
            # Ensure user exists in database
            user = self._ensure_user_exists(user_id)
            
            # Save user message
            self.conversation_manager.save_message(
                session_id=session_id,
                user_id=user_id,
                role="user",
                content=message
            )
            
            # Get conversation history
            history = self.conversation_manager.get_conversation_history(session_id, user_id)
            
            # Determine which agent to use
            agent = self._select_agent(message, history)
            
            # Get RAG context
            rag_context = rag_service.retrieve_documents(message)
            
            # Extract user information from conversation
            user_info = self._extract_user_info(message, history, user_id)
            
            # Generate response
            response, sources = self._generate_response(
                agent=agent,
                message=message,
                history=history,
                rag_context=rag_context,
                user_info=user_info,
                context=context
            )
            
            # Save assistant response
            message_id = self.conversation_manager.save_message(
                session_id=session_id,
                user_id=user_id,
                role="assistant",
                content=response,
                metadata={
                    "agent_used": agent.name,
                    "rag_sources": sources,
                    "user_info_extracted": user_info
                }
            )
            
            # Update conversation category
            self._update_conversation_category(session_id, user_id, message, response)
            
            processing_time = time.time() - start_time
            
            return {
                "response": response,
                "user_id": user_id,
                "session_id": session_id,
                "conversation_id": self._get_conversation_id(session_id, user_id),
                "sources": sources,
                "metadata": {
                    "agent_used": agent.name,
                    "processing_time": processing_time,
                    "rag_documents_found": len(rag_context),
                    "user_info_extracted": user_info
                },
                "processing_time": processing_time
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            raise
    
    def _ensure_user_exists(self, user_id: str) -> User:
        """Ensure user exists in the database."""
        try:
            with get_db_context() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    user = User(id=user_id)
                    db.add(user)
                    db.commit()
                return user
        except Exception as e:
            logger.error(f"Error ensuring user exists: {e}")
            raise
    
    def _select_agent(self, message: str, history: List[Dict]) -> Agent:
        """Select the appropriate agent based on message content."""
        message_lower = message.lower()
        
        # Real estate keywords
        real_estate_keywords = [
            "property", "rent", "lease", "office", "space", "building", "address",
            "square feet", "sf", "floor", "suite", "broker", "real estate",
            "commercial", "residential", "listing", "available", "price"
        ]
        
        # CRM keywords
        crm_keywords = [
            "my name is", "i am", "contact", "email", "phone", "company",
            "call me", "reach me", "information", "details"
        ]
        
        # Check for real estate context
        if any(keyword in message_lower for keyword in real_estate_keywords):
            return self.agents["real_estate_agent"]
        
        # Check for CRM context
        if any(keyword in message_lower for keyword in crm_keywords):
            return self.agents["crm_agent"]
        
        # Check conversation history for context
        if history:
            recent_messages = " ".join([msg["content"] for msg in history[-3:]])
            if any(keyword in recent_messages.lower() for keyword in real_estate_keywords):
                return self.agents["real_estate_agent"]
        
        # Default to general agent
        return self.agents["general_agent"]
    
    def _extract_user_info(self, message: str, history: List[Dict], user_id: str) -> Dict[str, Any]:
        """Extract user information from the conversation."""
        try:
            # Use OpenAI to extract structured information
            extraction_prompt = f"""
            Analyze this conversation and extract any personal information about the user.
            
            Current message: {message}
            
            Recent conversation history:
            {chr(10).join([f"{msg['role']}: {msg['content']}" for msg in history[-5:]])}
            
            Extract the following information if mentioned:
            - Name
            - Email
            - Phone number
            - Company name
            - Job title/role
            - Preferences or interests
            
            Return a JSON object with the extracted information. If no information is found, return an empty object.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an information extraction assistant. Return only valid JSON."},
                    {"role": "user", "content": extraction_prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            import json
            extracted_info = json.loads(response.choices[0].message.content)
            
            # Update user in database if new information is found
            if extracted_info:
                self._update_user_info(user_id, extracted_info)
            
            return extracted_info
            
        except Exception as e:
            logger.error(f"Error extracting user info: {e}")
            return {}
    
    def _update_user_info(self, user_id: str, info: Dict[str, Any]):
        """Update user information in the database."""
        try:
            with get_db_context() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    if "name" in info and info["name"]:
                        user.name = info["name"]
                    if "email" in info and info["email"]:
                        user.email = info["email"]
                    if "phone" in info and info["phone"]:
                        user.phone = info["phone"]
                    if "company" in info and info["company"]:
                        user.company = info["company"]
                    if "role" in info and info["role"]:
                        user.role = info["role"]
                    
                    # Update preferences
                    if not user.preferences:
                        user.preferences = {}
                    
                    for key, value in info.items():
                        if key not in ["name", "email", "phone", "company", "role"]:
                            user.preferences[key] = value
                    
                    user.updated_at = datetime.utcnow()
                    db.commit()
                    
        except Exception as e:
            logger.error(f"Error updating user info: {e}")
    
    def _generate_response(self, agent: Agent, message: str, history: List[Dict],
                          rag_context: List[Dict], user_info: Dict, context: Optional[Dict] = None) -> Tuple[str, List[Dict]]:
        """Generate a response using the selected agent."""
        try:
            # Prepare context
            context_text = ""
            sources = []
            
            if rag_context:
                context_text = "Relevant information from knowledge base:\n"
                for i, doc in enumerate(rag_context):
                    context_text += f"{i+1}. {doc['content']}\n"
                    sources.append({
                        "source": doc['metadata'].get('filename', 'Unknown'),
                        "content": doc['content'][:200] + "..." if len(doc['content']) > 200 else doc['content'],
                        "similarity_score": doc['similarity_score']
                    })
                context_text += "\n"
            
            # Prepare user context
            user_context = ""
            if user_info:
                user_context = f"User information: {user_info}\n"
            
            # Prepare conversation history
            history_text = ""
            if history:
                history_text = "Previous conversation:\n"
                for msg in history[-10:]:  # Last 10 messages
                    history_text += f"{msg['role']}: {msg['content']}\n"
                history_text += "\n"
            
            # Create the prompt
            system_prompt = agent.get_system_prompt()
            user_prompt = f"""
            {context_text}
            {user_context}
            {history_text}
            
            Current user message: {message}
            
            Please provide a helpful and accurate response based on the available context.
            """
            
            # Generate response
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=settings.default_temperature,
                max_tokens=settings.max_tokens
            )
            
            return response.choices[0].message.content, sources
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again later.", []
    
    def _update_conversation_category(self, session_id: str, user_id: str, user_message: str, response: str):
        """Update conversation category based on content."""
        try:
            with get_db_context() as db:
                conversation = db.query(Conversation).filter(
                    Conversation.session_id == session_id,
                    Conversation.user_id == user_id
                ).first()
                
                if conversation:
                    # Analyze conversation to determine category
                    combined_text = user_message + " " + response
                    
                    if any(keyword in combined_text.lower() for keyword in ["property", "rent", "lease", "office", "real estate"]):
                        conversation.category = "real_estate"
                    elif any(keyword in combined_text.lower() for keyword in ["contact", "information", "details"]):
                        conversation.category = "crm"
                    elif any(keyword in combined_text.lower() for keyword in ["help", "support", "problem"]):
                        conversation.category = "support"
                    else:
                        conversation.category = "general"
                    
                    db.commit()
                    
        except Exception as e:
            logger.error(f"Error updating conversation category: {e}")
    
    def _get_conversation_id(self, session_id: str, user_id: str) -> str:
        """Get conversation ID for a session."""
        try:
            with get_db_context() as db:
                conversation = db.query(Conversation).filter(
                    Conversation.session_id == session_id,
                    Conversation.user_id == user_id
                ).first()
                
                return conversation.id if conversation else ""
                
        except Exception as e:
            logger.error(f"Error getting conversation ID: {e}")
            return ""

# Global chat agent instance
chat_agent = ChatAgent() 