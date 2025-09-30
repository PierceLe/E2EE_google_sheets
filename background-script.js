const MESSAGE_TYPES = {
  TEST: 'TEST',
  // Auth messages
  CHECK_AUTH: 'CHECK_AUTH',
  LOGIN: 'LOGIN',
  LOGOUT: 'LOGOUT',
  AUTH_CHANGED: 'AUTH_CHANGED',

  // Crypto messages
  ENCRYPT_CELL: 'ENCRYPT_CELL',
  DECRYPT_SHEET: 'DECRYPT_SHEET',
  GENERATE_KEY: 'GENERATE_KEY',

  // Drive messages
  SAVE_TO_DRIVE: 'SAVE_TO_DRIVE',
  READ_FROM_DRIVE: 'READ_FROM_DRIVE',

  // Sheets messages
  // SHEET_DETECTED: 'SHEET_DETECTED',
  // CELL_CHANGED: 'CELL_CHANGED',
  GET_USER_ME_INFO: 'GET_USER_ME_INFO',
  GET_SHEET_INFO: 'GET_SHEET_INFO',
  CREATE_ENCRYPTED_SHEET: 'CREATE_ENCRYPTED_SHEET',
  CREATE_PIN: 'CREATE_PIN',
};

const STORAGE_KEYS = {
  USER_GOOGLE_INFO: 'userGoogleInfo',
  AUTH_TOKEN: 'authToken',
  BE_TOKEN: 'BEToken',
  USER_INFO: 'userInfo',
};

