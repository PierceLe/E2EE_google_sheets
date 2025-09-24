// import { AuthManager } from './auth-manager.js';
// import { CryptoManager } from './crypto-manager.js';
// // import { DriveManager } from './drive-manager.js';
// import { MessageRouter } from './message-router.js';
// import { Logger } from './utils.js';

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
  CELL_CHANGED: 'CELL_CHANGED'
};

const STORAGE_KEYS = {
  AUTH_USER: 'authUser',
  AUTH_TOKEN: 'authToken',
  SHEET_KEYS: 'sheetKeys',
  USER_PREFERENCES: 'userPrefs'
};

const GOOGLE_APIS = {
  USER_INFO: 'https://openidconnect.googleapis.com/v1/userinfo',
  DRIVE_FILES: 'https://www.googleapis.com/drive/v3/files',
  SHEETS_API: 'https://sheets.googleapis.com/v4/spreadsheets'
};

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

class StorageHelper {
  static async get(keys) {
    return new Promise((resolve) => {
      chrome.storage.local.get(keys, resolve);
    });
  }

  static async set(data) {
    return new Promise((resolve) => {
      chrome.storage.local.set(data, resolve);
    });
  }

  static async remove(keys) {
    return new Promise((resolve) => {
      chrome.storage.local.remove(keys, resolve);
    });
  }
}

class AuthManager {
  constructor() {
    this.currentUser = null;
    this.authToken = null;
  }

  async initialize() {
    Logger.log('AuthManager', 'Initializing...');
    await this.loadStoredAuth();
  }

  async loadStoredAuth() {
    try {
      const stored = await StorageHelper.get([STORAGE_KEYS.AUTH_USER, STORAGE_KEYS.AUTH_TOKEN]);

      if (stored.authUser && stored.authToken) {
        const isValid = await this.verifyToken(stored.authToken);

        if (isValid) {
          this.currentUser = stored.authUser;
          this.authToken = stored.authToken;
          Logger.log('AuthManager', 'Auth restored from storage');
          return true;
        } else {
          await this.clearStoredAuth();
        }
      }
    } catch (error) {
      Logger.error('AuthManager', 'Failed to load stored auth', error);
    }

    return false;
  }

  async login() {
    try {
      Logger.log('AuthManager', 'Starting login process');

      const token = await this.getGoogleAuthToken();
      const userProfile = await this.fetchUserProfile(token);
      const idToken = await this.getIDToken()
      await StorageHelper.set({
        [STORAGE_KEYS.AUTH_USER]: userProfile,
        [STORAGE_KEYS.AUTH_TOKEN]: token
      });


      this.currentUser = userProfile;
      this.authToken = token;

      Logger.log('AuthManager', 'Login successful', userProfile.email);
      this.notifyAuthChange(true);

      return { success: true, user: userProfile };
    } catch (error) {
      Logger.error('AuthManager', 'Login failed', error);
      return { success: false, error: error.message };
    }
  }

  async logout() {
    try {
      if (this.authToken) {
        await this.revokeToken(this.authToken);
      }

      await this.clearStoredAuth();
      this.currentUser = null;
      this.authToken = null;

      Logger.log('AuthManager', 'Logout successful');
      this.notifyAuthChange(false);

      return { success: true };
    } catch (error) {
      Logger.error('AuthManager', 'Logout failed', error);
      return { success: false, error: error.message };
    }
  }

  async getGoogleAuthToken() {
    return new Promise((resolve, reject) => {
      chrome.identity.getAuthToken({ interactive: false }, (oldToken) => {
        if (oldToken) {
          chrome.identity.removeCachedAuthToken({ token: oldToken }, () => {
            console.log("Old token removed");
            chrome.identity.getAuthToken({ interactive: true }, (token) => {
              if (chrome.runtime.lastError) {
                reject(new Error(chrome.runtime.lastError.message));
              } else if (!token) {
                reject(new Error('No token received'));
              } else {
                resolve(token);
              }
            });
            // requestNewToken(resolve, reject);
          });
        } else {
          // requestNewToken(resolve, reject);
          chrome.identity.getAuthToken({ interactive: true }, (token) => {
            if (chrome.runtime.lastError) {
              reject(new Error(chrome.runtime.lastError.message));
            } else if (!token) {
              reject(new Error('No token received'));
            } else {
              resolve(token);
            }
          });
        }
      })
    });
  }

