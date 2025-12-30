// Configuration
const CONFIG = {
  USE_PRODUCTION: false,
  PRODUCTION_URL: 'https://careerattendant-production.up.railway.app/entries',
  LOCAL_URL: 'http://localhost:8080/entries',
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

// Detect job board source from URL
function detectSource(url) {
  try {
    const hostname = new URL(url).hostname.toLowerCase();
    if (hostname.includes('linkedin')) return 'linkedin';
    if (hostname.includes('indeed')) return 'indeed';
    if (hostname.includes('greenhouse')) return 'greenhouse';
    if (hostname.includes('lever')) return 'lever';
    if (hostname.includes('workday')) return 'workday';
    if (hostname.includes('glassdoor')) return 'glassdoor';
    if (hostname.includes('ziprecruiter')) return 'ziprecruiter';
    if (hostname.includes('monster')) return 'monster';
    if (hostname.includes('dice')) return 'dice';
    if (hostname.includes('angel') || hostname.includes('wellfound')) return 'angellist';
    if (hostname.includes('simplyhired')) return 'simplyhired';
    if (hostname.includes('careerbuilder')) return 'careerbuilder';
    return hostname.replace('www.', '').split('.')[0]; // fallback to domain name
  } catch {
    return null;
  }
}

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
  
  // Show info message with AI fit score if available
  const form = document.getElementById('captureForm');
  const infoDiv = document.createElement('div');
  infoDiv.className = 'info-message';
  
  let statusText = `Status: ${savedJob.applicationStatus || 'saved'} | Interest: ${savedJob.interestLevel || 'medium'}`;
  if (savedJob.jobFitScore) {
    statusText += ` | Fit: ${savedJob.jobFitScore}`;
  }
  
  infoDiv.innerHTML = `
    <strong>✓ This job was saved on ${new Date(savedJob.created_at).toLocaleDateString()}</strong>
    <br>
    <small>${statusText}</small>
  `;
  form.insertBefore(infoDiv, form.firstChild);
  
  // Pre-fill form with saved data
  populateFormWithEntry(savedJob);
}

// Populate form with existing entry
// Handles both nested (new) and flat (legacy) response structures
function populateFormWithEntry(entry) {
  // Support both nested job object (new API) and flat structure (legacy/local storage)
  const job = entry.job || entry;
  
  document.getElementById('title').value = job.jobTitle || '';
  document.getElementById('company').value = job.companyName || '';
  document.getElementById('workType').value = job.remoteType || '';
  // Handle new salary structure (salaryRaw) or legacy (salaryRange)
  document.getElementById('salaryRange').value = job.salaryRaw || job.salaryRange || '';
  document.getElementById('jobType').value = job.roleType || '';
  document.getElementById('location').value = job.location || '';
  
  // User-specific fields are always at top level
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
    
    // Extract derived signals from page (no raw content stored)
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab?.id) {
      submitBtn.textContent = 'Extracting job data...';
      const signals = await extractJobSignals(tab.id);
      
      // Merge extracted signals into form data
      // Only use extracted values if form fields are empty
      if (signals.salaryMin && !formData.salaryMin) formData.salaryMin = signals.salaryMin;
      if (signals.salaryMax && !formData.salaryMax) formData.salaryMax = signals.salaryMax;
      if (signals.salaryPeriod && !formData.salaryPeriod) formData.salaryPeriod = signals.salaryPeriod;
      if (signals.salaryRaw && !formData.salaryRaw) formData.salaryRaw = signals.salaryRaw;
      if (signals.seniority && !formData.seniority) formData.seniority = signals.seniority;
      if (signals.yearsExperienceMin !== null) formData.yearsExperienceMin = signals.yearsExperienceMin;
      if (signals.requiredSkills?.length > 0) formData.requiredSkills = signals.requiredSkills;
      if (signals.remoteType && !formData.remoteType) formData.remoteType = signals.remoteType;
      if (signals.roleType && !formData.roleType) formData.roleType = signals.roleType;
      if (signals.easyApply !== undefined) formData.easyApply = signals.easyApply;
      if (signals.extractedLocation && !formData.location) formData.location = signals.extractedLocation;
      formData.extractionConfidence = signals.extractionConfidence;
      
      // DEBUG: Include raw text for debugging extraction
      if (signals.scrapedTextDebug) formData.scrapedTextDebug = signals.scrapedTextDebug;
      
      console.log('Extracted signals:', signals);
    }
    
    submitBtn.textContent = 'Saving...';
    
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
          if (chrome.runtime.lastError) {
            console.error('Runtime error:', chrome.runtime.lastError);
            showErrorMessage('Extension error: ' + chrome.runtime.lastError.message);
            submitBtn.disabled = false;
            submitBtn.textContent = 'Save Entry';
            return;
          }
          
          if (response && response.success) {
            await saveToLocalStorage(formData);
            markAsSaved();
            showSuccessMessage();
          } else {
            console.error('Save failed:', response);
            showErrorMessage(response?.error || 'Failed to save job');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Save Entry';
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
    // Job identification
    jobUrl: document.getElementById('currentUrl').textContent,
    jobTitle: valueOrNull(document.getElementById('title').value),
    companyName: valueOrNull(document.getElementById('company').value),
    
    // Salary (will be populated by extraction if available)
    salaryMin: null,
    salaryMax: null,
    salaryCurrency: 'USD',
    salaryPeriod: null,
    salaryRaw: valueOrNull(document.getElementById('salaryRange').value),
    
    // Location
    location: valueOrNull(document.getElementById('location').value),
    
    // Work arrangement
    remoteType: valueOrNull(document.getElementById('workType').value),
    roleType: valueOrNull(document.getElementById('jobType').value),
    seniority: null, // Will be populated by extraction
    
    // Extracted skills (will be populated by extraction)
    requiredSkills: null,
    preferredSkills: null,
    yearsExperienceMin: null,
    
    // Metadata
    easyApply: null,
    source: detectSource(document.getElementById('currentUrl').textContent),
    extractionConfidence: null,
    
    // User-specific
    interestLevel: ratingToInterestLevel(ratingValue),
    applicationStatus: appliedValue === true ? 'applied' : 'saved',
    applicationDate: null,
    notes: valueOrNull(document.getElementById('notes').value),
    userEmail: authState.userEmail,
    userId: authState.userId,
  };
}

