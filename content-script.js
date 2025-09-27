// content/content.js
(async () => {
  const MESSAGE_TYPES = {
    // Auth messages
    CHECK_AUTH: 'CHECK_AUTH',
    LOGIN: 'LOGIN',
    LOGOUT: 'LOGOUT',
    AUTH_CHANGED: 'AUTH_CHANGED',

    // Crypto messages
    ENCRYPT_CELL: 'ENCRYPT_CELL',
    DECRYPT_CELL: 'DECRYPT_CELL',
    GENERATE_KEY: 'GENERATE_KEY',

    // Drive messages
    SAVE_TO_DRIVE: 'SAVE_TO_DRIVE',
    READ_FROM_DRIVE: 'READ_FROM_DRIVE',

    // Sheets messages
    SHEET_DETECTED: 'SHEET_DETECTED',
    CELL_CHANGED: 'CELL_CHANGED',
    GET_SHEET_INFO: 'GET_SHEET_INFO',
    CREATE_ENCRYPTED_SHEET: 'CREATE_ENCRYPTED_SHEET',
  };

  class AuthGuard {
    constructor() {
      this.isAuthenticated = false;
      this.currentUser = null;
      this.authOverlay = null;
      this.authCallbacks = [];
      this.checkInterval = null;
      this.retryCount = 0;
      this.maxRetries = 3;

      // Setup message listener for auth changes
      this.setupMessageListener();
    }

    // AUTHENTICATION STATUS
    async checkAuth() {
      try {
        Logger.log('AuthGuard', 'Checking authentication status');

        const response = await MessageHelper.sendToBackground({
          type: MESSAGE_TYPES.CHECK_AUTH
        });

        this.isAuthenticated = response.authenticated;
        this.currentUser = response.user;
        this.retryCount = 0; // Reset on successful check
        if (this.isAuthenticated) {
          Logger.log('AuthGuard', `User authenticated: ${this.currentUser.email}`);
          this.hideAuthRequired();
        } else {
          Logger.log('AuthGuard', 'User not authenticated');
        }

        // Notify callbacks
        this.notifyAuthCallbacks(this.isAuthenticated);

        return this.isAuthenticated;

      } catch (error) {
        Logger.error('AuthGuard', 'Auth check failed', error);

        // Handle retries
        this.retryCount++;
        if (this.retryCount <= this.maxRetries) {
          Logger.log('AuthGuard', `Retrying auth check (${this.retryCount}/${this.maxRetries})`);
          setTimeout(() => this.checkAuth(), 2000);
        } else {
          this.showAuthError('Unable to verify authentication. Please refresh the page.');
        }

        return false;
      }
    }

    async login() {
      try {
        Logger.log('AuthGuard', 'Initiating login');
        this.showAuthLoading('Signing in...');

        const response = await MessageHelper.sendToBackground({
          type: MESSAGE_TYPES.LOGIN
        });

        if (response.success) {
          this.isAuthenticated = true;
          this.currentUser = response.user;

          Logger.log('AuthGuard', `Login successful: ${this.currentUser.email}`);
          this.hideAuthRequired();
          this.notifyAuthCallbacks(true);

          return true;
        } else {
          throw new Error(response.error || 'Login failed');
        }

      } catch (error) {
        Logger.error('AuthGuard', 'Login failed', error);
        this.showAuthError(`Login failed: ${error.message}`);
        return false;
      }
    }

    async logout() {
      try {
        Logger.log('AuthGuard', 'Initiating logout');

        const response = await MessageHelper.sendToBackground({
          type: MESSAGE_TYPES.LOGOUT
        });

        if (response.success) {
          this.isAuthenticated = false;
          this.currentUser = null;

          Logger.log('AuthGuard', 'Logout successful');
          this.showAuthRequired();
          this.notifyAuthCallbacks(false);

          return true;
        } else {
          throw new Error(response.error || 'Logout failed');
        }

      } catch (error) {
        Logger.error('AuthGuard', 'Logout failed', error);
        return false;
      }
    }

    // MESSAGE HANDLING
    setupMessageListener() {
      chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
        if (message.type === MESSAGE_TYPES.AUTH_CHANGED) {
          this.handleAuthChange(message.authenticated, message.user);
        }
      });
    }

    handleAuthChange(authenticated, user) {
      Logger.log('AuthGuard', `Auth change received: ${authenticated ? 'logged in' : 'logged out'}`);

      const wasAuthenticated = this.isAuthenticated;
      this.isAuthenticated = authenticated;
      this.currentUser = user;

      if (authenticated && !wasAuthenticated) {
        // User just logged in
        this.hideAuthRequired();
      } else if (!authenticated && wasAuthenticated) {
        // User just logged out
        this.showAuthRequired();
      }

      this.notifyAuthCallbacks(authenticated);
    }

    // AUTH OVERLAY UI
    showAuthRequired() {
      if (this.authOverlay) {
        // Update existing overlay instead of creating new one
        this.updateAuthOverlay('login');
        return;
      }

      Logger.log('AuthGuard', 'Showing authentication required overlay');

      this.authOverlay = document.createElement('div');
      this.authOverlay.id = 'e2ee-auth-overlay';
      this.authOverlay.innerHTML = this.getAuthOverlayHTML();

      document.documentElement.appendChild(this.authOverlay);

      // Setup event handlers
      this.setupAuthOverlayEvents();

      // Add entrance animation
      setTimeout(() => {
        this.authOverlay.classList.add('visible');
      }, 100);
    }

    hideAuthRequired() {
      if (!this.authOverlay) return;

      Logger.log('AuthGuard', 'Hiding authentication overlay');

      this.authOverlay.classList.add('hiding');

      setTimeout(() => {
        if (this.authOverlay) {
          this.authOverlay.remove();
          this.authOverlay = null;
        }
      }, 300);
    }

    showAuthLoading(message = 'Loading...') {
      this.updateAuthOverlay('loading', message);
    }

    showAuthError(errorMessage) {
      this.updateAuthOverlay('error', errorMessage);

      // Auto-hide error after 5 seconds and show login again
      setTimeout(() => {
        if (this.authOverlay && !this.isAuthenticated) {
          this.updateAuthOverlay('login');
        }
      }, 5000);
    }

    updateAuthOverlay(state, message = '') {
      if (!this.authOverlay) return;

      const content = this.authOverlay.querySelector('.auth-content');
      if (!content) return;

      switch (state) {
        case 'login':
          content.innerHTML = this.getLoginContentHTML();
          this.setupAuthOverlayEvents();
          break;

        case 'loading':
          content.innerHTML = this.getLoadingContentHTML(message);
          break;

        case 'error':
          content.innerHTML = this.getErrorContentHTML(message);
          break;
      }
    }

    // HTML TEMPLATES
    getAuthOverlayHTML() {
      return `
        <style>
          #e2ee-auth-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.85);
            backdrop-filter: blur(8px);
            z-index: 999999;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Google Sans', Roboto, Arial, sans-serif;
            opacity: 0;
            transition: all 0.3s ease;
          }

          #e2ee-auth-overlay.visible {
            opacity: 1;
          }

          #e2ee-auth-overlay.hiding {
            opacity: 0;
            transform: scale(0.95);
          }

          .auth-modal {
            background: white;
            border-radius: 16px;
            box-shadow: 0 24px 48px rgba(0, 0, 0, 0.3);
            padding: 0;
            max-width: 400px;
            width: 90%;
            max-height: 80vh;
            overflow: hidden;
            transform: scale(0.9);
            transition: transform 0.3s ease;
          }

          #e2ee-auth-overlay.visible .auth-modal {
            transform: scale(1);
          }

          .auth-header {
            background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%);
            color: white;
            padding: 24px;
            text-align: center;
          }

          .auth-header h2 {
            margin: 0 0 8px 0;
            font-size: 24px;
            font-weight: 500;
          }

          .auth-header p {
            margin: 0;
            opacity: 0.9;
            font-size: 14px;
          }

          .auth-content {
            padding: 32px 24px;
            text-align: center;
          }

          .auth-icon {
            font-size: 48px;
            margin-bottom: 16px;
          }

          .auth-title {
            font-size: 20px;
            font-weight: 500;
            margin: 0 0 8px 0;
            color: #1f1f1f;
          }

          .auth-description {
            color: #5f6368;
            margin: 0 0 24px 0;
            line-height: 1.4;
          }

          .auth-button {
            background: #1976d2;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            text-decoration: none;
            min-width: 200px;
            justify-content: center;
          }

          .auth-button:hover {
            background: #1565c0;
            box-shadow: 0 4px 12px rgba(25, 118, 210, 0.3);
            transform: translateY(-1px);
          }

          .auth-button:active {
            transform: translateY(0);
          }

          .auth-button.secondary {
            background: transparent;
            color: #1976d2;
            border: 1px solid #dadce0;
          }

          .auth-button.secondary:hover {
            background: #f8f9fa;
            box-shadow: none;
          }

          .auth-button:disabled {
            background: #f1f3f4;
            color: #9aa0a6;
            cursor: not-allowed;
            transform: none;
          }

          .auth-spinner {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid #ffffff33;
            border-left: 2px solid #ffffff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
          }

          .auth-error {
            background: #fce8e6;
            color: #d93025;
            border: 1px solid #fce8e6;
            border-radius: 8px;
            padding: 12px;
            margin: 16px 0;
            font-size: 14px;
          }

          .auth-features {
            margin: 24px 0;
            text-align: left;
          }

          .auth-feature {
            display: flex;
            align-items: center;
            gap: 12px;
            margin: 12px 0;
            color: #5f6368;
            font-size: 14px;
          }

          .auth-feature-icon {
            width: 20px;
            height: 20px;
            background: #e8f0fe;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            flex-shrink: 0;
          }

          .auth-footer {
            background: #f8f9fa;
            padding: 16px 24px;
            text-align: center;
            font-size: 12px;
            color: #5f6368;
            border-top: 1px solid #e8eaed;
          }

          .auth-footer a {
            color: #1976d2;
            text-decoration: none;
          }

          .auth-footer a:hover {
            text-decoration: underline;
          }

          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        </style>

        <div class="auth-modal">
          <div class="auth-header">
            <h2>🔐 E2EE Google Sheets</h2>
            <p>End-to-End Encrypted Spreadsheets</p>
          </div>
          
          <div class="auth-content">
            ${this.getLoginContentHTML()}
          </div>
          
          <div class="auth-footer">
            Your data is encrypted locally before being saved to Google Drive.<br>
            <a href="#" id="learn-more-link">Learn more about E2EE</a>
          </div>
        </div>
      `;
    }

    getLoginContentHTML() {
      return `
        <div class="auth-icon">🔒</div>
        <h3 class="auth-title">Authentication Required</h3>
        <p class="auth-description">
          Sign in with your Google account to access end-to-end encrypted spreadsheet features.
        </p>
        
        <div class="auth-features">
          <div class="auth-feature">
            <div class="auth-feature-icon">🔐</div>
            <span>Military-grade encryption for your data</span>
          </div>
          <div class="auth-feature">
            <div class="auth-feature-icon">👥</div>
            <span>Secure collaboration with team members</span>
          </div>
          <div class="auth-feature">
            <div class="auth-feature-icon">☁️</div>
            <span>Seamlessly integrates with Google Sheets</span>
          </div>
        </div>
        
        <button id="auth-login-btn" class="auth-button">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Sign in with Google
        </button>
        
        <button id="auth-refresh-btn" class="auth-button secondary" style="margin-top: 12px;">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/>
          </svg>
          Refresh Status
        </button>
      `;
    }

    getLoadingContentHTML(message) {
      return `
        <div class="auth-icon">⏳</div>
        <h3 class="auth-title">${message}</h3>
        <p class="auth-description">Please wait while we verify your authentication...</p>
        
        <div class="auth-spinner"></div>
      `;
    }

    getErrorContentHTML(errorMessage) {
      return `
        <div class="auth-icon">❌</div>
        <h3 class="auth-title">Authentication Failed</h3>
        
        <div class="auth-error">
          ${errorMessage}
        </div>
        
        <button id="auth-retry-btn" class="auth-button">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/>
          </svg>
          Try Again
        </button>
      `;
    }

    // EVENT HANDLING
    setupAuthOverlayEvents() {
      // Login button
      const loginBtn = this.authOverlay?.querySelector('#auth-login-btn');
      if (loginBtn) {
        loginBtn.onclick = () => this.login();
      }

      // Refresh button
      const refreshBtn = this.authOverlay?.querySelector('#auth-refresh-btn');
      if (refreshBtn) {
        refreshBtn.onclick = () => this.checkAuth();
      }

      // Retry button
      const retryBtn = this.authOverlay?.querySelector('#auth-retry-btn');
      if (retryBtn) {
        retryBtn.onclick = () => this.login();
      }

      // Learn more link
      const learnMoreLink = this.authOverlay?.querySelector('#learn-more-link');
      if (learnMoreLink) {
        learnMoreLink.onclick = (e) => {
          e.preventDefault();
          this.showLearnMore();
        };
      }

      // Keyboard shortcuts
      const handleKeydown = (e) => {
        if (!this.authOverlay || this.isAuthenticated) return;

        switch (e.key) {
          case 'Enter':
            e.preventDefault();
            this.login();
            break;
          case 'Escape':
            e.preventDefault();
            // Don't close auth overlay, but could minimize it
            break;
          case 'F5':
            e.preventDefault();
            this.checkAuth();
            break;
        }
      };

      document.addEventListener('keydown', handleKeydown);

      // Store reference to remove later
      this.authKeydownHandler = handleKeydown;
    }

    showLearnMore() {
      const content = this.authOverlay?.querySelector('.auth-content');
      if (!content) return;

      content.innerHTML = `
        <div class="auth-icon">📚</div>
        <h3 class="auth-title">About E2EE Sheets</h3>
        
        <div style="text-align: left; margin: 20px 0;">
          <p><strong>End-to-End Encryption (E2EE)</strong> means your data is encrypted on your device before being sent to Google Drive. Even Google cannot read your spreadsheet content.</p>
          
          <p><strong>How it works:</strong></p>
          <ul style="margin: 10px 0; padding-left: 20px;">
            <li>Each spreadsheet gets a unique encryption key</li>
            <li>Your data is encrypted locally in your browser</li>
            <li>Only users with permission can decrypt the data</li>
            <li>Google sees only encrypted, unreadable data</li>
          </ul>
          
          <p><strong>Security features:</strong></p>
          <ul style="margin: 10px 0; padding-left: 20px;">
            <li>AES-256 encryption (military-grade)</li>
            <li>RSA key exchange for sharing</li>
            <li>Automatic key rotation</li>
            <li>Zero-knowledge architecture</li>
          </ul>
        </div>
        
        <button id="auth-back-btn" class="auth-button secondary">
          ← Back to Sign In
        </button>
      `;

      // Setup back button
      const backBtn = this.authOverlay.querySelector('#auth-back-btn');
      if (backBtn) {
        backBtn.onclick = () => {
          this.updateAuthOverlay('login');
        };
      }
    }

    // CALLBACK SYSTEM
    onAuthChange(callback) {
      if (typeof callback === 'function') {
        this.authCallbacks.push(callback);
      }

      // Return unsubscribe function
      return () => {
        const index = this.authCallbacks.indexOf(callback);
        if (index > -1) {
          this.authCallbacks.splice(index, 1);
        }
      };
    }

    notifyAuthCallbacks(authenticated) {
      this.authCallbacks.forEach(callback => {
        try {
          callback(authenticated, this.currentUser);
        } catch (error) {
          Logger.error('AuthGuard', 'Callback error', error);
        }
      });
    }

    // PERIODIC CHECKS
    startPeriodicCheck(intervalMs = 60000) {
      this.stopPeriodicCheck();

      Logger.log('AuthGuard', `Starting periodic auth check (${intervalMs}ms)`);

      this.checkInterval = setInterval(() => {
        // Only check if currently authenticated
        // Avoid spam when user is logged out
        if (this.isAuthenticated) {
          this.checkAuth();
        }
      }, intervalMs);
    }

    stopPeriodicCheck() {
      if (this.checkInterval) {
        clearInterval(this.checkInterval);
        this.checkInterval = null;
        Logger.log('AuthGuard', 'Stopped periodic auth check');
      }
    }

    // UTILITY METHODS
    requireAuth() {
      if (!this.isAuthenticated) {
        throw new Error('Authentication required');
      }
    }

    getCurrentUser() {
      this.requireAuth();
      return this.currentUser;
    }

    getUserEmail() {
      return this.currentUser?.email || null;
    }

    getUserId() {
      return this.currentUser?.id || null;
    }

    hasValidAuth() {
      return this.isAuthenticated && this.currentUser && this.currentUser.email;
    }

    // CLEANUP
    destroy() {
      Logger.log('AuthGuard', 'Destroying AuthGuard');

      // Stop periodic checks
      this.stopPeriodicCheck();

      // Remove auth overlay
      this.hideAuthRequired();

      // Remove keyboard handler
      if (this.authKeydownHandler) {
        document.removeEventListener('keydown', this.authKeydownHandler);
      }

      // Clear callbacks
      this.authCallbacks = [];

      // Reset state
      this.isAuthenticated = false;
      this.currentUser = null;
    }
  }
  class Logger {
    static log(component, message, data = null) {
      const timestamp = new Date().toISOString();
      console.log(`[${timestamp}] [${component}] ${message}`, data || '');
    }

    static error(component, message, error = null) {
      const timestamp = new Date().toISOString();
      console.error(`[${timestamp}] [${component}] ERROR: ${message}`, error || '');
    }
  }
  class MessageHelper {
    static async sendToBackground(message) {
      return new Promise((resolve, reject) => {
        chrome.runtime.sendMessage(message, (response) => {
          if (chrome.runtime.lastError) {
            reject(new Error(chrome.runtime.lastError.message));
          } else {
            resolve(response);
          }
        });
      });
    }

    static async sendToTab(tabId, message) {
      return new Promise((resolve, reject) => {
        chrome.tabs.sendMessage(tabId, message, (response) => {
          if (chrome.runtime.lastError) {
            reject(new Error(chrome.runtime.lastError.message));
          } else {
            resolve(response);
          }
        });
      });
    }
  }

  class OverlayManager {
    constructor() {
      this.overlay = null;
    }
    showOverlay(state) {
      if (this.overlay) {
        // Update existing overlay instead of creating new one
        this.updateAuthOverlay(state);
        return;
      }

      Logger.log('OverlayManager', `Showing ${state} required overlay`);

      this.overlay = document.createElement('div');
      this.overlay.id = 'e2ee-overlay';
      this.overlay.innerHTML = this.getOverlayHTML(state);

      document.documentElement.appendChild(this.overlay);

      // Setup event handlers
      this.setupOverlayEvents();

      // Add entrance animation
      setTimeout(() => {
        this.overlay.classList.add('visible');
      }, 100);
    }

    hideOverlay() {
      if (!this.overlay) return;

      Logger.log('OverlayManager', 'Hiding overlay');

      this.overlay.classList.add('hiding');

      setTimeout(() => {
        if (this.overlay) {
          this.overlay.remove();
          this.overlay = null;
        }
      }, 300);
    }

    updateContentOverlay(state, message = '') {
      if (!this.overlay) return;

      const content = this.overlay.querySelector('.auth-content');
      if (!content) return;

      switch (state) {
        // case 'login':
        //   content.innerHTML = this.getLoginContentHTML();
        //   this.setupAuthOverlayEvents();
        //   break;

        // case 'loading':
        //   content.innerHTML = this.getLoadingContentHTML(message);
        //   break;

        // case 'error':
        //   content.innerHTML = this.getErrorContentHTML(message);
        //   break;
      }
    }

    // HTML TEMPLATES
    getOverlayHTML(state) {
      return `
        <style>
          #e2ee-auth-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.85);
            backdrop-filter: blur(8px);
            z-index: 999999;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Google Sans', Roboto, Arial, sans-serif;
            opacity: 0;
            transition: all 0.3s ease;
          }

          #e2ee-auth-overlay.visible {
            opacity: 1;
          }

          #e2ee-auth-overlay.hiding {
            opacity: 0;
            transform: scale(0.95);
          }

          .auth-modal {
            background: white;
            border-radius: 16px;
            box-shadow: 0 24px 48px rgba(0, 0, 0, 0.3);
            padding: 0;
            max-width: 400px;
            width: 90%;
            max-height: 80vh;
            overflow: hidden;
            transform: scale(0.9);
            transition: transform 0.3s ease;
          }

          #e2ee-auth-overlay.visible .auth-modal {
            transform: scale(1);
          }

          .auth-header {
            background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%);
            color: white;
            padding: 24px;
            text-align: center;
          }

          .auth-header h2 {
            margin: 0 0 8px 0;
            font-size: 24px;
            font-weight: 500;
          }

          .auth-header p {
            margin: 0;
            opacity: 0.9;
            font-size: 14px;
          }

          .auth-content {
            padding: 32px 24px;
            text-align: center;
          }

          .auth-icon {
            font-size: 48px;
            margin-bottom: 16px;
          }

          .auth-title {
            font-size: 20px;
            font-weight: 500;
            margin: 0 0 8px 0;
            color: #1f1f1f;
          }

          .auth-description {
            color: #5f6368;
            margin: 0 0 24px 0;
            line-height: 1.4;
          }

          .auth-button {
            background: #1976d2;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            text-decoration: none;
            min-width: 200px;
            justify-content: center;
          }

          .auth-button:hover {
            background: #1565c0;
            box-shadow: 0 4px 12px rgba(25, 118, 210, 0.3);
            transform: translateY(-1px);
          }

          .auth-button:active {
            transform: translateY(0);
          }

          .auth-button.secondary {
            background: transparent;
            color: #1976d2;
            border: 1px solid #dadce0;
          }

          .auth-button.secondary:hover {
            background: #f8f9fa;
            box-shadow: none;
          }

          .auth-button:disabled {
            background: #f1f3f4;
            color: #9aa0a6;
            cursor: not-allowed;
            transform: none;
          }

          .auth-spinner {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid #ffffff33;
            border-left: 2px solid #ffffff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
          }

          .auth-error {
            background: #fce8e6;
            color: #d93025;
            border: 1px solid #fce8e6;
            border-radius: 8px;
            padding: 12px;
            margin: 16px 0;
            font-size: 14px;
          }

          .auth-features {
            margin: 24px 0;
            text-align: left;
          }

          .auth-feature {
            display: flex;
            align-items: center;
            gap: 12px;
            margin: 12px 0;
            color: #5f6368;
            font-size: 14px;
          }

          .auth-feature-icon {
            width: 20px;
            height: 20px;
            background: #e8f0fe;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            flex-shrink: 0;
          }

          .auth-footer {
            background: #f8f9fa;
            padding: 16px 24px;
            text-align: center;
            font-size: 12px;
            color: #5f6368;
            border-top: 1px solid #e8eaed;
          }

          .auth-footer a {
            color: #1976d2;
            text-decoration: none;
          }

          .auth-footer a:hover {
            text-decoration: underline;
          }

          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        </style>

        <div class="auth-modal">
          <div class="auth-header">
            <h2>🔐 E2EE Google Sheets</h2>
            <p>End-to-End Encrypted Spreadsheets</p>
          </div>
          
          <div class="auth-content">
            ${this.getContentHTML(state)}
          </div>
          
          <div class="auth-footer">
            Your data is encrypted locally before being saved to Google Sheets.<br>
            <a href="#" id="learn-more-link">Learn more about E2EE</a>
          </div>
        </div>
      `;
    }

    getContentHTML(state) {
      switch (state) {
        case "confirm-encrypt-sheet":
          return `
            <p class="auth-description">
              Your sheet is not encrypted yet. Do you want to encrypt right now? Your data will be encrypted and only user that has authorization can view true data.
            </p>
            <button id="confirm-encrypt-btn" class="auth-button">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              Encrypt Data.
            </button>
          `
        default:
          break;
      }
    }

    // EVENT HANDLING
    setupOverlayEvents() {
      // Login button
      const confirmEncryptBtn = this.authOverlay?.querySelector('#confirm-encrypt-btn');
      if (confirmEncryptBtn) {
        confirmEncryptBtn.onclick = async () => {
          await MessageHelper.sendToBackground({
            type: MESSAGE_TYPES.CREATE_ENCRYPTED_SHEET,
            sheetId: this.sheetId
          }, (res => {
            console.log(res)
            // if (res.code === 2001) {
            //   this.isSheetEncrypted = false
            //   this.overlayManager.showOverlay("confirm-encrypt-sheet")
            // } else {
            //   this.isSheetEncrypted = true
            // }
          }));
        };
      }

      // Keyboard shortcuts
      const handleKeydown = (e) => {
        if (!this.authOverlay || this.isAuthenticated) return;

        switch (e.key) {
          case 'Enter':
            e.preventDefault();
            this.login();
            break;
          case 'Escape':
            e.preventDefault();
            // Don't close auth overlay, but could minimize it
            break;
          case 'F5':
            e.preventDefault();
            this.checkAuth();
            break;
        }
      };

      document.addEventListener('keydown', handleKeydown);

      // Store reference to remove later
      this.authKeydownHandler = handleKeydown;
    }
  }

  class SheetManager {
    constructor(authManager, overlayManager) {
      this.authManager = authManager;
      this.overlayManager = overlayManager;
      this.sheetId = null;
      this.isSheetEncrypted = null
    }

    async sendSheetIdToBackground() {
      this.sheetId = window.location.href.match(/spreadsheets\/d\/([a-zA-Z0-9-_]+)/)?.[1];
      await MessageHelper.sendToBackground({
        type: MESSAGE_TYPES.GET_SHEET_INFO,
        sheetId: this.sheetId
      }, (res => {
        if (res.code === 2001) {
          this.isSheetEncrypted = false
          this.overlayManager.updateContentOverlay("confirm-encrypt-sheet")
        } else {
          this.isSheetEncrypted = true
        }
      }));
    }
  }

  Logger.log('ContentScript', 'Initializing E2EE extension');

  const authGuard = new AuthGuard();
  const overlayManager = new OverlayManager();
  const sheetManager = new SheetManager(authGuard, overlayManager);

  // Check authentication
  const isAuthenticated = await authGuard.checkAuth();

  if (isAuthenticated) {
    Logger.log('ContentScript', 'User is authenticated, initializing features');
    sheetManager.sendSheetIdToBackground()
    // TODO: Initialize overlay manager
  } else {
    Logger.log('ContentScript', 'User not authenticated, showing auth overlay');
    authGuard.showAuthRequired();
  }

  // Listen for auth changes
  authGuard.onAuthChange((authenticated, user) => {
    if (authenticated) {
      Logger.log('ContentScript', `User logged in: ${user.email}`);
      sheetManager.sendSheetIdToBackground()
      // TODO: Initialize E2EE features
    } else {
      Logger.log('ContentScript', 'User logged out');
      // TODO: Cleanup E2EE features
    }
  });
})();