# User Management Service - Implementation Specification

## Executive Summary

This document outlines a phased implementation approach for building a robust user management service for a job search automation tool. The system is designed to be cloud-agnostic, starting with Railway but portable to other providers.

**Key Technologies:**
- **Backend:** Python, FastAPI, PostgreSQL
- **Authentication:** Clerk (managed service)
- **Payments:** Stripe Billing
- **Frontend:** React (Web), Chrome Extension, Future iOS

**Timeline:** 4-6 weeks total
- Phase 1: Authentication & Authorization (2-3 weeks)
- Phase 2: Payment Integration (2-3 weeks)

---

## Phase 1: Authentication & Authorization

### 1.1 Overview

**Duration:** 2-3 weeks  
**Objective:** Implement secure user authentication and data authorization

**Key Deliverables:**
- User registration and login (email/password + social logins)
- Session management across Chrome extension and web app
- User profile management
- Row-level security for saved jobs
- API authentication middleware

### 1.2 Setup Requirements

#### 1.2.1 Clerk Account Setup

1. Sign up at [clerk.com](https://clerk.com) (free tier)
2. Create a new application
3. Configure authentication methods:
   - Email/Password
   - Google OAuth
   - LinkedIn OAuth (recommended for job seekers)
   - Magic Links
4. Obtain credentials:
   - `CLERK_PUBLISHABLE_KEY`
   - `CLERK_SECRET_KEY`
   - `CLERK_JWT_KEY`

#### 1.2.2 Environment Configuration

```bash
# .env file
CLERK_PUBLISHABLE_KEY=pk_test_xxxxx
CLERK_SECRET_KEY=sk_test_xxxxx
CLERK_JWT_KEY=-----BEGIN PUBLIC KEY-----xxxxx-----END PUBLIC KEY-----
DATABASE_URL=postgresql://user:pass@localhost/jobsearch
FRONTEND_URL=http://localhost:3000
EXTENSION_ID=your-chrome-extension-id
```

### 1.3 Database Schema

```sql
-- Users table (synced with Clerk)
CREATE TABLE users (
    id VARCHAR(255) PRIMARY KEY, -- Clerk user_id
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100),
    full_name VARCHAR(255),
    subscription_tier VARCHAR(50) DEFAULT 'free',
    subscription_status VARCHAR(50) DEFAULT 'active',
    stripe_customer_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Saved jobs table
CREATE TABLE saved_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_title VARCHAR(500),
    company_name VARCHAR(255),
    job_url TEXT,
    job_description TEXT,
    salary_range VARCHAR(100),
    location VARCHAR(255),
    remote_type VARCHAR(50), -- 'remote', 'hybrid', 'onsite'
    application_status VARCHAR(50) DEFAULT 'saved', -- 'saved', 'applied', 'interviewing', 'rejected', 'offer'
    application_date DATE,
    notes TEXT,
    scraped_data JSONB,
    source VARCHAR(100), -- 'linkedin', 'indeed', 'company_site', etc.
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- User sessions (for tracking)
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(500),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

-- Feature access control
CREATE TABLE feature_access (
    user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    feature_name VARCHAR(100) NOT NULL,
    access_granted BOOLEAN DEFAULT false,
    usage_count INTEGER DEFAULT 0,
    usage_limit INTEGER,
    reset_period VARCHAR(50), -- 'daily', 'weekly', 'monthly'
    last_reset TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, feature_name)
);

-- Indexes for performance
CREATE INDEX idx_saved_jobs_user_id ON saved_jobs(user_id);
CREATE INDEX idx_saved_jobs_status ON saved_jobs(application_status);
CREATE INDEX idx_saved_jobs_created ON saved_jobs(created_at DESC);
CREATE INDEX idx_feature_access_user ON feature_access(user_id);
```

### 1.4 Backend Implementation (FastAPI)

#### 1.4.1 Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── clerk_client.py
│   │   ├── middleware.py
│   │   └── dependencies.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── job.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── users.py
│   │   └── jobs.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   └── job_service.py
│   └── database/
│       ├── __init__.py
│       └── connection.py
├── requirements.txt
└── .env
```

#### 1.4.2 Dependencies

```txt
# requirements.txt
fastapi==0.104.1
uvicorn==0.24.0
python-dotenv==1.0.0
pydantic==2.4.2
sqlalchemy==2.0.23
asyncpg==0.29.0
psycopg2-binary==2.9.9
clerk-backend-api==0.1.0
python-jose[cryptography]==3.3.0
httpx==0.25.0
python-multipart==0.0.6
cors==1.0.1
```

#### 1.4.3 Core Authentication Module

```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    clerk_secret_key: str
    clerk_publishable_key: str
    clerk_jwt_key: str
    database_url: str
    frontend_url: str
    extension_id: str
    
    class Config:
        env_file = ".env"

settings = Settings()
```

```python
# app/auth/clerk_client.py
from clerk_backend_api import Clerk
from typing import Optional
import httpx
from app.config import settings

class ClerkClient:
    def __init__(self):
        self.client = Clerk(bearer_auth=settings.clerk_secret_key)
        
    async def verify_session(self, session_token: str) -> Optional[dict]:
        """Verify a Clerk session token"""
        try:
            response = await self.client.sessions.verify(
                session_id=session_token
            )
            return response.to_dict()
        except Exception as e:
            print(f"Session verification failed: {e}")
            return None
    
    async def get_user(self, user_id: str) -> Optional[dict]:
        """Get user details from Clerk"""
        try:
            user = await self.client.users.get(user_id=user_id)
            return user.to_dict()
        except Exception as e:
            print(f"Failed to get user: {e}")
            return None
    
    async def sync_user_to_db(self, clerk_user: dict, db_session):
        """Sync Clerk user to local database"""
        from app.models.user import User
        
        user = db_session.query(User).filter_by(
            id=clerk_user['id']
        ).first()
        
        if not user:
            user = User(
                id=clerk_user['id'],
                email=clerk_user['email_addresses'][0]['email_address'],
                username=clerk_user.get('username'),
                full_name=f"{clerk_user.get('first_name', '')} {clerk_user.get('last_name', '')}".strip()
            )
            db_session.add(user)
        else:
            user.email = clerk_user['email_addresses'][0]['email_address']
            user.updated_at = datetime.utcnow()
        
        db_session.commit()
        return user

clerk_client = ClerkClient()
```

```python
# app/auth/middleware.py
from fastapi import Request, HTTPException, status
from jose import jwt, JWTError
from app.config import settings
from app.auth.clerk_client import clerk_client
import re

class AuthMiddleware:
    async def __call__(self, request: Request, call_next):
        # Skip auth for public endpoints
        public_paths = ['/docs', '/openapi.json', '/health', '/webhook']
        if any(request.url.path.startswith(path) for path in public_paths):
            return await call_next(request)
        
        # Extract token from header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid authorization header"
            )
        
        token = auth_header.split(' ')[1]
        
        try:
            # Decode and verify JWT
            payload = jwt.decode(
                token,
                settings.clerk_jwt_key,
                algorithms=['RS256'],
                options={"verify_aud": False}
            )
            
            # Add user context to request
            request.state.user_id = payload.get('sub')
            request.state.session_id = payload.get('sid')
            request.state.user_email = payload.get('email')
            
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
        
        response = await call_next(request)
        return response
