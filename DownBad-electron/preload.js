const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
    chooseFolder: () => ipcRenderer.invoke('choose-folder'),
    openFolder: (folderPath) => ipcRenderer.invoke('open-folder', folderPath),
    startDownload: (args) => ipcRenderer.invoke('start-download', args),
    
    // Listen for download events
    onDownloadProgress: (callback) => {
        ipcRenderer.on('download-progress', (event, data) => callback(data));
    },
    onDownloadComplete: (callback) => {
        ipcRenderer.on('download-complete', (event, data) => callback(data));
    },
    onDownloadError: (callback) => {
        ipcRenderer.on('download-error', (event, data) => callback(data));
    }
}); 