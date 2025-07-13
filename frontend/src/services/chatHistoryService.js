import { crmAPI } from './api';

class ChatHistoryService {
  constructor() {
    this.CHAT_SESSIONS_KEY = 'crm_chatbot_sessions';
    this.CURRENT_SESSION_KEY = 'crm_chatbot_current_session';
    this.ACTIVE_USER_KEY = 'crm_chatbot_active_user';
  }

  // Get all chat sessions
  getAllSessions() {
    try {
      const sessions = localStorage.getItem(this.CHAT_SESSIONS_KEY);
      return sessions ? JSON.parse(sessions) : {};
    } catch (error) {
      console.error('Error getting chat sessions:', error);
      return {};
    }
  }

  // Get current session ID
  getCurrentSessionId() {
    return localStorage.getItem(this.CURRENT_SESSION_KEY);
  }

  // Set current session ID
  setCurrentSessionId(sessionId) {
    localStorage.setItem(this.CURRENT_SESSION_KEY, sessionId);
  }

  // Get active user
  getActiveUser() {
    try {
      const user = localStorage.getItem(this.ACTIVE_USER_KEY);
      return user ? JSON.parse(user) : null;
    } catch (error) {
      console.error('Error getting active user:', error);
      return null;
    }
  }

  // Set active user
  setActiveUser(user) {
    localStorage.setItem(this.ACTIVE_USER_KEY, JSON.stringify(user));
  }

  // Create a new chat session
  createNewSession(title = null) {
    const sessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const sessions = this.getAllSessions();
    
    const newSession = {
      id: sessionId,
      title: title || `Chat ${Object.keys(sessions).length + 1}`,
      messages: [{
        id: Date.now(),
        type: 'bot',
        content: 'Hello! I\'m your AI assistant. I can help you with real estate inquiries, customer management, and general questions. How can I assist you today?',
        timestamp: new Date().toISOString(),
        metadata: { agent_used: 'System' }
      }],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      user_id: null
    };

    sessions[sessionId] = newSession;
    this.saveAllSessions(sessions);
    this.setCurrentSessionId(sessionId);
    
    return newSession;
  }

  // Get a specific session
  getSession(sessionId) {
    const sessions = this.getAllSessions();
    return sessions[sessionId] || null;
  }

  // Get current session
  getCurrentSession() {
    const currentSessionId = this.getCurrentSessionId();
    if (!currentSessionId) {
      return this.createNewSession();
    }
    
    const session = this.getSession(currentSessionId);
    if (!session) {
      return this.createNewSession();
    }
    
    return session;
  }

  // Save all sessions
  saveAllSessions(sessions) {
    localStorage.setItem(this.CHAT_SESSIONS_KEY, JSON.stringify(sessions));
  }

  // Update session
  updateSession(sessionId, updates) {
    const sessions = this.getAllSessions();
    if (sessions[sessionId]) {
      sessions[sessionId] = {
        ...sessions[sessionId],
        ...updates,
        updated_at: new Date().toISOString()
      };
      this.saveAllSessions(sessions);
      return sessions[sessionId];
    }
    return null;
  }

  // Add message to session
  addMessageToSession(sessionId, message) {
    const sessions = this.getAllSessions();
    if (sessions[sessionId]) {
      sessions[sessionId].messages.push({
        ...message,
        timestamp: message.timestamp || new Date().toISOString()
      });
      sessions[sessionId].updated_at = new Date().toISOString();
      
      // Update title if it's the first user message
      if (message.type === 'user' && sessions[sessionId].messages.filter(m => m.type === 'user').length === 1) {
        sessions[sessionId].title = this.generateTitleFromMessage(message.content);
      }
      
      this.saveAllSessions(sessions);
      return sessions[sessionId];
    }
    return null;
  }

  // Generate title from first message
  generateTitleFromMessage(message) {
    const words = message.split(' ');
    const title = words.slice(0, 6).join(' ');
    return title.length > 50 ? title.substring(0, 50) + '...' : title;
  }

  // Delete session
  deleteSession(sessionId) {
    const sessions = this.getAllSessions();
    if (sessions[sessionId]) {
      delete sessions[sessionId];
      this.saveAllSessions(sessions);
      
      // If this was the current session, switch to another one or create new
      if (this.getCurrentSessionId() === sessionId) {
        const remainingSessions = Object.keys(sessions);
        if (remainingSessions.length > 0) {
          this.setCurrentSessionId(remainingSessions[0]);
        } else {
          this.createNewSession();
        }
      }
      
      return true;
    }
    return false;
  }

  // Get sessions list for sidebar (sorted by updated_at)
  getSessionsList() {
    const sessions = this.getAllSessions();
    return Object.values(sessions).sort((a, b) => 
      new Date(b.updated_at) - new Date(a.updated_at)
    );
  }

  // Switch to a different session
  switchToSession(sessionId) {
    const session = this.getSession(sessionId);
    if (session) {
      this.setCurrentSessionId(sessionId);
      return session;
    }
    return null;
  }

  // Clear all sessions (for reset functionality)
  clearAllSessions() {
    localStorage.removeItem(this.CHAT_SESSIONS_KEY);
    localStorage.removeItem(this.CURRENT_SESSION_KEY);
    localStorage.removeItem(this.ACTIVE_USER_KEY);
  }

  // Load session from backend (if available)
  async loadSessionFromBackend(sessionId, userId) {
    try {
      if (!userId) return null;
      
      const conversations = await crmAPI.getUserConversations(userId);
      const conversation = conversations.data.find(conv => conv.session_id === sessionId);
      
      if (conversation) {
        const details = await crmAPI.getConversationDetails(userId, conversation.id);
        return this.convertBackendConversationToSession(details.data);
      }
      
      return null;
    } catch (error) {
      console.error('Error loading session from backend:', error);
      return null;
    }
  }

  // Convert backend conversation to session format
  convertBackendConversationToSession(conversation) {
    return {
      id: conversation.session_id,
      title: conversation.title,
      messages: conversation.messages.map(msg => ({
        id: msg.id,
        type: msg.role === 'user' ? 'user' : 'bot',
        content: msg.content,
        timestamp: msg.timestamp,
        metadata: msg.message_metadata
      })),
      created_at: conversation.created_at,
      updated_at: conversation.updated_at,
      user_id: conversation.user_id
    };
  }

  // Update session user
  updateSessionUser(sessionId, userId) {
    const sessions = this.getAllSessions();
    if (sessions[sessionId]) {
      sessions[sessionId].user_id = userId;
      sessions[sessionId].updated_at = new Date().toISOString();
      this.saveAllSessions(sessions);
      return sessions[sessionId];
    }
    return null;
  }

  // Get session count
  getSessionCount() {
    const sessions = this.getAllSessions();
    return Object.keys(sessions).length;
  }
}

// Export singleton instance
const chatHistoryService = new ChatHistoryService();
export default chatHistoryService; 