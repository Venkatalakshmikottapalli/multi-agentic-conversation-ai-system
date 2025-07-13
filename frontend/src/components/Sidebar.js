import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  MessageSquare, 
  Users, 
  FileText, 
  X,
  Search,
  Trash2,
  Clock
} from 'lucide-react';
import chatHistoryService from '../services/chatHistoryService';
import sessionManager from '../services/sessionManager';

const Sidebar = ({ isOpen, onClose, currentUser, onUserSelect, onSessionChange, refreshTrigger }) => {
  const location = useLocation();
  const [chatSessions, setChatSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(null);

  useEffect(() => {
    loadChatSessions();
    const currentId = chatHistoryService.getCurrentSessionId();
    setCurrentSessionId(currentId);
  }, []);

  // Refresh sessions when refreshTrigger changes
  useEffect(() => {
    if (refreshTrigger > 0) {
      loadChatSessions();
      const currentId = chatHistoryService.getCurrentSessionId();
      setCurrentSessionId(currentId);
    }
  }, [refreshTrigger]);

  const loadChatSessions = () => {
    const sessions = chatHistoryService.getSessionsList();
    setChatSessions(sessions);
  };

  const handleSessionClick = (sessionId) => {
    const session = chatHistoryService.switchToSession(sessionId);
    if (session) {
      setCurrentSessionId(sessionId);
      
      // Load user for this session if available
      if (session.user_id) {
        sessionManager.loadUserForSession(session.user_id);
      }
      
      // Notify parent component about session change
      if (onSessionChange) {
        onSessionChange(session);
      }
    }
  };

  const handleDeleteSession = (sessionId, e) => {
    e.stopPropagation();
    setShowDeleteConfirm(sessionId);
  };

  const confirmDeleteSession = () => {
    if (showDeleteConfirm) {
      const success = chatHistoryService.deleteSession(showDeleteConfirm);
      if (success) {
        loadChatSessions();
        
        // Update current session if it was deleted
        const newCurrentId = chatHistoryService.getCurrentSessionId();
        setCurrentSessionId(newCurrentId);
        
        // Notify parent component about session change
        if (onSessionChange) {
          const newSession = chatHistoryService.getCurrentSession();
          onSessionChange(newSession);
        }
      }
      setShowDeleteConfirm(null);
    }
  };

  const cancelDeleteSession = () => {
    setShowDeleteConfirm(null);
  };

  const formatSessionTime = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = (now - date) / (1000 * 60 * 60);
    
    if (diffInHours < 1) {
      return 'Just now';
    } else if (diffInHours < 24) {
      return `${Math.floor(diffInHours)}h ago`;
    } else if (diffInHours < 168) {
      return `${Math.floor(diffInHours / 24)}d ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  const getSessionPreview = (session) => {
    const userMessages = session.messages.filter(msg => msg.type === 'user');
    if (userMessages.length > 0) {
      return userMessages[0].content.substring(0, 50) + '...';
    }
    return 'New conversation';
  };

  const filteredSessions = chatSessions.filter(session =>
    session.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    getSessionPreview(session).toLowerCase().includes(searchTerm.toLowerCase())
  );

  const menuItems = [
    { name: 'Chat', icon: MessageSquare, path: '/chat' },
    { name: 'Documents', icon: FileText, path: '/documents' },
  ];

  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-50 w-80 bg-white shadow-lg transform transition-transform duration-300 ease-in-out
        lg:translate-x-0 lg:static lg:inset-0
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Navigation</h2>
            <button
              onClick={onClose}
              className="p-2 rounded-md hover:bg-gray-100 lg:hidden"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Navigation Menu */}
          <nav className="p-4 border-b border-gray-200">
            <ul className="space-y-2">
              {menuItems.map((item) => (
                <li key={item.name}>
                  <Link
                    to={item.path}
                    className={`
                      flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors
                      ${location.pathname === item.path
                        ? 'bg-blue-50 text-blue-700 border border-blue-200'
                        : 'text-gray-700 hover:bg-gray-100'
                      }
                    `}
                    onClick={() => onClose()}
                  >
                    <item.icon className="w-5 h-5" />
                    <span className="font-medium">{item.name}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </nav>

          {/* Chat History Section */}
          {location.pathname === '/chat' && (
            <div className="flex-1 flex flex-col overflow-hidden">
              {/* Chat History Header */}
              <div className="p-4 border-b border-gray-200">
                <div className="mb-3">
                  <h3 className="text-md font-semibold text-gray-900">Chat History</h3>
                </div>
                
                {/* Search */}
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search conversations..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                  />
                </div>
              </div>

              {/* Chat Sessions List */}
              <div className="flex-1 overflow-y-auto">
                {filteredSessions.length === 0 ? (
                  <div className="p-4 text-center text-gray-500">
                    <MessageSquare className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                    <p className="text-sm">No chat sessions found</p>
                  </div>
                ) : (
                  <div className="p-2 space-y-1">
                    {filteredSessions.map((session) => (
                      <div
                        key={session.id}
                        className={`
                          group relative p-3 rounded-lg cursor-pointer transition-all
                          ${currentSessionId === session.id
                            ? 'bg-blue-50 border border-blue-200'
                            : 'hover:bg-gray-50'
                          }
                        `}
                        onClick={() => handleSessionClick(session.id)}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center space-x-2 mb-1">
                              <MessageSquare className="w-4 h-4 text-gray-400 flex-shrink-0" />
                              <h4 className="text-sm font-medium text-gray-900 truncate">
                                {session.title}
                              </h4>
                            </div>
                            <p className="text-xs text-gray-500 truncate mb-1">
                              {getSessionPreview(session)}
                            </p>
                            <div className="flex items-center space-x-2 text-xs text-gray-400">
                              <Clock className="w-3 h-3" />
                              <span>{formatSessionTime(session.updated_at)}</span>
                              <span>|</span>
                              <span>{session.messages.filter(m => m.type === 'user').length} messages</span>
                            </div>
                          </div>
                          
                          <button
                            onClick={(e) => handleDeleteSession(session.id, e)}
                            className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-50 hover:text-red-600 transition-all"
                            title="Delete conversation"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Current User Info */}
          {currentUser && (
            <div className="p-4 border-t border-gray-200">
              <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                  <Users className="w-4 h-4 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {currentUser.name || 'Anonymous User'}
                  </p>
                  {currentUser.email && (
                    <p className="text-xs text-gray-500 truncate">
                      {currentUser.email}
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-sm w-full p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Delete Conversation
            </h3>
            <p className="text-gray-600 mb-6">
              Are you sure you want to delete this conversation? This action cannot be undone.
            </p>
            <div className="flex space-x-3">
              <button
                onClick={confirmDeleteSession}
                className="flex-1 bg-red-500 text-white py-2 px-4 rounded-lg hover:bg-red-600 transition-colors"
              >
                Delete
              </button>
              <button
                onClick={cancelDeleteSession}
                className="flex-1 bg-gray-200 text-gray-800 py-2 px-4 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default Sidebar; 