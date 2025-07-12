# Multi-Agent Conversational AI System

A comprehensive end-to-end chatbot system with Retrieval-Augmented Generation (RAG) and Customer Relationship Management (CRM) capabilities built with FastAPI, React, OpenAI GPT, and advanced multi-agent architecture.

## 🚀 Features

### Core Capabilities
- **Multi-Agent Architecture**: Specialized agents for different domains (Real Estate, CRM, General)
- **RAG Integration**: Advanced document retrieval and context-aware responses
- **CRM System**: Complete customer relationship management with conversation tracking
- **Memory Management**: Persistent conversation history with contextual awareness
- **Document Processing**: Support for CSV, TXT, JSON, and PDF file uploads
- **Real-time Chat**: WebSocket-ready chat interface with session management
- **Analytics & Insights**: Comprehensive conversation analytics and user statistics

### Frontend Features
- **Modern React Interface**: Responsive, intuitive web application
- **Interactive Chat**: Real-time messaging with AI agents
- **User Management**: Complete CRM functionality with user profiles
- **Analytics Dashboard**: Rich data visualization with charts and statistics
- **Document Upload**: Drag-and-drop file management for knowledge base
- **System Settings**: Configurable preferences and behavior

### Technical Features
- **FastAPI**: High-performance async REST API
- **React 18**: Modern frontend framework with hooks
- **OpenAI GPT-4**: Advanced language model integration
- **ChromaDB**: Vector database for efficient document retrieval
- **SQLite**: Lightweight database for CRM data
- **Tailwind CSS**: Utility-first CSS framework
- **Multi-Agent System**: Intelligent agent selection based on context
- **Comprehensive Testing**: Unit and integration tests included

## 🏗️ System Architecture

### Full Stack Architecture

```mermaid
graph TB
    Browser[Web Browser] --> Frontend[React Frontend]
    Frontend --> API[FastAPI REST API]
    API --> ChatAgent[Multi-Agent Chat System]
    API --> RAG[RAG Service]
    API --> CRM[CRM Service]
    
    ChatAgent --> RealEstateAgent[Real Estate Agent]
    ChatAgent --> CRMAgent[CRM Agent]
    ChatAgent --> GeneralAgent[General Agent]
    
    RAG --> ChromaDB[ChromaDB Vector Store]
    RAG --> Embeddings[Sentence Transformers]
    
    CRM --> SQLite[SQLite Database]
    CRM --> Models[SQLAlchemy Models]
    
    ChatAgent --> OpenAI[OpenAI GPT-4]
    RAG --> OpenAI
```

### Database Schema

```mermaid
erDiagram
    User {
        string id PK
        string name
        string email
        string phone
        string company
        string role
        json preferences
        datetime created_at
        datetime updated_at
        boolean is_active
    }
    
    Conversation {
        string id PK
        string user_id FK
        string session_id
        string title
        string category
        string status
        datetime created_at
        datetime updated_at
    }
    
    Message {
        string id PK
        string conversation_id FK
        string role
        text content
        json metadata
        datetime timestamp
    }
    
    Document {
        string id PK
        string filename
        string content_type
        integer file_size
        text content
        json metadata
        datetime created_at
        datetime indexed_at
        boolean is_active
    }
    
    User ||--o{ Conversation : has
    Conversation ||--o{ Message : contains
```

## 🛠️ Quick Start

### Option 1: Automated Installation (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd multi-agent-ai-system
   ```

2. **Run the installation script:**
   ```bash
   ./install.sh
   ```

3. **Update your OpenAI API key in `.env` file:**
   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
   ```

4. **Start the system:**
   ```bash
   ./start.sh
   ```

5. **Access the application:**
   - Frontend: `http://localhost:3000`
   - Backend API: `http://localhost:8000`
   - API Documentation: `http://localhost:8000/docs`

### Option 2: Manual Installation

#### Prerequisites
- Python 3.8+ with pip
- Node.js 14+ with npm
- OpenAI API Key

#### Backend Setup

1. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install backend dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key
   ```

4. **Initialize database:**
   ```bash
   python -c "from database import create_tables; create_tables()"
   ```

5. **Start backend server:**
   ```bash
   python main.py
   ```

#### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install frontend dependencies:**
   ```bash
   npm install
   ```

3. **Start frontend server:**
   ```bash
   npm start
   ```

## 📱 Frontend Interface

### Dashboard Features

#### 1. Chat Interface
- **Real-time Messaging**: Interactive chat with AI agents
- **Agent Selection**: Automatic selection based on context
- **User Profiles**: Switch between different user contexts
- **Session Management**: Create new chats or reset conversations
- **Message History**: Persistent conversation storage

#### 2. User Management
- **Create Users**: Add new customer profiles with detailed information
- **View Details**: Comprehensive user profiles with statistics
- **Edit Profiles**: Update user information and preferences
- **Search & Filter**: Find users quickly with advanced search
- **Conversation History**: Access all user conversations and messages

#### 3. Analytics Dashboard
- **Key Metrics**: Total conversations, active users, completion rates
- **Visual Charts**: Interactive pie charts, bar charts, and line graphs
- **User Analytics**: Filter analytics by specific users
- **Export Data**: Download analytics data in JSON format
- **Real-time Updates**: Live data refresh with manual refresh option

#### 4. Document Management
- **File Upload**: Drag-and-drop interface for multiple file types
- **Supported Formats**: CSV, TXT, JSON, PDF, DOCX, MD files
- **Knowledge Base**: Manage AI's document collection
- **Statistics**: View total documents, chunks, and collection size
- **Clear Data**: Remove all documents with confirmation

#### 5. System Settings
- **API Configuration**: Server URLs, timeouts, and retry settings
- **Chat Settings**: AI model selection, temperature, token limits
- **RAG Configuration**: Document processing and retrieval settings
- **UI Preferences**: Theme, animations, and notification settings

## 📚 API Documentation

### Core Endpoints

#### Chat System
- `POST /chat` - Send message to AI system
- `POST /reset` - Reset conversation memory

#### User Management
- `POST /crm/create_user` - Create new user
- `GET /crm/users` - List all users (paginated)
- `GET /crm/users/{user_id}` - Get user details
- `PUT /crm/update_user/{user_id}` - Update user information
- `DELETE /crm/users/{user_id}` - Delete user (soft delete)

#### Conversation Management
- `GET /crm/conversations/{user_id}` - Get user conversations
- `GET /crm/conversations/{user_id}/{conversation_id}` - Get conversation details
- `GET /crm/search` - Search conversations
- `GET /crm/analytics` - Get conversation analytics
- `GET /crm/users/{user_id}/stats` - Get user statistics

#### Document Management
- `POST /upload_docs` - Upload documents to knowledge base
- `GET /rag/stats` - Get RAG system statistics
- `DELETE /rag/clear` - Clear document collection

#### System
- `GET /health` - System health check
- `GET /` - API information

### Request/Response Examples

#### Chat Request
```json
{
  "message": "I'm looking for office space in Manhattan",
  "user_id": "user-123",
  "session_id": "session-456",
  "context": {
    "preferences": {
      "location": "Manhattan",
      "size": "large"
    }
  }
}
```

#### Chat Response
```json
{
  "response": "I can help you find office space in Manhattan. Based on our available properties, I have several options that might interest you...",
  "user_id": "user-123",
  "session_id": "session-456",
  "conversation_id": "conv-789",
  "sources": [
    {
      "source": "property_data.csv",
      "content": "Property at 123 Main St...",
      "similarity_score": 0.95
    }
  ],
  "metadata": {
    "agent_used": "Real Estate Specialist",
    "processing_time": 1.2,
    "rag_documents_found": 5
  },
  "processing_time": 1.2
}
```

## 🧪 Testing

### Running Tests

```bash
# Backend tests
pytest tests/ -v

# Frontend tests
cd frontend
npm test

# Integration tests
python test_system.py
```

### Test Coverage

- **Backend**: Unit tests for services, models, and API endpoints
- **Frontend**: Component tests and integration tests
- **End-to-End**: Full system workflow tests

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview

# Database Configuration
DATABASE_URL=sqlite:///./crm_chatbot.db

# Vector Database Configuration
CHROMA_DB_PATH=./chroma_db

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# RAG Configuration
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_RETRIEVAL_DOCS=5

# Chat Configuration
MAX_CONVERSATION_HISTORY=50
DEFAULT_TEMPERATURE=0.7
MAX_TOKENS=1000
```

#### Frontend (frontend/.env)
```bash
REACT_APP_API_URL=http://localhost:8000
```

## 🚀 Deployment

### Production Build

1. **Build frontend:**
   ```bash
   cd frontend
   npm run build
   ```

2. **Configure production environment:**
   ```bash
   export DEBUG=False
   export DATABASE_URL=postgresql://user:pass@localhost/db
   ```

