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
  console.log(credential)

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

  const response = await fetch(`${API_URL}${endpoint}`, {
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
  const response = await fetch(`${API_URL}/auth/login`, {
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
 * Get presigned URL for file upload
 * @param {object} fileInfo - File information
 * @returns {Promise<object>} Upload URL and metadata
 */
export async function getUploadUrl(fileInfo) {
  const response = await authenticatedFetch('/documents/upload-url', {
    method: 'POST',
    body: JSON.stringify(fileInfo),
  });

  if (!response.ok) {
    throw new Error('Failed to get upload URL');
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
 * Upload file to S3 using presigned URL
 * @param {string} uploadUrl - Presigned S3 URL
 * @param {File} file - File to upload
 * @param {string} contentType - File content type
 * @returns {Promise<void>}
 */
export async function uploadFileToS3(uploadUrl, file, contentType) {
  const response = await fetch(uploadUrl, {
    method: 'PUT',
    headers: {
      'Content-Type': contentType,
    },
    body: file,
  });

  if (!response.ok) {
    throw new Error('Failed to upload file to S3');
  }
}
