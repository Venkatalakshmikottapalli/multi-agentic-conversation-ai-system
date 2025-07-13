from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
import time
from typing import Optional, List
import aiofiles
import os
from datetime import datetime
from contextlib import asynccontextmanager
import PyPDF2
from io import BytesIO
import json

# Import configurations and services
from config import settings
from database import get_db, create_tables, get_db_context
from services.chat_agent import chat_agent
from services.rag_service import rag_service
from services.crm_service import crm_service
from services.settings_service import settings_service
from schemas.api_schemas import (
    ChatMessage, ChatResponse, UserCreate, UserUpdate, UserResponse,
    ConversationResponse, ConversationWithMessages, MessageResponse,
    DocumentResponse, ResetRequest, ResetResponse, APIResponse,
    PaginatedResponse, HealthResponse, SystemAnalytics, UserAnalytics,
    SystemSettings, SettingsUpdate, SystemOverview
)
from models.crm_models import User, UserSession, Conversation, Message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    try:
        create_tables()
        logger.info("Application started successfully")
        
        # Load initial CSV data into RAG system
        await load_initial_data()
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    
    yield
    
    # Shutdown (if needed)
    logger.info("Application shutting down")

# Create FastAPI app
app = FastAPI(
    title="Multi-Agent Conversational AI System",
    description="A comprehensive chatbot system with RAG and CRM capabilities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for serving React frontend
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Database initialization is now handled in the lifespan context manager

async def load_initial_data():
    """Load all data files from the data/ directory into the RAG system."""
    try:
        # Check if data already exists to prevent duplicates
        stats = rag_service.get_collection_stats()
        if stats.get("total_documents", 0) > 0:
            logger.info(f"Initial data already loaded ({stats['total_documents']} documents), skipping data processing")
            return
            
        data_directory = "data"
        if not os.path.exists(data_directory):
            logger.warning(f"Data directory '{data_directory}' not found")
            return
            
        # Get all files from the data directory
        data_files = []
        for filename in os.listdir(data_directory):
            file_path = os.path.join(data_directory, filename)
            if os.path.isfile(file_path):
                data_files.append((filename, file_path))
        
        if not data_files:
            logger.warning("No files found in data directory")
            return
            
        logger.info(f"Found {len(data_files)} files to process in data directory")
        
        # Process each file based on its type
        loaded_count = 0
        for filename, file_path in data_files:
            try:
                file_extension = filename.lower().split('.')[-1]
                
                if file_extension == 'csv':
                    # Process CSV files
                    with open(file_path, 'r', encoding='utf-8') as f:
                        csv_content = f.read()
                    rag_service.process_csv_data(csv_content, filename)
                    logger.info(f"Loaded CSV file: {filename}")
                    loaded_count += 1
                    
                elif file_extension == 'json':
                    # Process JSON files
                    with open(file_path, 'r', encoding='utf-8') as f:
                        json_content = f.read()
                        try:
                            json_data = json.loads(json_content)
                            # Convert JSON to readable text format
                            readable_text = _json_to_readable_text(json_data, filename)
                            rag_service.process_document(readable_text, filename, "application/json")
                            logger.info(f"Loaded JSON file: {filename}")
                            loaded_count += 1
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON format in file: {filename}")
                            
                elif file_extension == 'txt':
                    # Process text files
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text_content = f.read()
                    rag_service.process_document(text_content, filename, "text/plain")
                    logger.info(f"Loaded text file: {filename}")
                    loaded_count += 1
                    
                elif file_extension == 'pdf':
                    # Process PDF files
                    try:
                        with open(file_path, 'rb') as f:
                            pdf_reader = PyPDF2.PdfReader(f)
                            text_content = ""
                            for page in pdf_reader.pages:
                                text_content += page.extract_text() + "\n"
                        
                        if text_content.strip():
                            rag_service.process_document(text_content, filename, "application/pdf")
                            logger.info(f"Loaded PDF file: {filename}")
                            loaded_count += 1
                        else:
                            logger.warning(f"No text content extracted from PDF: {filename}")
                    except Exception as pdf_error:
                        logger.error(f"Error processing PDF {filename}: {pdf_error}")
                        
                else:
                    # Handle other file types as plain text
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        rag_service.process_document(content, filename, "text/plain")
                        logger.info(f"Loaded file as text: {filename}")
                        loaded_count += 1
                    except UnicodeDecodeError:
                        logger.warning(f"Skipping binary file: {filename}")
                        
            except Exception as file_error:
                logger.error(f"Error processing file {filename}: {file_error}")
                
        logger.info(f"Successfully loaded {loaded_count} out of {len(data_files)} files from data directory")
        
    except Exception as e:
        logger.error(f"Error loading initial data: {e}")

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        # Check database connection
        db_status = "healthy"
        try:
            with get_db_context() as db:
                db.execute(text("SELECT 1"))
        except Exception:
            db_status = "unhealthy"
        
        # Check vector store
        vector_status = "healthy"
        try:
            stats = rag_service.get_collection_stats()
            if "error" in stats:
                vector_status = "unhealthy"
        except Exception:
            vector_status = "unhealthy"
        
        # Check OpenAI connection
        openai_status = "healthy"
        try:
            # This is a simple check - in production you might want to make a test call
            if not settings.openai_api_key:
                openai_status = "unhealthy"
        except Exception:
            openai_status = "unhealthy"
        
        overall_status = "healthy" if all([
            db_status == "healthy",
            vector_status == "healthy",
            openai_status == "healthy"
        ]) else "unhealthy"
        
        return HealthResponse(
            status=overall_status,
            database=db_status,
            vector_store=vector_status,
            openai=openai_status
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            database="unknown",
            vector_store="unknown",
            openai="unknown"
        )

# Chat endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Process a chat message and return AI response."""
    try:
        start_time = time.time()
        
        # Ensure we have a session_id (required for user tracking)
        if not message.session_id:
            raise HTTPException(status_code=400, detail="Session ID is required")
        
        # Process the message using the chat agent
        response = chat_agent.process_message(
            message=message.message,
            user_id=message.user_id,
            session_id=message.session_id,
            context=message.context
        )
        
        # Get updated user information after processing
        user_info = None
        if response.get("user_id"):
            try:
                with get_db_context() as db:
                    user = crm_service.get_user_with_session(response["user_id"], db)
                    if user:
                        user_info = user.to_dict()
            except Exception as e:
                logger.warning(f"Could not fetch user info: {e}")
        
        # Add user info to response metadata
        if user_info:
            if not response.get("metadata"):
                response["metadata"] = {}
            response["metadata"]["user_info"] = user_info
        
        return ChatResponse(**response)
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Session Management Endpoints
@app.post("/sessions/create", response_model=APIResponse)
async def create_session(user_id: str):
    """Create a new user session."""
    try:
        session_data = crm_service.create_user_session(user_id)
        return APIResponse(
            success=True,
            message="Session created successfully",
            data=session_data
        )
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions/validate/{session_token}", response_model=APIResponse)
async def validate_session(session_token: str):
    """Validate a session token."""
    try:
        user = crm_service.validate_session(session_token)
        if user:
            return APIResponse(
                success=True,
                message="Session is valid",
                data={
                    "user": user.to_dict(),
                    "valid": True
                }
            )
        else:
            return APIResponse(
                success=False,
                message="Session is invalid or expired",
                data={"valid": False}
            )
    except Exception as e:
        logger.error(f"Error validating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sessions/extend/{session_token}", response_model=APIResponse)
async def extend_session(session_token: str, extend_hours: int = 24):
    """Extend session expiration."""
    try:
        success = crm_service.extend_session(session_token, extend_hours)
        if success:
            return APIResponse(
                success=True,
                message=f"Session extended by {extend_hours} hours",
                data={"extended": True}
            )
        else:
            return APIResponse(
                success=False,
                message="Failed to extend session",
                data={"extended": False}
            )
    except Exception as e:
        logger.error(f"Error extending session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sessions/revoke/{session_token}", response_model=APIResponse)
async def revoke_session(session_token: str):
    """Revoke a session."""
    try:
        success = crm_service.revoke_session(session_token)
        if success:
            return APIResponse(
                success=True,
                message="Session revoked successfully",
                data={"revoked": True}
            )
        else:
            return APIResponse(
                success=False,
                message="Failed to revoke session",
                data={"revoked": False}
            )
    except Exception as e:
        logger.error(f"Error revoking session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions/user/{user_id}", response_model=APIResponse)
async def get_user_sessions(user_id: str, active_only: bool = True):
    """Get all sessions for a user."""
    try:
        sessions = crm_service.get_user_sessions(user_id, active_only)
        return APIResponse(
            success=True,
            message="Sessions retrieved successfully",
            data={
                "sessions": sessions,
                "total": len(sessions)
            }
        )
    except Exception as e:
        logger.error(f"Error getting user sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sessions/cleanup", response_model=APIResponse)
async def cleanup_expired_sessions():
    """Clean up expired sessions."""
    try:
        count = crm_service.cleanup_expired_sessions()
        return APIResponse(
            success=True,
            message=f"Cleaned up {count} expired sessions",
            data={"cleaned_up": count}
        )
    except Exception as e:
        logger.error(f"Error cleaning up sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sessions/create-for-all-users", response_model=APIResponse)
async def create_sessions_for_all_users():
    """Create sessions for all users who don't have them."""
    try:
        with get_db_context() as db:
            users_without_sessions = []
            sessions_created = 0
            
            # Get all active users
            users = db.query(User).filter(User.is_active == True).all()
            
            for user in users:
                # Check if user has any active sessions
                existing_sessions = crm_service.get_user_sessions(user.id, active_only=True)
                
                if len(existing_sessions) == 0:
                    try:
                        session_data = crm_service.create_user_session(user.id)
                        users_without_sessions.append({
                            "user_id": user.id,
                            "user_name": user.name,
                            "session_created": session_data['session_id']
                        })
                        sessions_created += 1
                        logger.info(f"Created session for user {user.id}: {session_data['session_id']}")
                    except Exception as e:
                        logger.error(f"Failed to create session for user {user.id}: {e}")
                        users_without_sessions.append({
                            "user_id": user.id,
                            "user_name": user.name,
                            "error": str(e)
                        })
            
            return APIResponse(
                success=True,
                message=f"Created {sessions_created} sessions for users without sessions",
                data={
                    "sessions_created": sessions_created,
                    "total_users": len(users),
                    "details": users_without_sessions
                }
            )
    except Exception as e:
        logger.error(f"Error creating sessions for all users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/debug/session-status", response_model=APIResponse)
async def get_session_debug_status():
    """Debug endpoint to check session table status."""
    try:
        with get_db_context() as db:
            # Count users and sessions
            total_users = db.query(User).count()
            active_users = db.query(User).filter(User.is_active == True).count()
            total_sessions = db.query(UserSession).count()
            active_sessions = db.query(UserSession).filter(UserSession.is_active == True).count()
            
            # Get sample data
            sample_users = db.query(User).limit(5).all()
            sample_sessions = db.query(UserSession).limit(5).all()
            
            # Count conversations and messages
            total_conversations = db.query(Conversation).count()
            total_messages = db.query(Message).count()
            
            return APIResponse(
                success=True,
                message="Session debug information",
                data={
                    "database_stats": {
                        "total_users": total_users,
                        "active_users": active_users,
                        "total_sessions": total_sessions,
                        "active_sessions": active_sessions,
                        "total_conversations": total_conversations,
                        "total_messages": total_messages
                    },
                    "sample_users": [
                        {
                            "id": user.id,
                            "name": user.name,
                            "email": user.email,
                            "is_active": user.is_active,
                            "created_at": user.created_at.isoformat() if user.created_at else None
                        } for user in sample_users
                    ],
                    "sample_sessions": [
                        {
                            "id": session.id,
                            "user_id": session.user_id,
                            "is_active": session.is_active,
                            "created_at": session.created_at.isoformat() if session.created_at else None,
                            "expires_at": session.expires_at.isoformat() if session.expires_at else None
                        } for session in sample_sessions
                    ]
                }
            )
    except Exception as e:
        logger.error(f"Error getting session debug status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _json_to_readable_text(data, filename: str) -> str:
    """Convert JSON data to readable text for better RAG processing."""
    
    def format_value(key, value, indent=0):
        """Recursively format JSON values into readable text."""
        spaces = "  " * indent
        
        if isinstance(value, dict):
            if not value:  # Empty dict
                return f"{spaces}{key}: Empty object\n"
            
            result = f"{spaces}{key}:\n"
            for k, v in value.items():
                result += format_value(k, v, indent + 1)
            return result
            
        elif isinstance(value, list):
            if not value:  # Empty list
                return f"{spaces}{key}: Empty list\n"
            
            result = f"{spaces}{key} (list with {len(value)} items):\n"
            for i, item in enumerate(value):
                if isinstance(item, (dict, list)):
                    result += format_value(f"Item {i+1}", item, indent + 1)
                else:
                    result += f"{spaces}  - {item}\n"
            return result
            
        elif isinstance(value, str):
            return f"{spaces}{key}: {value}\n"
        
        elif isinstance(value, (int, float, bool)):
            return f"{spaces}{key}: {value}\n"
        
        elif value is None:
            return f"{spaces}{key}: null\n"
        
        else:
            return f"{spaces}{key}: {str(value)}\n"
    
    try:
        # Start with file header
        readable_text = f"JSON Document: {filename}\n"
        readable_text += "=" * 50 + "\n\n"
        
        if isinstance(data, dict):
            # Handle JSON object
            for key, value in data.items():
                readable_text += format_value(key, value)
        
        elif isinstance(data, list):
            # Handle JSON array
            readable_text += f"Array with {len(data)} items:\n\n"
            for i, item in enumerate(data):
                readable_text += format_value(f"Item {i+1}", item)
                readable_text += "\n"
        
        else:
            # Handle primitive JSON value
            readable_text += f"Value: {data}\n"
        
        return readable_text
        
    except Exception as e:
        # Fallback to string representation
        return f"JSON Document: {filename}\nContent: {str(data)}"

# Document upload endpoint
@app.post("/upload_docs", response_model=APIResponse)
async def upload_documents(files: List[UploadFile] = File(...)):
    """Upload documents to the RAG knowledge base."""
    try:
        from database import get_db_context
        from models.crm_models import Document
        
        uploaded_docs = []
        replaced_docs = []
        
        for file in files:
            # Check if document already exists
            with get_db_context() as db:
                existing_doc = db.query(Document).filter(
                    Document.filename == file.filename,
                    Document.is_active == True
                ).first()
                
                is_replacement = existing_doc is not None
            
            # Read file content
            content = await file.read()
            
            # Determine content type and process accordingly
            if file.content_type == "text/csv":
                # Process CSV file
                doc_id = rag_service.process_csv_data(
                    content.decode('utf-8'),
                    file.filename
                )
            elif file.content_type == "text/plain":
                # Process text file
                doc_id = rag_service.process_document(
                    content.decode('utf-8'),
                    file.filename,
                    file.content_type
                )
            elif file.content_type == "application/json" or file.filename.lower().endswith('.json'):
                # Process JSON file
                try:
                    # Decode and parse JSON
                    json_text = content.decode('utf-8')
                    import json
                    parsed_json = json.loads(json_text)
                    
                    # Convert JSON to readable text description
                    readable_text = _json_to_readable_text(parsed_json, file.filename)
                    
                    # Process the readable text
                    doc_id = rag_service.process_document(
                        readable_text,
                        file.filename,
                        file.content_type or "application/json",
                        metadata={"original_format": "json", "has_structure": True}
                    )
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in file {file.filename}: {e}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid JSON format in file {file.filename}: {str(e)}"
                    )
                except Exception as e:
                    logger.error(f"Error processing JSON file {file.filename}: {e}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to process JSON file: {str(e)}"
                    )
            elif file.content_type == "application/pdf":
                # Process PDF file
                try:
                    # Extract text from PDF using PyPDF2
                    pdf_reader = PyPDF2.PdfReader(BytesIO(content))
                    text_content = ""
                    
                    # Extract text from all pages
                    for page_num, page in enumerate(pdf_reader.pages):
                        try:
                            page_text = page.extract_text()
                            if page_text.strip():  # Only add non-empty pages
                                text_content += f"\n--- Page {page_num + 1} ---\n"
                                text_content += page_text
                                text_content += "\n"
                        except Exception as e:
                            logger.warning(f"Could not extract text from page {page_num + 1} of {file.filename}: {e}")
                            continue
                    
                    if not text_content.strip():
                        raise HTTPException(
                            status_code=400,
                            detail=f"Could not extract text from PDF: {file.filename}"
                        )
                    
                    # Process extracted text as document
                    doc_id = rag_service.process_document(
                        text_content,
                        file.filename,
                        file.content_type,
                        metadata={"total_pages": len(pdf_reader.pages)}
                    )
                    
                except Exception as e:
                    logger.error(f"Error processing PDF {file.filename}: {e}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to process PDF file: {str(e)}"
                    )
            else:
                # For other file types, try to process as text
                try:
                    doc_id = rag_service.process_document(
                        content.decode('utf-8'),
                        file.filename,
                        file.content_type or "text/plain"
                    )
                except UnicodeDecodeError:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Unsupported file type: {file.content_type}"
                    )
            
            doc_info = {
                "filename": file.filename,
                "document_id": doc_id,
                "content_type": file.content_type
            }
            
            if is_replacement:
                replaced_docs.append(doc_info)
            else:
                uploaded_docs.append(doc_info)
        
        # Create appropriate response message
        message_parts = []
        if uploaded_docs:
            message_parts.append(f"Successfully uploaded {len(uploaded_docs)} new documents")
        if replaced_docs:
            message_parts.append(f"Successfully replaced {len(replaced_docs)} existing documents")
        
        message = "; ".join(message_parts) if message_parts else "No documents processed"
        
        return APIResponse(
            success=True,
            message=message,
            data={
                "uploaded_documents": uploaded_docs,
                "replaced_documents": replaced_docs,
                "total_processed": len(uploaded_docs) + len(replaced_docs)
            }
        )
        
    except Exception as e:
        logger.error(f"Error uploading documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# CRM User Management Endpoints
@app.post("/crm/create_user", response_model=APIResponse)
async def create_user(user_data: UserCreate):
    """Create a new user in the CRM system."""
    try:
        user_dict = crm_service.create_user(user_data)
        return APIResponse(
            success=True,
            message="User created successfully",
            data=user_dict
        )
        
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/crm/update_user/{user_id}", response_model=APIResponse)
async def update_user(user_id: str, user_data: UserUpdate):
    """Update user information."""
    try:
        user_dict = crm_service.update_user(user_id, user_data)
        if not user_dict:
            raise HTTPException(status_code=404, detail="User not found")
        
        return APIResponse(
            success=True,
            message="User updated successfully",
            data=user_dict
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/crm/users", response_model=PaginatedResponse)
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    active_only: bool = Query(True)
):
    """List all users with pagination."""
    try:
        result = crm_service.list_users(page, per_page, active_only)
        
        return PaginatedResponse(
            success=True,
            message="Users retrieved successfully",
            data=result["users"],
            total=result["total"],
            page=result["page"],
            per_page=result["per_page"],
            pages=result["pages"]
        )
        
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/crm/users/{user_id}", response_model=APIResponse)
async def get_user(user_id: str):
    """Get user information by ID."""
    try:
        user = crm_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return APIResponse(
            success=True,
            message="User retrieved successfully",
            data=user.to_dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/crm/users/find/{email}", response_model=APIResponse)
async def find_user_by_email(email: str):
    """Find user by email address."""
    try:
        user = crm_service.get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return APIResponse(
            success=True,
            message="User found successfully",
            data=user.to_dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding user by email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/crm/users/{user_id}", response_model=APIResponse)
async def delete_user(user_id: str):
    """Delete a user (soft delete)."""
    try:
        success = crm_service.delete_user(user_id)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        
        return APIResponse(
            success=True,
            message="User deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Conversation Management Endpoints
@app.get("/crm/conversations/{user_id}", response_model=PaginatedResponse)
async def get_user_conversations(
    user_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100)
):
    """Get conversation history for a user."""
    try:
        # Check if user exists
        user = crm_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        result = crm_service.get_user_conversations(user_id, page, per_page)
        
        return PaginatedResponse(
            success=True,
            message="Conversations retrieved successfully",
            data=result["conversations"],
            total=result["total"],
            page=result["page"],
            per_page=result["per_page"],
            pages=result["pages"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/crm/conversations/{user_id}/{conversation_id}", response_model=APIResponse)
async def get_conversation_details(user_id: str, conversation_id: str):
    """Get detailed conversation with messages."""
    try:
        conversation = crm_service.get_conversation_with_messages(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        if conversation.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Format the response
        conv_data = conversation.to_dict()
        conv_data["messages"] = [msg.to_dict() for msg in conversation.messages]
        
        return APIResponse(
            success=True,
            message="Conversation retrieved successfully",
            data=conv_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Reset endpoint
@app.post("/reset", response_model=ResetResponse)
async def reset_data(reset_request: ResetRequest):
    """Reset conversation memory or user data."""
    try:
        affected_records = 0
        
        if reset_request.reset_type == "conversation":
            if reset_request.user_id:
                # Reset conversations for specific user
                affected_records = crm_service.clear_user_conversations(reset_request.user_id)
            else:
                # Reset all conversations (not implemented for safety)
                raise HTTPException(
                    status_code=400,
                    detail="User ID required for conversation reset"
                )
        
        elif reset_request.reset_type == "user":
            if reset_request.user_id:
                # Delete specific user
                success = crm_service.delete_user(reset_request.user_id)
                affected_records = 1 if success else 0
            else:
                raise HTTPException(
                    status_code=400,
                    detail="User ID required for user reset"
                )
        
        elif reset_request.reset_type == "all":
            # This is a dangerous operation - implement with caution
            raise HTTPException(
                status_code=400,
                detail="Full reset not implemented for safety"
            )
        
        return ResetResponse(
            message=f"Reset completed successfully",
            reset_type=reset_request.reset_type,
            affected_records=affected_records
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in reset operation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Analytics and Stats Endpoints
@app.get("/crm/analytics", response_model=APIResponse)
async def get_analytics(user_id: Optional[str] = Query(None)):
    """Get conversation analytics."""
    try:
        analytics = crm_service.get_conversation_analytics(user_id)
        
        return APIResponse(
            success=True,
            message="Analytics retrieved successfully",
            data=analytics
        )
        
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/crm/users/{user_id}/stats", response_model=APIResponse)
async def get_user_stats(user_id: str):
    """Get detailed statistics for a user."""
    try:
        stats = crm_service.get_user_stats(user_id)
        if not stats:
            raise HTTPException(status_code=404, detail="User not found")
        
        return APIResponse(
            success=True,
            message="User statistics retrieved successfully",
            data=stats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Search endpoint
@app.get("/crm/search", response_model=PaginatedResponse)
async def search_conversations(
    q: str = Query(..., min_length=1),
    user_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100)
):
    """Search conversations by content."""
    try:
        result = crm_service.search_conversations(q, user_id, page, per_page)
        conversations_data = [conv.to_dict() for conv in result["conversations"]]
        
        return PaginatedResponse(
            success=True,
            message=f"Search completed for '{q}'",
            data=conversations_data,
            total=result["total"],
            page=result["page"],
            per_page=result["per_page"],
            pages=result["pages"]
        )
        
    except Exception as e:
        logger.error(f"Error searching conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# RAG Management Endpoints
@app.get("/rag/stats", response_model=APIResponse)
async def get_rag_stats():
    """Get RAG system statistics."""
    try:
        stats = rag_service.get_collection_stats()
        
        return APIResponse(
            success=True,
            message="RAG statistics retrieved successfully",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"Error getting RAG stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/rag/clear", response_model=APIResponse)
async def clear_rag_collection():
    """Clear all documents from the RAG collection."""
    try:
        rag_service.clear_collection()
        
        return APIResponse(
            success=True,
            message="RAG collection cleared successfully"
        )
        
    except Exception as e:
        logger.error(f"Error clearing RAG collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rag/documents", response_model=PaginatedResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100)
):
    """List all documents in the RAG collection."""
    try:
        result = rag_service.list_documents(page, per_page)
        
        return PaginatedResponse(
            success=True,
            message="Documents retrieved successfully",
            data=result["documents"],
            total=result["total"],
            page=result["page"],
            per_page=result["per_page"],
            pages=result["pages"]
        )
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/rag/documents/{filename}", response_model=APIResponse)
async def delete_document(filename: str):
    """Delete a specific document from the RAG collection."""
    try:
        # URL decode the filename in case it contains special characters
        from urllib.parse import unquote
        decoded_filename = unquote(filename)
        
        success = rag_service.remove_document_by_filename(decoded_filename)
        
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return APIResponse(
            success=True,
            message=f"Document '{decoded_filename}' deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Admin Analytics Endpoints
@app.get("/admin/analytics/system", response_model=APIResponse)
async def get_system_analytics():
    """Get comprehensive system analytics for admin use."""
    try:
        analytics = crm_service.get_system_analytics()
        
        return APIResponse(
            success=True,
            message="System analytics retrieved successfully",
            data=analytics
        )
        
    except Exception as e:
        logger.error(f"Error getting system analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/data/reload", response_model=APIResponse)
async def reload_data():
    """Manually reload all data from the data directory."""
    try:
        # Clear existing data first
        rag_service.clear_collection()
        logger.info("Cleared existing data collection")
        
        # Reload all data
        await load_initial_data()
        
        # Get updated stats
        stats = rag_service.get_collection_stats()
        
        return APIResponse(
            success=True,
            message="Data reloaded successfully",
            data=stats
        )
    except Exception as e:
        logger.error(f"Error reloading data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/data/force-load", response_model=APIResponse)
async def force_load_data():
    """Force load data from the data directory, even if data already exists."""
    try:
        # Temporarily force loading by clearing stats check
        original_load_initial_data = load_initial_data
        
        async def force_load():
            data_directory = "data"
            if not os.path.exists(data_directory):
                logger.warning(f"Data directory '{data_directory}' not found")
                return
                
            # Get all files from the data directory
            data_files = []
            for filename in os.listdir(data_directory):
                file_path = os.path.join(data_directory, filename)
                if os.path.isfile(file_path):
                    data_files.append((filename, file_path))
            
            if not data_files:
                logger.warning("No files found in data directory")
                return
                
            logger.info(f"Force loading {len(data_files)} files from data directory")
            
            # Process each file based on its type
            loaded_count = 0
            for filename, file_path in data_files:
                try:
                    file_extension = filename.lower().split('.')[-1]
                    
                    if file_extension == 'csv':
                        # Process CSV files
                        with open(file_path, 'r', encoding='utf-8') as f:
                            csv_content = f.read()
                        rag_service.process_csv_data(csv_content, filename)
                        logger.info(f"Loaded CSV file: {filename}")
                        loaded_count += 1
                        
                    elif file_extension == 'json':
                        # Process JSON files
                        with open(file_path, 'r', encoding='utf-8') as f:
                            json_content = f.read()
                            try:
                                json_data = json.loads(json_content)
                                # Convert JSON to readable text format
                                readable_text = _json_to_readable_text(json_data, filename)
                                rag_service.process_document(readable_text, filename, "application/json")
                                logger.info(f"Loaded JSON file: {filename}")
                                loaded_count += 1
                            except json.JSONDecodeError:
                                logger.warning(f"Invalid JSON format in file: {filename}")
                                
                    elif file_extension == 'txt':
                        # Process text files
                        with open(file_path, 'r', encoding='utf-8') as f:
                            text_content = f.read()
                        rag_service.process_document(text_content, filename, "text/plain")
                        logger.info(f"Loaded text file: {filename}")
                        loaded_count += 1
                        
                    elif file_extension == 'pdf':
                        # Process PDF files
                        try:
                            with open(file_path, 'rb') as f:
                                pdf_reader = PyPDF2.PdfReader(f)
                                text_content = ""
                                for page in pdf_reader.pages:
                                    text_content += page.extract_text() + "\n"
                            
                            if text_content.strip():
                                rag_service.process_document(text_content, filename, "application/pdf")
                                logger.info(f"Loaded PDF file: {filename}")
                                loaded_count += 1
                            else:
                                logger.warning(f"No text content extracted from PDF: {filename}")
                        except Exception as pdf_error:
                            logger.error(f"Error processing PDF {filename}: {pdf_error}")
                            
                    else:
                        # Handle other file types as plain text
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            rag_service.process_document(content, filename, "text/plain")
                            logger.info(f"Loaded file as text: {filename}")
                            loaded_count += 1
                        except UnicodeDecodeError:
                            logger.warning(f"Skipping binary file: {filename}")
                            
                except Exception as file_error:
                    logger.error(f"Error processing file {filename}: {file_error}")
                    
            logger.info(f"Successfully loaded {loaded_count} out of {len(data_files)} files from data directory")
        
        await force_load()
        
        # Get updated stats
        stats = rag_service.get_collection_stats()
        
        return APIResponse(
            success=True,
            message="Data force-loaded successfully",
            data=stats
        )
    except Exception as e:
        logger.error(f"Error force loading data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/data/files", response_model=APIResponse)
async def list_data_files():
    """List all files in the data directory."""
    try:
        data_directory = "data"
        if not os.path.exists(data_directory):
            return APIResponse(
                success=False,
                message="Data directory not found"
            )
            
        files = []
        for filename in os.listdir(data_directory):
            file_path = os.path.join(data_directory, filename)
            if os.path.isfile(file_path):
                file_stat = os.stat(file_path)
                files.append({
                    "filename": filename,
                    "size": file_stat.st_size,
                    "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                    "extension": filename.lower().split('.')[-1] if '.' in filename else 'unknown'
                })
        
        return APIResponse(
            success=True,
            data={
                "files": files,
                "total_files": len(files)
            }
        )
    except Exception as e:
        logger.error(f"Error listing data files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/analytics/user/{user_id}", response_model=APIResponse)
async def get_detailed_user_analytics(user_id: str):
    """Get detailed analytics for a specific user."""
    try:
        analytics = crm_service.get_detailed_user_analytics(user_id)
        if not analytics:
            raise HTTPException(status_code=404, detail="User not found")
        
        return APIResponse(
            success=True,
            message="User analytics retrieved successfully",
            data=analytics
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/analytics/overview", response_model=APIResponse)
async def get_analytics_overview():
    """Get analytics overview combining system and user metrics."""
    try:
        system_analytics = crm_service.get_system_analytics()
        rag_stats = rag_service.get_collection_stats()
        
        overview = {
            "system_metrics": system_analytics,
            "rag_metrics": rag_stats,
            "summary": {
                "total_users": system_analytics.get("total_users", 0),
                "total_conversations": system_analytics.get("total_conversations", 0),
                "total_documents": rag_stats.get("total_documents", 0),
                "system_health": "operational"
            }
        }
        
        return APIResponse(
            success=True,
            message="Analytics overview retrieved successfully",
            data=overview
        )
        
    except Exception as e:
        logger.error(f"Error getting analytics overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Admin Settings Endpoints
@app.get("/admin/settings", response_model=APIResponse)
async def get_system_settings():
    """Get current system settings for admin viewing."""
    try:
        settings_data = settings_service.get_system_settings()
        
        return APIResponse(
            success=True,
            message="System settings retrieved successfully",
            data=settings_data
        )
        
    except Exception as e:
        logger.error(f"Error getting system settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/admin/settings", response_model=APIResponse)
async def update_system_settings(settings_update: SettingsUpdate):
    """Update system settings."""
    try:
        success = settings_service.update_settings(
            settings_update.category,
            settings_update.settings
        )
        
        if success:
            return APIResponse(
                success=True,
                message=f"Settings updated successfully for category: {settings_update.category}",
                data={"category": settings_update.category, "updated": True}
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to update settings")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating system settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/overview", response_model=APIResponse)
async def get_system_overview():
    """Get comprehensive system overview for admin dashboard."""
    try:
        overview = settings_service.get_system_overview()
        
        return APIResponse(
            success=True,
            message="System overview retrieved successfully",
            data=overview
        )
        
    except Exception as e:
        logger.error(f"Error getting system overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/health/detailed", response_model=APIResponse)
async def get_detailed_health():
    """Get detailed health information for admin monitoring."""
    try:
        # Get basic health
        basic_health = {
            "status": "healthy",
            "database": "healthy",
            "vector_store": "healthy",
            "openai": "healthy" if settings.openai_api_key else "not_configured"
        }
        
        # Get system overview
        system_overview = settings_service.get_system_overview()
        
        # Combine health data
        detailed_health = {
            "basic_health": basic_health,
            "system_overview": system_overview,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return APIResponse(
            success=True,
            message="Detailed health information retrieved successfully",
            data=detailed_health
        )
        
    except Exception as e:
        logger.error(f"Error getting detailed health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Root endpoint
@app.get("/", response_model=APIResponse)
async def root():
    """Root endpoint with API information."""
    return APIResponse(
        success=True,
        message="Multi-Agent Conversational AI System API",
        data={
            "version": "1.0.0",
            "description": "A comprehensive chatbot system with RAG and CRM capabilities",
            "endpoints": {
                "chat": "/chat",
                "upload_docs": "/upload_docs",
                "health": "/health",
                "docs": "/docs",
                "crm": "/crm/*",
                "rag": "/rag/*",
                "admin": "/admin/*"
            },
            "admin_endpoints": {
                "system_analytics": "/admin/analytics/system",
                "user_analytics": "/admin/analytics/user/{user_id}",
                "analytics_overview": "/admin/analytics/overview",
                "system_settings": "/admin/settings",
                "system_overview": "/admin/overview",
                "detailed_health": "/admin/health/detailed"
            }
        }
    )

# Catch-all route to serve React app (must be last)
@app.get("/{path:path}")
async def serve_react_app(path: str):
    """Serve React app for any non-API routes."""
    # Check if it's a static file
    static_file_path = os.path.join("static", path)
    if os.path.exists(static_file_path) and os.path.isfile(static_file_path):
        return StaticFiles(directory="static").get_response(path, scope={"type": "http"})
    
    # Serve index.html for React Router routes
    index_file_path = os.path.join("static", "index.html")
    if os.path.exists(index_file_path):
        with open(index_file_path, 'r') as f:
            return HTMLResponse(content=f.read())
    
    # Fallback
    raise HTTPException(status_code=404, detail="Not Found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    ) 