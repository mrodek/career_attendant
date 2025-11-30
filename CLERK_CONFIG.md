# Clerk Configuration Reference

## Your Clerk Instance Details

### API Keys
```bash
# Backend (Railway/API)
CLERK_SECRET_KEY=<your-secret-key>
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=<your-publishable-key>
CLERK_JWKS_URL=https://apparent-javelin-61.clerk.accounts.dev/.well-known/jwks.json

# Frontend (if you build a React app later)
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=<your-publishable-key>
```

### URLs
- **Frontend API URL**: `https://apparent-javelin-61.clerk.accounts.dev`
- **Backend API URL**: `https://api.clerk.com`
- **JWKS URL**: `https://apparent-javelin-61.clerk.accounts.dev/.well-known/jwks.json`

## Quick Setup Checklist

### Railway Environment Variables
Set these in Railway Dashboard → Your Project → Variables:

- [ ] `CLERK_SECRET_KEY` - Your secret key (starts with `sk_`)
- [ ] `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` - Your publishable key (starts with `pk_`)
- [ ] `CLERK_JWKS_URL` - `https://apparent-javelin-61.clerk.accounts.dev/.well-known/jwks.json`
- [ ] `FRONTEND_URL` - Your frontend URL (if you have one)
- [ ] `EXTENSION_ID` - Your Chrome extension ID (after publishing)

### Browser Extension
Update `browser_extension/background.js`:
```javascript
const CONFIG = {
  CLERK_FRONTEND_API: 'https://apparent-javelin-61.clerk.accounts.dev',
  // ... other config
};
```

### Local Development
Create `api/.env`:
```bash
CLERK_SECRET_KEY=sk_test_xxxxx
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_xxxxx
CLERK_JWKS_URL=https://apparent-javelin-61.clerk.accounts.dev/.well-known/jwks.json
DATABASE_URL=postgresql+psycopg://jobaid:jobaidpass@localhost:5432/jobaid
FRONTEND_URL=http://localhost:3000
CORS_ORIGINS=*
```

## Testing the Configuration

### 1. Test JWKS Endpoint
Open in browser:
```
https://apparent-javelin-61.clerk.accounts.dev/.well-known/jwks.json
```
You should see a JSON response with public keys.

### 2. Test API Health
```bash
curl http://localhost:8080/health
```
Should return: `{"status": "ok"}`

### 3. Test Authentication (after getting a token)
```bash
curl -X GET http://localhost:8080/api/auth/me \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## How JWT Verification Works

1. User authenticates with Clerk (via extension or web app)
2. Clerk issues a JWT token
3. Extension/app sends token in `Authorization: Bearer <token>` header
4. API middleware:
   - Extracts the token
   - Gets the key ID (`kid`) from token header
   - Fetches public keys from JWKS URL
   - Finds matching key by `kid`
   - Verifies token signature using public key
   - Extracts user info from token payload

## Clerk Dashboard Links

- **Dashboard**: https://dashboard.clerk.com
- **API Keys**: https://dashboard.clerk.com/last-active?path=api-keys
- **Webhooks**: https://dashboard.clerk.com/last-active?path=webhooks
- **Users**: https://dashboard.clerk.com/last-active?path=users

## Webhook Configuration

When ready to set up webhooks:

1. Go to Clerk Dashboard → Webhooks
2. Add endpoint: `https://your-api-domain.railway.app/api/auth/webhook/clerk`
3. Subscribe to events:
   - `user.created`
   - `user.updated`
   - `user.deleted`
4. Save the webhook signing secret (optional, for verification)

## Security Notes

- ✅ Never commit `.env` files
- ✅ Use test keys (`sk_test_`, `pk_test_`) for development
- ✅ Use live keys (`sk_live_`, `pk_live_`) for production only
- ✅ JWKS keys are public (safe to expose)
- ✅ Secret key must remain private (server-side only)
- ✅ Publishable key is safe for client-side use

## Common Issues

### Token Verification Fails
- Check JWKS URL is accessible
- Verify token hasn't expired
- Ensure token's `kid` matches a key in JWKS
- Check for clock skew between servers

### "Unable to fetch JWKS keys"
- Verify JWKS URL is correct
- Check network connectivity from API server
- Ensure no firewall blocking the request

### Extension Can't Authenticate
- Verify `CLERK_FRONTEND_API` in `background.js`
- Check manifest.json has correct host_permissions
- Ensure callback.html is included in extension

## Next Steps

1. Get your actual keys from Clerk Dashboard
2. Set environment variables in Railway
3. Update browser extension with your Clerk subdomain
4. Test authentication flow end-to-end
5. Configure webhooks for user sync