```

```python
# app/auth/dependencies.py
from fastapi import Depends, HTTPException, Request, status
from typing import Optional

async def get_current_user(request: Request) -> str:
    """Dependency to get current user from request state"""
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user_id

async def check_subscription_tier(
    required_tier: str = "free"
) -> callable:
    """Dependency to check user's subscription tier"""
    async def tier_checker(
        user_id: str = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(404, "User not found")
        
        tier_levels = {"free": 0, "basic": 1, "pro": 2}
        user_level = tier_levels.get(user.subscription_tier, 0)
        required_level = tier_levels.get(required_tier, 0)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires {required_tier} subscription"
            )
        
        return user
    
    return tier_checker
```

#### 1.4.4 API Routes Implementation

```python
# app/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, Request
from app.auth.clerk_client import clerk_client
from app.auth.dependencies import get_current_user
from app.database.connection import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/auth", tags=["authentication"])

@router.post("/webhook/clerk")
async def clerk_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Clerk webhook events (user created, updated, deleted)"""
    payload = await request.json()
    event_type = payload.get('type')
    
    if event_type == 'user.created' or event_type == 'user.updated':
        clerk_user = payload['data']
        await clerk_client.sync_user_to_db(clerk_user, db)
        return {"status": "success"}
    
    elif event_type == 'user.deleted':
        user_id = payload['data']['id']
        user = db.query(User).filter_by(id=user_id).first()
        if user:
            db.delete(user)
            db.commit()
        return {"status": "success"}
    
    return {"status": "ignored"}

@router.get("/me")
async def get_current_user_info(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current authenticated user information"""
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        # Fetch from Clerk and sync
        clerk_user = await clerk_client.get_user(user_id)
        if clerk_user:
            user = await clerk_client.sync_user_to_db(clerk_user, db)
        else:
            raise HTTPException(404, "User not found")
    
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "subscription_tier": user.subscription_tier,
        "created_at": user.created_at
    }

@router.post("/validate-session")
async def validate_session(
    session_token: str,
    db: Session = Depends(get_db)
):
    """Validate a Clerk session token (used by Chrome extension)"""
    session = await clerk_client.verify_session(session_token)
    if not session:
        raise HTTPException(401, "Invalid session")
    
    return {
        "valid": True,
        "user_id": session['user_id'],
        "expires_at": session['expire_at']
    }
```

```python
# app/routes/jobs.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.auth.dependencies import get_current_user, check_subscription_tier
from app.models.job import SavedJob, JobCreate, JobUpdate
from app.services.job_service import JobService
from app.database.connection import get_db
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

@router.get("/", response_model=List[SavedJob])
async def get_user_jobs(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0)
):
    """Get all jobs for the authenticated user"""
    query = db.query(SavedJob).filter_by(user_id=user_id)
    
    if status:
        query = query.filter_by(application_status=status)
    
    jobs = query.order_by(SavedJob.created_at.desc()).offset(offset).limit(limit).all()
    return jobs