const GOOGLE_APIS = {
  USER_INFO: 'https://openidconnect.googleapis.com/v1/userinfo',
  DRIVE_FILES: 'https://www.googleapis.com/drive/v3/files',
  SHEETS_API: 'https://sheets.googleapis.com/v4/spreadsheets'
};
// Lấy manifest
const manifest = chrome.runtime.getManifest();
// Lấy client_id trong manifest
const CLIENT_ID = manifest.oauth2.client_id;
const BE_HOST = "https://hbjb3s1m-9990.aue.devtunnels.ms/api/"
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
    this.currentUserGoogleInfo = null;
    this.authToken = null;
    this.beToken = null;
  }

  async initialize() {
    Logger.log('AuthManager', 'Initializing...');
    await this.loadStoredAuth();
  }

  async loadStoredAuth() {
    try {
      const stored = await StorageHelper.get([STORAGE_KEYS.USER_GOOGLE_INFO, STORAGE_KEYS.AUTH_TOKEN, STORAGE_KEYS.BE_TOKEN]);

      if (stored.userGoogleInfo && stored.authToken && stored.beToken) {
        const isValid = await this.verifyToken(stored.authToken);

        if (isValid) {
          this.currentUserGoogleInfo = stored.userGoogleInfo;
          this.authToken = stored.authToken;
          this.beToken = stored.beToken;
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
      const userGoogleInfo = await this.fetchUserGoogleInfo(token);
      const resBE = await this.loginBE(token)
      await StorageHelper.set({
        [STORAGE_KEYS.USER_GOOGLE_INFO]: userGoogleInfo,
        [STORAGE_KEYS.AUTH_TOKEN]: token,
        [STORAGE_KEYS.BE_TOKEN]: resBE.result
      });


      this.currentUserGoogleInfo = userGoogleInfo;
      this.authToken = token;
      this.beToken = resBE.result;

      Logger.log('AuthManager', 'Login successful', userGoogleInfo.email);
      this.notifyAuthChange(true);

      return { success: true, user: userGoogleInfo };
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
      this.currentUserGoogleInfo = null;
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

  async fetchUserGoogleInfo(token) {
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
    await StorageHelper.remove([STORAGE_KEYS.USER_GOOGLE_INFO, STORAGE_KEYS.AUTH_TOKEN]);
  }

  notifyAuthChange(authenticated) {
    chrome.tabs.query({}, (tabs) => {
      tabs.forEach(tab => {
        if (tab.url?.includes('docs.google.com/spreadsheets')) {
          chrome.tabs.sendMessage(tab.id, {
            type: MESSAGE_TYPES.AUTH_CHANGED,
            authenticated,
            user: this.currentUserGoogleInfo
          }).catch(() => {
            // Tab might not have content script
          });
        }
      });
    });
  }

  async loginBE(token) {
    const res = await fetch(`${BE_HOST}login/google`, {
      method: "POST",
      headers: {
        'accept': `application/json`,
        'Content-Type': `application/json`,
      },
      body: JSON.stringify({
        "token": token
      })
    });
    if (!res.ok) {
      throw new Error('Failed to fetch user profile');
    }

    return await res.json();
  }

  isAuthenticated() {
    return !!(this.currentUserGoogleInfo && this.authToken);
  }

  getCurrentUserGoogleInfo() {
    return this.currentUserGoogleInfo;
  }

  getAuthToken() {
    return this.authToken;
  }
}

class CryptoManager {
  constructor() {
    this.keyCache = new Map();
  }

  async generateAESKey() {
    return await crypto.subtle.generateKey(
      { name: 'AES-GCM', length: 256 },
      true,
      ['encrypt', 'decrypt']
    );
  }

  async encryptData(data, symmetricKeyBase64) {
    try {
      const symmetricKey = await this.importSymmetricKey(symmetricKeyBase64);
      const iv = crypto.getRandomValues(new Uint8Array(12));
      const encoder = new TextEncoder();
      const encodedData = encoder.encode(JSON.stringify(data));

      const encrypted = await crypto.subtle.encrypt(
        { name: 'AES-GCM', iv: iv },
        symmetricKey,
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

  async decryptData(encryptedData, symmetricKeyBase64) {
    try {
      const symmetricKey = await this.importSymmetricKey(symmetricKeyBase64);
      console.log(symmetricKey)
      const iv = this.base64ToArrayBuffer(encryptedData.iv);
      console.log(iv)
      const data = this.base64ToArrayBuffer(encryptedData.data);
      console.log(data)

      const decrypted = await crypto.subtle.decrypt(
        { name: 'AES-GCM', iv: iv },
        symmetricKey,
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

  async importSymmetricKey(base64Key) {
    const keyData = this.base64ToArrayBuffer(base64Key);
    return await crypto.subtle.importKey(
      'raw',
      keyData,
      { name: 'AES-GCM', length: 256 },
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

  async generateSymmetricKey() {
    const aesKey = await this.generateAESKey()
    return await this.exportKey(aesKey)
  }

  async generateAsymmetricKeyPair() {
    const keyPair = await crypto.subtle.generateKey(
      {
        name: 'RSA-OAEP',
        modulusLength: 2048,
        publicExponent: new Uint8Array([0x01, 0x00, 0x01]),
        hash: 'SHA-256',
      },
      true,
      ['encrypt', 'decrypt']
    );
    const publicKey = await crypto.subtle.exportKey('spki', keyPair.publicKey);
    const privateKey = await crypto.subtle.exportKey('pkcs8', keyPair.privateKey);
    return {
      publicKey: this.arrayBufferToBase64(publicKey),
      privateKey: this.arrayBufferToBase64(privateKey),
    };
  }

  async encryptPrivateKey(privateKeyBase64, pin) {
    const salt = crypto.getRandomValues(new Uint8Array(16));
    const pinKey = await crypto.subtle.importKey(
      'raw',
      new TextEncoder().encode(pin),
      { name: 'PBKDF2' },
      false,
      ['deriveKey']
    );
    const derivedKey = await crypto.subtle.deriveKey(
      {
        name: 'PBKDF2',
        salt: salt,
        iterations: 100000,
        hash: 'SHA-256',
      },
      pinKey,
      { name: 'AES-GCM', length: 256 },
      true,
      ['encrypt']
    );

    const iv = crypto.getRandomValues(new Uint8Array(12));
    const encodedPrivateKey = new TextEncoder().encode(privateKeyBase64);
    const encryptedPrivateKey = await crypto.subtle.encrypt(
      {
        name: 'AES-GCM',
        iv: iv,
      },
      derivedKey,
      encodedPrivateKey
    );

    const combined = new Uint8Array(salt.length + iv.length + encryptedPrivateKey.byteLength);
    combined.set(salt, 0);
    combined.set(iv, salt.length);
    combined.set(new Uint8Array(encryptedPrivateKey), salt.length + iv.length);
    return this.arrayBufferToBase64(combined);
  }
}

class SheetManager {
  constructor(authManager, cryptoManager) {
    this.authManager = authManager;
    this.cryptoManager = cryptoManager;
    this.sheetGoogleId = null;
    this.userInfo = {
      user_id: null,
      publicKey: null,
      encryptedPrivateKey: null,
    };
    this.sheetInfo = {
      created_at: null,
      creator: null,
      creator_id: null,
      encrypted_sheet_key: null,
      is_favorite: null,
      last_accessed_at: null,
      link: null,
      role: null,
      sheet_id: null,
    }
  }

  initialize() {
    Logger.log('SheetManager', 'Initializing...');
  }

  async getUserMeInfo() {
    const res = await fetch(`${BE_HOST}user/me`, {
      method: "POST",
      headers: {
        'accept': `application/json`,
        'Authorization': `Bearer ${this.authManager.beToken}`,
        'Cookie': `access_token=${this.authManager.beToken}`,
      }
    });
    if (!res.ok) {
      throw new Error('Failed to fetch user me info');
    }
    const resolveRes = await res.json()
    this.userInfo = {
      ...resolveRes.result,
      encryptedPrivateKey: resolveRes.result.encrypted_private_key,
      publicKey: resolveRes.result.public_key
    }
    await StorageHelper.set({
      [STORAGE_KEYS.USER_INFO]: this.userInfo,
    });
    return this.userInfo
  }

  async getSheetInfo() {
    const res = await fetch(`${BE_HOST}sheet?sheet_id=${this.sheetGoogleId}`, {
      method: "GET",
      headers: {
        'accept': `application/json`,
        'Authorization': `Bearer ${this.authManager.beToken}`,
        'Cookie': `access_token=${this.authManager.beToken}`,
      }
    });
    if (!res.ok) {
      throw new Error('Failed to fetch sheet info');
    }
    const resolveRes = await res.json()
    console.log("getSheetInfo: ", resolveRes)
    return resolveRes
  }

  async getSheetKey() {
    const res = await fetch(`${BE_HOST}sheet/sheet-key?sheet_id=${this.sheetGoogleId}`, {
      method: "GET",
      headers: {
        'accept': `application/json`,
        'Authorization': `Bearer ${this.authManager.beToken}`,
        'Cookie': `access_token=${this.authManager.beToken}`,
      }
    });
    if (!res.ok) {
      return {
        code: 2001
      }
    }
    const resolveRes = await res.json()
    console.log("getSheetKey: ", resolveRes)
    return resolveRes
  }

  async getSheetData(sheetGoogleId, range) {
    return await new Promise((resolve, reject) => {
      chrome.identity.getAuthToken({ interactive: true }, async (token) => {
        if (chrome.runtime.lastError || !token) {
          return reject(chrome.runtime.lastError || new Error("Cannot get token"));
        }

        try {
          const res = await fetch(
            `https://sheets.googleapis.com/v4/spreadsheets/${sheetGoogleId}/values/${range}`,
            {
              method: "GET",
              headers: {
                Authorization: `Bearer ${token}`,
                Accept: "application/json",
              },
            }
          );

          if (!res.ok) {
            const errorText = await res.text();
            return reject(new Error(`API error: ${res.status} ${errorText}`));
          }

          const data = await res.json();
          resolve(data);
        } catch (err) {
          reject(err);
        }
      });
    });
  }

  async updateSheetData(sheetGoogleId, sheetName, values, token) {
    // values: mảng 2D, ví dụ [["cipher1", "cipher2"], ["cipher3", "cipher4"]]
    // const range = `${sheetName}!A1`; // bắt đầu ghi từ A1
    const body = {
      range: sheetName,
      majorDimension: "ROWS",
      values
    };

    const res = await fetch(
      `https://sheets.googleapis.com/v4/spreadsheets/${sheetGoogleId}/values/${encodeURIComponent(sheetName)}?valueInputOption=RAW`,
      {
        method: "PUT",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify(body)
      }
    );

    if (!res.ok) {
      const err = await res.json();
      throw new Error(`Error writing data: ${JSON.stringify(err)}`);
    }

    const result = await res.json();
    console.log("✅ Data written:", result);
    return result;
  }

  async createEncryptedSheet(sheetGoogleId) {
    let sheetKey
    const res = await this.getSheetByLink(`https://docs.google.com/spreadsheets/d/${sheetGoogleId}/edit`)
    // ZtIP6XbUC5II9NevT8joGUPPokE71+TfFdX91yh7plU=
    if (res.code === 2001) {
      sheetKey = await this.cryptoManager.generateSymmetricKey()
      const res = await fetch(`${BE_HOST}sheet`, {
        method: "POST",
        headers: {
          'accept': `application/json`,
          "Content-Type": "application/json",
          'Authorization': `Bearer ${this.authManager.beToken}`,
          'Cookie': `access_token=${this.authManager.beToken}`,
        },
        body: JSON.stringify({
          "encrypted_sheet_key": sheetKey,
          "encrypted_sheet_keys": [this.userInfo.encryptedPrivateKey],
          "link": `https://docs.google.com/spreadsheets/d/${sheetGoogleId}/edit`,
          "member_ids": [this.userInfo.user_id]
        })
      });
      if (!res.ok) {
        throw new Error('Failed create encrypted sheet');
      }
      const resolveRes = await res.json()
      this.sheetInfo = resolveRes.result
    } else {
      sheetKey = res.result.encrypted_sheet_key
    }
    const sheetData = await this.getSheetData(sheetGoogleId, "Sheet1!A1:Z1000")
    console.log("sheetData: ", sheetData)
    const encryptedSheetData = await this.cryptoManager.encryptData(sheetData, sheetKey)
    console.log("encryptedData: ", encryptedSheetData)
    const ress = await this.updateSheetData(sheetGoogleId, "Sheet1!A1:Z1000", [[JSON.stringify(encryptedSheetData)]], this.authManager.authToken)
    console.log(ress)
    return ress
  }

  async decryptedSheet(sheetGoogleId) {
    const encryptedSheetData = await this.getSheetData(sheetGoogleId, "Sheet1!A1:Z1000")
    console.log("encryptedSheetData: ", encryptedSheetData)
    let sheetKey
    const res = await this.getSheetByLink(`https://docs.google.com/spreadsheets/d/${sheetGoogleId}/edit`)
    sheetKey = res.code === 2001 ? this.sheetInfo.encrypted_sheet_key : res.result.encrypted_sheet_key
    console.log("Sheet key by info: ", this.sheetInfo.encrypted_sheet_key)
    console.log("Sheet key by link: ", res.result.encrypted_sheet_key)
    // const decryptSheetData = await this.cryptoManager.decryptData(JSON.parse(encryptedSheetData.values), "RJkGddyrBvLsmj96/NUQK5lclGjVFe6Mshc/WYM+2Qo=")
    const decryptSheetData = await this.cryptoManager.decryptData(JSON.parse(encryptedSheetData.values), sheetKey)
    console.log("decryptedData: ", decryptSheetData)
    const ress = await this.updateSheetData(sheetGoogleId, "Sheet1!A1:Z1000", decryptSheetData.values, this.authManager.authToken)
    console.log(ress)
    return ress
  }

  async createPIN(pinInput) {
    const { publicKey, privateKey } = await this.cryptoManager.generateAsymmetricKeyPair();
    const encryptedPrivateKey = await this.cryptoManager.encryptPrivateKey(privateKey, pinInput);
    const res = await fetch(`${BE_HOST}user/set-pin`, {
      method: "POST",
      headers: {
        'accept': `application/json`,
        "Content-Type": "application/json",
        'Authorization': `Bearer ${this.authManager.beToken}`,
        'Cookie': `access_token=${this.authManager.beToken}`,
      },
      body: JSON.stringify({
        "encrypted_private_key": encryptedPrivateKey,
        "public_key": publicKey,
        "pin": String(pinInput),
      })
    });

    if (!res.ok) {
      throw new Error('Failed to fetch sheet info');
    }
    const resolveRes = await res.json()
    this.userInfo = {
      ...resolveRes.result,
      encryptedPrivateKey: encryptedPrivateKey,
      publicKey: publicKey
    }
    return this.userInfo
  }

  async getSheetByLink(link) {
    const res = await fetch(`${BE_HOST}sheet/by-link?link=${link}`, {
      method: "GET",
      headers: {
        'accept': `application/json`,
        'Authorization': `Bearer ${this.authManager.beToken}`,
        'Cookie': `access_token=${this.authManager.beToken}`,
      }
    });
    if (!res.ok) {
      throw new Error('Failed to fetch sheet info');
    }
    const resolveRes = await res.json()
    console.log("Sheet Info By Link: ", resolveRes.result)
    return resolveRes
  }
}
class MessageRouter {
  constructor(authManager, cryptoManager, sheetManager) {
    this.authManager = authManager;
    this.cryptoManager = cryptoManager;
    this.sheetManager = sheetManager;
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
          sendResponse({
            authenticated: this.authManager.isAuthenticated(),
            user: this.authManager.getCurrentUserGoogleInfo()
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

        // Sheet messages
        case MESSAGE_TYPES.GET_USER_ME_INFO:
          const userMeResult = await this.sheetManager.getUserMeInfo();
          sendResponse(userMeResult);
          break;
        case MESSAGE_TYPES.GET_SHEET_INFO:
          this.sheetManager.sheetGoogleId = message.sheetGoogleId
          const resolveResult = await this.sheetManager.getSheetInfo(message.sheetGoogleId);
          sendResponse(resolveResult);
          break;
        case MESSAGE_TYPES.CREATE_PIN:
          console.log(message)
          const pinResult = await this.sheetManager.createPIN(message.pin);
          console.log("Create PIN result: ", pinResult)
          sendResponse(pinResult);
          break;
        case MESSAGE_TYPES.CREATE_ENCRYPTED_SHEET:
          this.sheetManager.sheetGoogleId = message.sheetGoogleId
          const createdSheetResult = await this.sheetManager.createEncryptedSheet(message.sheetGoogleId);
          sendResponse(createdSheetResult);
          break;
        case MESSAGE_TYPES.DECRYPT_SHEET:
          this.sheetManager.sheetGoogleId = message.sheetGoogleId
          const decryptedSheetResult = await this.sheetManager.decryptedSheet(message.sheetGoogleId);
          sendResponse(decryptedSheetResult);
          break;
        case MESSAGE_TYPES.SAVE_TO_DRIVE:
          const saveResult = await this.sheetManager.saveFile(
            message.fileName,
            message.content
          );
          sendResponse(saveResult);
          break;

        case MESSAGE_TYPES.READ_FROM_DRIVE:
          const readResult = await this.sheetManager.readFile(message.fileName);
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
      this.sheetManager = new SheetManager(this.authManager, this.cryptoManager);
      this.messageRouter = new MessageRouter(
        this.authManager,
        this.cryptoManager,
        this.sheetManager
      );
    }

    async initialize() {
      Logger.log('BackgroundService', 'Starting initialization');

      try {
        await this.authManager.initialize();
        await this.sheetManager.initialize();
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