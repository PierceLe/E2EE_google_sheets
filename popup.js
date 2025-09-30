// document.getElementById("enable").addEventListener("click", () => {
//   chrome.storage.local.set({ sheets_encrypt_enabled: true }, () => {
//     chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
//       tabs.forEach(tab => {
//         chrome.scripting.executeScript({
//           target: { tabId: tab.id },
//           func: () => localStorage.setItem('sheets_encrypt_enabled', '1')
//         });
//       });
//     });
//     window.close();
//   });
// });
// document.getElementById("disable").addEventListener("click", () => {
//   chrome.storage.local.set({ sheets_encrypt_enabled: false }, () => {
//     chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
//       tabs.forEach(tab => {
//         chrome.scripting.executeScript({
//           target: { tabId: tab.id },
//           func: () => localStorage.setItem('sheets_encrypt_enabled', '0')
//         });
//       });
//     });
//     window.close();
//   });
// });
class PopupUI {
  constructor() {
    this.init();
  }

  async init() {
    // Add event listeners
    document.getElementById('login-btn').onclick = () => this.login();
    document.getElementById('logout-btn').onclick = () => this.logout();
    document.getElementById('encrypt-btn').onclick = () => this.encryptSheet();
    document.getElementById('decrypt-btn').onclick = () => this.decryptSheet();

    // Check initial auth status
    await this.checkAuthStatus();
  }

  async checkAuthStatus() {
    this.showLoading();

    try {
      const response = await chrome.runtime.sendMessage({ type: 'CHECK_AUTH' });
      if (response.authenticated) {
        this.showLoggedIn(response.user);
      } else {
        this.showLoggedOut();
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      this.showLoggedOut();
    }
  }

  async login() {
    this.showLoading();

    try {
      const response = await chrome.runtime.sendMessage({ type: 'LOGIN' });

      if (response.success) {
        this.showLoggedIn(response.user);
      } else {
        alert('Login failed: ' + response.error);
        this.showLoggedOut();
      }
    } catch (error) {
      console.error('Login failed:', error);
      alert('Login failed: ' + error.message);
      this.showLoggedOut();
    }
  }

  async logout() {
    this.showLoading();

    try {
      const response = await chrome.runtime.sendMessage({ type: 'LOGOUT' });

      if (response.success) {
        this.showLoggedOut();
      } else {
        alert('Logout failed: ' + response.error);
      }
    } catch (error) {
      console.error('Logout failed:', error);
      alert('Logout failed: ' + error.message);
    }
  }

  encryptSheet() {
    chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
      if (tabs[0]) {
        const url = tabs[0].url;
        const match = url.match(/\/spreadsheets\/d\/([a-zA-Z0-9-_]+)/);
        if (match && match[1]) {
          const sheetGoogleId = match[1];
          try {
            const response = await chrome.runtime.sendMessage({
              type: 'CREATE_ENCRYPTED_SHEET',
              sheetGoogleId: sheetGoogleId
            });
            console.log(response)
            if (response.spreadsheetId) {
              alert('Success');
            }
          } catch (error) {
            console.error('Failed: ', error);
            alert('Failed: ' + error.message);
          }
        }
      }
    });
  }

  decryptSheet() {
    chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
      if (tabs[0]) {
        const url = tabs[0].url;
        const match = url.match(/\/spreadsheets\/d\/([a-zA-Z0-9-_]+)/);
        if (match && match[1]) {
          const sheetGoogleId = match[1];
          try {
            const response = await chrome.runtime.sendMessage({
              type: 'DECRYPT_SHEET',
              sheetGoogleId: sheetGoogleId
            });
            console.log(response)
            if (response) {
              alert('Success');
            }
          } catch (error) {
            console.error('Failed: ', error);
            alert('Failed: ' + error.message);
          }
        }
      }
    });
  }

  showLoading() {
    console.log("show loading")
    document.getElementById('loading').style.display = 'block';
    document.getElementById('logged-in').style.display = 'none';
    document.getElementById('logged-out').style.display = 'none';
  }

  showLoggedIn(user) {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('logged-in').style.display = 'block';
    document.getElementById('logged-out').style.display = 'none';

    document.getElementById('user-avatar').src = user.picture || '';
    document.getElementById('user-name').textContent = user.name || '';
    document.getElementById('user-email').textContent = user.email || '';
  }

  showLoggedOut() {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('logged-in').style.display = 'none';
    document.getElementById('logged-out').style.display = 'block';
  }
}

// Initialize popup when DOM is ready
if (typeof document !== 'undefined') {
  document.addEventListener('DOMContentLoaded', () => {
    console.log("DOMContentLoaded")
    new PopupUI();
  });
}
