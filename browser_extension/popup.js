// Configuration
const CONFIG = {
  USE_PRODUCTION: false,
  PRODUCTION_URL: 'https://careerattendant-production.up.railway.app/entries/',
  LOCAL_URL: 'http://localhost:8080/entries/',
};

// Authentication state
let authState = {
  isAuthenticated: false,
  userId: null,
  userEmail: null,
  sessionToken: null
};

const API_URL = CONFIG.USE_PRODUCTION ? CONFIG.PRODUCTION_URL : CONFIG.LOCAL_URL;
let DEV_MODE = false; // Will be detected from API

// Initialize on load
document.addEventListener('DOMContentLoaded', async () => {
  updateEnvBadge();
  await detectDevMode(); // Check if API is in dev mode
  await loadAuthState();
  updateAuthUI();
  setupEventListeners();
  loadCurrentTab();
});

// Detect if API is in dev mode by checking health endpoint
async function detectDevMode() {
  try {
    const response = await fetch(`${API_URL.replace('/entries/', '')}/health`);
    if (response.ok) {
      const data = await response.json();
      DEV_MODE = data.dev_mode === true;
      console.log('Dev mode detected:', DEV_MODE);
    }
  } catch (error) {
    console.log('Could not detect dev mode, assuming production');
  }
}

// Load authentication state from background
async function loadAuthState() {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage({ type: 'GET_AUTH_STATE' }, (response) => {
      if (response && response.isAuthenticated) {
        authState = response;
        // Fetch user info
        chrome.runtime.sendMessage({ type: 'GET_USER_INFO' }, (userResponse) => {
          if (userResponse && userResponse.success) {
            authState.userEmail = userResponse.user.email;
          }
          resolve();
        });
      } else {
        resolve();
      }
    });
  });
}

// Update authentication UI
function updateAuthUI() {
  const userInfo = document.getElementById('userInfo');
  const authButton = document.getElementById('authButton');
  const authRequired = document.getElementById('authRequired');
  const captureForm = document.getElementById('captureForm');
  const authSection = document.querySelector('.auth-section');

  // In dev mode, hide auth UI and enable form
  if (DEV_MODE) {
    if (authSection) authSection.style.display = 'none';
    authRequired.classList.remove('show');
    captureForm.classList.remove('disabled');
    return;
  }

  // Production mode - show auth UI
  if (authState.isAuthenticated) {
    userInfo.textContent = authState.userEmail || `User ${authState.userId}`;
    authButton.textContent = 'Sign Out';
    authButton.classList.add('logout');
    authRequired.classList.remove('show');
    captureForm.classList.remove('disabled');
  } else {
    userInfo.textContent = 'Not signed in';
    authButton.textContent = 'Sign In';
    authButton.classList.remove('logout');
    authRequired.classList.add('show');
    captureForm.classList.add('disabled');
  }
}

// Setup event listeners
function setupEventListeners() {
  // Auth button
  document.getElementById('authButton').addEventListener('click', handleAuthClick);
  
  // Form submission
  document.getElementById('captureForm').addEventListener('submit', handleFormSubmit);
}

// Handle auth button click
async function handleAuthClick() {
  const authButton = document.getElementById('authButton');
  
  if (authState.isAuthenticated) {
    // Logout
    authButton.disabled = true;
    authButton.textContent = 'Signing out...';
    
    chrome.runtime.sendMessage({ type: 'LOGOUT' }, async (response) => {
      if (response && response.success) {
        authState = {
          isAuthenticated: false,
          userId: null,
          userEmail: null,
          sessionToken: null
        };
        updateAuthUI();
      }
      authButton.disabled = false;
    });
  } else {
    // Login
    authButton.disabled = true;
    authButton.textContent = 'Opening sign in...';
    
    try {
      chrome.runtime.sendMessage({ type: 'AUTHENTICATE' }, async (response) => {
        authButton.disabled = false;
        
        // Check for runtime errors
        if (chrome.runtime.lastError) {
          console.error('Runtime error:', chrome.runtime.lastError);
          showErrorMessage('Extension error: ' + chrome.runtime.lastError.message);
          authButton.textContent = 'Sign In';
          return;
        }
        
        if (response && response.success) {
          await loadAuthState();
          updateAuthUI();
        } else {
          console.error('Auth response:', response);
          showErrorMessage('Authentication failed: ' + (response?.error || 'Unknown error'));
          authButton.textContent = 'Sign In';
        }
      });
    } catch (error) {
      console.error('Auth error:', error);
      showErrorMessage('Error: ' + error.message);
      authButton.disabled = false;
      authButton.textContent = 'Sign In';
    }
  }
}

