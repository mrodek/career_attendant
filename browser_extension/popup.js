// Configuration - update these for your environment
const CONFIG = {
  USE_PRODUCTION: true, // Set to true for Railway, false for local development
  
  PRODUCTION_URL: 'https://careerattendant-production.up.railway.app/entries/',
  LOCAL_URL: 'http://localhost:8080/entries/',
  
  API_KEY: 'career_attendant_dev_987', // TODO: Move to options page or env-specific config
};

// Get the current tab's URL when popup opens
let userProfile = { email: '', id: '' };
const API_URL = CONFIG.USE_PRODUCTION ? CONFIG.PRODUCTION_URL : CONFIG.LOCAL_URL;
document.addEventListener('DOMContentLoaded', () => {
  // Get current tab URL
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    const currentTab = tabs[0];
    const urlDisplay = document.getElementById('currentUrl');
    const titleInput = document.getElementById('title');
    
    if (currentTab && currentTab.url) {
      urlDisplay.textContent = currentTab.url;
      // Auto-fill title with page title if available
      if (currentTab.title) {
        titleInput.value = currentTab.title;
      }
    } else {
      urlDisplay.textContent = 'Unable to get URL';
    }
  });

  // Fetch Chrome profile's Google account info
  if (chrome.identity && chrome.identity.getProfileUserInfo) {
    try {
      // Try with details (broader match in newer Chrome versions)
      chrome.identity.getProfileUserInfo({ accountStatus: 'ANY' }, (info) => {
        if (chrome.runtime && chrome.runtime.lastError) {
          // Fallback to legacy call without details
          chrome.identity.getProfileUserInfo((legacyInfo) => {
            userProfile = { email: legacyInfo?.email || '', id: legacyInfo?.id || '' };
          });
          return;
        }
        userProfile = { email: info?.email || '', id: info?.id || '' };
      });
    } catch (e) {
      // Final fallback
      chrome.identity.getProfileUserInfo((legacyInfo) => {
        userProfile = { email: legacyInfo?.email || '', id: legacyInfo?.id || '' };
      });
    }
  }

  // Load any previously saved entries (optional - shows count)
  loadSavedEntries();
});

// Handle form submission
document.getElementById('captureForm').addEventListener('submit', (e) => {
  e.preventDefault();

  // Helper: map rating (1-3) to interest level
  function ratingToInterestLevel(r) {
    if (r === 3) return 'high';
    if (r === 2) return 'medium';
    if (r === 1) return 'low';
    return 'medium'; // default
  }

  // Get rating value
  const ratingValue = parseInt(
    document.querySelector('input[name="rating"]:checked')?.value || '2',
    10
  );

  // Get applied value
  const appliedValue = (() => {
    const v = document.getElementById('applied')?.value;
    if (v === 'true') return true;
    if (v === 'false') return false;
    return null;
  })();

  // Helper: convert empty string to null
  const valueOrNull = (val) => (val && val.trim() !== '' ? val : null);

  // Build payload matching new EntryIn schema
  const formData = {
    jobUrl: document.getElementById('currentUrl').textContent,
    jobTitle: valueOrNull(document.getElementById('title').value),
    companyName: valueOrNull(document.getElementById('company').value),
    jobDescription: null, // no UI field yet
    salaryRange: valueOrNull(document.getElementById('salaryRange').value),
    location: valueOrNull(document.getElementById('location').value),
    remoteType: valueOrNull(document.getElementById('workType').value),
    roleType: valueOrNull(document.getElementById('jobType').value),
    interestLevel: ratingToInterestLevel(ratingValue),
    applicationStatus: appliedValue === true ? 'applied' : 'saved',
    applicationDate: null, // no date picker yet
    userEmail: userProfile.email || null,
    userId: userProfile.id || null,
    notes: valueOrNull(document.getElementById('notes').value),
    source: null,
    scrapedData: null,
  };

  // Save to Chrome storage and post to API
  Promise.all([
    saveEntry(formData),
    postToApi(formData)
  ])
    .then(() => {
      console.log('Entry saved to both local storage and API');
    })
    .catch((err) => {
      console.error('Failed to save entry:', err);
      alert(`Warning: Entry saved locally but API sync failed: ${err.message}`);
    });
});

// Post entry to API backend
function postToApi(entry) {
  return fetch(API_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': CONFIG.API_KEY,
    },
    body: JSON.stringify(entry),
  })
    .then((response) => {
      if (!response.ok) {
        console.error('API POST failed with status', response.status);
        return response.text().then(text => {
          console.error('API error response:', text);
          throw new Error(`API returned ${response.status}: ${text}`);
        });
      }
      return response.json();
    })
    .then((data) => {
      console.log('API entry created successfully:', data);
      return data;
    })
    .catch((err) => {
      console.error('Error posting to API:', err);
      throw err;
    });
}

// Save entry to local storage
function saveEntry(entry) {
  return new Promise((resolve, reject) => {
    chrome.storage.local.get(['entries'], (result) => {
      const entries = result.entries || [];
      entries.push(entry);
      
      chrome.storage.local.set({ entries: entries }, () => {
        if (chrome.runtime.lastError) {
          reject(chrome.runtime.lastError);
          return;
        }
        
        // Show success message
        const successMsg = document.getElementById('successMessage');
        successMsg.classList.add('show');
        
        // Reset form after short delay
        setTimeout(() => {
          document.getElementById('captureForm').reset();
          successMsg.classList.remove('show');
        }, 1500);

        console.log('Entry saved to local storage:', entry);
        console.log('Total entries:', entries.length);
        resolve();
      });
    });
  });
}

// Load saved entries (for debugging/display purposes)
function loadSavedEntries() {
  chrome.storage.local.get(['entries'], (result) => {
    const entries = result.entries || [];
    console.log('Saved entries:', entries);
  });
}

// Utility function to export all entries (can be called from console)
function exportEntries() {
  chrome.storage.local.get(['entries'], (result) => {
    const entries = result.entries || [];
    const dataStr = JSON.stringify(entries, null, 2);
    console.log('All entries:\n', dataStr);
    
    // Copy to clipboard
    navigator.clipboard.writeText(dataStr).then(() => {
      console.log('Entries copied to clipboard!');
    });
  });
}

// Make export function available globally for debugging
window.exportEntries = exportEntries;
