const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

let mainWindow;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        minWidth: 800,
        minHeight: 600,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false
        },
        titleBarStyle: 'hiddenInset', // For macOS - allows dragging from title bar area
        frame: true, // Keep the frame for proper window controls
        icon: path.join(__dirname, '../app_icon.icns'),
        show: false,
        backgroundColor: '#1a1a2e'
    });

    mainWindow.loadFile('index.html');

    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
    });

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});

// IPC Handlers
ipcMain.handle('choose-folder', async () => {
    const result = await dialog.showOpenDialog(mainWindow, {
        properties: ['openDirectory'],
        title: 'Select Download Folder'
    });
    
    if (!result.canceled && result.filePaths.length > 0) {
        return result.filePaths[0];
    }
    return null;
});

ipcMain.handle('open-folder', async (event, folderPath) => {
    try {
        await shell.openPath(folderPath);
        return true;
    } catch (error) {
        console.error('Failed to open folder:', error);
        return false;
    }
});

ipcMain.handle('start-download', async (event, args) => {
    return new Promise((resolve, reject) => {
        const [url, folder, ...options] = args;
        
        // Determine Python executable path
        let pythonPath;
        if (app.isPackaged) {
            // In packaged app, use the bundled Python
            pythonPath = path.join(process.resourcesPath, 'venv', 'bin', 'python');
        } else {
            // In development, use the virtual environment
            pythonPath = path.join(__dirname, '..', 'venv', 'bin', 'python');
        }
        
        // CLI script path
        const cliPath = path.join(__dirname, '..', 'download_cli.py');
        
        // Check if files exist
        if (!fs.existsSync(pythonPath)) {
            reject(new Error(`Python not found at: ${pythonPath}`));
            return;
        }
        
        if (!fs.existsSync(cliPath)) {
            reject(new Error(`CLI script not found at: ${cliPath}`));
            return;
        }
        
        console.log('Starting download with:', {
            pythonPath,
            cliPath,
            url,
            folder,
            options
        });
        
        const child = spawn(pythonPath, [cliPath, url, folder, ...options], {
            stdio: ['pipe', 'pipe', 'pipe'],
            env: {
                ...process.env,
                PYTHONIOENCODING: 'utf-8'
            }
        });
        
        let stdout = '';
        let stderr = '';
        
        child.stdout.on('data', (data) => {
            const output = data.toString();
            stdout += output;
            console.log('Download output:', output);
            
            // Send progress updates to renderer
            if (mainWindow && !mainWindow.isDestroyed()) {
                const progressData = {
                    id: Date.now().toString(), // Simple ID for now
                    progress: parseProgress(output),
                    speed: parseSpeed(output),
                    eta: parseETA(output),
                    stage: parseStage(output)
                };
                
                // Only send if we have meaningful data
                if (progressData.progress > 0 || progressData.stage || progressData.speed) {
                    mainWindow.webContents.send('download-progress', progressData);
                }
            }
        });
        
        child.stderr.on('data', (data) => {
            const error = data.toString();
            stderr += error;
            console.error('Download error:', error);
        });
        
        child.on('close', (code) => {
            console.log('Download process closed with code:', code);
            
            if (code === 0) {
                // Success
                if (mainWindow && !mainWindow.isDestroyed()) {
                    mainWindow.webContents.send('download-complete', {
                        id: Date.now().toString(),
                        success: true
                    });
                }
                resolve({ success: true, output: stdout });
            } else {
                // Error
                const error = stderr || `Process exited with code ${code}`;
                if (mainWindow && !mainWindow.isDestroyed()) {
                    mainWindow.webContents.send('download-error', {
                        id: Date.now().toString(),
                        error: error
                    });
                }
                resolve({ success: false, error: error });
            }
        });
        
        child.on('error', (error) => {
            console.error('Failed to start download process:', error);
            if (mainWindow && !mainWindow.isDestroyed()) {
                mainWindow.webContents.send('download-error', {
                    id: Date.now().toString(),
                    error: error.message
                });
            }
            reject(error);
        });
    });
});

// Helper functions to parse yt-dlp output
function parseProgress(output) {
    // Look for various progress patterns
    const patterns = [
        /\[download\]\s+(\d+(?:\.\d+)?)%/,  // [download] 45.2%
        /(\d+(?:\.\d+)?)%\s*of\s*\d+/,      // 45.2% of 100MB
        /(\d+(?:\.\d+)?)%/,                 // Just percentage
    ];
    
    for (const pattern of patterns) {
        const match = output.match(pattern);
        if (match) {
            return parseFloat(match[1]);
        }
    }
    return 0;
}

function parseSpeed(output) {
    const patterns = [
        /(\d+\.\d+\s*[KMGT]iB\/s)/i,       // 1.2MiB/s
        /(\d+\.\d+\s*[KMGT]B\/s)/i,        // 1.2MB/s
        /(\d+\s*[KMGT]iB\/s)/i,            // 1MiB/s
    ];
    
    for (const pattern of patterns) {
        const match = output.match(pattern);
        if (match) {
            return match[1];
        }
    }
    return '';
}

function parseETA(output) {
    const patterns = [
        /(\d{2}:\d{2})/,                   // 12:34
        /ETA\s+(\d{2}:\d{2})/,             // ETA 12:34
        /(\d+:\d{2}:\d{2})/,               // 1:23:45
    ];
    
    for (const pattern of patterns) {
        const match = output.match(pattern);
        if (match) {
            return match[1];
        }
    }
    return '';
}

function parseStage(output) {
    const patterns = [
        /Stage:\s*(.+)/,                    // Stage: message
        /\[download\]\s*(.+)/,              // [download] message
        /Downloading\s*(.+)/,               // Downloading message
    ];
    
    for (const pattern of patterns) {
        const match = output.match(pattern);
        if (match) {
            return match[1].trim();
        }
    }
    return '';
}