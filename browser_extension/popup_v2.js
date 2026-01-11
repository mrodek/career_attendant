// ==========================================================================
// Career Attendant Extension - Progressive Extraction UI
// ==========================================================================

const CONFIG = {
  USE_PRODUCTION: true,
  PRODUCTION_URL: 'https://careerattendant-production.up.railway.app',
  LOCAL_URL: 'http://localhost:8080',
};

const API_BASE = CONFIG.USE_PRODUCTION ? CONFIG.PRODUCTION_URL : CONFIG.LOCAL_URL;

// State
let authState = {
  isAuthenticated: false,
  userId: null,
  userEmail: null,
  sessionToken: null,
};

let DEV_MODE = false;
let extractionState = {
  status: 'idle', // idle, extracting, complete, error
  fields: {},
  confidence: {},
  summary: null,
  errors: [],
};
let interestLevel = 'medium';
let currentUrl = '';
let rawText = '';

// ==========================================================================
// Initialization
// ==========================================================================

document.addEventListener('DOMContentLoaded', async () => {
  updateEnvBadge();
  await detectDevMode();
  await loadAuthState();
  updateAuthUI();
  setupEventListeners();
  await loadCurrentTab();
  
  // Auto-start extraction
  startExtraction();
});

// Detect if API is in dev mode
async function detectDevMode() {
  try {
    const response = await fetch(`${API_BASE}/health`);
    if (response.ok) {
      const data = await response.json();
      DEV_MODE = data.dev_mode === true;
    }
  } catch (error) {
    console.log('Could not detect dev mode, assuming production');
  }
}

// Load auth state from background
async function loadAuthState() {
  return new Promise((resolve) => {
    if (typeof chrome !== 'undefined' && chrome.runtime) {
      chrome.runtime.sendMessage({ type: 'GET_AUTH_STATE' }, (response) => {
        if (response && response.isAuthenticated) {
          authState = response;
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
    } else {
      resolve();
    }
  });
}

// ==========================================================================
// Cache Helper Functions
// ==========================================================================

async function checkCache(url) {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage(
      { type: 'CHECK_JOB_CACHED', url },
      (response) => resolve(response)
    );
  });
}

async function setCache(url, data) {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage(
      { type: 'SET_JOB_CACHE', url, data },
      (response) => resolve(response)
    );
  });
}

async function invalidateCache(url) {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage(
      { type: 'INVALIDATE_JOB_CACHE', url },
      (response) => resolve(response)
    );
  });
}

// Check if job exists via API
async function checkJobExistsAPI(url) {
  try {
    const response = await fetch(
      `${API_BASE}/entries/check-by-url?url=${encodeURIComponent(url)}`,
      {
        headers: {
          'Authorization': `Bearer ${authState.sessionToken}`
        }
      }
    );
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Failed to check job existence:', error);
    return { exists: false };
  }
}

// Update auth UI
function updateAuthUI() {
  const authSection = document.getElementById('authSection');
  const authUser = document.getElementById('authUser');
  const authButton = document.getElementById('authButton');

  if (DEV_MODE) {
    authSection.classList.add('hidden');
    return;
  }

  if (authState.isAuthenticated) {
    authUser.textContent = authState.userEmail || `User ${authState.userId}`;
    authButton.textContent = 'Sign Out';
    authButton.classList.remove('login');
    authButton.classList.add('logout');
  } else {
    authUser.textContent = 'Not signed in';
    authButton.textContent = 'Sign In';
    authButton.classList.add('login');
    authButton.classList.remove('logout');
  }
}

// Setup event listeners
function setupEventListeners() {
  // Auth button
  document.getElementById('authButton').addEventListener('click', handleAuthClick);
  
  // Interest level buttons
  document.querySelectorAll('.interest-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.interest-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      interestLevel = btn.dataset.level;
    });
  });
  
  // Retry button
  document.getElementById('retryBtn').addEventListener('click', () => {
    startExtraction();
  });
  
  // Save button
  document.getElementById('saveBtn').addEventListener('click', handleSave);
}

// Handle auth click
async function handleAuthClick() {
  const authButton = document.getElementById('authButton');
  
  if (authState.isAuthenticated) {
    authButton.disabled = true;
    authButton.textContent = 'Signing out...';
    
    chrome.runtime.sendMessage({ type: 'LOGOUT' }, async (response) => {
      if (response && response.success) {
        authState = { isAuthenticated: false, userId: null, userEmail: null, sessionToken: null };
        updateAuthUI();
      }
      authButton.disabled = false;
    });
  } else {
    authButton.disabled = true;
    authButton.textContent = 'Opening...';
    
    chrome.runtime.sendMessage({ type: 'AUTHENTICATE' }, async (response) => {
      authButton.disabled = false;
      if (response && response.success) {
        await loadAuthState();
        updateAuthUI();
      } else {
        showMessage('Authentication failed', 'error');
        authButton.textContent = 'Sign In';
      }
    });
  }
}

