// Authentication callback handler
// This page receives the token from the API's auth page via URL parameters
(async () => {
  const messageEl = document.querySelector('.message');
  
  try {
    // Get token from URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    const userId = urlParams.get('userId');
    const email = urlParams.get('email');
    
    console.log('Callback received:', { userId, email, hasToken: !!token });
    
    if (token && userId) {
      // Send to background script
      chrome.runtime.sendMessage({
        type: 'AUTH_SUCCESS',
        token: token,
        userId: userId,
        email: email
      }, (response) => {
        if (chrome.runtime.lastError) {
          console.error('Error sending message:', chrome.runtime.lastError);
          messageEl.innerHTML = `
            <p style="color: #ef4444;">Error saving authentication</p>
            <p style="font-size: 12px;">${chrome.runtime.lastError.message}</p>
            <button onclick="window.close()">Close</button>
          `;
          return;
        }
        
        // Success! Show message and close
        messageEl.innerHTML = `
          <p style="color: #10b981; font-size: 18px;">✓ Signed in successfully!</p>
          <p style="font-size: 14px;">${email || userId}</p>
          <p style="font-size: 12px; color: #6b7280;">This tab will close automatically...</p>
        `;
        
        // Close this tab after a short delay
        setTimeout(() => window.close(), 1500);
      });
    } else {
      // No token - show error
      messageEl.innerHTML = `
        <p style="color: #ef4444;">Authentication failed</p>
        <p style="font-size: 12px;">No authentication token received</p>
        <button onclick="window.close()" style="margin-top: 12px; padding: 8px 16px; cursor: pointer;">Close</button>
      `;
    }
    
  } catch (error) {
    console.error('Callback error:', error);
    messageEl.innerHTML = `
      <p style="color: #ef4444;">Authentication error</p>
      <p style="font-size: 12px;">${error.message}</p>
      <button onclick="window.close()" style="margin-top: 12px; padding: 8px 16px; cursor: pointer;">Close</button>
    `;
  }
})();
