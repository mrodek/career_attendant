// Background service worker for authentication and API communication

const CONFIG = {
  // Set to true to force production API
  USE_PRODUCTION: true,
  API_URLS: [
    'http://localhost:8080',
    'https://careerattendant-production.up.railway.app'
  ],
};

// Use production or try auto-detect
let API_BASE_URL = CONFIG.USE_PRODUCTION 
  ? CONFIG.API_URLS[1]  // Production
  : CONFIG.API_URLS[0]; // Local
let CLERK_FRONTEND_API = null; // Will be fetched from API

// Auto-detect which API URL is available and get Clerk config
async function detectApiUrl() {
  // If USE_PRODUCTION is true, skip auto-detection and use production
  if (CONFIG.USE_PRODUCTION) {
    const url = CONFIG.API_URLS[1]; // Production URL
    try {
      const response = await fetch(`${url}/health`, { method: 'GET' });
      if (response.ok) {
        const data = await response.json();
        API_BASE_URL = url;
        CLERK_FRONTEND_API = data.clerk_frontend_api;
        console.log('API detected at:', API_BASE_URL);
        console.log('Clerk Frontend API:', CLERK_FRONTEND_API);
        return;
      }
    } catch (error) {
      console.error('Production API not available:', error);
    }
  }
  
  // Auto-detect from all URLs
  for (const url of CONFIG.API_URLS) {
    try {
      const response = await fetch(`${url}/health`, { method: 'GET' });
      if (response.ok) {
        const data = await response.json();
        API_BASE_URL = url;
        CLERK_FRONTEND_API = data.clerk_frontend_api;
        console.log('API detected at:', API_BASE_URL);
        console.log('Clerk Frontend API:', CLERK_FRONTEND_API);
        return;
      }
    } catch (error) {
      console.log(`API not available at ${url}`);
    }
  }
  console.warn('No API available, using default:', API_BASE_URL);
}

// Store authentication state
// Note: We store a long-lived session token (7 days) from our API
let authState = {
  sessionToken: null,  // Server-side session token (valid for 7 days)
  userId: null,
  userEmail: null,
  isAuthenticated: false
};

// Job cache to avoid redundant API calls and extraction
// Maps normalized URL -> { exists, job_id, job_data, has_extraction, has_summary, timestamp }
const jobCache = new Map();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

// Normalize URL for consistent cache keys
function normalizeUrl(url) {
  if (!url) return '';
  // Remove trailing slash, query params, fragments
  return url.split('?')[0].split('#')[0].replace(/\/$/, '').toLowerCase();
}

// Get cached job check result
function getCachedJobCheck(url) {
  const normalized = normalizeUrl(url);
  const cached = jobCache.get(normalized);
  
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    console.log('✓ Cache hit for:', url);
    return cached;
  }
  
  if (cached) {
    console.log('✗ Cache expired for:', url);
    jobCache.delete(normalized);
  } else {
    console.log('✗ Cache miss for:', url);
  }
  
  return null;
}

// Set cached job check result
function setCachedJobCheck(url, data) {
  const normalized = normalizeUrl(url);
  jobCache.set(normalized, {
    ...data,
    timestamp: Date.now()
  });
  console.log('✓ Cached job data for:', url);
}

// Invalidate cache for a specific URL
function invalidateJobCache(url) {
  const normalized = normalizeUrl(url);
  const deleted = jobCache.delete(normalized);
  if (deleted) {
    console.log('✓ Cache invalidated for:', url);
  }
  return deleted;
}

// Clear all cache (useful for debugging or logout)
function clearJobCache() {
  const size = jobCache.size;
  jobCache.clear();
  console.log(`✓ Cleared ${size} cached jobs`);
}

// Initialize authentication state on startup
chrome.runtime.onStartup.addListener(async () => {
  await detectApiUrl();
  await loadAuthState();
});

chrome.runtime.onInstalled.addListener(async () => {
  await detectApiUrl();
  await loadAuthState();
});

// Load authentication state from storage
async function loadAuthState() {
  return new Promise((resolve) => {
    chrome.storage.local.get(['sessionToken', 'userId', 'userEmail'], (result) => {
      if (result.sessionToken && result.userId) {
        authState.sessionToken = result.sessionToken;
        authState.userId = result.userId;
        authState.userEmail = result.userEmail;
        authState.isAuthenticated = true;
        console.log('Auth state loaded:', { userId: authState.userId });
      }
      resolve();
    });
  });
}

// Save authentication state to storage
async function saveAuthState(sessionToken, userId, email) {
  authState.sessionToken = sessionToken;
  authState.userId = userId;
  authState.userEmail = email;
  authState.isAuthenticated = true;
  
  return new Promise((resolve) => {
    chrome.storage.local.set({ sessionToken, userId, userEmail: email }, () => {
      console.log('Auth state saved');
      resolve();
    });
  });
}

// Clear authentication state
async function clearAuthState() {
  authState.sessionToken = null;
  authState.userId = null;
  authState.userEmail = null;
  authState.isAuthenticated = false;
  
  return new Promise((resolve) => {
    chrome.storage.local.remove(['sessionToken', 'userId', 'userEmail'], () => {
      console.log('Auth state cleared');
      resolve();
    });
  });
}

