# Phase 1: Authentication & Authorization - Setup Guide

## Overview
Phase 1 implements Clerk-based authentication for the Career Attendant application, including:
- User authentication via Clerk
- JWT token validation
- Row-level security for job entries
- Subscription tier enforcement
- Browser extension authentication

## Prerequisites

### 1. Clerk Account Setup
1. Sign up at [clerk.com](https://clerk.com) (free tier available)
2. Create a new application
3. Configure authentication methods:
   - Email/Password
   - Google OAuth (recommended)
   - LinkedIn OAuth (optional, good for job seekers)

### 2. Obtain Clerk Credentials
From your Clerk Dashboard → API Keys:

- **Publishable Key**: `pk_test_xxxxx` (labeled as `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`)
- **Secret Key**: `sk_test_xxxxx` (labeled as `CLERK_SECRET_KEY`)
- **Frontend API URL**: `https://your-subdomain.clerk.accounts.dev`
- **JWKS URL**: `https://your-subdomain.clerk.accounts.dev/.well-known/jwks.json`

Example from your Clerk instance:
- Frontend API: `https://apparent-javelin-61.clerk.accounts.dev`
- JWKS URL: `https://apparent-javelin-61.clerk.accounts.dev/.well-known/jwks.json`

## Environment Configuration

### Backend (API) - Railway Variables

Set these in Railway Dashboard → Variables:

```bash
# Clerk Authentication
CLERK_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxxxxxxx
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxxxxxxxxxx
CLERK_JWKS_URL=https://apparent-javelin-61.clerk.accounts.dev/.well-known/jwks.json

# Frontend/Extension Configuration
FRONTEND_URL=https://your-frontend-domain.com
EXTENSION_ID=your-chrome-extension-id

# Database (auto-configured by Railway)
DATABASE_URL=postgresql://...

# CORS (optional - defaults to *)
CORS_ORIGINS=*
```

### Local Development (.env file)

Create `api/.env` (DO NOT commit this file):

```bash
# Clerk Test Keys
CLERK_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxxxxxxx
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxxxxxxxxxx
CLERK_JWKS_URL=https://apparent-javelin-61.clerk.accounts.dev/.well-known/jwks.json

# Local URLs
FRONTEND_URL=http://localhost:3000
EXTENSION_ID=

# Local Database
DATABASE_URL=postgresql+psycopg://jobaid:jobaidpass@localhost:5432/jobaid

# Development
CORS_ORIGINS=*
DROP_ALL_TABLES=false
```

### Browser Extension Configuration

Update `browser_extension/background.js`:

```javascript
const CONFIG = {
  USE_PRODUCTION: false, // Set to true for production
  PRODUCTION_URL: 'https://careerattendant-production.up.railway.app',
  LOCAL_URL: 'http://localhost:8080',
  CLERK_FRONTEND_API: 'https://your-clerk-subdomain.clerk.accounts.dev',
};
```

## Installation Steps

### 1. Install Backend Dependencies

```bash
cd api
pip install -r requirements.txt
```

New dependencies added:
- `clerk-backend-api==1.0.0` - Clerk SDK
- `python-jose[cryptography]==3.3.0` - JWT handling
- `python-multipart==0.0.6` - Form data support

### 2. Database Migration

The new tables will be created automatically on startup:
- `user_sessions` - Track user sessions
- `feature_access` - Feature gating and usage limits

To manually create tables:

```bash
cd api
python -c "from app.startup import init_db; init_db(drop_all=False)"
```

### 3. Configure Clerk Webhooks

In Clerk Dashboard → Webhooks:

1. Add endpoint: `https://your-api-domain.com/api/auth/webhook/clerk`
2. Subscribe to events:
   - `user.created`
   - `user.updated`
   - `user.deleted`
3. Copy the webhook signing secret (optional, for verification)

### 4. Test the API

Start the API server:

```bash
cd api
uvicorn app.main:app --reload --port 8080
```

Test endpoints:
- Health check: `GET http://localhost:8080/health`
- API docs: `http://localhost:8080/docs`

## Testing Authentication

### 1. Get a Test Token from Clerk

Option A - Use Clerk Dashboard:
1. Go to Users → Create User
2. Copy the user ID
3. Use Clerk's API to generate a session token

Option B - Use the browser extension:
1. Load the extension in Chrome
2. Click "Sign In"
3. Complete authentication
4. Token is stored automatically

### 2. Test API with Token

```bash
# Get current user info
curl -X GET http://localhost:8080/api/auth/me \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Create a job entry
curl -X POST http://localhost:8080/entries \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jobUrl": "https://example.com/job",
    "jobTitle": "Software Engineer",
    "companyName": "Test Company"
  }'

# List user's jobs
curl -X GET http://localhost:8080/entries \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Security Features Implemented

✅ **JWT Token Validation** - All protected endpoints verify Clerk JWT tokens
✅ **Row-Level Security** - Users can only access their own job entries
✅ **Subscription Limits** - Free tier limited to 100 jobs
✅ **CORS Configuration** - Properly configured for frontend and extension
✅ **Session Tracking** - User sessions logged for security auditing
✅ **Feature Gating** - Infrastructure for feature access control

## API Endpoints

### Authentication Routes

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/webhook/clerk` | Clerk webhook handler | No |
| GET | `/api/auth/me` | Get current user info | Yes |
| POST | `/api/auth/validate-session` | Validate session token | No |
| POST | `/api/auth/sync-user` | Sync user from Clerk | Yes |

### Job Entry Routes

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/entries` | Create job entry | Yes |
| GET | `/entries` | List user's jobs | Yes |

## Troubleshooting

### "Missing Clerk Publishable Key" Error
- Ensure `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` is set in environment variables
- Check that the key starts with `pk_test_` or `pk_live_`

### "Invalid token" Error
- Verify `CLERK_JWKS_URL` is correctly set
- Ensure the JWKS URL is accessible (test in browser)
- Check token hasn't expired
- Verify the token's `kid` (key ID) matches a key in the JWKS

### "Not authenticated" Error
- Ensure `Authorization: Bearer TOKEN` header is present
- Verify token is valid using Clerk Dashboard
- Check middleware is not blocking the request

### Database Connection Issues
- Verify `DATABASE_URL` is correct
- Ensure PostgreSQL is running
- Check database credentials

### CORS Errors in Extension
- Add extension ID to `EXTENSION_ID` environment variable
- Verify `CORS_ORIGINS` includes extension protocol
- Check manifest.json has correct host_permissions

## Next Steps

After Phase 1 is complete:

1. **Test thoroughly** - Verify all authentication flows work
2. **Deploy to Railway** - Set production environment variables
3. **Configure production Clerk** - Switch to live keys
4. **Phase 2** - Implement Stripe payment integration

## Development Mode

For development without Clerk configured:

The middleware will skip JWT validation if `CLERK_JWKS_URL` is not set, allowing you to test the API structure. This should **NEVER** be used in production.

## Support

- Clerk Documentation: https://clerk.com/docs
- FastAPI Documentation: https://fastapi.tiangolo.com/
- Project Issues: [GitHub Issues](https://github.com/your-repo/issues)
