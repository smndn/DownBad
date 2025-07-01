// Global state
let downloads = [];
let downloadFolder = '';
let autoDownloadEnabled = false;

// DOM elements
const urlInput = document.getElementById('url');
const folderInput = document.getElementById('folder');
const videoCheckbox = document.getElementById('video');
const audioCheckbox = document.getElementById('audio');
const autoDownloadCheckbox = document.getElementById('autoDownload');
const downloadBtn = document.getElementById('downloadBtn');
const downloadsList = document.getElementById('downloadsList');
const downloadCount = document.getElementById('downloadCount');
const statusText = document.getElementById('statusText');
const statusDetails = document.getElementById('statusDetails');
const notification = document.getElementById('notification');

// Load saved settings
function loadSettings() {
    const savedFolder = localStorage.getItem('downloadFolder');
    const savedAutoDownload = localStorage.getItem('autoDownload');
    
    if (savedFolder) {
        downloadFolder = savedFolder;
        folderInput.value = savedFolder;
    }
    
    if (savedAutoDownload === 'true') {
        autoDownloadEnabled = true;
        autoDownloadCheckbox.checked = true;
    }
}

// Save settings
function saveSettings() {
    localStorage.setItem('downloadFolder', downloadFolder);
    localStorage.setItem('autoDownload', autoDownloadEnabled.toString());
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadSettings();
    updateDownloadCount();
    updateStatus('Ready to download');
});

// Event listeners
autoDownloadCheckbox.addEventListener('change', (e) => {
    autoDownloadEnabled = e.target.checked;
    saveSettings();
});

// Handle key press in URL input
function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        if (autoDownloadEnabled) {
            startDownload();
        }
    }
}

// Handle paste in URL input
function handlePaste(event) {
    // Use setTimeout to get the pasted content after the paste event
    setTimeout(() => {
        if (autoDownloadEnabled && urlInput.value.trim()) {
            startDownload();
        }
    }, 100);
}

// Paste URL from clipboard
function pasteUrl() {
    navigator.clipboard.readText().then(text => {
        urlInput.value = text;
        if (autoDownloadEnabled && text.trim()) {
            startDownload();
        }
    }).catch(err => {
        console.error('Failed to read clipboard:', err);
        showNotification('Failed to read clipboard', 'error');
    });
}

// Choose download folder
function chooseFolder() {
    window.electronAPI.chooseFolder().then(folder => {
        if (folder) {
            downloadFolder = folder;
            folderInput.value = folder;
            saveSettings();
            showNotification('Download folder updated');
        }
    }).catch(err => {
        console.error('Failed to choose folder:', err);
        showNotification('Failed to select folder', 'error');
    });
}

// Start download
function startDownload() {
    const url = urlInput.value.trim();
    const downloadVideo = videoCheckbox.checked;
    const downloadAudio = audioCheckbox.checked;

    if (!url) {
        showNotification('Please enter a URL', 'error');
        return;
    }

    if (!downloadFolder) {
        showNotification('Please select a download folder', 'error');
        return;
    }

    if (!downloadVideo && !downloadAudio) {
        showNotification('Please select at least video or audio', 'error');
        return;
    }

    // Create download object
    const download = {
        id: Date.now().toString(),
        url: url,
        title: 'Extracting info...',
        status: 'queued',
        progress: 0,
        speed: '',
        eta: '',
        downloadVideo: downloadVideo,
        downloadAudio: downloadAudio,
        startTime: Date.now()
    };

    // Add to downloads list
    downloads.push(download);
    updateDownloadsList();
    updateDownloadCount();
    updateStatus(`Queued: ${download.title}`);

    // Clear URL input if auto-download is enabled
    if (autoDownloadEnabled) {
        urlInput.value = '';
    }

    // Start the download process
    startDownloadProcess(download);
}

// Start download process
function startDownloadProcess(download) {
    download.status = 'downloading';
    download.stage = 'Starting download...';
    updateDownloadsList();
    updateStatus(`Downloading: ${download.title}`);

    // Prepare arguments for CLI
    const args = [
        download.url,
        downloadFolder
    ];

    if (download.downloadVideo) {
        args.push('video');
    }
    if (download.downloadAudio) {
        args.push('audio');
    }

    // Call the Python CLI
    window.electronAPI.startDownload(args).then(result => {
        if (result.success) {
            download.status = 'complete';
            download.progress = 100;
            updateDownloadsList();
            updateStatus('Download completed successfully');
            showNotification('Download completed!', 'success');
            
            // Open folder in Finder
            window.electronAPI.openFolder(downloadFolder);
        } else {
            download.status = 'error';
            download.error = result.error;
            updateDownloadsList();
            updateStatus('Download failed');
            showNotification('Download failed: ' + result.error, 'error');
        }
    }).catch(err => {
        download.status = 'error';
        download.error = err.message;
        updateDownloadsList();
        updateStatus('Download failed');
        showNotification('Download failed: ' + err.message, 'error');
    });

    // Simulate progress updates (since CLI doesn't provide real-time progress)
    simulateProgress(download);
}

