const { app, BrowserWindow, Menu, dialog, ipcMain, shell } = require('electron');
const path = require('path');
const Store = require('electron-store');

// Initialize store for persistent data
const store = new Store();

class E2EEGoogleSheetsApp {
    constructor() {
        this.mainWindow = null;
        this.isQuitting = false;
        
        // App configuration
        this.config = {
            apiUrl: process.env.API_URL || 'http://localhost:8000',
            windowConfig: {
                width: 1200,
                height: 800,
                minWidth: 800,
                minHeight: 600,
                webPreferences: {
                    nodeIntegration: false,
                    contextIsolation: true,
                    enableRemoteModule: false,
                    preload: path.join(__dirname, 'preload.js'),
                    webSecurity: true
                },
                icon: path.join(__dirname, '../public/icon.png'),
                titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default'
            }
        };
    }

    async createWindow() {
        // Create the browser window
        this.mainWindow = new BrowserWindow(this.config.windowConfig);

        // Load the main page
        await this.mainWindow.loadFile(path.join(__dirname, '../public/index.html'));

        // Development tools
        if (process.env.NODE_ENV === 'development') {
            this.mainWindow.webContents.openDevTools();
        }

        // Handle window events
        this.setupWindowEvents();
        
        // Setup menu
        this.createMenu();
        
        // Setup IPC handlers
        this.setupIPC();
    }

    setupWindowEvents() {
        this.mainWindow.on('closed', () => {
            this.mainWindow = null;
        });

        this.mainWindow.on('close', (event) => {
            if (process.platform === 'darwin' && !this.isQuitting) {
                event.preventDefault();
                this.mainWindow.hide();
            }
        });

        // Handle external links
        this.mainWindow.webContents.setWindowOpenHandler(({ url }) => {
            shell.openExternal(url);
            return { action: 'deny' };
        });
    }

    createMenu() {
        const template = [
            {
                label: 'File',
                submenu: [
                    {
                        label: 'New Sheet',
                        accelerator: 'CmdOrCtrl+N',
                        click: () => {
                            this.mainWindow.webContents.send('menu-new-sheet');
                        }
                    },
                    {
                        label: 'Open Sheet',
                        accelerator: 'CmdOrCtrl+O',
                        click: () => {
                            this.mainWindow.webContents.send('menu-open-sheet');
                        }
                    },
                    { type: 'separator' },
                    {
                        label: 'Settings',
                        accelerator: 'CmdOrCtrl+,',
                        click: () => {
                            this.mainWindow.webContents.send('menu-settings');
                        }
                    },
                    { type: 'separator' },
                    {
                        label: process.platform === 'darwin' ? 'Quit E2EE Google Sheets' : 'Exit',
                        accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
                        click: () => {
                            this.isQuitting = true;
                            app.quit();
                        }
                    }
                ]
            },
            {
                label: 'Edit',
                submenu: [
                    { role: 'undo' },
                    { role: 'redo' },
                    { type: 'separator' },
                    { role: 'cut' },
                    { role: 'copy' },
                    { role: 'paste' },
                    { role: 'selectall' }
                ]
            },
            {
                label: 'View',
                submenu: [
                    { role: 'reload' },
                    { role: 'forceReload' },
                    { role: 'toggleDevTools' },
                    { type: 'separator' },
                    { role: 'resetZoom' },
                    { role: 'zoomIn' },
                    { role: 'zoomOut' },
                    { type: 'separator' },
                    { role: 'togglefullscreen' }
                ]
            },
            {
                label: 'Security',
                submenu: [
                    {
                        label: 'Generate New Key Pair',
                        click: () => {
                            this.mainWindow.webContents.send('menu-generate-keys');
                        }
                    },
                    {
                        label: 'Export Public Key',
                        click: () => {
                            this.mainWindow.webContents.send('menu-export-public-key');
                        }
                    },
                    {
                        label: 'Import Contact Key',
                        click: () => {
                            this.mainWindow.webContents.send('menu-import-contact-key');
                        }
                    }
                ]
            },
            {
                label: 'Help',
                submenu: [
                    {
                        label: 'About E2EE Google Sheets',
                        click: () => {
                            dialog.showMessageBox(this.mainWindow, {
                                type: 'info',
                                title: 'About E2EE Google Sheets',
                                message: 'E2EE Google Sheets v1.0.0',
                                detail: 'End-to-End Encrypted Google Sheets Wrapper\\nBuilt with Electron and FastAPI\\n\\nProtect your sensitive data with client-side encryption.'
                            });
                        }
                    },
                    {
                        label: 'Documentation',
                        click: () => {
                            shell.openExternal('https://github.com/piercele/e2ee-google-sheets');
                        }
                    }
                ]
            }
        ];

        // macOS specific menu adjustments
        if (process.platform === 'darwin') {
            template.unshift({
                label: app.getName(),
                submenu: [
                    { role: 'about' },
                    { type: 'separator' },
                    { role: 'services' },
                    { type: 'separator' },
                    { role: 'hide' },
                    { role: 'hideOthers' },
                    { role: 'unhide' },
                    { type: 'separator' },
                    { role: 'quit' }
                ]
            });
        }

        const menu = Menu.buildFromTemplate(template);
        Menu.setApplicationMenu(menu);
    }

    setupIPC() {
        // Store operations
        ipcMain.handle('store-get', (event, key) => {
            return store.get(key);
        });

        ipcMain.handle('store-set', (event, key, value) => {
            store.set(key, value);
            return true;
        });

        ipcMain.handle('store-delete', (event, key) => {
            store.delete(key);
            return true;
        });

        // Dialog operations
        ipcMain.handle('show-message-box', async (event, options) => {
            const result = await dialog.showMessageBox(this.mainWindow, options);
            return result;
        });

        ipcMain.handle('show-save-dialog', async (event, options) => {
            const result = await dialog.showSaveDialog(this.mainWindow, options);
            return result;
        });

        ipcMain.handle('show-open-dialog', async (event, options) => {
            const result = await dialog.showOpenDialog(this.mainWindow, options);
            return result;
        });

        // App info
        ipcMain.handle('get-app-info', () => {
            return {
                version: app.getVersion(),
                name: app.getName(),
                platform: process.platform,
                apiUrl: this.config.apiUrl
            };
        });

        // Window operations
        ipcMain.handle('window-minimize', () => {
            this.mainWindow.minimize();
        });

        ipcMain.handle('window-maximize', () => {
            if (this.mainWindow.isMaximized()) {
                this.mainWindow.unmaximize();
            } else {
                this.mainWindow.maximize();
            }
        });

        ipcMain.handle('window-close', () => {
            this.mainWindow.close();
        });
    }

    async initialize() {
        // Wait for app to be ready
        await app.whenReady();
        
        // Create main window
        await this.createWindow();

        // App event handlers
        app.on('window-all-closed', () => {
            if (process.platform !== 'darwin') {
                app.quit();
            }
        });

        app.on('activate', async () => {
            if (BrowserWindow.getAllWindows().length === 0) {
                await this.createWindow();
            } else if (this.mainWindow) {
                this.mainWindow.show();
            }
        });

        app.on('before-quit', () => {
            this.isQuitting = true;
        });
    }
}

// Initialize and start the app
const e2eeApp = new E2EEGoogleSheetsApp();
e2eeApp.initialize().catch(console.error);
