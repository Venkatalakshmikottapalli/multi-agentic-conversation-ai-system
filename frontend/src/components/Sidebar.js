import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  MessageSquare, 
  Users, 
  BarChart3, 
  FileText, 
  Settings, 
  X,
  Search
} from 'lucide-react';
import { crmAPI } from '../services/api';

const Sidebar = ({ isOpen, onClose, currentUser, onUserSelect }) => {
  const location = useLocation();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showUserSearch, setShowUserSearch] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    if (isOpen) {
      loadUsers();
    }
  }, [isOpen]);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const response = await crmAPI.getUsers(1, 20);
      setUsers(response.data || []);
    } catch (error) {
      console.error('Error loading users:', error);
    } finally {
      setLoading(false);
    }
  };

  const menuItems = [
    { name: 'Chat', icon: MessageSquare, path: '/chat' },
    { name: 'Users', icon: Users, path: '/users' },
    { name: 'Analytics', icon: BarChart3, path: '/analytics' },
    { name: 'Documents', icon: FileText, path: '/documents' },
    { name: 'Settings', icon: Settings, path: '/settings' },
  ];

  const filteredUsers = users.filter(user =>
    user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleUserSelect = (user) => {
    onUserSelect(user);
    onClose();
  };

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
              className="lg:hidden p-2 rounded-md hover:bg-gray-100"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Menu Items */}
          <nav className="flex-1 px-4 py-4 space-y-2">
            {menuItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              
              return (
                <Link
                  key={item.name}
                  to={item.path}
                  onClick={onClose}
                  className={`
                    flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors
                    ${isActive 
                      ? 'bg-blue-100 text-blue-700' 
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    }
                  `}
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>

          {/* Quick User Access */}
          <div className="border-t border-gray-200 p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-gray-900">Quick Access</h3>
              <button
                onClick={() => setShowUserSearch(!showUserSearch)}
                className="p-1 rounded-md hover:bg-gray-100"
              >
                <Search className="w-4 h-4" />
              </button>
            </div>

            {showUserSearch && (
              <div className="mb-3">
                <input
                  type="text"
                  placeholder="Search users..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            )}

            <div className="space-y-2 max-h-40 overflow-y-auto">
              {loading ? (
                <div className="text-center py-2 text-sm text-gray-500">
                  Loading users...
                </div>
              ) : filteredUsers.length > 0 ? (
                filteredUsers.slice(0, 5).map((user) => (
                  <button
                    key={user.id}
                    onClick={() => handleUserSelect(user)}
                    className={`
                      w-full text-left px-3 py-2 rounded-md text-sm transition-colors
                      ${currentUser?.id === user.id 
                        ? 'bg-blue-50 text-blue-700 border border-blue-200' 
                        : 'hover:bg-gray-50 text-gray-700'
                      }
                    `}
                  >
                    <div className="font-medium">{user.name}</div>
                    <div className="text-xs text-gray-500">{user.email}</div>
                  </button>
                ))
              ) : (
                <div className="text-center py-2 text-sm text-gray-500">
                  No users found
                </div>
              )}
            </div>

            {/* Current User Display */}
            {currentUser && (
              <div className="mt-3 p-3 bg-blue-50 rounded-md">
                <div className="text-sm font-medium text-blue-900">
                  Active User
                </div>
                <div className="text-xs text-blue-700 mt-1">
                  {currentUser.name}
                </div>
                <div className="text-xs text-blue-600">
                  {currentUser.email}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
};

export default Sidebar; 