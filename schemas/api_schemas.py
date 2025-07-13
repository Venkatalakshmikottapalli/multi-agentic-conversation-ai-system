from pydantic import BaseModel, Field, validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

# User Schemas
class UserCreate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    company: Optional[str] = Field(None, max_length=100)
    role: Optional[str] = Field(None, max_length=50)
    preferences: Optional[Dict[str, Any]] = None

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    company: Optional[str] = Field(None, max_length=100)
    role: Optional[str] = Field(None, max_length=50)
    preferences: Optional[Dict[str, Any]] = None

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    company: Optional[str]
    role: Optional[str]
    preferences: Optional[Dict[str, Any]]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    is_active: bool

# Chat Schemas
class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    user_id: str
    session_id: str
    conversation_id: str
    sources: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    processing_time: float

# Document Schemas
class DocumentUpload(BaseModel):
    filename: str
    content_type: str
    metadata: Optional[Dict[str, Any]] = None

class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    filename: str
    content_type: str
    file_size: Optional[int]
    metadata: Optional[Dict[str, Any]]
    created_at: Optional[datetime]
    indexed_at: Optional[datetime]
    is_active: bool

# Conversation Schemas
class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    user_id: str
    session_id: str
    title: Optional[str]
    category: Optional[str]
    status: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    message_count: int

class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    conversation_id: str
    role: str
    content: str
    metadata: Optional[Dict[str, Any]]
    timestamp: Optional[datetime]

class ConversationWithMessages(ConversationResponse):
    messages: List[MessageResponse]

# Reset Schemas
class ResetRequest(BaseModel):
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    reset_type: str = Field(default="conversation", pattern="^(conversation|user|all)$")

class ResetResponse(BaseModel):
    message: str
    reset_type: str
    affected_records: int

# API Response Schemas
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class PaginatedResponse(BaseModel):
    success: bool
    message: str
    data: List[Any]
    total: int
    page: int
    per_page: int
    pages: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Health Check Schema
class HealthResponse(BaseModel):
    status: str
    database: str
    vector_store: str
    openai: str
    timestamp: datetime = Field(default_factory=datetime.utcnow) 