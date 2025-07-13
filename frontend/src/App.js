import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Chat from './components/Chat';
import Documents from './components/Documents';
import { systemAPI } from './services/api';
import sessionManager from './services/sessionManager';
import chatHistoryService from './services/chatHistoryService';
import { AlertCircle, CheckCircle, Clock } from 'lucide-react';

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [currentSession, setCurrentSession] = useState(null);
  const [systemHealth, setSystemHealth] = useState(null);
  const [healthLoading, setHealthLoading] = useState(true);
  const [refreshSidebar, setRefreshSidebar] = useState(0);

  useEffect(() => {
    initializeApp();
    checkSystemHealth();
    const interval = setInterval(checkSystemHealth, 60000); // Check every minute
    return () => clearInterval(interval);
  }, []);

  const initializeApp = () => {
    // Initialize session and user
    const { session, user } = sessionManager.initializeSession();
    setCurrentSession(session);
    setCurrentUser(user);
  };

  const checkSystemHealth = async () => {
    try {
      setHealthLoading(true);
      const health = await systemAPI.getHealth();
      setSystemHealth(health);
    } catch (error) {
      console.error('Health check failed:', error);
      setSystemHealth({ status: 'unhealthy', error: error.message });
    } finally {
      setHealthLoading(false);
    }
  };

  const getHealthIcon = (status) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'unhealthy':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4 text-yellow-500" />;
    }
  };

  const handleUserSelect = (user) => {
    setCurrentUser(user);
  };

  const handleSessionChange = (session) => {
    setCurrentSession(session);
    
    // Update the current session in the history service
    if (session && session.id) {
      chatHistoryService.setCurrentSessionId(session.id);
    }
    
    // Trigger sidebar refresh when sessions are changed
    setRefreshSidebar(prev => prev + 1);
  };

  const handleSessionUpdate = (updatedSession) => {
    setCurrentSession(updatedSession);
    // Trigger sidebar refresh when sessions are updated
    setRefreshSidebar(prev => prev + 1);
  };

  return (
    <Router>
      <div className="flex h-screen bg-gray-100">
        <Sidebar 
          isOpen={sidebarOpen} 
          onClose={() => setSidebarOpen(false)}
          currentUser={currentUser}
          onUserSelect={handleUserSelect}
          onSessionChange={handleSessionChange}
          refreshTrigger={refreshSidebar}
        />
        
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Header */}
          <header className="bg-white shadow-sm border-b border-gray-200">
            <div className="flex items-center justify-between px-4 py-3">
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => setSidebarOpen(true)}
                  className="lg:hidden p-2 rounded-md hover:bg-gray-100"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                  </svg>
                </button>
                <h1 className="text-xl font-semibold text-gray-900">
                  CRM Chatbot System
                </h1>
              </div>
              
              <div className="flex items-center space-x-4">
                {/* System Health Indicator */}
                <div className="flex items-center space-x-2">
                  {healthLoading ? (
                    <div className="animate-pulse">
                      <Clock className="w-4 h-4 text-gray-400" />
                    </div>
                  ) : (
                    <>
                      {getHealthIcon(systemHealth?.status)}
                      <span className="text-sm text-gray-600">
                        {systemHealth?.status || 'unknown'}
                      </span>
                    </>
                  )}
                </div>
                
                {/* Current User */}
                {currentUser && (
                  <div className="flex items-center space-x-2 bg-blue-50 px-3 py-1 rounded-full">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <span className="text-sm text-blue-700">
                      {currentUser.name || `User ${currentUser.id?.slice(-4)}`}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </header>

          {/* Main Content */}
          <main className="flex-1 overflow-hidden">
            <Routes>
              <Route path="/" element={<Navigate to="/chat" replace />} />
              <Route 
                path="/chat" 
                element={
                  <Chat 
                    currentUser={currentUser} 
                    onUserSelect={handleUserSelect}
                    currentSession={currentSession}
                    onSessionUpdate={handleSessionUpdate}
                  />
                } 
              />
              <Route path="/documents" element={<Documents />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}

export default App; 