// Load current tab info and scrape content
async function loadCurrentTab() {
  return new Promise((resolve) => {
    chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
      const tab = tabs[0];
      if (tab && tab.url) {
        currentUrl = tab.url;
        document.getElementById('currentUrl').textContent = currentUrl;
        
        // Scrape the page content
        try {
          const [result] = await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            func: scrapePageContent,
          });
          rawText = result.result || '';
        } catch (error) {
          console.error('Failed to scrape page:', error);
          rawText = '';
        }
      }
      resolve();
    });
  });
}

// Scrape page content (runs in page context)
function scrapePageContent() {
  let bodyText = document.body.innerText;
  const hostname = window.location.hostname.toLowerCase();
  
  // LinkedIn-specific extraction
  if (hostname.includes('linkedin')) {
    const selectors = [
      '.jobs-description__content',
      '.jobs-box__html-content',
      '#job-details',
      '.jobs-search__job-details--wrapper',
    ];
    
    for (const selector of selectors) {
      const el = document.querySelector(selector);
      if (el && el.innerText.length > 200) {
        bodyText = el.innerText;
        break;
      }
    }
    
    // Clean up LinkedIn noise
    const cutoffs = ['See how you compare', 'About the company', 'People also viewed'];
    for (const pattern of cutoffs) {
      const idx = bodyText.indexOf(pattern);
      if (idx > 200) bodyText = bodyText.slice(0, idx);
    }
  }
  // Indeed-specific extraction
  else if (hostname.includes('indeed')) {
    const descEl = document.querySelector('#jobDescriptionText') ||
                   document.querySelector('.jobsearch-jobDescriptionText');
    if (descEl) bodyText = descEl.innerText;
  }
  
  return bodyText.slice(0, 30000);
}

// ==========================================================================
// Extraction Flow
// ==========================================================================

async function startExtraction() {
  if (!rawText || rawText.length < 100) {
    showMessage('Could not extract job content from this page', 'error');
    document.getElementById('retryBtn').style.display = 'flex';
    return;
  }
  
  // STEP 1: Check authentication FIRST
  if (!authState.isAuthenticated) {
    showMessage('Please sign in to save jobs', 'error');
    return;
  }
  
  // STEP 2: Check in-memory cache (instant)
  const cached = await checkCache(currentUrl);
  if (cached && cached.exists) {
    console.log('✓ Using cached job data');
    displayExistingJob(cached);
    showMessage('✓ Job already saved (from cache)', 'success');
    return;
  }
  
  // STEP 3: Check API (if cache miss)
  showMessage('Checking if job exists...', 'info');
  const apiCheck = await checkJobExistsAPI(currentUrl);
  
  // If API check failed (500 error), fall through to extraction
  if (apiCheck.exists === undefined) {
    console.warn('API check failed, proceeding with extraction');
    showMessage('Running extraction...', 'info');
    await runFullExtraction();
    return;
  }
  
  if (apiCheck.exists) {
    // Cache the result for next time
    await setCache(currentUrl, apiCheck);
    
    if (apiCheck.has_extraction && apiCheck.has_summary) {
      // Complete - show existing data
      displayExistingJob(apiCheck);
      showMessage('✓ Job already saved! Showing existing data.', 'success');
      return;
    } else if (apiCheck.has_extraction) {
      // Has extraction but no summary - only run AI summary
      showMessage('Job exists but missing AI summary. Running analysis...', 'info');
      // TODO: Implement summary-only endpoint if needed
      // For now, fall through to full extraction
    }
    // Has job but no extraction - fall through to full extraction
  }
  
  // STEP 4: Job doesn't exist or incomplete - run full extraction
  await runFullExtraction();
}

