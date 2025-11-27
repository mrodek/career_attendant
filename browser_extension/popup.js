// Get the current tab's URL when popup opens
let userProfile = { email: '', id: '' };
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
            const emailInput = document.getElementById('userEmail');
            if (emailInput) {
              if (userProfile.email) {
                emailInput.value = userProfile.email;
                emailInput.readOnly = true;
              } else {
                emailInput.value = '';
                emailInput.placeholder = 'Email unavailable — enter manually';
                emailInput.readOnly = false;
                emailInput.title = 'Sign into Chrome and enable sync to auto-fill, or type manually';
              }
            }
          });
          return;
        }
        userProfile = { email: info?.email || '', id: info?.id || '' };
        const emailInput = document.getElementById('userEmail');
        if (emailInput) {
          if (userProfile.email) {
            emailInput.value = userProfile.email;
            emailInput.readOnly = true;
          } else {
            emailInput.value = '';
            emailInput.placeholder = 'Email unavailable — enter manually';
            emailInput.readOnly = false;
            emailInput.title = 'Sign into Chrome and enable sync to auto-fill, or type manually';
          }
        }
      });
    } catch (e) {
      // Final fallback
      chrome.identity.getProfileUserInfo((legacyInfo) => {
        userProfile = { email: legacyInfo?.email || '', id: legacyInfo?.id || '' };
        const emailInput = document.getElementById('userEmail');
        if (emailInput) {
          if (userProfile.email) {
            emailInput.value = userProfile.email;
            emailInput.readOnly = true;
          } else {
            emailInput.value = '';
            emailInput.placeholder = 'Email unavailable — enter manually';
            emailInput.readOnly = false;
            emailInput.title = 'Sign into Chrome and enable sync to auto-fill, or type manually';
          }
        }
      });
    }
  }

  // Load any previously saved entries (optional - shows count)
  loadSavedEntries();
});

// Handle form submission
document.getElementById('captureForm').addEventListener('submit', (e) => {
  e.preventDefault();

  // Get form data
  const formData = {
    url: document.getElementById('currentUrl').textContent,
    title: document.getElementById('title').value,
    company: document.getElementById('company').value,
    workType: document.getElementById('workType').value,
    salaryRange: document.getElementById('salaryRange').value,
    jobType: document.getElementById('jobType').value,
    location: document.getElementById('location').value,
    applied: (() => {
      const v = document.getElementById('applied')?.value;
      if (v === 'true') return true;
      if (v === 'false') return false;
      return null;
    })(),
    userEmail: (document.getElementById('userEmail')?.value || '').trim() || userProfile.email,
    userId: userProfile.id,
    rating: document.querySelector('input[name="rating"]:checked')?.value || '3',
    notes: document.getElementById('notes').value,
    timestamp: new Date().toISOString()
  };

  // Save to Chrome storage
  saveEntry(formData);
});

// Save entry to local storage
function saveEntry(entry) {
  chrome.storage.local.get(['entries'], (result) => {
    const entries = result.entries || [];
    entries.push(entry);
    
    chrome.storage.local.set({ entries: entries }, () => {
      // Show success message
      const successMsg = document.getElementById('successMessage');
      successMsg.classList.add('show');
      
      // Reset form after short delay
      setTimeout(() => {
        document.getElementById('captureForm').reset();
        successMsg.classList.remove('show');
      }, 1500);

      console.log('Entry saved:', entry);
      console.log('Total entries:', entries.length);
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
