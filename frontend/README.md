# CRM Chatbot Frontend

A modern React-based frontend for the Multi-Agent Conversational AI CRM System. This interface provides a comprehensive dashboard for managing conversations, users, analytics, and document uploads.

## Features

### 🎯 Core Features
- **Interactive Chat Interface**: Real-time messaging with AI agents
- **Multi-Agent Support**: Automatic agent selection based on conversation context
- **User Management**: Complete CRM functionality with user profiles
- **Analytics Dashboard**: Comprehensive insights with charts and statistics
- **Document Management**: Upload and manage knowledge base documents
- **Settings Panel**: Configure system preferences and behavior

### 🎨 UI/UX Features
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Modern Interface**: Clean, professional design with Tailwind CSS
- **Real-time Updates**: Live chat updates and system status monitoring
- **Intuitive Navigation**: Easy-to-use sidebar navigation
- **Interactive Charts**: Rich data visualization with Recharts
- **Drag & Drop**: File upload with drag-and-drop support

## Tech Stack

- **React 18** - Frontend framework
- **React Router** - Client-side routing
- **Tailwind CSS** - Utility-first CSS framework
- **Axios** - HTTP client for API calls
- **Recharts** - Data visualization library
- **Lucide React** - Beautiful icons

## Prerequisites

- Node.js (v14 or higher)
- npm or yarn package manager
- Running CRM Chatbot Backend (see backend README)

## Installation

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Configure environment (optional):**
   Create a `.env` file in the frontend directory:
   ```env
   REACT_APP_API_URL=http://localhost:8000
   ```

4. **Start the development server:**
   ```bash
   npm start
   ```

   The frontend will be available at `http://localhost:3000`

## Available Scripts

- `npm start` - Runs the app in development mode
- `npm run build` - Builds the app for production
- `npm test` - Launches the test runner
- `npm run eject` - Ejects from Create React App (irreversible)

## Project Structure

```
frontend/
├── public/
│   └── index.html          # Main HTML file
├── src/
│   ├── components/         # React components
│   │   ├── Analytics.js    # Analytics dashboard
│   │   ├── Chat.js         # Chat interface
│   │   ├── Documents.js    # Document management
│   │   ├── Settings.js     # Settings panel
│   │   ├── Sidebar.js      # Navigation sidebar
│   │   └── UserManager.js  # User management
│   ├── services/
│   │   └── api.js          # API service layer
│   ├── App.js              # Main application component
│   ├── index.js            # Application entry point
│   └── index.css           # Global styles
├── package.json            # Dependencies and scripts
├── tailwind.config.js      # Tailwind CSS configuration
└── README.md               # This file
```

## Usage Guide

### 1. Chat Interface
- **Start Conversations**: Type messages in the chat input
- **Agent Selection**: System automatically chooses the best agent
- **User Context**: Select a user profile for personalized responses
- **Session Management**: Create new chats or reset conversations

### 2. User Management
- **Create Users**: Add new customer profiles
- **View Details**: Access comprehensive user information
- **Edit Profiles**: Update user information
- **Search & Filter**: Find users quickly
- **Conversation History**: View user's chat history

### 3. Analytics Dashboard
- **Key Metrics**: View conversation statistics
- **Visual Charts**: Interactive charts for data insights
- **User Analytics**: Filter by specific users
- **Export Data**: Download analytics in JSON format
- **Real-time Updates**: Live data refresh

### 4. Document Management
- **Upload Files**: Drag-and-drop or browse to upload
- **Supported Formats**: CSV, TXT, JSON, PDF, DOCX, MD
- **Knowledge Base**: Manage AI's knowledge base
- **Statistics**: View document collection metrics
- **Clear Data**: Remove all documents when needed

### 5. Settings
- **API Configuration**: Server settings and timeouts
- **Chat Settings**: AI model and behavior parameters
- **RAG Configuration**: Document processing settings
- **UI Preferences**: Theme and interface options

## API Integration

The frontend communicates with the backend through a comprehensive API service layer:

```javascript
// Example API usage
import { chatAPI, crmAPI, docAPI, systemAPI } from './services/api';

// Send a chat message
const response = await chatAPI.sendMessage(message, userId, sessionId);

// Create a new user
const user = await crmAPI.createUser(userData);

// Upload documents
const result = await docAPI.uploadDocuments(files);

// Get system health
const health = await systemAPI.getHealth();
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REACT_APP_API_URL` | Backend API URL | `http://localhost:8000` |

## Building for Production

1. **Build the application:**
   ```bash
   npm run build
   ```

2. **Serve the built files:**
   ```bash
   # Using serve (install globally: npm install -g serve)
   serve -s build

   # Or using any static file server
   python -m http.server 3000 -d build
   ```

## Development Tips

### Hot Reloading
The development server includes hot reloading. Changes to components will automatically refresh the browser.

### Error Handling
The application includes comprehensive error handling with user-friendly messages and retry mechanisms.

### Responsive Design
The interface adapts to different screen sizes:
- Desktop: Full sidebar navigation
- Mobile: Collapsible sidebar with overlay

### Performance
- Lazy loading for large datasets
- Efficient state management
- Optimized API calls with caching

## Customization

### Styling
Modify `tailwind.config.js` to customize colors, fonts, and spacing:

```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          500: '#your-color',
        },
      },
    },
  },
};
```

### API Endpoints
Update `src/services/api.js` to change API endpoints or add new ones:

```javascript
export const customAPI = {
  newEndpoint: async (data) => {
    const response = await api.post('/custom-endpoint', data);
    return response.data;
  },
};
```

## Troubleshooting

### Common Issues

1. **API Connection Failed**
   - Ensure backend server is running
   - Check API URL in environment variables
   - Verify CORS settings on backend

2. **Build Errors**
   - Clear node_modules and package-lock.json
   - Reinstall dependencies: `npm install`
   - Check for version conflicts

3. **Styling Issues**
   - Rebuild Tailwind CSS: `npm run build`
   - Check for conflicting CSS rules
   - Verify Tailwind configuration

### Performance Issues
- Use React DevTools to profile components
- Check network tab for slow API calls
- Optimize images and assets

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is part of the Multi-Agent Conversational AI System. Please refer to the main project license for details.

## Support

For issues and questions:
- Check the troubleshooting section above
- Review the backend documentation
- Create an issue in the main repository

---

**Built with ❤️ using React and modern web technologies** 