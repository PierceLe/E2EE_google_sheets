const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
    // Store operations
    store: {
        get: (key) => ipcRenderer.invoke('store-get', key),
        set: (key, value) => ipcRenderer.invoke('store-set', key, value),
        delete: (key) => ipcRenderer.invoke('store-delete', key)
    },
    
    // Dialog operations
    dialog: {
        showMessageBox: (options) => ipcRenderer.invoke('show-message-box', options),
        showSaveDialog: (options) => ipcRenderer.invoke('show-save-dialog', options),
        showOpenDialog: (options) => ipcRenderer.invoke('show-open-dialog', options)
    },
    
    // App operations
    app: {
        getInfo: () => ipcRenderer.invoke('get-app-info'),
        minimize: () => ipcRenderer.invoke('window-minimize'),
        maximize: () => ipcRenderer.invoke('window-maximize'),
        close: () => ipcRenderer.invoke('window-close')
    },
    
    // Menu event listeners
    onMenuAction: (callback) => {
        ipcRenderer.on('menu-new-sheet', callback);
        ipcRenderer.on('menu-open-sheet', callback);
        ipcRenderer.on('menu-settings', callback);
        ipcRenderer.on('menu-generate-keys', callback);
        ipcRenderer.on('menu-export-public-key', callback);
        ipcRenderer.on('menu-import-contact-key', callback);
    },
    
    // Remove listeners
    removeAllListeners: (channel) => {
        ipcRenderer.removeAllListeners(channel);
    }
});

// Crypto utilities for the renderer process
contextBridge.exposeInMainWorld('cryptoAPI', {
    // We'll implement these in the renderer process using Web Crypto API
    // and crypto-js for compatibility
    generateKeyPair: 'PLACEHOLDER_FOR_CRYPTO_FUNCTIONS',
    encrypt: 'PLACEHOLDER_FOR_CRYPTO_FUNCTIONS',
    decrypt: 'PLACEHOLDER_FOR_CRYPTO_FUNCTIONS'
});