3. **Run with production server:**
   ```bash
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```

### Docker Deployment

```dockerfile
# Backend Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Frontend Dockerfile
FROM node:16-alpine
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## 🤖 Multi-Agent System

### Agent Types

1. **Real Estate Agent**
   - Specializes in property inquiries
   - Handles location-based searches
   - Provides property details and broker information

2. **CRM Agent**
   - Focuses on customer information extraction
   - Manages user preferences and data
   - Handles relationship building

3. **General Agent**
   - Handles general inquiries
   - Provides fallback responses
   - Manages miscellaneous tasks

### Agent Selection Logic

The system automatically selects the most appropriate agent based on:
- Message content analysis
- Conversation context
- User history
- Keywords and intent detection

## 📊 Analytics & Monitoring

### Available Metrics

- **Conversation Analytics**: Status breakdown, category distribution
- **User Statistics**: Message counts, conversation frequency
- **System Performance**: Response times, error rates
- **RAG Performance**: Document retrieval accuracy, relevance scores

### Frontend Analytics Features

- **Interactive Dashboards**: Real-time charts and graphs
- **Data Export**: Download analytics in JSON format
- **Filtering**: View analytics by user, time range, or category
- **Visual Insights**: Pie charts, bar charts, and line graphs

## 🛡️ Security & Privacy

### Data Protection
- **Input Validation**: Comprehensive validation with Pydantic models
- **Error Handling**: Secure error messages and logging
- **Session Management**: Secure session handling
- **Data Privacy**: Soft deletion for user data

### API Security
- **CORS Configuration**: Proper cross-origin resource sharing
- **Rate Limiting**: Configurable request limits
- **Authentication**: Ready for authentication system integration

## 🔗 Integration Guide

### Adding New Agents

1. **Create Agent Class:**
   ```python
   class CustomAgent(Agent):
       def __init__(self):
           super().__init__(
               name="Custom Agent",
               role="Custom Role",
               instructions="Custom instructions..."
           )
   ```

2. **Register Agent:**
   ```python
   # In chat_agent.py
   self.agents["custom_agent"] = CustomAgent()
   ```

3. **Update Selection Logic:**
   ```python
   # Add selection criteria
   if "custom_keyword" in message.lower():
       return "custom_agent"
   ```

### Adding New API Endpoints

1. **Backend (FastAPI):**
   ```python
   @app.post("/custom_endpoint")
   async def custom_endpoint(data: CustomSchema):
       # Implementation
       return {"result": "success"}
   ```

2. **Frontend (React):**
   ```javascript
   // In services/api.js
   export const customAPI = {
     customEndpoint: async (data) => {
       const response = await api.post('/custom_endpoint', data);
       return response.data;
     }
   };
   ```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Use ESLint and Prettier for JavaScript code
- Add tests for new features
- Update documentation as needed

## 📈 Roadmap

### Upcoming Features
- [ ] WebSocket real-time chat
- [ ] Advanced user authentication
- [ ] Email notifications
- [ ] Mobile app support
- [ ] Advanced analytics
- [ ] Multi-language support
- [ ] Voice interface integration

### Known Issues
- Large file uploads may timeout
- Analytics charts may not refresh automatically
- Mobile responsiveness needs improvement

## 🆘 Troubleshooting

### Common Issues

1. **Backend won't start:**
   - Check Python version (3.8+)
   - Verify OpenAI API key
   - Check port 8000 availability

2. **Frontend won't start:**
   - Check Node.js version (14+)
   - Clear node_modules: `rm -rf node_modules && npm install`
   - Check port 3000 availability

3. **API connection failed:**
   - Ensure backend is running
   - Check CORS settings
   - Verify API URL in frontend env

4. **Database errors:**
   - Check database file permissions
   - Recreate database: `python -c "from database import create_tables; create_tables()"`

5. **Chat not working:**
   - Verify OpenAI API key
   - Check API quota limits
   - Review network connectivity

### Getting Help

- Check the [Issues](https://github.com/your-repo/issues) page
- Review the API documentation at `/docs`
- Run the test suite to identify issues
- Check system logs for error messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for GPT-4 language model
- ChromaDB for vector database
- FastAPI for the excellent backend framework
- React and the frontend ecosystem
- All contributors and testers

---

**Built with ❤️ for intelligent customer relationship management**

For more detailed information, check the individual README files in the `frontend/` directory and the API documentation at `/docs` when the server is running. 