// Handle messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'GET_AUTH_STATE') {
    // Always reload from storage in case service worker was restarted
    loadAuthState().then(() => {
      sendResponse(authState);
    });
    return true;
  }
  
  if (request.type === 'AUTHENTICATE') {
    // Ensure API URL is detected before authenticating
    detectApiUrl().then(() => {
      return authenticateUser();
    }).then(sendResponse).catch((error) => {
      sendResponse({ success: false, error: error.message });
    });
    return true;
  }
  
  if (request.type === 'AUTH_SUCCESS') {
    // Handle successful authentication from callback page
    saveAuthState(request.token, request.userId, request.email).then(() => {
      sendResponse({ success: true });
    }).catch((error) => {
      sendResponse({ success: false, error: error.message });
    });
    return true;
  }
  
  if (request.type === 'LOGOUT') {
    clearAuthState().then(() => {
      clearJobCache(); // Clear cache on logout
      sendResponse({ success: true });
    });
    return true;
  }
  
  // Cache operations
  if (request.type === 'CHECK_JOB_CACHED') {
    const cached = getCachedJobCheck(request.url);
    sendResponse(cached);
    return true;
  }
  
  if (request.type === 'SET_JOB_CACHE') {
    setCachedJobCheck(request.url, request.data);
    sendResponse({ success: true });
    return true;
  }
  
  if (request.type === 'INVALIDATE_JOB_CACHE') {
    const deleted = invalidateJobCache(request.url);
    sendResponse({ success: true, deleted });
    return true;
  }
  
  if (request.type === 'CLEAR_JOB_CACHE') {
    clearJobCache();
    sendResponse({ success: true });
    return true;
  }
  
  if (request.type === 'SAVE_JOB') {
    // Reload auth state first in case service worker was restarted
    loadAuthState().then(() => {
      console.log('SAVE_JOB - Auth state after reload:', {
        isAuthenticated: authState.isAuthenticated,
        hasToken: !!authState.sessionToken,
        userId: authState.userId
      });
      return saveJob(request.jobData);
    }).then(sendResponse).catch((error) => {
      console.error('SAVE_JOB error:', error);
      sendResponse({ success: false, error: error.message });
    });
    return true;
  }
  
  if (request.type === 'GET_USER_INFO') {
    // Reload auth state first in case service worker was restarted
    loadAuthState().then(() => {
      return getUserInfo();
    }).then(sendResponse).catch((error) => {
      sendResponse({ success: false, error: error.message });
    });
    return true;
  }
});

// Authenticate user via Clerk
async function authenticateUser() {
  try {
    // Open the API's auth page (which can load Clerk JS)
    const authUrl = `${API_BASE_URL}/auth/login`;
    const authTab = await chrome.tabs.create({ url: authUrl });
    
    // Watch for the callback URL which contains the token
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        chrome.tabs.onUpdated.removeListener(listener);
        reject(new Error('Authentication timeout'));
      }, 300000); // 5 minute timeout
      
      const listener = async (tabId, changeInfo, tab) => {
        // Only check our auth tab
        if (tabId !== authTab.id) return;
        
        // Check if URL contains our callback
        if (changeInfo.url && changeInfo.url.includes('/auth/callback?')) {
          clearTimeout(timeout);
          chrome.tabs.onUpdated.removeListener(listener);
          
          try {
            // Extract token from URL
            const url = new URL(changeInfo.url);
            const token = url.searchParams.get('token');
            const userId = url.searchParams.get('userId');
            const email = url.searchParams.get('email');
            
            console.log('Auth callback received:', { userId, email, hasToken: !!token });
            
            if (token && userId) {
              // Save auth state
              await saveAuthState(token, userId);
              
              // Close the auth tab after a short delay
              setTimeout(() => {
                chrome.tabs.remove(tabId).catch(() => {});
              }, 1500);
              
              resolve({ success: true, userId, email });
            } else {
              reject(new Error('No token received'));
            }
          } catch (err) {
            reject(err);
          }
        }
      };
      
      chrome.tabs.onUpdated.addListener(listener);
    });
  } catch (error) {
    console.error('Authentication failed:', error);
    throw error;
  }
}

// Get user information from API
async function getUserInfo() {
  if (!authState.isAuthenticated || !authState.sessionToken) {
    throw new Error('Not authenticated');
  }
  
  const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${authState.sessionToken}`,
      'Content-Type': 'application/json'
    }
  });
  
  if (!response.ok) {
    if (response.status === 401) {
      // Session expired (after 7 days) - clear auth state
      await clearAuthState();
      throw new Error('Your session has expired. Please sign in again.');
    }
    throw new Error(`Failed to get user info: ${response.status}`);
  }
  
  const data = await response.json();
  return { success: true, user: data };
}

// Save job to API
async function saveJob(jobData) {
  if (!authState.isAuthenticated || !authState.sessionToken) {
    throw new Error('Not authenticated');
  }
  
  try {
    // Use PUT for updates, POST for new jobs
    const isUpdate = !!jobData.existingJobId;
    const url = isUpdate 
      ? `${API_BASE_URL}/entries/${jobData.existingJobId}`
      : `${API_BASE_URL}/entries`;
    const method = isUpdate ? 'PUT' : 'POST';
    
    const response = await fetch(url, {
      method: method,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authState.sessionToken}`
      },
      body: JSON.stringify(jobData)
    });
    
    if (!response.ok) {
      if (response.status === 401) {
        // Session expired (after 7 days) - user needs to sign in again
        await clearAuthState();
        throw new Error('Your session has expired. Please sign in again.');
      }
      
      const errorText = await response.text();
      throw new Error(`API error: ${response.status} - ${errorText}`);
    }
    
    const data = await response.json();
    return { success: true, job: data };
  } catch (error) {
    console.error('Failed to save job:', error);
    throw error;
  }
}
