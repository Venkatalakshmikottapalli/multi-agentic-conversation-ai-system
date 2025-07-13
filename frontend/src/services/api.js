import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`Making ${config.method.toUpperCase()} request to ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Chat API
export const chatAPI = {
  sendMessage: async (message, userId, sessionId, context = {}) => {
    const response = await api.post('/chat', {
      message,
      user_id: userId,
      session_id: sessionId,
      context,
    });
    return response.data;
  },

  resetConversation: async (resetType, userId = null) => {
    const response = await api.post('/reset', {
      reset_type: resetType,
      user_id: userId,
    });
    return response.data;
  },
};

// User/CRM API
export const crmAPI = {
  createUser: async (userData) => {
    const response = await api.post('/crm/create_user', userData);
    return response.data;
  },

  getUsers: async (page = 1, perPage = 10) => {
    const response = await api.get('/crm/users', {
      params: { page, per_page: perPage },
    });
    return response.data;
  },

  getUser: async (userId) => {
    const response = await api.get(`/crm/users/${userId}`);
    return response.data;
  },

  findUserByEmail: async (email) => {
    const response = await api.get(`/crm/users/find/${email}`);
    return response.data;
  },

  updateUser: async (userId, userData) => {
    const response = await api.put(`/crm/update_user/${userId}`, userData);
    return response.data;
  },

  deleteUser: async (userId) => {
    const response = await api.delete(`/crm/users/${userId}`);
    return response.data;
  },

  getUserConversations: async (userId, page = 1, perPage = 10) => {
    const response = await api.get(`/crm/conversations/${userId}`, {
      params: { page, per_page: perPage },
    });
    return response.data;
  },

  getConversationDetails: async (userId, conversationId) => {
    const response = await api.get(`/crm/conversations/${userId}/${conversationId}`);
    return response.data;
  },

  getUserStats: async (userId) => {
    const response = await api.get(`/crm/users/${userId}/stats`);
    return response.data;
  },

  searchConversations: async (query, userId = null, page = 1, perPage = 10) => {
    const response = await api.get('/crm/search', {
      params: { q: query, user_id: userId, page, per_page: perPage },
    });
    return response.data;
  },
};

// Session Management API
export const sessionAPI = {
  createSession: async (userId) => {
    const response = await api.post('/sessions/create', null, {
      params: { user_id: userId },
    });
    return response.data;
  },

  validateSession: async (sessionToken) => {
    const response = await api.get(`/sessions/validate/${sessionToken}`);
    return response.data;
  },

  extendSession: async (sessionToken, extendHours = 24) => {
    const response = await api.post(`/sessions/extend/${sessionToken}`, null, {
      params: { extend_hours: extendHours },
    });
    return response.data;
  },

  revokeSession: async (sessionToken) => {
    const response = await api.post(`/sessions/revoke/${sessionToken}`);
    return response.data;
  },

  getUserSessions: async (userId, activeOnly = true) => {
    const response = await api.get(`/sessions/user/${userId}`, {
      params: { active_only: activeOnly },
    });
    return response.data;
  },

  cleanupExpiredSessions: async () => {
    const response = await api.post('/sessions/cleanup');
    return response.data;
  },
};

// Document/RAG API
export const docAPI = {
  uploadDocuments: async (files) => {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });

    const response = await api.post('/upload_docs', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  getRagStats: async () => {
    const response = await api.get('/rag/stats');
    return response.data;
  },

  clearRagData: async () => {
    const response = await api.delete('/rag/clear');
    return response.data;
  },

  getDocuments: async (page = 1, perPage = 10) => {
    const response = await api.get('/rag/documents', {
      params: { page, per_page: perPage },
    });
    return response.data;
  },

  deleteDocument: async (filename) => {
    // URL encode the filename to handle special characters
    const encodedFilename = encodeURIComponent(filename);
    const response = await api.delete(`/rag/documents/${encodedFilename}`);
    return response.data;
  },
};

// System API
export const systemAPI = {
  getHealth: async () => {
    const response = await api.get('/health');
    return response.data;
  },

  getApiInfo: async () => {
    const response = await api.get('/');
    return response.data;
  },
};

export default api; 