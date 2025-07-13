# Multi-Agentic Conversational AI System - API Documentation

## Overview

This document provides comprehensive API documentation for the Multi-Agentic Conversational AI System. The system is built using FastAPI and provides RESTful endpoints for chat functionality, CRM operations, document management, and system administration.

**Base URL:** `http://localhost:8000`  
**API Version:** v1.0.0  
**Authentication:** Session-based (Random tokens)

## Table of Contents

1. [Authentication & Sessions](#authentication--sessions)
2. [Chat API](#chat-api)
3. [CRM API](#crm-api)
4. [Document Management API](#document-management-api)
5. [Analytics API](#analytics-api)
6. [System Administration API](#system-administration-api)
7. [Error Handling](#error-handling)
8. [Rate Limiting](#rate-limiting)
9. [Sample Usage](#sample-usage)

---

## Authentication & Sessions

The system uses simple session-based authentication with secure random tokens (32-character URL-safe strings generated using `secrets.token_urlsafe(32)`). These tokens are stored in the database and validated through database lookups.

### Create Session

Creates a new user session with authentication token.

**Endpoint:** `POST /sessions/create`

**Request Body:**
```json
{
  "user_id": "string"
}
```

**Response Schema:**
```json
{
  "success": true,
  "data": {
    "session_id": "string",
    "session_token": "string",
    "user_id": "string",
    "expires_at": "2024-01-01T00:00:00Z",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "metadata": {
    "response_time": 0.123,
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

**Sample Request:**
```bash
curl -X POST "http://localhost:8000/sessions/create" \
     -H "Content-Type: application/json" \
     -d '{"user_id": "user123"}'
```

### Validate Session

Validates an existing session token.

**Endpoint:** `GET /sessions/validate/{session_token}`

**Response Schema:**
```json
{
  "success": true,
  "data": {
    "valid": true,
    "session_id": "string",
    "user_id": "string",
    "expires_at": "2024-01-01T00:00:00Z"
  },
  "metadata": {
    "response_time": 0.045,
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

---

## Chat API

### Send Message

Sends a message to the chatbot and receives a response.

**Endpoint:** `POST /chat`

**Request Schema:**
```json
{
  "message": "string",
  "user_id": "string",
  "conversation_id": "string (optional)",
  "session_token": "string (optional)",
  "context": {
    "additional_context": "string"
  }
}
```

**Response Schema:**
```json
{
  "response": "string",
  "conversation_id": "string",
  "user_info": {
    "id": "string",
    "name": "string",
    "email": "string",
    "company": "string"
  },
  "rag_context": [
    {
      "content": "string",
      "source": "string",
      "score": 0.95,
      "metadata": {
        "filename": "string",
        "chunk_id": "string"
      }
    }
  ],
  "metadata": {
    "response_time": 1.234,
    "tokens_used": 150,
    "agent_used": "general_agent",
    "rag_documents_retrieved": 3,
    "openai_model": "gpt-4-turbo-preview",
    "conversation_length": 5,
    "timestamp": "2024-01-01T00:00:00Z",
    "request_id": "string"
  }
}
```

**Sample Request:**
```bash
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "What are the key features of our CRM system?",
       "user_id": "user123",
       "conversation_id": "conv456"
     }'
```

**Sample Response:**
```json
{
  "response": "Our CRM system includes several key features: 1) Contact Management...",
  "conversation_id": "conv456",
  "user_info": {
    "id": "user123",
    "name": "John Doe",
    "email": "john@example.com",
    "company": "Acme Corp"
  },
  "rag_context": [
    {
      "content": "CRM system features include contact management, lead tracking...",
      "source": "crm_documentation.pdf",
      "score": 0.95,
      "metadata": {
        "filename": "crm_documentation.pdf",
        "chunk_id": "chunk_123"
      }
    }
  ],
  "metadata": {
    "response_time": 1.234,
    "tokens_used": 150,
    "agent_used": "sales_agent",
    "rag_documents_retrieved": 3,
    "openai_model": "gpt-4-turbo-preview",
    "conversation_length": 5,
    "timestamp": "2024-01-01T12:00:00Z",
    "request_id": "req_789"
  }
}
```

---

## CRM API

### Create User

Creates a new user in the CRM system.

**Endpoint:** `POST /crm/create_user`

**Request Schema:**
```json
{
  "name": "string",
  "email": "string",
  "phone": "string (optional)",
  "company": "string (optional)",
  "role": "string (optional)",
  "preferences": {
    "key": "value"
  }
}
```

**Response Schema:**
```json
{
  "success": true,
  "data": {
    "id": "string",
    "name": "string",
    "email": "string",
    "phone": "string",
    "company": "string",
    "role": "string",
    "preferences": {},
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "is_active": true
  },
  "metadata": {
    "response_time": 0.089,
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

**Sample Request:**
```bash
curl -X POST "http://localhost:8000/crm/create_user" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "John Doe",
       "email": "john@example.com",
       "phone": "+1234567890",
       "company": "Acme Corp",
       "role": "Manager"
     }'
```

### Get User

Retrieves user information by ID.

**Endpoint:** `GET /crm/users/{user_id}`

**Response Schema:**
```json
{
  "success": true,
  "data": {
    "id": "string",
    "name": "string",
    "email": "string",
    "phone": "string",
    "company": "string",
    "role": "string",
    "preferences": {},
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "is_active": true,
    "stats": {
      "total_conversations": 15,
      "total_messages": 45,
      "last_active": "2024-01-01T00:00:00Z"
    }
  },
  "metadata": {
    "response_time": 0.045,
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### List Users

Retrieves a paginated list of users.

**Endpoint:** `GET /crm/users`

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (default: 10, max: 100)
- `active_only` (bool): Filter active users only (default: true)

**Response Schema:**
```json
{
  "success": true,
  "data": [
    {
      "id": "string",
      "name": "string",
      "email": "string",
      "company": "string",
      "created_at": "2024-01-01T00:00:00Z",
      "is_active": true
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 100,
    "pages": 10
  },
  "metadata": {
    "response_time": 0.156,
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### Get User Conversations

Retrieves conversations for a specific user.

**Endpoint:** `GET /crm/conversations/{user_id}`

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (default: 10, max: 100)

**Response Schema:**
```json
{
  "success": true,
  "data": [
    {
      "id": "string",
      "title": "string",
      "status": "active|completed|archived",
      "category": "support|sales|general",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "message_count": 10,
      "last_message": {
        "content": "string",
        "type": "user|assistant",
        "created_at": "2024-01-01T00:00:00Z"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 50,
    "pages": 5
  },
  "metadata": {
    "response_time": 0.234,
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

---

## Document Management API

### Upload Documents

Uploads one or more documents to the knowledge base.

**Endpoint:** `POST /upload_docs`

**Request:** Multipart form data with file uploads

**Response Schema:**
```json
{
  "success": true,
  "data": {
    "uploaded_files": [
      {
        "filename": "string",
        "size": 1024,
        "type": "application/pdf",
        "status": "success|failed",
        "chunks_created": 15,
        "error": "string (if failed)"
      }
    ],
    "total_uploaded": 3,
    "total_failed": 0,
    "total_chunks": 45
  },
  "metadata": {
    "response_time": 2.345,
    "timestamp": "2024-01-01T00:00:00Z",
    "processing_time": 2.1
  }
}
```

**Sample Request:**
```bash
curl -X POST "http://localhost:8000/upload_docs" \
     -F "files=@document1.pdf" \
     -F "files=@document2.csv" \
     -F "files=@document3.txt"
```

### Get RAG Statistics

Retrieves statistics about the knowledge base.

**Endpoint:** `GET /rag/stats`

**Response Schema:**
```json
{
  "success": true,
  "data": {
    "total_documents": 50,
    "total_chunks": 500,
    "total_size_bytes": 10485760,
    "file_types": {
      "pdf": 20,
      "csv": 15,
      "txt": 10,
      "json": 5
    },
    "last_updated": "2024-01-01T00:00:00Z",
    "avg_chunk_size": 1024,
    "collection_health": "healthy"
  },
  "metadata": {
    "response_time": 0.067,
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### List Documents

Retrieves a paginated list of documents in the knowledge base.

**Endpoint:** `GET /rag/documents`

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (default: 10, max: 100)

**Response Schema:**
```json
{
  "success": true,
  "data": [
    {
      "id": "string",
      "filename": "string",
      "content_type": "application/pdf",
      "size": 1024,
      "chunks": 15,
      "uploaded_at": "2024-01-01T00:00:00Z",
      "status": "processed|processing|failed"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 50,
    "pages": 5
  },
  "metadata": {
    "response_time": 0.089,
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### Delete Document

Deletes a document from the knowledge base.

**Endpoint:** `DELETE /rag/documents/{filename}`

**Response Schema:**
```json
{
  "success": true,
  "data": {
    "filename": "string",
    "chunks_removed": 15,
    "size_freed": 1024
  },
  "metadata": {
    "response_time": 0.156,
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

---

## Analytics API

### Get System Analytics

Retrieves system-wide analytics and metrics.

**Endpoint:** `GET /admin/analytics/system`

**Response Schema:**
```json
{
  "success": true,
  "data": {
    "overview": {
      "total_users": 100,
      "active_users": 85,
      "total_conversations": 500,
      "total_messages": 2000,
      "avg_response_time": 1.23
    },
    "usage_metrics": {
      "messages_per_day": 150,
      "conversations_per_day": 50,
      "new_users_per_day": 5,
      "avg_session_length": 15.5
    },
    "performance_metrics": {
      "avg_api_response_time": 0.234,
      "avg_openai_response_time": 1.567,
      "error_rate": 0.02,
      "uptime_percentage": 99.9
    },
    "document_metrics": {
      "total_documents": 50,
      "total_chunks": 500,
      "avg_retrieval_time": 0.045
    }
  },
  "metadata": {
    "response_time": 0.123,
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### Get User Analytics

Retrieves detailed analytics for a specific user.

**Endpoint:** `GET /admin/analytics/user/{user_id}`

**Response Schema:**
```json
{
  "success": true,
  "data": {
    "user_info": {
      "id": "string",
      "name": "string",
      "email": "string",
      "created_at": "2024-01-01T00:00:00Z"
    },
    "conversation_stats": {
      "total_conversations": 15,
      "avg_messages_per_conversation": 10,
      "most_active_day": "Monday",
      "preferred_agent": "general_agent"
    },
    "engagement_metrics": {
      "total_time_spent": 1800,
      "avg_session_length": 300,
      "response_satisfaction": 4.5,
      "last_active": "2024-01-01T00:00:00Z"
    },
    "conversation_history": [
      {
        "id": "string",
        "title": "string",
        "created_at": "2024-01-01T00:00:00Z",
        "message_count": 10,
        "category": "support"
      }
    ]
  },
  "metadata": {
    "response_time": 0.234,
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

---

## System Administration API

### System Health Check

Performs a comprehensive health check of the system.

**Endpoint:** `GET /admin/health/detailed`

**Response Schema:**
```json
{
  "success": true,
  "data": {
    "status": "healthy|degraded|unhealthy",
    "timestamp": "2024-01-01T00:00:00Z",
    "uptime": "5 days, 12 hours, 30 minutes",
    "version": "1.0.0",
    "components": {
      "database": {
        "status": "healthy",
        "response_time": 0.012,
        "details": "SQLite connection successful"
      },
      "vector_db": {
        "status": "healthy",
        "response_time": 0.045,
        "details": "ChromaDB operational"
      },
      "openai_api": {
        "status": "healthy",
        "response_time": 0.567,
        "details": "API key valid, quota available"
      },
      "memory_usage": {
        "status": "healthy",
        "used": "256 MB",
        "total": "1024 MB",
        "percentage": 25
      },
      "disk_space": {
        "status": "healthy",
        "used": "2.5 GB",
        "total": "10 GB",
        "percentage": 25
      }
    }
  },
  "metadata": {
    "response_time": 0.234,
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### System Settings

Retrieves current system settings.

**Endpoint:** `GET /admin/settings`

**Response Schema:**
```json
{
  "success": true,
  "data": {
    "api_config": {
      "host": "0.0.0.0",
      "port": 8000,
      "debug": false
    },
    "ai_config": {
      "model": "gpt-4-turbo-preview",
      "temperature": 0.7,
      "max_tokens": 1000
    },
    "rag_config": {
      "chunk_size": 1000,
      "chunk_overlap": 200,
      "max_retrieval_docs": 5
    },
    "system_info": {
      "version": "1.0.0",
      "python_version": "3.9.0",
      "start_time": "2024-01-01T00:00:00Z"
    }
  },
  "metadata": {
    "response_time": 0.045,
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

---

## Error Handling

### Standard Error Response

All API endpoints return errors in a consistent format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": "Additional technical details",
    "field": "field_name (for validation errors)"
  },
  "metadata": {
    "response_time": 0.012,
    "timestamp": "2024-01-01T00:00:00Z",
    "request_id": "string"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `NOT_FOUND` | 404 | Resource not found |
| `UNAUTHORIZED` | 401 | Authentication required |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `RATE_LIMITED` | 429 | Rate limit exceeded |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `OPENAI_ERROR` | 502 | OpenAI API error |
| `DATABASE_ERROR` | 503 | Database connection error |

### Example Error Responses

**Validation Error:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Email is required",
    "details": "The email field cannot be empty",
    "field": "email"
  },
  "metadata": {
    "response_time": 0.012,
    "timestamp": "2024-01-01T00:00:00Z",
    "request_id": "req_123"
  }
}
```

**Not Found Error:**
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "User not found",
    "details": "User with ID 'user123' does not exist"
  },
  "metadata": {
    "response_time": 0.045,
    "timestamp": "2024-01-01T00:00:00Z",
    "request_id": "req_456"
  }
}
```

---

## Rate Limiting

API endpoints are protected by rate limiting to ensure fair usage:

- **Default Limit:** 100 requests per minute per IP
- **Burst Limit:** 10 requests per second
- **Headers:** Rate limit information is included in response headers

**Rate Limit Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

---

## Sample Usage

### Complete Chat Flow

```bash
# 1. Create a user
curl -X POST "http://localhost:8000/crm/create_user" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "John Doe",
       "email": "john@example.com",
       "company": "Acme Corp"
     }'

# 2. Create a session
curl -X POST "http://localhost:8000/sessions/create" \
     -H "Content-Type: application/json" \
     -d '{"user_id": "user123"}'

# 3. Upload a document
curl -X POST "http://localhost:8000/upload_docs" \
     -F "files=@product_manual.pdf"

# 4. Send a chat message
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "What features does the product have?",
       "user_id": "user123",
       "session_token": "session_token_here"
     }'

# 5. Get conversation history
curl -X GET "http://localhost:8000/crm/conversations/user123"

# 6. Get system analytics
curl -X GET "http://localhost:8000/admin/analytics/system"
```

### Python Client Example

```python
import requests

class ChatbotClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session_token = None
    
    def create_user(self, name, email, company=None):
        response = requests.post(
            f"{self.base_url}/crm/create_user",
            json={
                "name": name,
                "email": email,
                "company": company
            }
        )
        return response.json()
    
    def create_session(self, user_id):
        response = requests.post(
            f"{self.base_url}/sessions/create",
            json={"user_id": user_id}
        )
        data = response.json()
        self.session_token = data["data"]["session_token"]
        return data
    
    def send_message(self, message, user_id, conversation_id=None):
        response = requests.post(
            f"{self.base_url}/chat",
            json={
                "message": message,
                "user_id": user_id,
                "conversation_id": conversation_id,
                "session_token": self.session_token
            }
        )
        return response.json()
    
    def upload_document(self, file_path):
        with open(file_path, 'rb') as f:
            response = requests.post(
                f"{self.base_url}/upload_docs",
                files={'files': f}
            )
        return response.json()

# Usage example
client = ChatbotClient()
user = client.create_user("John Doe", "john@example.com", "Acme Corp")
session = client.create_session(user["data"]["id"])
response = client.send_message("Hello, how can you help me?", user["data"]["id"])
print(response["response"])
```

---

## Processing Metadata

All API responses include processing metadata to help with debugging and monitoring:

```json
{
  "metadata": {
    "response_time": 1.234,
    "timestamp": "2024-01-01T00:00:00Z",
    "request_id": "req_123",
    "api_version": "1.0.0",
    "processing_details": {
      "database_queries": 3,
      "database_time": 0.045,
      "openai_calls": 1,
      "openai_time": 0.567,
      "rag_retrieval_time": 0.123,
      "total_tokens": 150
    }
  }
}
```

---

## API Usage

### Using cURL

All examples in this document use cURL for demonstration. Make sure to:

1. Replace `localhost:8000` with your actual API URL
2. Include proper authentication headers when required
3. Handle rate limiting appropriately

### Using the Interactive Docs

FastAPI provides automatic interactive documentation:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## Conclusion

This API provides a comprehensive set of endpoints for building chatbot applications with CRM integration and document-based AI responses. All endpoints include detailed metadata for monitoring and debugging, and follow RESTful principles for ease of use.

For additional support or questions, please refer to the main README.md file or contact the development team.

---

**Generated on:** 2024-01-01  
**API Version:** 1.0.0  
**Documentation Version:** 1.0.0 