  async fetchUserProfile(token) {
    const response = await fetch(GOOGLE_APIS.USER_INFO, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!response.ok) {
      throw new Error('Failed to fetch user profile');
    }

    return await response.json();
  }

  async verifyToken(token) {
    try {
      const response = await fetch(
        `https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=${token}`
      );
      return response.ok;
    } catch {
      return false;
    }
  }

  async revokeToken(token) {
    const response = await fetch(
      `https://oauth2.googleapis.com/revoke?token=${token}`,
      { method: 'POST' }
    );

    if (!response.ok) {
      throw new Error('Failed to revoke token');
    }
  }

  async clearStoredAuth() {
    await StorageHelper.remove([STORAGE_KEYS.AUTH_USER, STORAGE_KEYS.AUTH_TOKEN]);
  }

  notifyAuthChange(authenticated) {
    chrome.tabs.query({}, (tabs) => {
      tabs.forEach(tab => {
        if (tab.url?.includes('docs.google.com/spreadsheets')) {
          chrome.tabs.sendMessage(tab.id, {
            type: MESSAGE_TYPES.AUTH_CHANGED,
            authenticated,
            user: this.currentUser
          }).catch(() => {
            // Tab might not have content script
          });
        }
      });
    });
  }

  isAuthenticated() {
    return !!(this.currentUser && this.authToken);
  }

  getCurrentUser() {
    return this.currentUser;
  }

  getAuthToken() {
    return this.authToken;
  }

  getIDToken() {
    const CLIENT_ID = "455306255228-m8pa01lvc4iop133el6rsfdkvgks9ho5.apps.googleusercontent.com"
    const REDIRECT_URI = "https://bfpbflebkfbcamehejajfikegbmpajib.chromiumapp.org/"
    const authUrl = `https://accounts.google.com/o/oauth2/v2/auth` +
      `?client_id=${encodeURIComponent(CLIENT_ID)}` +
      `&redirect_uri=${encodeURIComponent(REDIRECT_URI)}` +
      `&response_type=id_token` +           // trả về id_token (JWT) trực tiếp
      `&scope=${encodeURIComponent('openid email profile')}` +
      `&nonce=${encodeURIComponent(Math.random().toString(36).slice(2))}`;

    chrome.identity.launchWebAuthFlow({ url: authUrl, interactive: true }, (redirectUrl) => {
      if (chrome.runtime.lastError) {
        console.error(chrome.runtime.lastError);
        return;
      }
      // redirectUrl sẽ chứa fragment #id_token=... hoặc ?id_token=...
      const m = redirectUrl.match(/[#?].*id_token=([^&]+)/);
      if (!m) return console.error('No id_token found');
      const idToken = decodeURIComponent(m[1]);
      console.log('ID Token:', idToken);
      return idToken
    });

  }
}

class CryptoManager {
  constructor() {
    this.keyCache = new Map();
  }

  async generateAESKey() {
    Logger.log('CryptoManager', 'Generating AES key');

    return await crypto.subtle.generateKey(
      { name: 'AES-GCM', length: 256 },
      true,
      ['encrypt', 'decrypt']
    );
  }

  async encryptData(data, key) {
    try {
      const iv = crypto.getRandomValues(new Uint8Array(12));
      const encoder = new TextEncoder();
      const encodedData = encoder.encode(JSON.stringify(data));

      const encrypted = await crypto.subtle.encrypt(
        { name: 'AES-GCM', iv: iv },
        key,
        encodedData
      );

      return {
        iv: this.arrayBufferToBase64(iv),
        data: this.arrayBufferToBase64(encrypted)
      };
    } catch (error) {
      Logger.error('CryptoManager', 'Encryption failed', error);
      throw error;
    }
  }

  async decryptData(encryptedData, key) {
    try {
      const iv = this.base64ToArrayBuffer(encryptedData.iv);
      const data = this.base64ToArrayBuffer(encryptedData.data);

      const decrypted = await crypto.subtle.decrypt(
        { name: 'AES-GCM', iv: iv },
        key,
        data
      );

      const decoder = new TextDecoder();
      return JSON.parse(decoder.decode(decrypted));
    } catch (error) {
      Logger.error('CryptoManager', 'Decryption failed', error);
      throw error;
    }
  }

  async exportKey(key) {
    const exported = await crypto.subtle.exportKey('raw', key);
    return this.arrayBufferToBase64(exported);
  }

  async importKey(base64Key) {
    const keyData = this.base64ToArrayBuffer(base64Key);
    return await crypto.subtle.importKey(
      'raw',
      keyData,
      { name: 'AES-GCM' },
      true,
      ['encrypt', 'decrypt']
    );
  }

  arrayBufferToBase64(buffer) {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    bytes.forEach(byte => binary += String.fromCharCode(byte));
    return btoa(binary);
  }

  base64ToArrayBuffer(base64) {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer;
  }
}

class MessageRouter {
  constructor(authManager, cryptoManager, driveManager) {
    this.authManager = authManager;
    this.cryptoManager = cryptoManager;
    this.driveManager = driveManager;
    this.setupListeners();
  }

  setupListeners() {
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
      console.log("message received: ", message)
      this.handleMessage(message, sender, sendResponse);
      return true; // Keep channel open for async responses
    });
  }

