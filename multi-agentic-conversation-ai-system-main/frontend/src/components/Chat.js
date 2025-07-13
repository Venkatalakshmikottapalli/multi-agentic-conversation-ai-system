import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Send, User, Bot, Loader2, Plus, RotateCcw, AlertCircle } from 'lucide-react';
import { chatAPI } from '../services/api';
import sessionManager from '../services/sessionManager';

// Move MessageBubble outside main component and memoize it
const MessageBubble = React.memo(({ message }) => {
  const isUser = message.type === 'user';
  const isError = message.type === 'error';
  
  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`
        max-w-xs lg:max-w-md xl:max-w-lg px-4 py-3 rounded-lg
        ${isUser 
          ? 'bg-blue-500 text-white' 
          : isError 
            ? 'bg-red-100 text-red-700 border border-red-300'
            : 'bg-white text-gray-800 shadow-sm border border-gray-200'
        }
      `}>
        <div className="flex items-start space-x-2">
          {!isUser && (
            <div className={`
              w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0
              ${isError ? 'bg-red-500' : 'bg-blue-500'}
            `}>
              {isError ? (
                <AlertCircle className="w-4 h-4 text-white" />
              ) : (
                <Bot className="w-4 h-4 text-white" />
              )}
            </div>
          )}
          
          <div className="flex-1">
            <div className="text-sm whitespace-pre-wrap">{message.content}</div>
            
            {message.metadata && (
              <div className="mt-2 text-xs opacity-75">
                Agent: {message.metadata.agent_used}
                {message.processing_time && (
                  <span className="ml-2">
                    ({message.processing_time.toFixed(2)}s)
                  </span>
                )}
              </div>
            )}
            
            {message.sources && message.sources.length > 0 && (
              <div className="mt-2 text-xs">
                <div className="font-medium">Sources:</div>
                {message.sources.map((source, index) => (
                  <div key={index} className="mt-1 opacity-75">
                    {source.source} (Score: {source.similarity_score?.toFixed(2)})
                  </div>
                ))}
              </div>
            )}
            
            <div className="mt-2 text-xs opacity-50">
              {formatTime(message.timestamp)}
            </div>
          </div>
          
          {isUser && (
            <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0">
              <User className="w-4 h-4 text-white" />
            </div>
          )}
        </div>
      </div>
    </div>
  );
});

MessageBubble.displayName = 'MessageBubble';

// Utility to normalize backend user info keys to frontend keys
function normalizeUserInfo(userInfo) {
  console.log('normalizeUserInfo called with:', userInfo);
  if (!userInfo) return userInfo;
  const prefs = userInfo.preferences || {};
  return {
    ...userInfo,
    name: userInfo.name || userInfo.Name || prefs.name || prefs.Name || '',
    email: userInfo.email || userInfo.Email || prefs.email || prefs.Email || '',
    company: userInfo.company || userInfo['Company name'] || prefs.company || prefs['Company name'] || '',
    role: userInfo.role || userInfo['Job title/role'] || prefs.role || prefs['Job title/role'] || '',
    phone: userInfo.phone || userInfo.Phone || prefs.phone || prefs.Phone || '',
  };
}

