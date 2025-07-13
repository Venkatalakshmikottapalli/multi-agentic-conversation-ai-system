import { crmAPI } from './api';

// Session Manager for automatic user creation and recognition
class SessionManager {
  constructor() {
    this.SESSION_KEY = 'crm_chatbot_session';
    this.USER_KEY = 'crm_chatbot_user';
  }

  // Get or create session ID
  getSessionId() {
    let sessionId = localStorage.getItem(this.SESSION_KEY);
    if (!sessionId) {
      sessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem(this.SESSION_KEY, sessionId);
    }
    return sessionId;
  }

  // Create new session (clears old data)
  createNewSession() {
    this.clearSession();
    return this.getSessionId();
  }

  // Get stored user info
  getStoredUser() {
    const userData = localStorage.getItem(this.USER_KEY);
    return userData ? JSON.parse(userData) : null;
  }

  // Store user info
  storeUser(user) {
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
  }

  // Clear session data
  clearSession() {
    localStorage.removeItem(this.SESSION_KEY);
    localStorage.removeItem(this.USER_KEY);
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
    return {
      id: `anonymous-${Date.now()}`,
      name: null,
      email: null,
      company: null,
      is_anonymous: true,
      created_at: new Date().toISOString()
    };
  }
}

export default new SessionManager(); 