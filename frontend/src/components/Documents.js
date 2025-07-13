import React, { useState, useEffect } from 'react';
import { 
  Upload, 
  FileText, 
  Trash2, 
  RefreshCw,
  AlertCircle,
  CheckCircle,
  X,
  Database,
  Info
} from 'lucide-react';
import { docAPI } from '../services/api';

const Documents = () => {
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [ragStats, setRagStats] = useState(null);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const [showDocumentsModal, setShowDocumentsModal] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [documentsLoading, setDocumentsLoading] = useState(false);
  const [deletingDocument, setDeletingDocument] = useState(null);

  useEffect(() => {
    loadRagStats();
  }, []);

  const loadRagStats = async () => {
    try {
      const response = await docAPI.getRagStats();
      setRagStats(response.data);
    } catch (error) {
      console.error('Error loading RAG stats:', error);
      setError('Failed to load document statistics');
    }
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    setSelectedFiles(files);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const files = Array.from(e.dataTransfer.files);
    setSelectedFiles(files);
  };

  const handleUpload = async () => {
    if (!selectedFiles.length) return;

    try {
      setUploading(true);
      setError(null);
      setSuccess(null);
      
      const response = await docAPI.uploadDocuments(selectedFiles);
      
      // Use the message from the backend response (distinguishes uploads vs replacements)
      setSuccess(response.message || `Successfully uploaded ${selectedFiles.length} file(s)`);
      setSelectedFiles([]);
      loadRagStats();
      
      // Reset file input
      const fileInput = document.getElementById('file-input');
      if (fileInput) fileInput.value = '';
      
    } catch (error) {
      console.error('Error uploading documents:', error);
      setError(error.response?.data?.detail || 'Failed to upload documents');
    } finally {
      setUploading(false);
    }
  };

  const handleClearData = async () => {
    try {
      await docAPI.clearRagData();
      setSuccess('Document collection cleared successfully');
      setShowClearConfirm(false);
      loadRagStats();
    } catch (error) {
      console.error('Error clearing RAG data:', error);
      setError('Failed to clear document collection');
    }
  };

  const removeSelectedFile = (index) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const loadDocuments = async () => {
    try {
      setDocumentsLoading(true);
      const response = await docAPI.getDocuments(1, 100); // Load first 100 documents
      console.log('Documents API response:', response); // Debug log
      // The backend returns { success: true, data: [documents], ... }
      // So we need to access response.data to get the documents array
      setDocuments(response.data || []);
    } catch (error) {
      console.error('Error loading documents:', error);
      setError('Failed to load documents');
    } finally {
      setDocumentsLoading(false);
    }
  };

  const handleDeleteDocument = async (filename) => {
    if (!window.confirm(`Are you sure you want to delete "${filename}"?`)) return;
    
    try {
      setDeletingDocument(filename);
      await docAPI.deleteDocument(filename);
      setSuccess(`Document "${filename}" deleted successfully`);
      loadDocuments(); // Reload documents list
      loadRagStats(); // Refresh stats
    } catch (error) {
      console.error('Error deleting document:', error);
      setError(error.response?.data?.detail || 'Failed to delete document');
    } finally {
      setDeletingDocument(null);
    }
  };

  const handleShowDocuments = () => {
    setShowDocumentsModal(true);
    loadDocuments();
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getSupportedFormats = () => {
    return [
      { ext: '.csv', description: 'CSV files for structured data' },
      { ext: '.txt', description: 'Plain text files' },
      { ext: '.json', description: 'JSON data files' },
      { ext: '.pdf', description: 'PDF documents' }
    ];
  };

  const StatCard = ({ title, value, icon: Icon, color, onClick, clickable = false }) => (
    <div 
      className={`bg-white rounded-lg shadow-sm p-6 border border-gray-200 ${
        clickable ? 'cursor-pointer hover:shadow-md transition-shadow' : ''
      }`}
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-semibold text-gray-900">{value}</p>
        </div>
        <div className={`p-3 rounded-full ${color}`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
      {clickable && (
        <div className="mt-2">
          <p className="text-xs text-blue-600">Click to view all documents</p>
        </div>
      )}
    </div>
  );

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Document Management</h2>
            <p className="text-sm text-gray-600">
              Upload and manage documents for the AI knowledge base
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={loadRagStats}
              className="flex items-center space-x-2 bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Refresh</span>
            </button>
            <button
              onClick={() => setShowClearConfirm(true)}
              className="flex items-center space-x-2 bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 transition-colors"
            >
              <Trash2 className="w-4 h-4" />
              <span>Clear All</span>
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

          {/* Stats Cards */}
          {ragStats && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <StatCard
                title="Total Documents"
                value={ragStats.total_documents || 0}
                icon={FileText}
                color="bg-blue-500"
                clickable={true}
                onClick={handleShowDocuments}
              />
              <StatCard
                title="Document Chunks"
                value={ragStats.total_chunks || 0}
                icon={Database}
                color="bg-green-500"
              />
              <StatCard
                title="Collection Size"
                value={formatFileSize(ragStats.collection_size || 0)}
                icon={Info}
                color="bg-purple-500"
              />
              <StatCard
                title="Last Updated"
                value={ragStats.last_updated ? new Date(ragStats.last_updated).toLocaleDateString() : 'Never'}
                icon={RefreshCw}
                color="bg-orange-500"
              />
            </div>
          )}

          {/* File Upload Section */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Upload Documents</h3>
              <p className="text-sm text-gray-600 mt-1">
                Add documents to enhance the AI's knowledge base
              </p>
            </div>

            <div className="p-6">
              {/* Drop Zone */}
              <div
                className={`
                  border-2 border-dashed rounded-lg p-8 text-center transition-colors
                  ${dragOver 
                    ? 'border-blue-500 bg-blue-50' 
                    : 'border-gray-300 bg-gray-50'
                  }
                `}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
              >
                <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-lg font-medium text-gray-900 mb-2">
                  Drop files here or click to browse
                </p>
                <p className="text-sm text-gray-600 mb-4">
                  Support for multiple file formats including CSV, TXT, JSON, and PDF
                </p>
                <input
                  id="file-input"
                  type="file"
                  multiple
                  onChange={handleFileSelect}
                  className="hidden"
                  accept=".csv,.txt,.json,.pdf"
                />
                <button
                  onClick={() => document.getElementById('file-input').click()}
                  className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition-colors"
                >
                  Choose Files
                </button>
              </div>

              {/* Selected Files */}
              {selectedFiles.length > 0 && (
                <div className="mt-6">
                  <h4 className="text-sm font-medium text-gray-900 mb-3">
                    Selected Files ({selectedFiles.length})
                  </h4>
                  <div className="space-y-2">
                    {selectedFiles.map((file, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                      >
                        <div className="flex items-center space-x-3">
                          <FileText className="w-5 h-5 text-gray-500" />
                          <div>
                            <p className="text-sm font-medium text-gray-900">{file.name}</p>
                            <p className="text-xs text-gray-500">
                              {formatFileSize(file.size)} | {file.type || 'Unknown type'}
                            </p>
                          </div>
                        </div>
                        <button
                          onClick={() => removeSelectedFile(index)}
                          className="text-red-500 hover:text-red-700"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>

                  <div className="mt-4 flex items-center justify-between">
                    <p className="text-sm text-gray-600">
                      {selectedFiles.length} file(s) selected
                    </p>
                    <div className="flex space-x-3">
                      <button
                        onClick={() => setSelectedFiles([])}
                        className="px-4 py-2 text-gray-600 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors"
                      >
                        Clear All
                      </button>
                      <button
                        onClick={handleUpload}
                        disabled={uploading}
                        className="px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        {uploading ? 'Uploading...' : 'Upload Files'}
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Supported Formats */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Supported File Formats</h3>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {getSupportedFormats().map((format, index) => (
                  <div key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                    <FileText className="w-5 h-5 text-gray-500" />
                    <div>
                      <p className="text-sm font-medium text-gray-900">{format.ext}</p>
                      <p className="text-xs text-gray-600">{format.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* RAG System Info */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Knowledge Base Information</h3>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-3">System Status</h4>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Vector Store</span>
                      <span className="text-sm font-medium text-green-600">Active</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Indexing</span>
                      <span className="text-sm font-medium text-blue-600">Ready</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Search</span>
                      <span className="text-sm font-medium text-green-600">Enabled</span>
                    </div>
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-3">Usage Tips</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>- Upload CSV files for structured data</li>
                    <li>- Use descriptive file names</li>
                    <li>- Larger files take longer to process</li>
                    <li>- Remove outdated documents regularly</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Documents Modal */}
      {showDocumentsModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg w-full max-w-4xl mx-4 max-h-[80vh] flex flex-col">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">All Documents</h3>
              <button
                onClick={() => setShowDocumentsModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            {/* Modal Content */}
            <div className="flex-1 overflow-auto p-6">
              {documentsLoading ? (
                <div className="flex items-center justify-center py-8">
                  <RefreshCw className="w-6 h-6 animate-spin text-blue-500" />
                  <span className="ml-2 text-gray-600">Loading documents...</span>
                </div>
              ) : documents.length === 0 ? (
                <div className="text-center py-8">
                  <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">No documents found</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {documents.map((doc) => (
                    <div
                      key={doc.id}
                      className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border"
                    >
                      <div className="flex items-center space-x-3 flex-1">
                        <FileText className="w-5 h-5 text-gray-500" />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {doc.filename}
                          </p>
                          <div className="flex items-center space-x-4 text-xs text-gray-500">
                            <span>{doc.content_type}</span>
                            {doc.file_size && (
                              <span>{formatFileSize(doc.file_size)}</span>
                            )}
                            <span>
                              {new Date(doc.created_at).toLocaleDateString()}
                            </span>
                          </div>
                        </div>
                      </div>
                      <button
                        onClick={() => handleDeleteDocument(doc.filename)}
                        disabled={deletingDocument === doc.filename}
                        className="flex items-center space-x-1 px-3 py-1 text-red-600 hover:text-red-800 hover:bg-red-50 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {deletingDocument === doc.filename ? (
                          <RefreshCw className="w-4 h-4 animate-spin" />
                        ) : (
                          <Trash2 className="w-4 h-4" />
                        )}
                        <span className="text-sm">Delete</span>
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
            
            {/* Modal Footer */}
            <div className="p-6 border-t border-gray-200">
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-600">
                  Total: {documents.length} document{documents.length !== 1 ? 's' : ''}
                </p>
                <button
                  onClick={() => setShowDocumentsModal(false)}
                  className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Clear Confirmation Modal */}
      {showClearConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-red-600">Clear All Documents</h3>
              <button
                onClick={() => setShowClearConfirm(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="mb-6">
              <p className="text-sm text-gray-600">
                Are you sure you want to clear all documents from the knowledge base? 
                This action cannot be undone and will remove all uploaded documents and their embeddings.
              </p>
            </div>

            <div className="flex space-x-3">
              <button
                onClick={handleClearData}
                className="flex-1 bg-red-500 text-white py-2 px-4 rounded-lg hover:bg-red-600 transition-colors"
              >
                Yes, Clear All
              </button>
              <button
                onClick={() => setShowClearConfirm(false)}
                className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-400 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Documents; 