// Simulate progress updates
function simulateProgress(download) {
    if (download.status !== 'downloading') return;

    const elapsed = Date.now() - download.startTime;
    const estimatedDuration = 30000; // 30 seconds estimate
    const progress = Math.min((elapsed / estimatedDuration) * 100, 95);
    
    download.progress = progress;
    download.speed = 'Calculating...';
    download.eta = 'Calculating...';
    
    updateDownloadsList();

    if (progress < 95) {
        setTimeout(() => simulateProgress(download), 1000);
    }
}

// Update downloads list UI
function updateDownloadsList() {
    if (downloads.length === 0) {
        downloadsList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📥</div>
                <p>No downloads yet</p>
                <p>Paste a URL and start downloading!</p>
            </div>
        `;
        return;
    }

    downloadsList.innerHTML = downloads.map(download => `
        <div class="download-item">
            <div class="download-header">
                <div class="download-title">${download.title}</div>
                <div class="download-status status-${download.status}">
                    ${getStatusText(download.status)}
                </div>
            </div>
            
            ${download.status === 'downloading' ? `
                <div class="progress-container">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${download.progress}%"></div>
                    </div>
                    <div class="progress-text">
                        <span>${Math.round(download.progress)}%</span>
                        <span>${download.speed} • ${download.eta}</span>
                    </div>
                </div>
                ${download.stage ? `
                    <div style="color: #8b5cf6; font-size: 0.8rem; margin-top: 8px; font-style: italic;">
                        ${download.stage}
                    </div>
                ` : ''}
            ` : ''}
            
            ${download.status === 'error' ? `
                <div style="color: #ef4444; font-size: 0.8rem; margin-top: 8px;">
                    ${download.error}
                </div>
            ` : ''}
            
            <div class="download-actions">
                ${download.status === 'downloading' ? `
                    <button class="btn btn-small btn-danger" onclick="cancelDownload('${download.id}')">
                        Cancel
                    </button>
                ` : ''}
                
                ${download.status === 'complete' ? `
                    <button class="btn btn-small btn-secondary" onclick="openDownloadFolder()">
                        Open Folder
                    </button>
                ` : ''}
                
                <button class="btn btn-small btn-secondary" onclick="removeDownload('${download.id}')">
                    Remove
                </button>
            </div>
        </div>
    `).join('');
}

// Get status text
function getStatusText(status) {
    switch (status) {
        case 'queued': return 'Queued';
        case 'downloading': return 'Downloading';
        case 'complete': return 'Complete';
        case 'error': return 'Error';
        default: return 'Unknown';
    }
}

// Cancel download
function cancelDownload(id) {
    const download = downloads.find(d => d.id === id);
    if (download) {
        download.status = 'cancelled';
        updateDownloadsList();
        updateDownloadCount();
        updateStatus('Download cancelled');
    }
}

// Remove download from list
function removeDownload(id) {
    downloads = downloads.filter(d => d.id !== id);
    updateDownloadsList();
    updateDownloadCount();
    updateStatus('Download removed from list');
}

// Open download folder
function openDownloadFolder() {
    window.electronAPI.openFolder(downloadFolder).catch(err => {
        console.error('Failed to open folder:', err);
        showNotification('Failed to open folder', 'error');
    });
}

// Update download count
function updateDownloadCount() {
    const activeCount = downloads.filter(d => d.status === 'downloading' || d.status === 'queued').length;
    downloadCount.textContent = activeCount;
}

// Update status
function updateStatus(text, details = '') {
    statusText.textContent = text;
    statusDetails.textContent = details;
}

// Show notification
function showNotification(message, type = 'success') {
    notification.textContent = message;
    notification.className = `notification ${type}`;
    notification.classList.add('show');
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

// Handle window focus
window.addEventListener('focus', () => {
    // Refresh clipboard content if needed
    if (urlInput.value === '') {
        navigator.clipboard.readText().then(text => {
            if (text && text.includes('youtube.com') || text.includes('youtu.be')) {
                // Don't auto-paste, just show a subtle hint
                urlInput.placeholder = 'URL detected in clipboard - paste to use';
            }
        }).catch(() => {
            // Ignore clipboard errors
        });
    }
});

// Handle window blur
window.addEventListener('blur', () => {
    urlInput.placeholder = 'Paste YouTube URL here...';
});

// Listen for download progress updates from main process
window.electronAPI.onDownloadProgress((data) => {
    const download = downloads.find(d => d.id === data.id);
    if (download) {
        download.progress = data.progress;
        download.speed = data.speed || '';
        download.eta = data.eta || '';
        if (data.stage) {
            download.stage = data.stage;
        }
        updateDownloadsList();
    }
});

// Listen for download completion
window.electronAPI.onDownloadComplete((data) => {
    const download = downloads.find(d => d.id === data.id);
    if (download) {
        download.status = 'complete';
        download.progress = 100;
        updateDownloadsList();
        updateDownloadCount();
        updateStatus('Download completed successfully');
        showNotification('Download completed!', 'success');
    }
});

// Listen for download error
window.electronAPI.onDownloadError((data) => {
    const download = downloads.find(d => d.id === data.id);
    if (download) {
        download.status = 'error';
        download.error = data.error;
        updateDownloadsList();
        updateStatus('Download failed');
        showNotification('Download failed: ' + data.error, 'error');
    }
}); 