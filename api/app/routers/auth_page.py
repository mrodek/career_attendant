from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from ..config import Settings

settings = Settings()

router = APIRouter(tags=["auth-page"])

@router.get("/auth/callback", response_class=HTMLResponse)
async def auth_callback_page(token: str = None, userId: str = None, email: str = None):
    """
    Callback page after successful Clerk sign-in.
    Extension's background script watches for this URL and extracts the token.
    """
    if token and userId:
        # Success - extension will pick this up
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Signed In - Career Attendant</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            text-align: center;
        }}
        h1 {{ color: #10b981; margin: 0 0 12px 0; }}
        p {{ color: #6b7280; margin: 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>✓ Signed In!</h1>
        <p>Welcome, {email or userId}</p>
        <p style="margin-top: 16px; font-size: 14px;">This tab will close automatically...</p>
    </div>
</body>
</html>
"""
    else:
        # Error
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>Auth Error - Career Attendant</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            background: #fef2f2;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 12px;
            text-align: center;
        }
        h1 { color: #ef4444; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Authentication Failed</h1>
        <p>No token received. Please try again.</p>
        <button onclick="window.close()">Close</button>
    </div>
</body>
</html>
"""
    return HTMLResponse(content=html)

@router.get("/auth/login", response_class=HTMLResponse)
async def auth_login_page(request: Request, extension_id: str = None):
    """
    Serve a login page that uses Clerk JS SDK.
    After sign-in, redirects to /auth/callback with token (extension watches for this).
    """
    
    # Build callback URL - redirect to our own API callback page
    # Extension's background script will watch for this URL and extract the token
    base_url = str(request.base_url).rstrip('/')
    callback_url = f"{base_url}/auth/callback"
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sign In - Career Attendant</title>
    <style>
        * {{
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            text-align: center;
            max-width: 400px;
            width: 90%;
        }}
        h1 {{
            margin: 0 0 8px 0;
            color: #1f2937;
            font-size: 24px;
        }}
        p {{
            color: #6b7280;
            margin: 0 0 24px 0;
        }}
        .spinner {{
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        .error {{
            color: #ef4444;
            padding: 12px;
            background: #fef2f2;
            border-radius: 6px;
            margin-top: 16px;
        }}
        .success {{
            color: #059669;
            padding: 12px;
            background: #ecfdf5;
            border-radius: 6px;
            margin-top: 16px;
        }}
        #clerk-container {{
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Career Attendant</h1>
        <p>Sign in to save and track your job applications</p>
        
        <div id="loading">
            <div class="spinner"></div>
            <p>Loading...</p>
        </div>
        
        <div id="clerk-container"></div>
        
        <div id="status"></div>
    </div>

    <script
        async
        crossorigin="anonymous"
        data-clerk-publishable-key="{settings.clerk_publishable_key}"
        src="https://cdn.jsdelivr.net/npm/@clerk/clerk-js@5/dist/clerk.browser.js"
        type="text/javascript"
    ></script>
    <script>
        const CALLBACK_URL = '{callback_url}';
        
        // Wait for Clerk to be ready
        window.addEventListener('load', async () => {{
            const loadingEl = document.getElementById('loading');
            const statusEl = document.getElementById('status');
            const containerEl = document.getElementById('clerk-container');
            
            try {{
                // Wait for Clerk to initialize (it auto-initializes with data-clerk-publishable-key)
                await window.Clerk.load();
                
                loadingEl.style.display = 'none';
                
                const clerk = window.Clerk;
                
                // Check if already signed in
                if (clerk.user) {{
                    statusEl.innerHTML = '<div class="success">Already signed in! Getting token...</div>';
                    
                    // Get JWT token
                    const token = await clerk.session.getToken();
                    const userId = clerk.user.id;
                    const email = clerk.user.primaryEmailAddress?.emailAddress || '';
                    
                    // Redirect to callback page with token (extension watches for this URL)
                    const redirectUrl = `${{CALLBACK_URL}}?token=${{encodeURIComponent(token)}}&userId=${{encodeURIComponent(userId)}}&email=${{encodeURIComponent(email)}}`;
                    console.log('Redirecting to:', redirectUrl);
                    statusEl.innerHTML = '<div class="success">Signed in! Redirecting...</div>';
                    window.location.href = redirectUrl;
                }} else {{
                    // Show sign-in UI
                    clerk.mountSignIn(containerEl, {{
                        afterSignInUrl: window.location.href,
                        afterSignUpUrl: window.location.href
                    }});
                }}
                
            }} catch (error) {{
                console.error('Clerk error:', error);
                loadingEl.style.display = 'none';
                statusEl.innerHTML = `<div class="error">Error: ${{error.message}}</div>`;
            }}
        }})();
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html_content)
