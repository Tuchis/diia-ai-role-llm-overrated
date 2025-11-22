// API utility functions for making authenticated requests

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Makes an authenticated API request
 * @param {string} endpoint - API endpoint (e.g., '/documents/upload-url')
 * @param {object} options - Fetch options (method, body, etc.)
 * @returns {Promise<Response>}
 */
export async function authenticatedFetch(endpoint, options = {}) {
  const credential = localStorage.getItem('google_credential');

    // if (credential) {
    // throw new Error(cre);
    // }

  if (!credential) {
    throw new Error('Not authenticated. Please log in.');
  }

  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${credential}`,
    ...options.headers,
  };

  const response = await fetch(`${API_URL}/api${endpoint}`, {
    ...options,
    headers,
  });

  // Handle 401 Unauthorized - token might be expired
  if (response.status === 401) {
    localStorage.removeItem('google_credential');
    window.location.href = '/';
    throw new Error('Session expired. Please log in again.');
  }

  return response;
}

/**
 * Login with Google credential
 * @param {string} credential - Google ID token
 * @returns {Promise<object>} User data
 */
export async function login(credential) {
  const response = await fetch(`${API_URL}/api/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ token: credential }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Login failed');
  }

  const data = await response.json();
  return data;
}

/**
 * Upload file directly to backend
 * @param {File} file - File to upload
 * @param {string} documentType - Type of document
 * @returns {Promise<object>} Upload result with request_id
 */
export async function uploadFile(file, documentType = 'custom_upload') {
  const credential = localStorage.getItem('google_credential');

  if (!credential) {
    throw new Error('Not authenticated. Please log in.');
  }

  const formData = new FormData();
  formData.append('file', file);
  formData.append('document_type', documentType);

  const response = await fetch(`${API_URL}/api/documents/upload`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${credential}`,
    },
    body: formData,
  });

  // Handle 401 Unauthorized - token might be expired
  if (response.status === 401) {
    localStorage.removeItem('google_credential');
    window.location.href = '/';
    throw new Error('Session expired. Please log in again.');
  }

  if (!response.ok) {
    throw new Error('Failed to upload file');
  }

  return await response.json();
}

/**
 * Start document processing
 * @param {string} requestId - Request ID
 * @returns {Promise<object>} Processing status
 */
export async function startProcessing(requestId) {
  const response = await authenticatedFetch(`/documents/${requestId}/start`, {
    method: 'POST',
  });

  if (!response.ok) {
    throw new Error('Failed to start processing');
  }

  return await response.json();
}

/**
 * Check document processing status
 * @param {string} requestId - Request ID
 * @returns {Promise<object>} Status and download URL (if ready)
 */
export async function checkStatus(requestId) {
  const response = await authenticatedFetch(`/documents/${requestId}`, {
    method: 'GET',
  });

  if (!response.ok) {
    throw new Error('Failed to check status');
  }

  return await response.json();
}

/**
 * Fetch all documents for the current user
 * @returns {Promise<object>} User's documents
 */
export async function fetchDocuments() {
  const response = await authenticatedFetch('/documents', {
    method: 'GET',
  });

  if (!response.ok) {
    throw new Error('Failed to fetch documents');
  }

  return await response.json();
}