  async handleMessage(message, sender, sendResponse) {
    try {
      Logger.log('MessageRouter', `Handling message: ${message.type}`);
      switch (message.type) {
        // Auth messages
        case MESSAGE_TYPES.CHECK_AUTH:
          console.log("MESSAGE_TYPES.CHECK_AUTH")
          sendResponse({
            authenticated: this.authManager.isAuthenticated(),
            user: this.authManager.getCurrentUser()
          });
          break;

        case MESSAGE_TYPES.LOGIN:
          const loginResult = await this.authManager.login();
          sendResponse(loginResult);
          break;

        case MESSAGE_TYPES.LOGOUT:
          const logoutResult = await this.authManager.logout();
          sendResponse(logoutResult);
          break;

        // Crypto messages
        case MESSAGE_TYPES.ENCRYPT_CELL:
          const encryptResult = await this.handleEncryptCell(message.data);
          sendResponse(encryptResult);
          break;

        case MESSAGE_TYPES.DECRYPT_CELL:
          const decryptResult = await this.handleDecryptCell(message.data);
          sendResponse(decryptResult);
          break;

        // Drive messages
        case MESSAGE_TYPES.SAVE_TO_DRIVE:
          const saveResult = await this.driveManager.saveFile(
            message.fileName,
            message.content
          );
          sendResponse(saveResult);
          break;

        case MESSAGE_TYPES.READ_FROM_DRIVE:
          const readResult = await this.driveManager.readFile(message.fileName);
          sendResponse(readResult);
          break;

        default:
          Logger.error('MessageRouter', `Unknown message type: ${message.type}`);
          sendResponse({ error: 'Unknown message type' });
      }
    } catch (error) {
      Logger.error('MessageRouter', 'Message handling failed', error);
      sendResponse({ error: error.message });
    }
  }

  async handleEncryptCell(data) {
    if (!this.authManager.isAuthenticated()) {
      throw new Error('Authentication required');
    }

    // Implementation for cell encryption
    return { success: true, encryptedData: 'placeholder' };
  }

  async handleDecryptCell(data) {
    if (!this.authManager.isAuthenticated()) {
      throw new Error('Authentication required');
    }

    // Implementation for cell decryption
    return { success: true, decryptedData: 'placeholder' };
  }
}

try {
  class BackgroundService {
    constructor() {
      this.authManager = new AuthManager();
      this.cryptoManager = new CryptoManager();
      // this.driveManager = new DriveManager(this.authManager);
      this.messageRouter = new MessageRouter(
        this.authManager,
        this.cryptoManager,
        // this.driveManager
      );
    }

    async initialize() {
      Logger.log('BackgroundService', 'Starting initialization');

      try {
        await this.authManager.initialize();
        Logger.log('BackgroundService', 'Background service ready');
      } catch (error) {
        Logger.error('BackgroundService', 'Initialization failed', error);
      }
    }
  }

  // Initialize background service
  const backgroundService = new BackgroundService();
  backgroundService.initialize();

} catch (e) {
  console.error(e);
}
