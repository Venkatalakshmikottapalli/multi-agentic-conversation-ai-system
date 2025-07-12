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

# Import configurations and services
from config import settings
from database import get_db, create_tables, get_db_context
from services.chat_agent import chat_agent
from services.rag_service import rag_service
from services.crm_service import crm_service
from schemas.api_schemas import (
    ChatMessage, ChatResponse, UserCreate, UserUpdate, UserResponse,
    ConversationResponse, ConversationWithMessages, MessageResponse,
    DocumentResponse, ResetRequest, ResetResponse, APIResponse,
    PaginatedResponse, HealthResponse
)

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
    """Load the initial CSV data into the RAG system."""
    try:
        csv_file_path = "HackathonInternalKnowledgeBase.csv"
        if os.path.exists(csv_file_path):
            with open(csv_file_path, 'r', encoding='utf-8') as f:
                csv_content = f.read()
            
            # Process the CSV data
            rag_service.process_csv_data(csv_content, "HackathonInternalKnowledgeBase.csv")
            logger.info("Initial CSV data loaded successfully")
        else:
            logger.warning("Initial CSV file not found")
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
        
        # Process the message using the chat agent
        response = chat_agent.process_message(
            message=message.message,
            user_id=message.user_id,
            session_id=message.session_id,
            context=message.context
        )
        
        return ChatResponse(**response)
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Document upload endpoint
@app.post("/upload_docs", response_model=APIResponse)
async def upload_documents(files: List[UploadFile] = File(...)):
    """Upload documents to the RAG knowledge base."""
    try:
        uploaded_docs = []
        
        for file in files:
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
            elif file.content_type == "application/json":
                # Process JSON file
                doc_id = rag_service.process_document(
                    content.decode('utf-8'),
                    file.filename,
                    file.content_type
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
            
            uploaded_docs.append({
                "filename": file.filename,
                "document_id": doc_id,
                "content_type": file.content_type
            })
        
        return APIResponse(
            success=True,
            message=f"Successfully uploaded {len(uploaded_docs)} documents",
            data={"uploaded_documents": uploaded_docs}
        )
        
    except Exception as e:
        logger.error(f"Error uploading documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# CRM User Management Endpoints
@app.post("/crm/create_user", response_model=APIResponse)
async def create_user(user_data: UserCreate):
    """Create a new user in the CRM system."""
    try:
        user = crm_service.create_user(user_data)
        return APIResponse(
            success=True,
            message="User created successfully",
            data=user.to_dict()
        )
        
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/crm/update_user/{user_id}", response_model=APIResponse)
async def update_user(user_id: str, user_data: UserUpdate):
    """Update user information."""
    try:
        user = crm_service.update_user(user_id, user_data)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return APIResponse(
            success=True,
            message="User updated successfully",
            data=user.to_dict()
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
        users_data = [user.to_dict() for user in result["users"]]
        
        return PaginatedResponse(
            success=True,
            message="Users retrieved successfully",
            data=users_data,
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
        conversations_data = [conv.to_dict() for conv in result["conversations"]]
        
        return PaginatedResponse(
            success=True,
            message="Conversations retrieved successfully",
            data=conversations_data,
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
                "rag": "/rag/*"
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