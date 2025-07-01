const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

function createWindow() {
  const win = new BrowserWindow({
    width: 800,
    height: 700,
    minWidth: 700,
    minHeight: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    },
    titleBarStyle: 'hiddenInset',
    vibrancy: 'under-window',
    visualEffectState: 'active'
  });
  win.loadFile('index.html');
}

app.whenReady().then(() => {
  createWindow();
  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});

// Helper function to get Python and CLI paths
function getPythonPaths() {
  const isDev = !app.isPackaged;
  
  if (isDev) {
    // Development mode - use relative paths
    const parentDir = path.join(__dirname, '..');
    return {
      pythonPath: path.join(parentDir, 'venv', 'bin', 'python'),
      cliPath: path.join(parentDir, 'download_cli.py'),
      workingDir: parentDir
    };
  } else {
    // Production mode - use bundled resources
    const resourcesPath = process.resourcesPath;
    return {
      pythonPath: path.join(resourcesPath, 'venv', 'bin', 'python'),
      cliPath: path.join(resourcesPath, 'download_cli.py'),
      workingDir: resourcesPath
    };
  }
}

// IPC handler to call Python backend
debug = true;
ipcMain.handle('run-python', async (event, args) => {
  return new Promise((resolve, reject) => {
    const { pythonPath, cliPath, workingDir } = getPythonPaths();
    
    // Verify files exist
    if (!fs.existsSync(pythonPath)) {
      reject(`Python not found at: ${pythonPath}`);
      return;
    }
    
    if (!fs.existsSync(cliPath)) {
      reject(`CLI script not found at: ${cliPath}`);
      return;
    }
    
    if (debug) {
      console.log('Python path:', pythonPath);
      console.log('CLI path:', cliPath);
      console.log('Working dir:', workingDir);
      console.log('Is packaged:', !app.isPackaged ? 'No (Development)' : 'Yes (Production)');
    }
    
    const py = spawn(pythonPath, [cliPath, ...args], {
      cwd: workingDir
    });
    
    let output = '';
    let error = '';
    py.stdout.on('data', (data) => {
      output += data.toString();
      if (debug) console.log('PYTHON STDOUT:', data.toString());
    });
    py.stderr.on('data', (data) => {
      error += data.toString();
      if (debug) console.error('PYTHON STDERR:', data.toString());
    });
    py.on('close', (code) => {
      if (code === 0) {
        resolve(output);
      } else {
        reject(error || 'Python process failed');
      }
    });
  });
});

// IPC handler for folder picker
ipcMain.handle('choose-folder', async () => {
  const result = await dialog.showOpenDialog({
    properties: ['openDirectory'],
    title: 'Select Download Folder'
  });
  if (result.canceled || result.filePaths.length === 0) {
    return '';
  }
  return result.filePaths[0];
});

// IPC handler for opening folder in Finder
ipcMain.handle('open-folder', async (event, folderPath) => {
  try {
    if (fs.existsSync(folderPath)) {
      await shell.openPath(folderPath);
      return true;
    } else {
      throw new Error('Folder does not exist');
    }
  } catch (error) {
    console.error('Error opening folder:', error);
    return false;
  }
});

async function chooseFolder() {
  const folder = await window.electronAPI.chooseFolder();
  if (folder) {
    document.getElementById('folder').value = folder;
  }
}