@router.post("/", response_model=SavedJob)
async def create_job(
    job_data: JobCreate,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save a new job"""
    # Check job limit for free users
    if user.subscription_tier == "free":
        job_count = db.query(SavedJob).filter_by(user_id=user_id).count()
        if job_count >= 100:
            raise HTTPException(
                403, 
                "Free tier limit reached. Upgrade to Pro for unlimited jobs."
            )
    
    job = SavedJob(
        id=str(uuid.uuid4()),
        user_id=user_id,
        **job_data.dict()
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    return job

@router.put("/{job_id}", response_model=SavedJob)
async def update_job(
    job_id: str,
    job_update: JobUpdate,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a saved job"""
    job = db.query(SavedJob).filter_by(
        id=job_id,
        user_id=user_id  # Ensure user owns this job
    ).first()
    
    if not job:
        raise HTTPException(404, "Job not found")
    
    for field, value in job_update.dict(exclude_unset=True).items():
        setattr(job, field, value)
    
    job.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(job)
    
    return job

@router.delete("/{job_id}")
async def delete_job(
    job_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a saved job"""
    job = db.query(SavedJob).filter_by(
        id=job_id,
        user_id=user_id
    ).first()
    
    if not job:
        raise HTTPException(404, "Job not found")
    
    db.delete(job)
    db.commit()
    
    return {"status": "deleted"}

@router.post("/bulk-import")
async def bulk_import_jobs(
    jobs: List[JobCreate],
    user_id: str = Depends(get_current_user),
    user = Depends(check_subscription_tier("pro")),
    db: Session = Depends(get_db)
):
    """Bulk import jobs (Pro feature)"""
    created_jobs = []
    
    for job_data in jobs[:100]:  # Limit to 100 per request
        job = SavedJob(
            id=str(uuid.uuid4()),
            user_id=user_id,
            **job_data.dict()
        )
        db.add(job)
        created_jobs.append(job)
    
    db.commit()
    
    return {
        "imported": len(created_jobs),
        "jobs": created_jobs
    }
```

### 1.5 Frontend Implementation (React)

#### 1.5.1 Installation

```bash
npm install @clerk/clerk-react axios react-query
```

#### 1.5.2 Clerk Provider Setup

```jsx
// src/App.jsx
import { ClerkProvider, SignedIn, SignedOut, RedirectToSignIn } from '@clerk/clerk-react';
import { BrowserRouter, Route, Routes, useNavigate } from 'react-router-dom';

const clerkPubKey = process.env.REACT_APP_CLERK_PUBLISHABLE_KEY;

function App() {
  const navigate = useNavigate();
  
  return (
    <ClerkProvider 
      publishableKey={clerkPubKey}
      navigate={(to) => navigate(to)}
    >
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route
          path="/dashboard"
          element={
            <>
              <SignedIn>
                <Dashboard />
              </SignedIn>
              <SignedOut>
                <RedirectToSignIn />
              </SignedOut>
            </>
          }
        />
      </Routes>
    </ClerkProvider>
  );
}
```

#### 1.5.3 API Client with Authentication

```javascript
// src/api/client.js
import axios from 'axios';
import { useAuth } from '@clerk/clerk-react';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Hook to get authenticated API client
export const useApiClient = () => {
  const { getToken } = useAuth();
  
  // Add auth token to requests
  apiClient.interceptors.request.use(async (config) => {
    const token = await getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });
  
  return apiClient;
};

// API functions
export const jobsApi = {
  getJobs: async (client, params = {}) => {
    const response = await client.get('/api/jobs', { params });
    return response.data;
  },
  
  createJob: async (client, jobData) => {
    const response = await client.post('/api/jobs', jobData);
    return response.data;
  },
  
  updateJob: async (client, jobId, updates) => {
    const response = await client.put(`/api/jobs/${jobId}`, updates);
    return response.data;
  },
  
  deleteJob: async (client, jobId) => {
    const response = await client.delete(`/api/jobs/${jobId}`);
    return response.data;
  },
};
```

### 1.6 Chrome Extension Integration

#### 1.6.1 Manifest Configuration

```json
{
  "manifest_version": 3,
  "name": "Job Search Assistant",
  "version": "1.0.0",
  "permissions": [
    "storage",
    "tabs",
    "activeTab",
    "identity"
  ],
  "host_permissions": [
    "https://*.linkedin.com/*",
    "https://*.indeed.com/*",
    "https://your-api-domain.com/*"
  ],
  "background": {
    "service_worker": "background.js"
  },
  "content_scripts": [
    {
      "matches": ["https://*.linkedin.com/*", "https://*.indeed.com/*"],
      "js": ["content.js"]
    }
  ],
  "action": {
    "default_popup": "popup.html"
  }
}
```

#### 1.6.2 Extension Authentication

```javascript
// background.js
const CLERK_FRONTEND_API = 'https://your-clerk-domain.clerk.accounts.dev';
const API_BASE_URL = 'https://your-api.com';

// Store session token
let sessionToken = null;

// Listen for authentication from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'AUTHENTICATE') {
    authenticateUser().then(sendResponse);
    return true; // Will respond asynchronously
  }
  
  if (request.type === 'SAVE_JOB') {
    saveJob(request.jobData).then(sendResponse);
    return true;
  }
});

async function authenticateUser() {
  try {
    // Open Clerk auth in new tab
    const authUrl = `${CLERK_FRONTEND_API}/sign-in?redirect_url=${encodeURIComponent(chrome.runtime.getURL('callback.html'))}`;
    
    const authTab = await chrome.tabs.create({ url: authUrl });
    
    // Wait for callback
    return new Promise((resolve) => {
      chrome.tabs.onUpdated.addListener(function listener(tabId, info, tab) {
        if (tabId === authTab.id && tab.url?.includes('callback.html')) {
          // Extract token from URL
          const url = new URL(tab.url);
          const token = url.searchParams.get('session_token');
          
          if (token) {
            sessionToken = token;
            chrome.storage.local.set({ sessionToken: token });
            chrome.tabs.remove(tabId);
            resolve({ success: true });
          }
          
          chrome.tabs.onUpdated.removeListener(listener);
        }
      });
    });
  } catch (error) {
    console.error('Authentication failed:', error);
    return { success: false, error: error.message };
  }
}

async function saveJob(jobData) {
  if (!sessionToken) {
    const stored = await chrome.storage.local.get('sessionToken');
    sessionToken = stored.sessionToken;
    
    if (!sessionToken) {
      return { success: false, error: 'Not authenticated' };
    }
  }
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/jobs`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${sessionToken}`
      },
      body: JSON.stringify(jobData)
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return { success: true, job: data };
  } catch (error) {
    console.error('Failed to save job:', error);
    return { success: false, error: error.message };
  }
}
```

```javascript
// content.js - Scraping logic
function scrapeLinkedInJob() {
  const jobData = {
    job_title: document.querySelector('.job-details-jobs-unified-top-card__job-title')?.textContent?.trim(),
    company_name: document.querySelector('.job-details-jobs-unified-top-card__company-name')?.textContent?.trim(),
    location: document.querySelector('.job-details-jobs-unified-top-card__location')?.textContent?.trim(),
    job_description: document.querySelector('.jobs-description__content')?.innerHTML,
    job_url: window.location.href,
    source: 'linkedin',
    scraped_data: {
      posted_date: document.querySelector('.job-details-jobs-unified-top-card__posted-date')?.textContent?.trim(),
      applicants: document.querySelector('.jobs-unified-top-card__applicant-count')?.textContent?.trim(),
    }
  };
  
  return jobData;
}

// Listen for save button click
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'SCRAPE_JOB') {
    const jobData = scrapeLinkedInJob();
    sendResponse(jobData);
  }
});
```

### 1.7 Testing & Validation

#### 1.7.1 Unit Tests

```python
# tests/test_auth.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import Mock, patch

client = TestClient(app)

@pytest.fixture
def mock_clerk_user():
    return {
        'id': 'user_123',
        'email_addresses': [{'email_address': 'test@example.com'}],
        'username': 'testuser',
        'first_name': 'Test',
        'last_name': 'User'
    }

@pytest.fixture
def auth_headers():
    # Mock JWT token
    return {"Authorization": "Bearer mock_token"}

def test_get_current_user_unauthenticated():
    response = client.get("/api/auth/me")
    assert response.status_code == 401

@patch('app.auth.middleware.jwt.decode')
def test_get_current_user_authenticated(mock_decode, auth_headers):
    mock_decode.return_value = {'sub': 'user_123', 'email': 'test@example.com'}
    
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200

def test_create_job_unauthorized():
    job_data = {"job_title": "Software Engineer"}
    response = client.post("/api/jobs", json=job_data)
    assert response.status_code == 401

@patch('app.auth.middleware.jwt.decode')
def test_job_authorization(mock_decode, auth_headers):
    # Test that users can only access their own jobs
    mock_decode.return_value = {'sub': 'user_123'}
    
    # Create a job
    job_data = {
        "job_title": "Software Engineer",
        "company_name": "Tech Corp"
    }
    response = client.post("/api/jobs", json=job_data, headers=auth_headers)
    assert response.status_code == 200
    job_id = response.json()['id']
    
    # Try to access with different user
    mock_decode.return_value = {'sub': 'different_user'}
    response = client.get(f"/api/jobs/{job_id}", headers=auth_headers)
    assert response.status_code == 404
```

#### 1.7.2 Security Checklist

- [ ] JWT tokens are properly validated
- [ ] API endpoints check user ownership of resources
- [ ] CORS is configured correctly
- [ ] Rate limiting is implemented
- [ ] SQL injection prevention (using ORMs/prepared statements)
- [ ] XSS prevention in stored job descriptions
- [ ] HTTPS enforced in production
- [ ] Secrets stored in environment variables
- [ ] Database connections use SSL
- [ ] User input validation on all endpoints

### 1.8 Deployment (Railway)

```toml
# railway.toml
[build]
builder = "NIXPACKS"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 100
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

[env]
PORT = { variable = "PORT", default = "8000" }
```

```python
# app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.auth.middleware import AuthMiddleware
from app.routes import auth, jobs, users
import uvicorn

app = FastAPI(title="Job Search API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, f"chrome-extension://{settings.extension_id}"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add authentication middleware
app.middleware("http")(AuthMiddleware())

# Include routers
app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(users.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
```

---

## Phase 2: Payment Integration (Stripe)

### 2.1 Overview

**Duration:** 2-3 weeks  
**Objective:** Implement subscription billing with Stripe

**Key Deliverables:**
- Stripe Checkout integration
- Subscription management
- Customer portal
- Webhook handling for subscription events
- Feature gating based on subscription tier
- Usage tracking and limits

### 2.2 Setup Requirements

#### 2.2.1 Stripe Account Setup

1. Create account at [stripe.com](https://stripe.com)
2. Obtain API keys:
   - `STRIPE_PUBLISHABLE_KEY`
   - `STRIPE_SECRET_KEY`
   - `STRIPE_WEBHOOK_SECRET`
3. Configure products and pricing:

```javascript
// Stripe Product Setup (via Dashboard or API)
const products = {
  basic: {
    name: "Basic Plan",
    prices: {
      monthly: "price_basic_monthly", // $9/month
      biannual: "price_basic_biannual", // $48.60 (10% off)
      annual: "price_basic_annual", // $86.40 (20% off)
    }
  },
  pro: {
    name: "Pro Plan",
    prices: {
      monthly: "price_pro_monthly", // $29/month
      biannual: "price_pro_biannual", // $156.60 (10% off)
      annual: "price_pro_annual", // $278.40 (20% off)
      lifetime: "price_pro_lifetime" // $499 one-time
    }
  }
};
```

#### 2.2.2 Environment Updates

```bash
# Additional .env variables
STRIPE_SECRET_KEY=sk_test_xxxxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
STRIPE_BASIC_MONTHLY_PRICE=price_xxxxx
STRIPE_PRO_MONTHLY_PRICE=price_xxxxx
FRONTEND_SUCCESS_URL=http://localhost:3000/success
FRONTEND_CANCEL_URL=http://localhost:3000/pricing
```

### 2.3 Database Schema Updates

```sql
-- Subscription plans table
CREATE TABLE subscription_plans (
    id VARCHAR(100) PRIMARY KEY, -- Stripe price ID
    product_id VARCHAR(100) NOT NULL, -- Stripe product ID
    name VARCHAR(100) NOT NULL,
    tier VARCHAR(50) NOT NULL, -- 'basic', 'pro'
    billing_period VARCHAR(50) NOT NULL, -- 'monthly', 'biannual', 'annual', 'lifetime'
    amount INTEGER NOT NULL, -- in cents
    currency VARCHAR(3) DEFAULT 'usd',
    features JSONB,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- User subscriptions table
CREATE TABLE user_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    stripe_subscription_id VARCHAR(255) UNIQUE,
    stripe_customer_id VARCHAR(255),
    plan_id VARCHAR(100) REFERENCES subscription_plans(id),
    status VARCHAR(50) NOT NULL, -- 'active', 'canceled', 'past_due', 'trialing'
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    cancel_at_period_end BOOLEAN DEFAULT false,
    canceled_at TIMESTAMP,
    trial_start TIMESTAMP,
    trial_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Payment history
CREATE TABLE payment_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    stripe_payment_intent_id VARCHAR(255),
    stripe_invoice_id VARCHAR(255),
    amount INTEGER NOT NULL, -- in cents
    currency VARCHAR(3) DEFAULT 'usd',
    status VARCHAR(50) NOT NULL, -- 'succeeded', 'failed', 'pending'
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Usage tracking
CREATE TABLE usage_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    feature_name VARCHAR(100) NOT NULL,
    usage_date DATE DEFAULT CURRENT_DATE,
    usage_count INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, feature_name, usage_date)
);

-- Indexes
CREATE INDEX idx_user_subscriptions_user ON user_subscriptions(user_id);
CREATE INDEX idx_user_subscriptions_status ON user_subscriptions(status);
CREATE INDEX idx_payment_history_user ON payment_history(user_id);
CREATE INDEX idx_usage_tracking_user_date ON usage_tracking(user_id, usage_date);
```

### 2.4 Backend Implementation

#### 2.4.1 Stripe Service

```python
# app/services/stripe_service.py
import stripe
from app.config import settings
from typing import Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session

stripe.api_key = settings.stripe_secret_key

class StripeService:
    @staticmethod
    async def create_customer(user_email: str, user_id: str) -> Dict:
        """Create a Stripe customer"""
        customer = stripe.Customer.create(
            email=user_email,
            metadata={
                "user_id": user_id
            }
        )
        return customer
    
    @staticmethod
    async def create_checkout_session(
        user_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        customer_id: Optional[str] = None
    ) -> Dict:
        """Create a Stripe Checkout session"""
        session_params = {
            'mode': 'subscription',
            'payment_method_types': ['card'],
            'line_items': [{
                'price': price_id,
                'quantity': 1,
            }],
            'success_url': f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}",
            'cancel_url': cancel_url,
            'metadata': {
                'user_id': user_id
            }
        }
        
        if customer_id:
            session_params['customer'] = customer_id
        else:
            session_params['customer_email'] = user_email
        
        # Add trial period for new users
        if not customer_id:
            session_params['subscription_data'] = {
                'trial_period_days': 7
            }
        
        session = stripe.checkout.Session.create(**session_params)
        return session
    
    @staticmethod
    async def create_customer_portal_session(
        customer_id: str,
        return_url: str
    ) -> Dict:
        """Create a Customer Portal session for subscription management"""
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        return session
    
    @staticmethod
    async def cancel_subscription(subscription_id: str, immediately: bool = False) -> Dict:
        """Cancel a subscription"""
        if immediately:
            subscription = stripe.Subscription.delete(subscription_id)
        else:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
        return subscription
    
    @staticmethod
    async def get_subscription(subscription_id: str) -> Dict:
        """Get subscription details"""
        subscription = stripe.Subscription.retrieve(subscription_id)
        return subscription
    
    @staticmethod
    async def update_subscription(
        subscription_id: str,
        new_price_id: str
    ) -> Dict:
        """Update subscription to a new plan"""
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        stripe.Subscription.modify(
            subscription_id,
            items=[{
                'id': subscription['items']['data'][0].id,
                'price': new_price_id,
            }],
            proration_behavior='create_prorations',
        )
        
        return subscription
```

#### 2.4.2 Subscription Routes

```python
# app/routes/subscriptions.py
from fastapi import APIRouter, Depends, HTTPException, Request
from app.auth.dependencies import get_current_user
from app.services.stripe_service import StripeService
from app.database.connection import get_db
from sqlalchemy.orm import Session
from app.models.user import User, UserSubscription
from typing import Dict

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])

@router.post("/create-checkout-session")
async def create_checkout_session(
    request: Dict,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a Stripe Checkout session for subscription"""
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    # Check if user already has a subscription
    existing_sub = db.query(UserSubscription).filter_by(
        user_id=user_id,
        status__in=['active', 'trialing']
    ).first()
    
    if existing_sub:
        raise HTTPException(400, "User already has an active subscription")
    
    # Create or get Stripe customer
    if not user.stripe_customer_id:
        customer = await StripeService.create_customer(user.email, user.id)
        user.stripe_customer_id = customer['id']
        db.commit()
    
    # Create checkout session
    session = await StripeService.create_checkout_session(
        user_id=user_id,
        price_id=request['price_id'],
        success_url=f"{settings.frontend_url}/subscription/success",
        cancel_url=f"{settings.frontend_url}/pricing",
        customer_id=user.stripe_customer_id
    )
    
    return {
        "checkout_url": session.url,
        "session_id": session.id
    }

@router.post("/create-portal-session")
async def create_portal_session(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a Stripe Customer Portal session"""
    user = db.query(User).filter_by(id=user_id).first()
    
    if not user or not user.stripe_customer_id:
        raise HTTPException(400, "No customer account found")
    
    session = await StripeService.create_customer_portal_session(
        customer_id=user.stripe_customer_id,
        return_url=f"{settings.frontend_url}/account"
    )
    
    return {"portal_url": session.url}

@router.get("/current")
async def get_current_subscription(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's subscription details"""
    subscription = db.query(UserSubscription).filter_by(
        user_id=user_id,
        status__in=['active', 'trialing', 'past_due']
    ).first()
    
    if not subscription:
        return {
            "has_subscription": False,
            "tier": "free"
        }
    
    plan = db.query(SubscriptionPlan).filter_by(
        id=subscription.plan_id
    ).first()
    
    return {
        "has_subscription": True,
        "tier": plan.tier,
        "status": subscription.status,
        "current_period_end": subscription.current_period_end,
        "cancel_at_period_end": subscription.cancel_at_period_end,
        "features": plan.features
    }

@router.post("/cancel")
async def cancel_subscription(
    immediately: bool = False,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel user's subscription"""
    subscription = db.query(UserSubscription).filter_by(
        user_id=user_id,
        status__in=['active', 'trialing']
    ).first()
    
    if not subscription:
        raise HTTPException(404, "No active subscription found")
    
    # Cancel in Stripe
    stripe_sub = await StripeService.cancel_subscription(
        subscription.stripe_subscription_id,
        immediately=immediately
    )
    
    # Update local database
    subscription.cancel_at_period_end = not immediately
    subscription.status = 'canceled' if immediately else subscription.status
    subscription.canceled_at = datetime.utcnow()
    
    if immediately:
        user = db.query(User).filter_by(id=user_id).first()
        user.subscription_tier = 'free'
    
    db.commit()
    
    return {
        "status": "canceled" if immediately else "will_cancel_at_period_end",
        "cancel_at": subscription.current_period_end if not immediately else None
    }
```

#### 2.4.3 Webhook Handler

```python
# app/routes/webhooks.py
from fastapi import APIRouter, Request, HTTPException
import stripe
from app.config import settings
from app.database.connection import get_db
from app.models.user import User, UserSubscription, PaymentHistory
from datetime import datetime

router = APIRouter(prefix="/api/webhook", tags=["webhooks"])

@router.post("/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    payload = await request.body()
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except ValueError:
        raise HTTPException(400, "Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(400, "Invalid signature")
    
    db = next(get_db())
    
    # Handle different event types
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session['metadata']['user_id']
        
        # Create subscription record
        subscription = UserSubscription(
            user_id=user_id,
            stripe_subscription_id=session['subscription'],
            stripe_customer_id=session['customer'],
            status='active'
        )
        db.add(subscription)
        
        # Update user tier
        user = db.query(User).filter_by(id=user_id).first()
        if user:
            user.stripe_customer_id = session['customer']
            user.subscription_tier = 'basic'  # Determine from price_id
        
        db.commit()
    
    elif event['type'] == 'customer.subscription.created':
        subscription = event['data']['object']
        user_id = subscription['metadata'].get('user_id')
        
        if user_id:
            sub_record = UserSubscription(
                user_id=user_id,
                stripe_subscription_id=subscription['id'],
                stripe_customer_id=subscription['customer'],
                plan_id=subscription['items']['data'][0]['price']['id'],
                status=subscription['status'],
                current_period_start=datetime.fromtimestamp(
                    subscription['current_period_start']
                ),
                current_period_end=datetime.fromtimestamp(
                    subscription['current_period_end']
                ),
                trial_start=datetime.fromtimestamp(subscription['trial_start']) 
                    if subscription.get('trial_start') else None,
                trial_end=datetime.fromtimestamp(subscription['trial_end']) 
                    if subscription.get('trial_end') else None,
            )
            db.add(sub_record)
            db.commit()
    
    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        sub_id = subscription['id']
        
        sub_record = db.query(UserSubscription).filter_by(
            stripe_subscription_id=sub_id
        ).first()
        
        if sub_record:
            sub_record.status = subscription['status']
            sub_record.plan_id = subscription['items']['data'][0]['price']['id']
            sub_record.current_period_start = datetime.fromtimestamp(
                subscription['current_period_start']
            )
            sub_record.current_period_end = datetime.fromtimestamp(
                subscription['current_period_end']
            )
            sub_record.cancel_at_period_end = subscription['cancel_at_period_end']
            
            # Update user tier based on plan
            user = db.query(User).filter_by(id=sub_record.user_id).first()
            if user:
                # Determine tier from plan_id
                if 'pro' in sub_record.plan_id:
                    user.subscription_tier = 'pro'
                elif 'basic' in sub_record.plan_id:
                    user.subscription_tier = 'basic'
            
            db.commit()
    
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        sub_id = subscription['id']
        
        sub_record = db.query(UserSubscription).filter_by(
            stripe_subscription_id=sub_id
        ).first()
        
        if sub_record:
            sub_record.status = 'canceled'
            
            # Downgrade user to free tier
            user = db.query(User).filter_by(id=sub_record.user_id).first()
            if user:
                user.subscription_tier = 'free'
            
            db.commit()
    
    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        
        # Record payment
        payment = PaymentHistory(
            user_id=invoice['metadata'].get('user_id'),
            stripe_invoice_id=invoice['id'],
            stripe_payment_intent_id=invoice['payment_intent'],
            amount=invoice['amount_paid'],
            currency=invoice['currency'],
            status='succeeded',
            description=f"Subscription payment for {invoice['period_start']} - {invoice['period_end']}"
        )
        db.add(payment)
        db.commit()
    
    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        
        # Record failed payment
        payment = PaymentHistory(
            user_id=invoice['metadata'].get('user_id'),
            stripe_invoice_id=invoice['id'],
            amount=invoice['amount_due'],
            currency=invoice['currency'],
            status='failed',
            description="Payment failed"
        )
        db.add(payment)
        
        # Update subscription status
        sub_record = db.query(UserSubscription).filter_by(
            stripe_customer_id=invoice['customer']
        ).first()
        
        if sub_record:
            sub_record.status = 'past_due'
        
        db.commit()
    
    return {"status": "success"}
```

### 2.5 Frontend Implementation

#### 2.5.1 Pricing Page Component

```jsx
// src/components/PricingPage.jsx
import React, { useState } from 'react';
import { useAuth } from '@clerk/clerk-react';
import { loadStripe } from '@stripe/stripe-js';
import { useApiClient } from '../api/client';

const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY);

const PricingPage = () => {
  const { isSignedIn } = useAuth();
  const apiClient = useApiClient();
  const [loading, setLoading] = useState(false);
  const [billingPeriod, setBillingPeriod] = useState('monthly');
  
  const plans = {
    basic: {
      name: 'Basic',
      monthly: 9,
      biannual: 48.60,
      annual: 86.40,
      features: [
        'Save up to 100 jobs',
        'Basic search and filters',
        'Application tracking',
        'Email reminders',
        'Chrome extension'
      ],
      priceIds: {
        monthly: process.env.REACT_APP_STRIPE_BASIC_MONTHLY,
        biannual: process.env.REACT_APP_STRIPE_BASIC_BIANNUAL,
        annual: process.env.REACT_APP_STRIPE_BASIC_ANNUAL,
      }
    },
    pro: {
      name: 'Pro',
      monthly: 29,
      biannual: 156.60,
      annual: 278.40,
      lifetime: 499,
      features: [
        'Unlimited job saves',
        'Advanced search and filters',
        'AI-powered insights',
        'Resume tailoring',
        'Automated applications',
        'Priority support',
        'API access',
        'Bulk import/export'
      ],
      priceIds: {
        monthly: process.env.REACT_APP_STRIPE_PRO_MONTHLY,
        biannual: process.env.REACT_APP_STRIPE_PRO_BIANNUAL,
        annual: process.env.REACT_APP_STRIPE_PRO_ANNUAL,
        lifetime: process.env.REACT_APP_STRIPE_PRO_LIFETIME,
      }
    }
  };
  
  const handleSubscribe = async (plan, period) => {
    if (!isSignedIn) {
      // Redirect to sign in
      window.location.href = '/sign-in';
      return;
    }
    
    setLoading(true);
    
    try {
      const response = await apiClient.post('/api/subscriptions/create-checkout-session', {
        price_id: plans[plan].priceIds[period]
      });
      
      // Redirect to Stripe Checkout
      const stripe = await stripePromise;
      await stripe.redirectToCheckout({
        sessionId: response.data.session_id
      });
    } catch (error) {
      console.error('Failed to create checkout session:', error);
      alert('Failed to start checkout. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  const calculateSavings = (plan, period) => {
    if (period === 'monthly') return 0;
    
    const monthlyTotal = plan.monthly * (period === 'biannual' ? 6 : 12);
    const periodPrice = plan[period];
    const savings = monthlyTotal - periodPrice;
    const percent = Math.round((savings / monthlyTotal) * 100);
    
    return { amount: savings, percent };
  };
  
  return (
    <div className="pricing-container">
      <h1>Choose Your Plan</h1>
      
      <div className="billing-toggle">
        <button 
          onClick={() => setBillingPeriod('monthly')}
          className={billingPeriod === 'monthly' ? 'active' : ''}
        >
          Monthly
        </button>
        <button 
          onClick={() => setBillingPeriod('biannual')}
          className={billingPeriod === 'biannual' ? 'active' : ''}
        >
          6 Months
          <span className="badge">Save 10%</span>
        </button>
        <button 
          onClick={() => setBillingPeriod('annual')}
          className={billingPeriod === 'annual' ? 'active' : ''}
        >
          Annual
          <span className="badge">Save 20%</span>
        </button>
      </div>
      
      <div className="pricing-cards">
        {/* Free Tier */}
        <div className="pricing-card free">
          <h2>Free</h2>
          <div className="price">
            <span className="amount">$0</span>
            <span className="period">forever</span>
          </div>
          <ul className="features">
            <li>Save up to 10 jobs</li>
            <li>Basic search</li>
            <li>Chrome extension</li>
          </ul>
          <button className="btn-secondary" disabled>
            Current Plan
          </button>
        </div>
        
        {/* Basic Plan */}
        <div className="pricing-card basic">
          <h2>{plans.basic.name}</h2>
          <div className="price">
            <span className="amount">${plans.basic[billingPeriod]}</span>
            <span className="period">
              {billingPeriod === 'monthly' ? '/month' : `/${billingPeriod}`}
            </span>
          </div>
          {billingPeriod !== 'monthly' && (
            <div className="savings">
              Save ${calculateSavings(plans.basic, billingPeriod).amount}
            </div>
          )}
          <ul className="features">
            {plans.basic.features.map((feature, idx) => (
              <li key={idx}>{feature}</li>
            ))}
          </ul>
          <button 
            className="btn-primary"
            onClick={() => handleSubscribe('basic', billingPeriod)}
            disabled={loading}
          >
            {loading ? 'Loading...' : 'Start 7-Day Free Trial'}
          </button>
        </div>
        
        {/* Pro Plan */}
        <div className="pricing-card pro recommended">
          <div className="badge">Most Popular</div>
          <h2>{plans.pro.name}</h2>
          <div className="price">
            <span className="amount">${plans.pro[billingPeriod]}</span>
            <span className="period">
              {billingPeriod === 'monthly' ? '/month' : `/${billingPeriod}`}
            </span>
          </div>
          {billingPeriod !== 'monthly' && (
            <div className="savings">
              Save ${calculateSavings(plans.pro, billingPeriod).amount}
            </div>
          )}
          <ul className="features">
            {plans.pro.features.map((feature, idx) => (
              <li key={idx}>{feature}</li>
            ))}
          </ul>
          <button 
            className="btn-primary"
            onClick={() => handleSubscribe('pro', billingPeriod)}
            disabled={loading}
          >
            {loading ? 'Loading...' : 'Start 7-Day Free Trial'}
          </button>
          
          {/* Lifetime option */}
          <div className="lifetime-option">
            <p>Or get lifetime access for just $499</p>
            <button 
              className="btn-secondary"
              onClick={() => handleSubscribe('pro', 'lifetime')}
            >
              Get Lifetime Access
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PricingPage;
```

#### 2.5.2 Subscription Management

```jsx
// src/components/SubscriptionManager.jsx
import React, { useState, useEffect } from 'react';
import { useApiClient } from '../api/client';

const SubscriptionManager = () => {
  const apiClient = useApiClient();
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    fetchSubscription();
  }, []);
  
  const fetchSubscription = async () => {
    try {
      const response = await apiClient.get('/api/subscriptions/current');
      setSubscription(response.data);
    } catch (error) {
      console.error('Failed to fetch subscription:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleManageSubscription = async () => {
    try {
      const response = await apiClient.post('/api/subscriptions/create-portal-session');
      window.location.href = response.data.portal_url;
    } catch (error) {
      console.error('Failed to open customer portal:', error);
    }
  };
  
  const handleCancelSubscription = async () => {
    if (!confirm('Are you sure you want to cancel your subscription?')) {
      return;
    }
    
    try {
      await apiClient.post('/api/subscriptions/cancel');
      alert('Subscription will be canceled at the end of the current billing period.');
      fetchSubscription();
    } catch (error) {
      console.error('Failed to cancel subscription:', error);
    }
  };
  
  if (loading) return <div>Loading...</div>;
  
  if (!subscription.has_subscription) {
    return (
      <div className="subscription-status">
        <h3>Free Plan</h3>
        <p>You're currently on the free plan.</p>
        <a href="/pricing" className="btn-primary">
          Upgrade Your Plan
        </a>
      </div>
    );
  }
  
  return (
    <div className="subscription-manager">
      <h3>Your Subscription</h3>
      
      <div className="subscription-details">
        <div className="plan-info">
          <span className="label">Plan:</span>
          <span className="value">{subscription.tier}</span>
        </div>
        
        <div className="status-info">
          <span className="label">Status:</span>
          <span className={`value status-${subscription.status}`}>
            {subscription.status}
          </span>
        </div>
        
        <div className="period-info">
          <span className="label">Next billing date:</span>
          <span className="value">
            {new Date(subscription.current_period_end).toLocaleDateString()}
          </span>
        </div>
        
        {subscription.cancel_at_period_end && (
          <div className="cancel-notice">
            Your subscription will end on {new Date(subscription.current_period_end).toLocaleDateString()}
          </div>
        )}
      </div>
      
      <div className="subscription-actions">
        <button 
          className="btn-primary"
          onClick={handleManageSubscription}
        >
          Manage Subscription
        </button>
        
        {!subscription.cancel_at_period_end && (
          <button 
            className="btn-secondary"
            onClick={handleCancelSubscription}
          >
            Cancel Subscription
          </button>
        )}
      </div>
      
      {subscription.features && (
        <div className="current-features">
          <h4>Your Features:</h4>
          <ul>
            {Object.entries(subscription.features).map(([key, value]) => (
              <li key={key}>
                {key}: {typeof value === 'boolean' ? (value ? '✓' : '✗') : value}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default SubscriptionManager;
```

### 2.6 Feature Gating Implementation

```python
# app/services/feature_service.py
from typing import Dict, Optional
from sqlalchemy.orm import Session
from app.models.user import User, FeatureAccess
from datetime import datetime, timedelta

class FeatureService:
    # Feature definitions
    FEATURES = {
        'free': {
            'max_saved_jobs': 10,
            'basic_search': True,
            'export_csv': False,
            'ai_insights': False,
            'automation': False,
            'api_access': False,
        },
        'basic': {
            'max_saved_jobs': 100,
            'basic_search': True,
            'export_csv': True,
            'ai_insights': False,
            'automation': False,
            'api_access': False,
        },
        'pro': {
            'max_saved_jobs': -1,  # Unlimited
            'basic_search': True,
            'advanced_search': True,
            'export_csv': True,
            'ai_insights': True,
            'automation': True,
            'api_access': True,
            'ai_chat_messages': 100,  # per day
        }
    }
    
    @classmethod
    def check_feature_access(
        cls, 
        user: User, 
        feature: str, 
        db: Session
    ) -> Dict:
        """Check if user has access to a feature"""
        tier_features = cls.FEATURES.get(user.subscription_tier, cls.FEATURES['free'])
        
        # Check if feature exists in tier
        if feature not in tier_features:
            return {'allowed': False, 'reason': 'Feature not available'}
        
        feature_value = tier_features[feature]
        
        # Boolean features
        if isinstance(feature_value, bool):
            return {'allowed': feature_value, 'reason': None if feature_value else 'Upgrade required'}
        
        # Numeric limits
        if isinstance(feature_value, int):
            if feature_value == -1:  # Unlimited
                return {'allowed': True, 'limit': None, 'used': 0}
            
            # Check usage
            usage = cls.get_feature_usage(user.id, feature, db)
            return {
                'allowed': usage < feature_value,
                'limit': feature_value,
                'used': usage,
                'reason': f'Limit reached ({usage}/{feature_value})' if usage >= feature_value else None
            }
        
        return {'allowed': False, 'reason': 'Unknown feature type'}
    
    @classmethod
    def get_feature_usage(
        cls,
        user_id: str,
        feature: str,
        db: Session,
        period: str = 'daily'
    ) -> int:
        """Get current usage for a feature"""
        # Determine time range
        if period == 'daily':
            start_date = datetime.utcnow().date()
        elif period == 'monthly':
            start_date = datetime.utcnow().replace(day=1).date()
        else:
            start_date = datetime.utcnow().date()
        
        usage_record = db.query(UsageTracking).filter_by(
            user_id=user_id,
            feature_name=feature,
            usage_date=start_date
        ).first()
        
        return usage_record.usage_count if usage_record else 0
    
    @classmethod
    def increment_usage(
        cls,
        user_id: str,
        feature: str,
        db: Session,
        amount: int = 1
    ):
        """Increment feature usage counter"""
        today = datetime.utcnow().date()
        
        usage_record = db.query(UsageTracking).filter_by(
            user_id=user_id,
            feature_name=feature,
            usage_date=today
        ).first()
        
        if usage_record:
            usage_record.usage_count += amount
        else:
            usage_record = UsageTracking(
                user_id=user_id,
                feature_name=feature,
                usage_date=today,
                usage_count=amount
            )
            db.add(usage_record)
        
        db.commit()
```

### 2.7 Testing & Monitoring

#### 2.7.1 Stripe Testing

```python
# tests/test_subscriptions.py
import pytest
from unittest.mock import Mock, patch
import stripe

@pytest.fixture
def mock_stripe():
    with patch('app.services.stripe_service.stripe') as mock:
        yield mock

def test_create_checkout_session(mock_stripe):
    # Mock Stripe response
    mock_session = Mock()
    mock_session.url = 'https://checkout.stripe.com/test'
    mock_session.id = 'cs_test_123'
    mock_stripe.checkout.Session.create.return_value = mock_session
    
    # Test checkout session creation
    response = client.post(
        '/api/subscriptions/create-checkout-session',
        json={'price_id': 'price_test_123'},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert 'checkout_url' in response.json()

def test_webhook_subscription_created(mock_stripe):
    # Simulate webhook event
    event_data = {
        'type': 'customer.subscription.created',
        'data': {
            'object': {
                'id': 'sub_test_123',
                'customer': 'cus_test_123',
                'status': 'active',
                'items': {
                    'data': [{
                        'price': {'id': 'price_test_123'}
                    }]
                },
                'current_period_start': 1234567890,
                'current_period_end': 1234567890,
                'metadata': {'user_id': 'user_123'}
            }
        }
    }
    
    with patch('stripe.Webhook.construct_event') as mock_construct:
        mock_construct.return_value = event_data
        
        response = client.post(
            '/api/webhook/stripe',
            data=json.dumps(event_data),
            headers={'Stripe-Signature': 'test_sig'}
        )
        
        assert response.status_code == 200
        
        # Verify subscription was created in database
        # Add database verification here
```

### 2.8 Deployment Configuration

```yaml
# docker-compose.yml for local development
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: jobsearch
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  stripe-cli:
    image: stripe/stripe-cli
    command: listen --forward-to http://backend:8000/api/webhook/stripe
    environment:
      STRIPE_API_KEY: ${STRIPE_SECRET_KEY}
    depends_on:
      - backend

  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:password@db/jobsearch
      REDIS_URL: redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./app:/app

volumes:
  postgres_data:
```

## Appendix A: Security Best Practices

1. **API Security**
   - Rate limiting per user/IP
   - Request signing for sensitive operations
   - Input validation on all endpoints
   - SQL injection prevention via ORMs

2. **Authentication**
   - JWT token expiration (15 minutes)
   - Refresh token rotation
   - Session invalidation on password change
   - MFA support (via Clerk)

3. **Payment Security**
   - Never store card details
   - Use Stripe's PCI-compliant infrastructure
   - Verify webhook signatures
   - Implement idempotency keys

4. **Data Protection**
   - Encrypt sensitive data at rest
   - Use HTTPS everywhere
   - Implement CORS properly
   - Regular security audits

## Appendix B: Monitoring & Analytics

```python
# app/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Define metrics
api_requests = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])
api_latency = Histogram('api_request_duration_seconds', 'API request latency')
active_subscriptions = Gauge('active_subscriptions', 'Number of active subscriptions', ['tier'])
failed_payments = Counter('failed_payments_total', 'Total failed payments')

# Usage example
@app.middleware("http")
async def track_metrics(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    api_requests.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    api_latency.observe(duration)
    
    return response
```

## Appendix C: Migration Guide

### Moving from Clerk to Self-Hosted Auth

1. Export user data from Clerk
2. Implement JWT generation
3. Build password reset flow
4. Add social OAuth providers
5. Migrate user sessions
6. Update frontend auth logic

### Scaling Considerations

- Database: Consider read replicas at 1000+ users
- Caching: Implement Redis for session storage
- CDN: Use for static assets
- Background jobs: Add Celery for async tasks
- Search: Consider Elasticsearch for job search

---

## Support & Resources

- **Clerk Documentation**: https://clerk.com/docs
- **Stripe Documentation**: https://stripe.com/docs
- **FastAPI Documentation**: https://fastapi.tiangolo.com
- **Railway Documentation**: https://docs.railway.app

## Version History

- **v1.0.0** - Initial implementation specification
- **v1.1.0** - Added webhook handling and usage tracking
- **v1.2.0** - Enhanced security and monitoring sections

---

*Last Updated: 2024*