const Chat = ({ currentUser, onUserSelect }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  // Memoize the scroll function to prevent unnecessary re-renders
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    // Create a fresh session for new conversations
    const sessionId = sessionManager.createNewSession();
    setSessionId(sessionId);
    
    // Clear any stored user for fresh start
    sessionManager.clearSession();
    
    // Add welcome message
    setMessages([{
      id: 1,
      type: 'bot',
      content: 'Hello! I\'m your AI assistant. I can help you with real estate inquiries, customer management, and general questions. How can I assist you today?',
      timestamp: new Date(),
      metadata: { agent_used: 'System' }
    }]);
  }, []);

  // Only scroll when messages actually change, not on every render
  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date(),
    };

    setMessages(prev => {
      const newMessages = [...prev, userMessage];
      console.log('Added user message:', newMessages);
      return newMessages;
    });
    setInputMessage('');
    setIsLoading(true);
    setError(null);

    try {
      // Use current user ID or create anonymous user
      let userId = currentUser?.id;
      if (!userId) {
        const anonymousUser = sessionManager.createAnonymousUser();
        userId = anonymousUser.id;
        // Store the anonymous user temporarily
        sessionManager.storeUser(anonymousUser);
        if (onUserSelect) {
          onUserSelect(anonymousUser);
        }
      }
      
      const response = await chatAPI.sendMessage(
        inputMessage,
        userId,
        sessionId,
        currentUser ? { user_context: currentUser } : {}
      );

      console.log('Chat API Response:', response);

      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: response.response,
        timestamp: new Date(),
        metadata: response.metadata,
        sources: response.sources,
        processing_time: response.processing_time,
        conversation_id: response.conversation_id
      };

      console.log('Bot Message:', botMessage);

      setMessages(prev => {
        const newMessages = [...prev, botMessage];
        console.log('Updated messages:', newMessages);
        return newMessages;
      });

      // Update current user if user info was extracted
      if (response.metadata?.user_info && onUserSelect) {
        const normalizedUser = normalizeUserInfo(response.metadata.user_info);
        onUserSelect(normalizedUser);
        // Store updated user info in session
        sessionManager.storeUser(normalizedUser);
      }

    } catch (error) {
      console.error('Chat error:', error);
      setError(error.response?.data?.detail || 'Failed to send message');
      
      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = () => {
    setMessages([{
      id: Date.now(),
      type: 'bot',
      content: 'New conversation started. How can I help you?',
      timestamp: new Date(),
      metadata: { agent_used: 'System' }
    }]);
    const newSessionId = sessionManager.createNewSession();
    setSessionId(newSessionId);
    setError(null);
  };

  const handleResetConversation = async () => {
    try {
      if (currentUser) {
        await chatAPI.resetConversation('conversation', currentUser.id);
      }
      setMessages([{
        id: Date.now(),
        type: 'bot',
        content: 'Conversation history has been reset. Starting fresh!',
        timestamp: new Date(),
        metadata: { agent_used: 'System' }
      }]);
      const newSessionId = sessionManager.getSessionId();
      setSessionId(newSessionId);
    } catch (error) {
      console.error('Reset error:', error);
    }
  };

  console.log('Current user info:', currentUser);

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Chat Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Chat Assistant</h2>
            <p className="text-sm text-gray-600">
              AI Assistant - Start chatting and I'll learn about you!
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={handleNewChat}
              className="flex items-center space-x-2 px-3 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>New Chat</span>
            </button>
            <button
              onClick={handleResetConversation}
              className="flex items-center space-x-2 px-3 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Reset</span>
            </button>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        
        {isLoading && (
          <div className="flex justify-start mb-4">
            <div className="bg-white rounded-lg px-4 py-3 shadow-sm border border-gray-200">
              <div className="flex items-center space-x-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="text-sm text-gray-600">AI is thinking...</span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Error Display */}
      {error && (
        <div className="px-4 py-2 bg-red-50 border-t border-red-200">
          <div className="flex items-center space-x-2 text-red-700">
            <AlertCircle className="w-4 h-4" />
            <span className="text-sm">{error}</span>
          </div>
        </div>
      )}

      {/* User Info Display */}
      {currentUser && (currentUser.name || currentUser.company || currentUser.email || currentUser.phone || currentUser.role) && (
        <div className="px-4 py-2 bg-green-50 border-t border-green-200">
          <div className="text-sm text-green-700">
            <strong>User Info:</strong>
            <ul className="list-disc ml-5">
              {currentUser.name && <li>Name: <strong>{currentUser.name}</strong></li>}
              {currentUser.company && <li>Company: <strong>{currentUser.company}</strong></li>}
              {currentUser.email && <li>Email: <strong>{currentUser.email}</strong></li>}
              {currentUser.phone && <li>Phone: <strong>{currentUser.phone}</strong></li>}
              {currentUser.role && <li>Role: <strong>{currentUser.role}</strong></li>}
            </ul>
          </div>
        </div>
      )}

      {/* Input Form */}
      <div className="bg-white border-t border-gray-200 p-4">
        <form onSubmit={handleSendMessage} className="flex space-x-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Type your message..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !inputMessage.trim()}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>
    </div>
  );
};

export default Chat; 