import React, { useState, useEffect } from 'react';
import { 
  Settings as SettingsIcon, 
  Save, 
  RefreshCw, 
  AlertCircle,
  CheckCircle,
  X,
  Info,
  Database,
  MessageSquare,
  Shield,
  Monitor
} from 'lucide-react';
import { systemAPI } from '../services/api';

const Settings = () => {
  const [settings, setSettings] = useState({
    api: {
      timeout: 30000,
      retries: 3,
      base_url: 'http://localhost:8000'
    },
    chat: {
      max_history: 50,
      temperature: 0.7,
      max_tokens: 1000,
      model: 'gpt-4-turbo-preview'
    },
    rag: {
      chunk_size: 1000,
      chunk_overlap: 200,
      max_docs: 5,
      similarity_threshold: 0.7
    },
    ui: {
      theme: 'light',
      animations: true,
      sound_notifications: false,
      auto_refresh: true
    }
  });

  const [systemInfo, setSystemInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [unsavedChanges, setUnsavedChanges] = useState(false);

  useEffect(() => {
    loadSystemInfo();
  }, []);

  const loadSystemInfo = async () => {
    try {
      const response = await systemAPI.getApiInfo();
      setSystemInfo(response.data);
    } catch (error) {
      console.error('Error loading system info:', error);
    }
  };

  const handleSettingChange = (category, key, value) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value
      }
    }));
    setUnsavedChanges(true);
  };

  const handleSave = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // Simulate API call to save settings
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setSuccess('Settings saved successfully');
      setUnsavedChanges(false);
      
      // Apply UI settings immediately
      if (settings.ui.theme === 'dark') {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }

    } catch (error) {
      setError('Failed to save settings');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setSettings({
      api: {
        timeout: 30000,
        retries: 3,
        base_url: 'http://localhost:8000'
      },
      chat: {
        max_history: 50,
        temperature: 0.7,
        max_tokens: 1000,
        model: 'gpt-4-turbo-preview'
      },
      rag: {
        chunk_size: 1000,
        chunk_overlap: 200,
        max_docs: 5,
        similarity_threshold: 0.7
      },
      ui: {
        theme: 'light',
        animations: true,
        sound_notifications: false,
        auto_refresh: true
      }
    });
    setUnsavedChanges(true);
  };

  const SettingsSection = ({ title, icon: Icon, children }) => (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          <Icon className="w-5 h-5 text-gray-500" />
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        </div>
      </div>
      <div className="p-6">
        {children}
      </div>
    </div>
  );

  const SettingField = ({ label, description, type = 'text', value, onChange, options = [] }) => (
    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
      </label>
      {description && (
        <p className="text-xs text-gray-500 mb-2">{description}</p>
      )}
      
      {type === 'select' ? (
        <select
          value={value}
          onChange={onChange}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      ) : type === 'checkbox' ? (
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={value}
            onChange={onChange}
            className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <span className="text-sm text-gray-700">Enable</span>
        </label>
      ) : type === 'range' ? (
        <div>
          <input
            type="range"
            value={value}
            onChange={onChange}
            min="0"
            max="1"
            step="0.1"
            className="w-full"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>0</span>
            <span className="font-medium">{value}</span>
            <span>1</span>
          </div>
        </div>
      ) : (
        <input
          type={type}
          value={value}
          onChange={onChange}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      )}
    </div>
  );

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Settings</h2>
            <p className="text-sm text-gray-600">
              Configure system preferences and behavior
            </p>
          </div>
          <div className="flex items-center space-x-3">
            {unsavedChanges && (
              <span className="text-sm text-orange-600 bg-orange-50 px-2 py-1 rounded">
                Unsaved changes
              </span>
            )}
            <button
              onClick={handleReset}
              className="flex items-center space-x-2 bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Reset</span>
            </button>
            <button
              onClick={handleSave}
              disabled={loading || !unsavedChanges}
              className="flex items-center space-x-2 bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Save className="w-4 h-4" />
              <span>{loading ? 'Saving...' : 'Save'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6">
        <div className="space-y-6">
          {/* Alert Messages */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center">
                <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
                <span className="text-red-700">{error}</span>
                <button
                  onClick={() => setError(null)}
                  className="ml-auto text-red-500 hover:text-red-700"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {success && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center">
                <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
                <span className="text-green-700">{success}</span>
                <button
                  onClick={() => setSuccess(null)}
                  className="ml-auto text-green-500 hover:text-green-700"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* System Information */}
          {systemInfo && (
            <SettingsSection title="System Information" icon={Info}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Application</h4>
                  <dl className="text-sm space-y-1">
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Version:</dt>
                      <dd className="text-gray-900">{systemInfo.version}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Description:</dt>
                      <dd className="text-gray-900">{systemInfo.description}</dd>
                    </div>
                  </dl>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Endpoints</h4>
                  <div className="text-sm space-y-1">
                    {Object.entries(systemInfo.endpoints || {}).map(([key, value]) => (
                      <div key={key} className="flex justify-between">
                        <span className="text-gray-600">{key}:</span>
                        <span className="text-gray-900 font-mono text-xs">{value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </SettingsSection>
          )}

          {/* API Settings */}
          <SettingsSection title="API Configuration" icon={Database}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <SettingField
                label="Base URL"
                description="API server base URL"
                value={settings.api.base_url}
                onChange={(e) => handleSettingChange('api', 'base_url', e.target.value)}
              />
              <SettingField
                label="Timeout (ms)"
                description="Request timeout in milliseconds"
                type="number"
                value={settings.api.timeout}
                onChange={(e) => handleSettingChange('api', 'timeout', parseInt(e.target.value))}
              />
              <SettingField
                label="Retries"
                description="Number of retry attempts"
                type="number"
                value={settings.api.retries}
                onChange={(e) => handleSettingChange('api', 'retries', parseInt(e.target.value))}
              />
            </div>
          </SettingsSection>

          {/* Chat Settings */}
          <SettingsSection title="Chat Configuration" icon={MessageSquare}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <SettingField
                label="AI Model"
                description="OpenAI model to use"
                type="select"
                value={settings.chat.model}
                onChange={(e) => handleSettingChange('chat', 'model', e.target.value)}
                options={[
                  { value: 'gpt-4-turbo-preview', label: 'GPT-4 Turbo' },
                  { value: 'gpt-4', label: 'GPT-4' },
                  { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' }
                ]}
              />
              <SettingField
                label="Max History"
                description="Maximum conversation history length"
                type="number"
                value={settings.chat.max_history}
                onChange={(e) => handleSettingChange('chat', 'max_history', parseInt(e.target.value))}
              />
              <SettingField
                label="Temperature"
                description="AI response creativity (0-1)"
                type="range"
                value={settings.chat.temperature}
                onChange={(e) => handleSettingChange('chat', 'temperature', parseFloat(e.target.value))}
              />
              <SettingField
                label="Max Tokens"
                description="Maximum tokens per response"
                type="number"
                value={settings.chat.max_tokens}
                onChange={(e) => handleSettingChange('chat', 'max_tokens', parseInt(e.target.value))}
              />
            </div>
          </SettingsSection>

          {/* RAG Settings */}
          <SettingsSection title="RAG Configuration" icon={Database}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <SettingField
                label="Chunk Size"
                description="Document chunk size for processing"
                type="number"
                value={settings.rag.chunk_size}
                onChange={(e) => handleSettingChange('rag', 'chunk_size', parseInt(e.target.value))}
              />
              <SettingField
                label="Chunk Overlap"
                description="Overlap between chunks"
                type="number"
                value={settings.rag.chunk_overlap}
                onChange={(e) => handleSettingChange('rag', 'chunk_overlap', parseInt(e.target.value))}
              />
              <SettingField
                label="Max Documents"
                description="Maximum documents to retrieve"
                type="number"
                value={settings.rag.max_docs}
                onChange={(e) => handleSettingChange('rag', 'max_docs', parseInt(e.target.value))}
              />
              <SettingField
                label="Similarity Threshold"
                description="Minimum similarity score (0-1)"
                type="range"
                value={settings.rag.similarity_threshold}
                onChange={(e) => handleSettingChange('rag', 'similarity_threshold', parseFloat(e.target.value))}
              />
            </div>
          </SettingsSection>

          {/* UI Settings */}
          <SettingsSection title="User Interface" icon={Monitor}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <SettingField
                label="Theme"
                description="Application theme"
                type="select"
                value={settings.ui.theme}
                onChange={(e) => handleSettingChange('ui', 'theme', e.target.value)}
                options={[
                  { value: 'light', label: 'Light' },
                  { value: 'dark', label: 'Dark' },
                  { value: 'auto', label: 'Auto' }
                ]}
              />
              <SettingField
                label="Animations"
                description="Enable UI animations"
                type="checkbox"
                value={settings.ui.animations}
                onChange={(e) => handleSettingChange('ui', 'animations', e.target.checked)}
              />
              <SettingField
                label="Sound Notifications"
                description="Enable sound notifications"
                type="checkbox"
                value={settings.ui.sound_notifications}
                onChange={(e) => handleSettingChange('ui', 'sound_notifications', e.target.checked)}
              />
              <SettingField
                label="Auto Refresh"
                description="Automatically refresh data"
                type="checkbox"
                value={settings.ui.auto_refresh}
                onChange={(e) => handleSettingChange('ui', 'auto_refresh', e.target.checked)}
              />
            </div>
          </SettingsSection>
        </div>
      </div>
    </div>
  );
};

export default Settings; 