// Extract derived job signals from the active tab (no raw content stored)
async function extractJobSignals(tabId) {
  try {
    const [result] = await chrome.scripting.executeScript({
      target: { tabId },
      func: () => {
        // Get page text for extraction
        let bodyText = document.body.innerText;
        let lowerText = bodyText.toLowerCase();
        const hostname = window.location.hostname.toLowerCase();
        
        // ========== SOURCE-SPECIFIC EXTRACTION ==========
        // LinkedIn: Extract only the job description section
        // Handles both dedicated job pages AND job search split-view
        if (hostname.includes('linkedin')) {
          // Try multiple selectors in order of specificity
          const selectors = [
            // Job detail panel in search view (2024+ layout)
            '.jobs-unified-top-card__content--two-pane + div',
            '.job-details-jobs-unified-top-card__primary-description-container',
            // "About the job" section specifically
            '[class*="jobs-description"]',
            '.jobs-description__content',
            '.jobs-box__html-content',
            '#job-details',
            // Fallback: the main job detail pane
            '.jobs-search__job-details--wrapper',
            '.job-view-layout',
          ];
          
          for (const selector of selectors) {
            const el = document.querySelector(selector);
            if (el && el.innerText.length > 200) {
              bodyText = el.innerText;
              break;
            }
          }
          
          // Start extraction after LinkedIn footer (job panel starts after this)
          const startMarker = 'LinkedIn Corporation ©';
          const startIdx = bodyText.indexOf(startMarker);
          if (startIdx > 0) {
            // Skip past the marker and any year/whitespace
            bodyText = bodyText.slice(startIdx + startMarker.length).replace(/^\s*\d{4}\s*/, '').trim();
          }
          
          // Clean up: Remove applicant insights section and other noise
          const cutoffPatterns = [
            'See how you compare to other applicants',
            'See how you compare to others who clicked apply',
            'About the company',
            'People also viewed',
            'Similar jobs',
          ];
          for (const pattern of cutoffPatterns) {
            const idx = bodyText.indexOf(pattern);
            if (idx > 200) {
              bodyText = bodyText.slice(0, idx);
            }
          }
          lowerText = bodyText.toLowerCase();
        }
        // Indeed: Extract job description section
        else if (hostname.includes('indeed')) {
          const descEl = document.querySelector('#jobDescriptionText')
                      || document.querySelector('.jobsearch-jobDescriptionText');
          if (descEl) {
            bodyText = descEl.innerText;
            lowerText = bodyText.toLowerCase();
          }
        }
        // Greenhouse/Ashby: Extract content section
        else if (hostname.includes('greenhouse') || hostname.includes('ashby')) {
          const descEl = document.querySelector('[data-testid="description"]')
                      || document.querySelector('.posting-page')
                      || document.querySelector('#content');
          if (descEl) {
            bodyText = descEl.innerText;
            lowerText = bodyText.toLowerCase();
          }
        }
        // Lever: Extract posting content
        else if (hostname.includes('lever')) {
          const descEl = document.querySelector('.posting-page')
                      || document.querySelector('.section-wrapper');
          if (descEl) {
            bodyText = descEl.innerText;
            lowerText = bodyText.toLowerCase();
          }
        }
        
        // ========== SALARY EXTRACTION ==========
        const parseSalary = () => {
          // Match patterns like "$193.8K – $227.7K", "$150,000 - $200,000", "$80/hr"
          // Support decimals (193.8K), various dashes, K/k suffix
          const salaryRegex = /\$([\d,.]+)\s*([kK])?\s*[-–—to]+\s*\$([\d,.]+)\s*([kK])?/;
          const singleSalaryRegex = /\$([\d,.]+)\s*([kK])?(?:\s*(?:\/|per)\s*(year|yr|hour|hr|month|annual))?/i;
          
          let match = salaryRegex.exec(bodyText);
          if (match) {
            let min = parseFloat(match[1].replace(/,/g, ''));
            let max = parseFloat(match[3].replace(/,/g, ''));
            
            // Handle K suffix
            if (match[2]?.toLowerCase() === 'k' || min < 1000) min *= 1000;
            if (match[4]?.toLowerCase() === 'k' || max < 1000) max *= 1000;
            
            // Get raw display string (capture more context)
            const rawMatch = bodyText.match(/\$[\d,.]+\s*[kK]?\s*[-–—]+\s*\$[\d,.]+\s*[kK]?[^\n]*/i);
            
            return {
              salaryMin: Math.round(min),
              salaryMax: Math.round(max),
              salaryPeriod: 'year', // Assume annual for K ranges
              salaryRaw: rawMatch ? rawMatch[0].trim().slice(0, 50) : null,
            };
          }
          
          // Try single salary
          match = singleSalaryRegex.exec(bodyText);
          if (match) {
            let amount = parseFloat(match[1].replace(/,/g, ''));
            if (match[2]?.toLowerCase() === 'k' || amount < 1000) amount *= 1000;
            
            const periodRaw = match[3]?.toLowerCase() || '';
            let period = 'year';
            if (periodRaw.includes('hour') || periodRaw.includes('hr')) period = 'hour';
            else if (periodRaw.includes('month')) period = 'month';
            
            return {
              salaryMin: Math.round(amount),
              salaryMax: null,
              salaryPeriod: period,
              salaryRaw: match[0].trim(),
            };
          }
          
          return { salaryMin: null, salaryMax: null, salaryPeriod: null, salaryRaw: null };
        };
        
        // ========== SENIORITY DETECTION ==========
        const detectSeniority = () => {
          const title = document.title.toLowerCase();
          const combined = title + ' ' + lowerText.slice(0, 5000);
          
          if (/\b(cto|ceo|cfo|coo|chief)\b/.test(combined)) return 'cxo';
          if (/\b(vp|vice president)\b/.test(combined)) return 'vp';
          if (/\b(director)\b/.test(combined)) return 'director';
          if (/\b(principal|distinguished|fellow)\b/.test(combined)) return 'principal';
          if (/\b(staff|lead|tech lead)\b/.test(combined)) return 'staff';
          if (/\b(senior|sr\.|sr )\b/.test(combined)) return 'senior';
          if (/\b(mid-level|mid level|intermediate)\b/.test(combined)) return 'mid';
          if (/\b(junior|jr\.|jr |entry[- ]level|associate)\b/.test(combined)) return 'junior';
          if (/\b(intern|internship|co-op)\b/.test(combined)) return 'intern';
          return null;
        };
        
        // ========== YEARS EXPERIENCE ==========
        const extractYearsExperience = () => {
          // Match "8+ years", "5-7 years experience", "minimum 3 years", "8+ years in"
          const patterns = [
            /(\d+)\+?\s*(?:years?|yrs?)\s*(?:of|in)?\s*(?:experience|exp|[a-z]+)?/gi,
            /(?:at least|minimum|min\.?)\s*(\d+)\s*(?:years?|yrs?)/gi,
            /(\d+)\s*[-–]\s*(\d+)\s*(?:years?|yrs?)/gi,
          ];
          
          for (const pattern of patterns) {
            const match = pattern.exec(bodyText);
            if (match) {
              const min = parseInt(match[1], 10);
              const max = match[2] ? parseInt(match[2], 10) : null;
              if (min >= 1 && min <= 30) {
                return { yearsExperienceMin: min, yearsExperienceMax: max };
              }
            }
          }
          return { yearsExperienceMin: null, yearsExperienceMax: null };
        };
        
        // ========== SKILLS EXTRACTION ==========
        const extractSkills = () => {
          // Common tech skills taxonomy
          const skillPatterns = [
            // Languages
            'python', 'javascript', 'typescript', 'java', 'go', 'golang', 'rust', 'c\\+\\+', 'c#', 'ruby', 'scala', 'kotlin', 'swift',
            // ML/AI
            'pytorch', 'tensorflow', 'keras', 'scikit-learn', 'sklearn', 'hugging face', 'transformers', 'llm', 'gpt', 'bert', 'machine learning', 'deep learning', 'nlp', 'computer vision', 'mlops',
            // Cloud
            'aws', 'azure', 'gcp', 'google cloud', 'amazon web services',
            // Infrastructure
            'kubernetes', 'k8s', 'docker', 'terraform', 'helm', 'ansible', 'jenkins', 'ci/cd', 'devops',
            // Data
            'sql', 'postgresql', 'postgres', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'kafka', 'spark', 'flink', 'snowflake', 'databricks', 'airflow', 'dbt',
            // Frameworks
            'react', 'vue', 'angular', 'node.js', 'nodejs', 'fastapi', 'django', 'flask', 'spring',
            // Other
            'git', 'agile', 'scrum', 'rest api', 'graphql', 'microservices',
          ];
          
          const found = [];
          for (const skill of skillPatterns) {
            const regex = new RegExp('\\b' + skill + '\\b', 'gi');
            if (regex.test(lowerText)) {
              // Normalize skill name
              let normalized = skill.replace(/\\/g, '');
              if (normalized === 'k8s') normalized = 'kubernetes';
              if (normalized === 'golang') normalized = 'go';
              if (normalized === 'sklearn') normalized = 'scikit-learn';
              if (!found.includes(normalized)) {
                found.push(normalized);
              }
            }
          }
          return found.slice(0, 30); // Limit to 30 skills
        };
        
        // ========== REMOTE TYPE DETECTION ==========
        const detectRemoteType = () => {
          // Check for explicit remote indicators
          if (/\b(fully remote|100% remote|remote[- ]only|work from anywhere)\b/i.test(bodyText)) return 'remote';
          // Check "Location Type" pattern (common in job boards)
          if (/location\s*type[:\s]+remote/i.test(bodyText)) return 'remote';
          // Check for "Remote, [Location]" pattern
          if (/\bremote,\s*[a-z]+/i.test(bodyText)) return 'remote';
          if (/\bhybrid\b/i.test(bodyText)) return 'hybrid';
          if (/\b(on[- ]?site|in[- ]?office|in[- ]?person)\b/i.test(bodyText)) return 'onsite';
          // Check title/header area
          const title = document.title.toLowerCase();
          if (title.includes('remote')) return 'remote';
          if (title.includes('hybrid')) return 'hybrid';
          return null;
        };
        
        // ========== ROLE TYPE DETECTION ==========
        const detectRoleType = () => {
          if (/\b(full[- ]?time|permanent)\b/i.test(bodyText)) return 'full_time';
          if (/\b(part[- ]?time)\b/i.test(bodyText)) return 'part_time';
          if (/\b(contract|contractor|freelance|consulting)\b/i.test(bodyText)) return 'contract';
          // Check Employment Type pattern
          if (/employment\s*type[:\s]+(full|part)/i.test(bodyText)) {
            return bodyText.match(/employment\s*type[:\s]+(full|part)/i)[1].toLowerCase() === 'full' ? 'full_time' : 'part_time';
          }
          return null;
        };
        
        // ========== EASY APPLY DETECTION ==========
        const detectEasyApply = () => {
          return /easy apply|quick apply|1-click apply/i.test(bodyText);
        };
        
        // ========== LOCATION EXTRACTION ==========
        const extractLocation = () => {
          // Try to find location near "Location:" or in common patterns
          const locationMatch = bodyText.match(/(?:location|based in|located in)[:\s]+([^\n]{5,50})/i);
          if (locationMatch) return locationMatch[1].trim();
          return null;
        };
        
        // ========== RUN EXTRACTION ==========
        const salary = parseSalary();
        const experience = extractYearsExperience();
        const skills = extractSkills();
        const seniority = detectSeniority();
        
        return {
          // Parsed salary
          ...salary,
          
          // Seniority
          seniority,
          
          // Experience
          ...experience,
          
          // Skills (derived list, not raw text)
          requiredSkills: skills,
          
          // Work arrangement
          remoteType: detectRemoteType(),
          roleType: detectRoleType(),
          
          // Easy apply
          easyApply: detectEasyApply(),
          
          // Location (if found in structured way)
          extractedLocation: extractLocation(),
          
          // Confidence score (simple heuristic)
          extractionConfidence: (() => {
            let score = 50; // Base
            if (salary.salaryMin) score += 15;
            if (experience.yearsExperienceMin !== null) score += 10;
            if (skills.length > 3) score += 15;
            if (seniority) score += 10;
            return Math.min(score, 100);
          })(),
          
          // DEBUG: Raw scraped text for debugging extraction (truncated)
          scrapedTextDebug: bodyText.slice(0, 30000),
        };
      },
    });

    return result.result;
  } catch (error) {
    console.error('Failed to extract job signals:', error);
    return { extractionConfidence: 0 };
  }
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