// Load current tab info
async function loadCurrentTab() {
  chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
    const currentTab = tabs[0];
    const urlDisplay = document.getElementById('currentUrl');
    const titleInput = document.getElementById('title');
    
    if (currentTab && currentTab.url) {
      urlDisplay.textContent = currentTab.url;
      
      // Check if this URL is already saved (works in both dev and production mode)
      await checkIfAlreadySaved(currentTab.url);
      
      // Auto-fill title with page title if available
      if (currentTab.title && !titleInput.value) {
        titleInput.value = currentTab.title;
      }
    } else {
      urlDisplay.textContent = 'Unable to get URL';
    }
  });
}

// Check if URL is already saved (check API, not just local storage)
async function checkIfAlreadySaved(url) {
  try {
    // Make request to API (with auth token in production, without in dev mode)
    const headers = {
      'Content-Type': 'application/json'
    };
    
    // Only add auth header in production mode
    if (!DEV_MODE && authState.sessionToken) {
      headers['Authorization'] = `Bearer ${authState.sessionToken}`;
    }
    
    const response = await fetch(`${API_URL}?jobUrl=${encodeURIComponent(url)}`, {
      headers: headers
    });
    
    if (response.ok) {
      const data = await response.json();
      if (data.items && data.items.length > 0) {
        // URL already saved in API
        const savedJob = data.items[0];
        showAlreadySavedStatus(savedJob);
      }
    }
  } catch (error) {
    console.log('Could not check if URL is saved:', error);
    // Fallback to local storage check
    chrome.storage.local.get(['entries'], (result) => {
      const entries = result.entries || [];
      const existingEntry = entries.find(entry => entry.jobUrl === url);
      
      if (existingEntry) {
        populateFormWithEntry(existingEntry);
        markAsSaved();
      }
    });
  }
}

// Show that this job is already saved
function showAlreadySavedStatus(savedJob) {
  const submitBtn = document.querySelector('button[type="submit"]');
  const urlDisplay = document.getElementById('currentUrl');
  
  // Add visual indicator
  urlDisplay.style.color = '#10b981';
  urlDisplay.style.fontWeight = 'bold';
  
  // Update button
  submitBtn.textContent = '✓ Already Saved';
  submitBtn.classList.add('saved');
  submitBtn.disabled = true;
  
  // Show info message
  const form = document.getElementById('captureForm');
  const infoDiv = document.createElement('div');
  infoDiv.className = 'info-message';
  infoDiv.innerHTML = `
    <strong>✓ This job was saved on ${new Date(savedJob.created_at).toLocaleDateString()}</strong>
    <br>
    <small>Status: ${savedJob.applicationStatus || 'saved'} | Interest: ${savedJob.interestLevel || 'medium'}</small>
  `;
  form.insertBefore(infoDiv, form.firstChild);
  
  // Pre-fill form with saved data
  populateFormWithEntry(savedJob);
}

// Populate form with existing entry
function populateFormWithEntry(entry) {
  document.getElementById('title').value = entry.jobTitle || '';
  document.getElementById('company').value = entry.companyName || '';
  document.getElementById('workType').value = entry.remoteType || '';
  document.getElementById('salaryRange').value = entry.salaryRange || '';
  document.getElementById('jobType').value = entry.roleType || '';
  document.getElementById('location').value = entry.location || '';
  document.getElementById('notes').value = entry.notes || '';
  
  if (entry.applicationStatus === 'applied') {
    document.getElementById('applied').value = 'true';
  } else if (entry.applicationStatus === 'saved') {
    document.getElementById('applied').value = 'false';
  }
  
  const interestMap = { 'low': '1', 'medium': '2', 'high': '3' };
  const ratingValue = interestMap[entry.interestLevel] || '2';
  const ratingRadio = document.querySelector(`input[name="rating"][value="${ratingValue}"]`);
  if (ratingRadio) {
    ratingRadio.checked = true;
  }
}

// Mark form as saved
function markAsSaved() {
  const submitBtn = document.querySelector('button[type="submit"]');
  submitBtn.textContent = '✓ Saved';
  submitBtn.classList.add('saved');
  submitBtn.disabled = true;
}

