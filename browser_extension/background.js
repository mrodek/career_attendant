// Background service worker for authentication and API communication

const CONFIG = {
  // Try local first, fallback to production
  API_URLS: [
    'http://localhost:8080',
    'https://careerattendant-production.up.railway.app'
  ],
};

let API_BASE_URL = CONFIG.API_URLS[0]; // Default to local
let CLERK_FRONTEND_API = null; // Will be fetched from API

// Auto-detect which API URL is available and get Clerk config
async function detectApiUrl() {
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
let authState = {
  sessionToken: null,
  userId: null,
  isAuthenticated: false
};

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
    chrome.storage.local.get(['sessionToken', 'userId'], (result) => {
      if (result.sessionToken && result.userId) {
        authState.sessionToken = result.sessionToken;
        authState.userId = result.userId;
        authState.isAuthenticated = true;
        console.log('Auth state loaded:', { userId: authState.userId });
      }
      resolve();
    });
  });
}

// Save authentication state to storage
async function saveAuthState(sessionToken, userId) {
  authState.sessionToken = sessionToken;
  authState.userId = userId;
  authState.isAuthenticated = true;
  
  return new Promise((resolve) => {
    chrome.storage.local.set({ sessionToken, userId }, () => {
      console.log('Auth state saved');
      resolve();
    });
  });
}

// Clear authentication state
async function clearAuthState() {
  authState.sessionToken = null;
  authState.userId = null;
  authState.isAuthenticated = false;
  
  return new Promise((resolve) => {
    chrome.storage.local.remove(['sessionToken', 'userId'], () => {
      console.log('Auth state cleared');
      resolve();
    });
  });
}

// Handle messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'GET_AUTH_STATE') {
    sendResponse(authState);
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
    saveAuthState(request.token, request.userId).then(() => {
      sendResponse({ success: true });
    }).catch((error) => {
      sendResponse({ success: false, error: error.message });
    });
    return true;
  }
  
  if (request.type === 'LOGOUT') {
    clearAuthState().then(() => {
      sendResponse({ success: true });
    });
    return true;
  }
  
  if (request.type === 'SAVE_JOB') {
    saveJob(request.jobData).then(sendResponse).catch((error) => {
      sendResponse({ success: false, error: error.message });
    });
    return true;
  }
  
  if (request.type === 'GET_USER_INFO') {
    getUserInfo().then(sendResponse).catch((error) => {
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
      await clearAuthState();
      throw new Error('Session expired');
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
    const response = await fetch(`${API_BASE_URL}/entries`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authState.sessionToken}`
      },
      body: JSON.stringify(jobData)
    });
    
    if (!response.ok) {
      if (response.status === 401) {
        await clearAuthState();
        throw new Error('Session expired. Please sign in again.');
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
