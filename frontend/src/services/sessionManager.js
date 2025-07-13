import { crmAPI } from './api';
import chatHistoryService from './chatHistoryService';

// Session Manager for user and session management
class SessionManager {
  constructor() {
    this.SESSION_KEY = 'crm_chatbot_session';
    this.USER_KEY = 'crm_chatbot_user';
  }

  // Get or create session ID (deprecated - use chatHistoryService instead)
  getSessionId() {
    const currentSessionId = chatHistoryService.getCurrentSessionId();
    if (currentSessionId) {
      return currentSessionId;
    }
    
    // Legacy fallback
    let sessionId = localStorage.getItem(this.SESSION_KEY);
    if (!sessionId) {
      sessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem(this.SESSION_KEY, sessionId);
    }
    return sessionId;
  }

  // Create new session using chatHistoryService
  createNewSession() {
    const newSession = chatHistoryService.createNewSession();
    return newSession.id;
  }

  // Get current session ID
  getCurrentSessionId() {
    return chatHistoryService.getCurrentSessionId();
  }

  // Get stored user info
  getStoredUser() {
    // Try to get from chatHistoryService first
    const activeUser = chatHistoryService.getActiveUser();
    if (activeUser) {
      return activeUser;
    }
    
    // Legacy fallback
    const userData = localStorage.getItem(this.USER_KEY);
    return userData ? JSON.parse(userData) : null;
  }

  // Store user info
  storeUser(user) {
    // Store in both places for compatibility
    chatHistoryService.setActiveUser(user);
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
    
    // Update current session with user
    const currentSessionId = chatHistoryService.getCurrentSessionId();
    if (currentSessionId && user) {
      chatHistoryService.updateSessionUser(currentSessionId, user.id);
    }
  }

  // Clear only user session data (not chat history)
  clearUserSession() {
    localStorage.removeItem(this.USER_KEY);
    chatHistoryService.setActiveUser(null);
  }

  // Clear specific session (legacy support)
  clearSession() {
    localStorage.removeItem(this.SESSION_KEY);
    localStorage.removeItem(this.USER_KEY);
    // Don't clear chat history - this is now managed by chatHistoryService
  }

  // Clear all sessions and history
  clearAllSessions() {
    localStorage.removeItem(this.SESSION_KEY);
    localStorage.removeItem(this.USER_KEY);
    chatHistoryService.clearAllSessions();
  }

  // Check if user exists by email (for returning users)
  async findUserByEmail(email) {
    try {
      const response = await crmAPI.findUserByEmail(email);
      return response.data;
    } catch (error) {
      console.error('Error finding user by email:', error);
      return null;
    }
  }

  // Create anonymous user for new sessions
  createAnonymousUser() {
    const anonymousUser = {
      id: `anonymous-${Date.now()}`,
      name: null,
      email: null,
      company: null,
      is_anonymous: true,
      created_at: new Date().toISOString()
    };
    
    // Store the anonymous user
    this.storeUser(anonymousUser);
    return anonymousUser;
  }

  // Get or create user for session
  getOrCreateSessionUser() {
    let user = this.getStoredUser();
    if (!user) {
      user = this.createAnonymousUser();
    }
    return user;
  }

  // Switch to different session
  switchToSession(sessionId) {
    const session = chatHistoryService.switchToSession(sessionId);
    if (session) {
      // Update active user based on session
      if (session.user_id) {
        // Try to load user info for this session
        this.loadUserForSession(session.user_id);
      }
      return session;
    }
    return null;
  }

  // Load user info for a specific session
  async loadUserForSession(userId) {
    try {
      const response = await crmAPI.getUser(userId);
      if (response.data) {
        this.storeUser(response.data);
        return response.data;
      }
    } catch (error) {
      console.error('Error loading user for session:', error);
    }
    return null;
  }

  // Get current session
  getCurrentSession() {
    return chatHistoryService.getCurrentSession();
  }

  // Get all sessions
  getAllSessions() {
    return chatHistoryService.getSessionsList();
  }

  // Delete a session
  deleteSession(sessionId) {
    return chatHistoryService.deleteSession(sessionId);
  }

  // Add message to current session
  addMessageToCurrentSession(message) {
    const currentSessionId = chatHistoryService.getCurrentSessionId();
    if (currentSessionId) {
      return chatHistoryService.addMessageToSession(currentSessionId, message);
    }
    return null;
  }

  // Update session with new message
  updateSessionWithMessage(sessionId, message) {
    return chatHistoryService.addMessageToSession(sessionId, message);
  }

  // Initialize session on app start
  initializeSession() {
    let currentSession = chatHistoryService.getCurrentSession();
    
    // Ensure we have a user
    let user = this.getStoredUser();
    if (!user) {
      user = this.createAnonymousUser();
    }
    
    // Update session with user if not already set
    if (currentSession && !currentSession.user_id && user) {
      chatHistoryService.updateSessionUser(currentSession.id, user.id);
    }
    
    return {
      session: currentSession,
      user: user
    };
  }

  // Sync session with backend (optional)
  async syncSessionWithBackend(sessionId, userId) {
    try {
      const backendSession = await chatHistoryService.loadSessionFromBackend(sessionId, userId);
      if (backendSession) {
        // Update local session with backend data
        chatHistoryService.updateSession(sessionId, backendSession);
        return backendSession;
      }
    } catch (error) {
      console.error('Error syncing session with backend:', error);
    }
    return null;
  }
}

// Export singleton instance
const sessionManager = new SessionManager();
export default sessionManager; 