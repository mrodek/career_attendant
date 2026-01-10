# ADR 001: Browser Extension Authentication Strategy

## Status
Accepted

## Context

The Career Attendant browser extension requires authentication to save jobs and interact with the API. We initially implemented authentication using Clerk's JWT tokens directly, which led to frequent authentication failures.

### Problem Statement
- Browser extensions cannot use Clerk's JavaScript SDK directly (no DOM access in service workers)
- Clerk JWTs expire after 60 seconds by default (security best practice)
- Users were experiencing "session expired" errors with every interaction
- The extension was storing short-lived JWTs and attempting to reuse them

### Initial Approach (Problematic)
1. User signs in via Clerk auth page
2. Extension receives and stores Clerk JWT token
3. Extension uses JWT for all API requests
4. JWT expires after 60 seconds
5. All subsequent requests fail with 401 Unauthorized

### Root Cause Analysis
The fundamental issue was architectural:
- **Clerk JWTs are designed for verification, not session management**
- **Browser extensions need long-lived authentication tokens**
- **Storing and reusing short-lived JWTs is an anti-pattern**

## Decision

We will implement a **two-phase authentication system**:

### Phase 1: Immediate Fix (Implemented)
Implement automatic token refresh as a temporary workaround:
- When a request fails with 401, automatically open auth page in background tab
- Extract fresh JWT from callback URL
- Retry the failed request with fresh token
- Also implemented JWKS caching with TTL to handle Clerk key rotation

**Status:** ✅ Implemented and working

**Limitations:**
- Opens background tabs (poor UX)
- Not industry standard
- Relies on browser tab APIs
- Token visible in URL during callback
- Resource intensive

### Phase 2: Proper Solution (Implementing Now)
Implement server-side session token management:
- Use Clerk JWT for initial authentication only (one-time verification)
- Create long-lived session tokens on the server (7 days)
- Store session tokens in database using existing `UserSession` model
- Extension uses session tokens for all API requests
- Server validates session tokens via simple database lookup

**Status:** 🚧 In Progress

## Consequences

### Phase 1 (Temporary Workaround)

**Positive:**
- ✅ Fixes immediate authentication failures
- ✅ Users can use the extension without constant re-authentication
- ✅ JWKS caching improves reliability when Clerk rotates keys
- ✅ Buys time to implement proper solution

**Negative:**
- ⚠️ Non-standard approach (opens background tabs)
- ⚠️ Potential browser compatibility issues
- ⚠️ Token exposed in URL during callback
- ⚠️ Unnecessary resource usage (loading auth page repeatedly)
- ⚠️ Maintenance burden

**Risks:**
- Browser popup blockers may interfere
- Future Chrome API changes could break the mechanism
- Race conditions in tab lifecycle events

### Phase 2 (Proper Solution)

**Positive:**
- ✅ Industry-standard approach (used by GitHub, Google, Slack)
- ✅ Better security (server-side token validation, revocation support)
- ✅ Better performance (simple DB lookup vs page load)
- ✅ Better UX (no background tabs)
- ✅ More control (configurable expiration, session management)
- ✅ Easier to maintain and debug

**Negative:**
- ⚠️ Requires migration effort (estimated 1-2 hours)
- ⚠️ Need to handle session expiration after 7 days
- ⚠️ Additional database queries for session validation

**Migration Complexity:** Low
- Database model (`UserSession`) already exists
- Minimal code changes required
- Backward compatible during transition

## Implementation Details

### Phase 2: Session Tokens

**API Changes:**

1. **New endpoint: `/api/auth/create-session`**
   - Validates Clerk JWT (one-time)
   - Creates session token
   - Stores in database with 7-day expiration
   - Returns session token to extension

2. **Updated middleware**
   - Supports both JWT and session token validation
   - Session tokens validated via database lookup
   - Backward compatible with existing JWT flow

3. **Session management**
   - Automatic cleanup of expired sessions
   - Support for session revocation
   - Track session metadata (IP, user agent)

**Extension Changes:**

1. **Sign-in flow**
   - Authenticate with Clerk (one-time)
   - Exchange JWT for session token
   - Store session token locally

2. **API requests**
   - Use session token for all requests
   - No refresh needed (valid for 7 days)
   - Handle session expiration gracefully

## Alternatives Considered

### Alternative 1: Store Clerk Session ID
**Approach:** Store Clerk's session ID and call Clerk API to get fresh JWTs
**Rejected because:**
- Requires Clerk API calls for every request (latency)
- Adds external dependency for critical path
- Clerk API rate limits could cause issues
- More complex error handling

### Alternative 2: Use Chrome Identity API
**Approach:** Implement OAuth2 flow using `chrome.identity.launchWebAuthFlow`
**Rejected because:**
- Requires OAuth2 provider configuration
- More complex setup
- Clerk doesn't provide standard OAuth2 endpoints for this use case
- Overkill for current needs

### Alternative 3: Cookie-Based Authentication
**Approach:** Use HTTP-only cookies for authentication
**Rejected because:**
- Browser extensions have limited cookie access from service workers
- CORS complications with extension origin
- Less control over token lifecycle

### Alternative 4: Keep Current Approach Permanently
**Approach:** Accept the background tab workaround as the solution
**Rejected because:**
- Non-standard and fragile
- Poor user experience
- Maintenance burden
- Security concerns (token in URL)

## References

- [Clerk JWT Documentation](https://clerk.com/docs/backend-requests/handling/manual-jwt)
- [Chrome Extension Authentication Best Practices](https://developer.chrome.com/docs/extensions/mv3/security/)
- [OAuth 2.0 for Browser-Based Apps](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-browser-based-apps)
- Related Code:
  - `api/app/auth/middleware.py` - JWKS caching and JWT validation
  - `api/app/models.py` - UserSession model (lines 162-173)
  - `browser_extension/background.js` - Token refresh logic
  - `api/app/routers/auth_page.py` - Clerk authentication page

## Migration Plan

### Timeline
- **Phase 1:** ✅ Completed (2026-01-10) - Auto-refresh workaround
- **Phase 2:** 🚧 In Progress (2026-01-10) - Session token migration

### Migration Steps
1. ✅ Create ADR documenting decision
2. 🚧 Implement `/api/auth/create-session` endpoint
3. 🚧 Update middleware to support session token validation
4. 🚧 Update extension to use session tokens
5. 📋 Deploy and test
6. 📋 Monitor metrics (session duration, auth failures)
7. 📋 Remove auto-refresh workaround code after validation

### Rollback Plan
If Phase 2 migration encounters issues:
- Middleware supports both JWT and session tokens (backward compatible)
- Can disable session token validation via feature flag
- Falls back to JWT validation (Phase 1 behavior)
- No data loss (UserSession table remains)

## Notes

- The `UserSession` model already exists in the database, making migration straightforward
- Current JWKS caching improvements (Phase 1) are valuable regardless and should be kept
- Session tokens will be hashed before storage (using SHA-256)
- Will implement session cleanup for expired sessions
- Future enhancement: Session revocation endpoint for "sign out all devices"

## Decision Makers
- Martin Rodek (Developer)
- Cascade AI (Technical Advisor)

## Date
2026-01-10

## Review Date
2026-02-10 (or after Phase 2 implementation)
