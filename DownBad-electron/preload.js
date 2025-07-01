const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  runPython: (args) => ipcRenderer.invoke('run-python', args),
  chooseFolder: () => ipcRenderer.invoke('choose-folder'),
  openFolder: (folderPath) => ipcRenderer.invoke('open-folder', folderPath)
}); 