// Handle form submission
async function handleFormSubmit(e) {
  e.preventDefault();
  
  // In dev mode, skip auth check
  if (!DEV_MODE && !authState.isAuthenticated) {
    showErrorMessage('Please sign in to save job entries');
    return;
  }
  
  const submitBtn = document.querySelector('button[type="submit"]');
  submitBtn.disabled = true;
  submitBtn.textContent = 'Saving...';
  
  try {
    const formData = buildFormData();
    
    // In dev mode, save directly to API
    if (DEV_MODE) {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API error: ${response.status} - ${errorText}`);
      }
      
      await saveToLocalStorage(formData);
      markAsSaved();
      showSuccessMessage();
    } else {
      // Production mode - save via background script
      chrome.runtime.sendMessage(
        { type: 'SAVE_JOB', jobData: formData },
        async (response) => {
          if (response && response.success) {
            await saveToLocalStorage(formData);
            markAsSaved();
            showSuccessMessage();
          } else {
            throw new Error(response?.error || 'Failed to save job');
          }
        }
      );
    }
  } catch (error) {
    console.error('Error saving entry:', error);
    showErrorMessage(`Failed to save: ${error.message}`);
    submitBtn.disabled = false;
    submitBtn.textContent = 'Save Entry';
  }
}

// Build form data object
function buildFormData() {
  const ratingValue = parseInt(
    document.querySelector('input[name="rating"]:checked')?.value || '2',
    10
  );
  
  const appliedValue = (() => {
    const v = document.getElementById('applied')?.value;
    if (v === 'true') return true;
    if (v === 'false') return false;
    return null;
  })();
  
  const valueOrNull = (val) => (val && val.trim() !== '' ? val : null);
  
  function ratingToInterestLevel(r) {
    if (r === 3) return 'high';
    if (r === 2) return 'medium';
    if (r === 1) return 'low';
    return 'medium';
  }
  
  return {
    jobUrl: document.getElementById('currentUrl').textContent,
    jobTitle: valueOrNull(document.getElementById('title').value),
    companyName: valueOrNull(document.getElementById('company').value),
    jobDescription: null,
    salaryRange: valueOrNull(document.getElementById('salaryRange').value),
    location: valueOrNull(document.getElementById('location').value),
    remoteType: valueOrNull(document.getElementById('workType').value),
    roleType: valueOrNull(document.getElementById('jobType').value),
    interestLevel: ratingToInterestLevel(ratingValue),
    applicationStatus: appliedValue === true ? 'applied' : 'saved',
    applicationDate: null,
    userEmail: authState.userEmail,
    userId: authState.userId,
    notes: valueOrNull(document.getElementById('notes').value),
    source: null,
    scrapedData: null,
  };
}

// Save to local storage
function saveToLocalStorage(entry) {
  return new Promise((resolve) => {
    chrome.storage.local.get(['entries'], (result) => {
      const entries = result.entries || [];
      entries.push(entry);
      chrome.storage.local.set({ entries }, () => {
        console.log('Saved to local storage');
        resolve();
      });
    });
  });
}

// Show success message
function showSuccessMessage() {
  const successMsg = document.getElementById('successMessage');
  successMsg.classList.add('show');
  setTimeout(() => {
    successMsg.classList.remove('show');
  }, 2000);
}

// Show error message
function showErrorMessage(message) {
  const successMsg = document.getElementById('successMessage');
  successMsg.textContent = '✗ ' + message;
  successMsg.style.background = '#fee2e2';
  successMsg.style.color = '#991b1b';
  successMsg.classList.add('show');
  setTimeout(() => {
    successMsg.classList.remove('show');
    successMsg.textContent = '✓ Entry saved successfully!';
    successMsg.style.background = '#d1fae5';
    successMsg.style.color = '#065f46';
  }, 3000);
}

// Update environment badge
function updateEnvBadge() {
  const badge = document.getElementById('envBadge');
  if (CONFIG.USE_PRODUCTION) {
    badge.style.display = 'none';
  } else {
    badge.textContent = 'LOCAL';
    badge.className = 'env-badge local';
    badge.style.display = 'inline-block';
  }
}

// Export function for debugging
window.exportEntries = function() {
  chrome.storage.local.get(['entries'], (result) => {
    const entries = result.entries || [];
    const dataStr = JSON.stringify(entries, null, 2);
    console.log('All entries:\n', dataStr);
    navigator.clipboard.writeText(dataStr).then(() => {
      console.log('Entries copied to clipboard!');
    });
  });
};