// Run full extraction (original startExtraction logic)
async function runFullExtraction() {
  // Reset UI
  resetExtractionUI();
  extractionState = { status: 'extracting', fields: {}, confidence: {}, summary: null, errors: [] };
  document.getElementById('retryBtn').style.display = 'none';
  document.getElementById('saveBtn').disabled = true;
  
  // Get extension-extracted fields for validation
  const extensionFields = extractClientSideFields();
  
  try {
    // Use fetch with streaming for SSE
    const response = await fetch(`${API_BASE}/extract/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        job_url: currentUrl,
        raw_text: rawText,
        extension_extracted: extensionFields,
      }),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    // Read SSE stream
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      
      // Process complete SSE messages
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || ''; // Keep incomplete message in buffer
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            handleExtractionEvent(data);
          } catch (e) {
            console.error('Failed to parse SSE:', e, line);
          }
        }
      }
    }
    
  } catch (error) {
    console.error('Extraction failed:', error);
    extractionState.status = 'error';
    extractionState.errors.push(error.message);
    showMessage(`Extraction failed: ${error.message}`, 'error');
    document.getElementById('retryBtn').style.display = 'flex';
    updateProgressUI('error', 0, 'Extraction failed');
  }
}

// Handle SSE event from extraction stream
function handleExtractionEvent(data) {
  console.log('Extraction event:', data);
  
  // Update progress
  if (data.progress !== undefined) {
    updateProgressUI(data.status, data.progress, data.message);
  }
  
  // Update step indicators
  if (data.node) {
    updateStepIndicator(data.node, data.status);
  }
  
  // Handle extracted fields
  if (data.fields) {
    extractionState.fields = { ...extractionState.fields, ...data.fields };
    updateFormFields(data.fields);
  }
  
  // Handle confidence scores
  if (data.confidence) {
    extractionState.confidence = { ...extractionState.confidence, ...data.confidence };
    updateConfidenceIndicators(data.confidence);
  }
  
  // Handle summary
  if (data.summary) {
    extractionState.summary = data.summary;
    updateSummary(data.summary);
  }
  
  // Handle completion
  if (data.status === 'done') {
    extractionState.status = 'complete';
    clearAllLoadingStates(); // Allow manual entry for any missing fields
    document.getElementById('saveBtn').disabled = false;
    showMessage('Extraction complete! Review and save.', 'success');
  }
  
  // Handle errors
  if (data.status === 'error' || data.status === 'failed') {
    extractionState.status = 'error';
    clearAllLoadingStates(); // Allow manual entry even on error
    if (data.error) extractionState.errors.push(data.error);
    document.getElementById('retryBtn').style.display = 'flex';
    document.getElementById('saveBtn').disabled = false; // Allow save with manual data
  }
}

// Display existing job data from cache/API
function displayExistingJob(jobData) {
  extractionState.status = 'complete';
  
  // Populate fields from existing data
  if (jobData.job_data && jobData.job_data.extracted_data) {
    extractionState.fields = jobData.job_data.extracted_data;
    
    // Update UI fields
    Object.entries(jobData.job_data.extracted_data).forEach(([field, value]) => {
      const input = document.getElementById(field);
      if (input && value) {
        input.value = value;
        input.classList.remove('loading');
      }
    });
  }
  
  // Display summary if available
  if (jobData.job_data && jobData.job_data.ai_summary) {
    extractionState.summary = jobData.job_data.ai_summary;
    updateSummary(jobData.job_data.ai_summary);
  }
  
  // Set interest level if available
  if (jobData.job_data && jobData.job_data.interest_level) {
    interestLevel = jobData.job_data.interest_level;
    updateInterestLevelUI(interestLevel);
  }
  
  // Enable save button (for updates)
  document.getElementById('saveBtn').disabled = false;
  document.getElementById('saveBtn').textContent = '💾 Update Job';
  
  // Show "Force Re-extract" button
  const retryBtn = document.getElementById('retryBtn');
  retryBtn.textContent = '🔄 Force Re-extract';
  retryBtn.style.display = 'flex';
  retryBtn.onclick = async () => {
    await invalidateCache(currentUrl);
    await runFullExtraction();
  };
  
  clearAllLoadingStates();
}

// Extract client-side fields (fallback/validation)
function extractClientSideFields() {
  // Basic extraction from page title and meta
  const title = document.getElementById('currentUrl')?.textContent || '';
  
  // Detect source
  const source = detectSource(currentUrl);
  
  return {
    source,
    job_url: currentUrl,
  };
}

// Detect job board source
function detectSource(url) {
  try {
    const hostname = new URL(url).hostname.toLowerCase();
    if (hostname.includes('linkedin')) return 'linkedin';
    if (hostname.includes('indeed')) return 'indeed';
    if (hostname.includes('greenhouse')) return 'greenhouse';
    if (hostname.includes('lever')) return 'lever';
    return hostname.replace('www.', '').split('.')[0];
  } catch {
    return null;
  }
}

// ==========================================================================
// UI Updates
// ==========================================================================

function resetExtractionUI() {
  // Reset progress
  updateProgressUI('idle', 0, 'Starting extraction...');
  
  // Reset step indicators
  ['ingest', 'preprocess', 'extract', 'summarize'].forEach(step => {
    const el = document.getElementById(`step-${step}`);
    el.classList.remove('active', 'complete', 'error');
  });
  
  // Reset form fields to loading state
  const fields = ['jobTitle', 'companyName', 'location', 'salaryMin', 'salaryMax'];
  fields.forEach(id => {
    const input = document.getElementById(id);
    if (input) {
      input.value = '';
      input.placeholder = 'Loading...';
      input.parentElement.classList.add('loading');
    }
  });
  
  // Reset confidence dots
  document.querySelectorAll('.confidence-dot').forEach(dot => {
    dot.className = 'confidence-dot';
  });
  
  // Reset skills
  document.getElementById('skillsContainer').innerHTML = '';
  
  // Reset summary
  document.getElementById('summaryContent').innerHTML = `
    <div class="loading">
      <div class="spinner"></div>
      <span style="margin-left: 8px;">Generating summary...</span>
    </div>
  `;
  
  // Hide messages
  hideMessage();
}

function updateProgressUI(status, percent, message) {
  const fill = document.getElementById('progressFill');
  const percentEl = document.getElementById('progressPercent');
  const titleEl = document.getElementById('progressTitle');
  
  fill.style.width = `${percent}%`;
  percentEl.textContent = `${percent}%`;
  titleEl.textContent = message || 'Analyzing...';
  
  // Update progress bar color based on status
  if (status === 'error') {
    fill.style.background = 'var(--error)';
  } else if (status === 'done') {
    fill.style.background = 'var(--success)';
  } else {
    fill.style.background = 'linear-gradient(90deg, var(--primary), #818cf8)';
  }
}

function updateStepIndicator(node, status) {
  const stepEl = document.getElementById(`step-${node}`);
  if (!stepEl) return;
  
  // Clear previous active states
  if (status === 'started') {
    document.querySelectorAll('.step.active').forEach(el => {
      if (el.id !== `step-${node}`) {
        el.classList.remove('active');
        el.classList.add('complete');
      }
    });
    stepEl.classList.add('active');
    stepEl.classList.remove('complete', 'error');
  } else if (status === 'complete') {
    stepEl.classList.remove('active');
    stepEl.classList.add('complete');
    // Update icon to checkmark
    stepEl.querySelector('.step-icon').innerHTML = '✓';
  } else if (status === 'error') {
    stepEl.classList.remove('active');
    stepEl.classList.add('error');
    stepEl.querySelector('.step-icon').innerHTML = '✗';
  }
}

function updateFormFields(fields) {
  const fieldMapping = {
    job_title: 'jobTitle',
    company_name: 'companyName',
    location: 'location',
    salary_min: 'salaryMin',
    salary_max: 'salaryMax',
    remote_type: 'remoteType',
    role_type: 'roleType',
    seniority: 'seniority',
    years_experience_min: 'yearsExperience',
  };
  
  for (const [key, elementId] of Object.entries(fieldMapping)) {
    if (fields[key] !== undefined && fields[key] !== null) {
      const element = document.getElementById(elementId);
      if (element) {
        element.value = fields[key];
        element.placeholder = '';
        element.parentElement.classList.remove('loading');
      }
    }
  }
  
  // Handle skills separately
  if (fields.required_skills && Array.isArray(fields.required_skills)) {
    updateSkillsTags(fields.required_skills);
  }
}

// Clear loading state from all fields - allows manual entry
function clearAllLoadingStates() {
  const fieldPlaceholders = {
    'jobTitle': 'Enter job title',
    'companyName': 'Enter company',
    'location': 'Enter location',
    'salaryMin': 'Min (e.g., 100000)',
    'salaryMax': 'Max (e.g., 150000)',
    'yearsExperience': 'e.g., 5+',
  };
  
  for (const [id, placeholder] of Object.entries(fieldPlaceholders)) {
    const element = document.getElementById(id);
    if (element && element.parentElement.classList.contains('loading')) {
      element.placeholder = placeholder;
      element.parentElement.classList.remove('loading');
    }
  }
  
  // Also clear select dropdowns
  ['remoteType', 'roleType', 'seniority'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.parentElement.classList.remove('loading');
  });
  
  // Clear summary loading if no summary was generated
  const summaryContent = document.getElementById('summaryContent');
  if (summaryContent && summaryContent.querySelector('.spinner')) {
    summaryContent.innerHTML = '<p style="color: var(--gray-400);">No summary available</p>';
  }
}

function updateConfidenceIndicators(confidence) {
  for (const [field, info] of Object.entries(confidence)) {
    const dot = document.getElementById(`conf-${field}`);
    if (dot) {
      dot.className = `confidence-dot ${info.confidence}`;
      dot.title = `${info.confidence} confidence (${info.source})`;
    }
  }
}

function updateSkillsTags(skills) {
  const container = document.getElementById('skillsContainer');
  container.innerHTML = skills.map(skill => `
    <span class="skill-tag">
      ${skill}
      <span class="remove" data-skill="${skill}">&times;</span>
    </span>
  `).join('');
  
  // Add remove handlers
  container.querySelectorAll('.remove').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const skill = e.target.dataset.skill;
      const idx = extractionState.fields.required_skills?.indexOf(skill);
      if (idx > -1) {
        extractionState.fields.required_skills.splice(idx, 1);
        updateSkillsTags(extractionState.fields.required_skills);
      }
    });
  });
}

function updateSummary(markdown) {
  const container = document.getElementById('summaryContent');
  // Simple markdown to HTML conversion
  let html = markdown
    .replace(/^### (.*$)/gm, '<h3>$1</h3>')
    .replace(/^## (.*$)/gm, '<h2>$1</h2>')
    .replace(/^# (.*$)/gm, '<h1>$1</h1>')
    .replace(/^\*\*(.*)\*\*$/gm, '<strong>$1</strong>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/^\- (.*$)/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>');
  
  container.innerHTML = `<p>${html}</p>`;
  container.classList.remove('loading');
}

function showMessage(text, type = 'info') {
  const box = document.getElementById('messageBox');
  box.textContent = text;
  box.className = `message ${type} show`;
}

function hideMessage() {
  const box = document.getElementById('messageBox');
  box.classList.remove('show');
}

function updateEnvBadge() {
  const badge = document.getElementById('envBadge');
  if (CONFIG.USE_PRODUCTION) {
    badge.style.display = 'none';
  } else {
    badge.textContent = 'LOCAL';
    badge.className = 'env-badge local';
  }
}

// ==========================================================================
// Save Handler
// ==========================================================================

async function handleSave() {
  const saveBtn = document.getElementById('saveBtn');
  saveBtn.disabled = true;
  saveBtn.innerHTML = '<div class="spinner"></div> Saving...';
  
  try {
    // Build job data from form
    const jobData = {
      jobUrl: currentUrl,
      jobTitle: document.getElementById('jobTitle').value || null,
      companyName: document.getElementById('companyName').value || null,
      location: document.getElementById('location').value || null,
      salaryMin: parseInt(document.getElementById('salaryMin').value) || null,
      salaryMax: parseInt(document.getElementById('salaryMax').value) || null,
      salaryCurrency: 'USD',
      remoteType: document.getElementById('remoteType').value || null,
      roleType: document.getElementById('roleType').value || null,
      seniority: document.getElementById('seniority').value || null,
      yearsExperienceMin: parseInt(document.getElementById('yearsExperience').value) || null,
      requiredSkills: extractionState.fields.required_skills || [],
      source: detectSource(currentUrl),
      interestLevel: interestLevel,
      applicationStatus: 'saved',
      notes: document.getElementById('notes').value || null,
      // Include summary for backend to save
      summary: extractionState.summary,
      // Include raw text for any additional processing
      scrapedTextDebug: rawText,
    };
    
    // Save via background script (handles auth)
    const result = await new Promise((resolve, reject) => {
      chrome.runtime.sendMessage({ type: 'SAVE_JOB', jobData }, (response) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
        } else if (response && response.success) {
          resolve(response);
        } else {
          reject(new Error(response?.error || 'Failed to save job'));
        }
      });
    });
    
    // Success - invalidate cache so next check gets fresh data
    await invalidateCache(currentUrl);
    
    saveBtn.classList.remove('btn-primary');
    saveBtn.classList.add('btn-success');
    saveBtn.innerHTML = `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="20,6 9,17 4,12"/>
      </svg>
      Saved!
    `;
    showMessage('Job saved successfully!', 'success');
    
  } catch (error) {
    console.error('Save failed:', error);
    showMessage(`Failed to save: ${error.message}`, 'error');
    saveBtn.disabled = false;
    saveBtn.innerHTML = `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/>
        <polyline points="17,21 17,13 7,13 7,21"/>
        <polyline points="7,3 7,8 15,8"/>
      </svg>
      Save Job
    `;
  }
}
