// DownBad v2.0 - Advanced Download Manager
class DownBadApp {
    constructor() {
        this.downloads = new Map();
        this.downloadCounter = 0;
        this.isDownloading = false;
        
        this.initializeElements();
        this.bindEvents();
        this.loadSavedFolder();
        this.updateUI();
    }

    initializeElements() {
        this.elements = {
            url: document.getElementById('url'),
            folder: document.getElementById('folder'),
            video: document.getElementById('video'),
            audio: document.getElementById('audio'),
            downloadBtn: document.getElementById('downloadBtn'),
            downloadsList: document.getElementById('downloadsList'),
            downloadCount: document.getElementById('downloadCount'),
            statusText: document.getElementById('statusText'),
            statusDetails: document.getElementById('statusDetails'),
            notification: document.getElementById('notification')
        };
    }

    bindEvents() {
        // URL input events
        this.elements.url.addEventListener('input', () => this.validateInputs());
        this.elements.folder.addEventListener('input', () => this.validateInputs());
        
        // Checkbox events
        this.elements.video.addEventListener('change', () => this.validateInputs());
        this.elements.audio.addEventListener('change', () => this.validateInputs());
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.metaKey && e.key === 'v') {
                e.preventDefault();
                this.pasteUrl();
            }
        });
    }

    async chooseFolder() {
        try {
            const folder = await window.electronAPI.chooseFolder();
            if (folder) {
                this.elements.folder.value = folder;
                this.saveFolder(folder);
                this.validateInputs();
                this.showNotification('Folder selected successfully', 'success');
            }
        } catch (error) {
            this.showNotification('Failed to select folder', 'error');
        }
    }

    async pasteUrl() {
        try {
            const text = await navigator.clipboard.readText();
            this.elements.url.value = text;
            this.validateInputs();
            this.showNotification('URL pasted from clipboard', 'success');
        } catch (error) {
            this.showNotification('Failed to paste from clipboard', 'error');
        }
    }

    handleKeyPress(event) {
        if (event.key === 'Enter') {
            this.startDownload();
        }
    }

    validateInputs() {
        const url = this.elements.url.value.trim();
        const folder = this.elements.folder.value.trim();
        const hasVideo = this.elements.video.checked;
        const hasAudio = this.elements.audio.checked;

        const isValidUrl = this.isValidYouTubeUrl(url);
        const isValidFolder = folder.length > 0;
        const hasSelection = hasVideo || hasAudio;

        const isValid = isValidUrl && isValidFolder && hasSelection;
        
        this.elements.downloadBtn.disabled = !isValid;
        this.elements.downloadBtn.textContent = isValid ? 'Start Download' : 'Fill in all fields';
        
        return isValid;
    }

    isValidYouTubeUrl(url) {
        return url.includes('youtube.com') || url.includes('youtu.be');
    }

    async startDownload() {
        if (!this.validateInputs()) {
            this.showNotification('Please fill in all required fields', 'error');
            return;
        }

        const url = this.elements.url.value.trim();
        const folder = this.elements.folder.value.trim();
        const downloadVideo = this.elements.video.checked;
        const downloadAudio = this.elements.audio.checked;

        // Create download object
        const downloadId = ++this.downloadCounter;
        const download = {
            id: downloadId,
            url: url,
            folder: folder,
            downloadVideo: downloadVideo,
            downloadAudio: downloadAudio,
            status: 'queued',
            progress: 0,
            title: 'Getting video info...',
            speed: '',
            eta: '',
            startTime: Date.now(),
            error: null
        };

        this.downloads.set(downloadId, download);
        this.addDownloadItem(download);
        this.updateUI();

        // Clear URL field for next download
        this.elements.url.value = '';
        this.validateInputs();

        // Start the download
        this.processDownload(download);
    }

    async processDownload(download) {
        try {
            download.status = 'downloading';
            this.updateDownloadItem(download);

            const args = [download.url, download.folder];
            if (download.downloadVideo) args.push('video');
            if (download.downloadAudio) args.push('audio');

            const result = await window.electronAPI.runPython(args);
            
            // Parse the result for progress updates
            this.parseDownloadOutput(download, result);
            
            download.status = 'complete';
            download.progress = 100;
            this.updateDownloadItem(download);
            
            this.showNotification(`Download completed: ${download.title}`, 'success');
            
        } catch (error) {
            download.status = 'error';
            download.error = error.toString();
            this.updateDownloadItem(download);
            
            this.showNotification(`Download failed: ${error}`, 'error');
        }

        this.updateUI();
    }

    parseDownloadOutput(download, output) {
        const lines = output.split('\n');
        
        for (const line of lines) {
            // Extract title
            if (line.includes('Title:')) {
                download.title = line.split('Title:')[1].trim();
                this.updateDownloadItem(download);
            }
            
            // Extract progress from yt-dlp output
            if (line.includes('[download]') && line.includes('%')) {
                const match = line.match(/(\d+(?:\.\d+)?)%/);
                if (match) {
                    download.progress = parseFloat(match[1]);
                    this.updateDownloadItem(download);
                }
            }
            
            // Extract speed
            if (line.includes('MiB/s')) {
                const match = line.match(/(\d+\.\d+MiB\/s)/);
                if (match) {
                    download.speed = match[1];
                    this.updateDownloadItem(download);
                }
            }
        }
    }

    addDownloadItem(download) {
        const downloadElement = document.createElement('div');
        downloadElement.className = 'download-item';
        downloadElement.id = `download-${download.id}`;
        
        downloadElement.innerHTML = `
            <div class="download-header">
                <div class="download-title">${download.title}</div>
                <div class="download-status status-${download.status}">${this.getStatusText(download.status)}</div>
            </div>
            <div class="progress-container">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${download.progress}%"></div>
                </div>
                <div class="progress-text">
                    <span>${download.progress.toFixed(1)}%</span>
                    <span>${download.speed || ''}</span>
                </div>
            </div>
            <div class="download-actions">
                <button class="btn btn-small btn-danger" onclick="app.removeDownload(${download.id})">Remove</button>
                ${download.status === 'complete' ? '<button class="btn btn-small btn-secondary" onclick="app.openFolder(\'' + download.folder + '\')">Open Folder</button>' : ''}
            </div>
        `;

        // Remove empty state if it exists
        const emptyState = this.elements.downloadsList.querySelector('.empty-state');
        if (emptyState) {
            emptyState.remove();
        }

        this.elements.downloadsList.appendChild(downloadElement);
    }

    updateDownloadItem(download) {
        const element = document.getElementById(`download-${download.id}`);
        if (!element) return;

        const statusElement = element.querySelector('.download-status');
        const titleElement = element.querySelector('.download-title');
        const progressFill = element.querySelector('.progress-fill');
        const progressText = element.querySelector('.progress-text');
        const actionsElement = element.querySelector('.download-actions');

        // Update status
        statusElement.className = `download-status status-${download.status}`;
        statusElement.textContent = this.getStatusText(download.status);

        // Update title
        titleElement.textContent = download.title;

        // Update progress
        progressFill.style.width = `${download.progress}%`;
        progressText.innerHTML = `
            <span>${download.progress.toFixed(1)}%</span>
            <span>${download.speed || ''}</span>
        `;

        // Update actions
        actionsElement.innerHTML = `
            <button class="btn btn-small btn-danger" onclick="app.removeDownload(${download.id})">Remove</button>
            ${download.status === 'complete' ? '<button class="btn btn-small btn-secondary" onclick="app.openFolder(\'' + download.folder + '\')">Open Folder</button>' : ''}
        `;
    }

    removeDownload(downloadId) {
        const download = this.downloads.get(downloadId);
        if (download) {
            this.downloads.delete(downloadId);
            
            const element = document.getElementById(`download-${downloadId}`);
            if (element) {
                element.remove();
            }

            this.updateUI();
        }
    }

    getStatusText(status) {
        const statusMap = {
            'queued': 'Queued',
            'downloading': 'Downloading',
            'complete': 'Complete',
            'error': 'Error'
        };
        return statusMap[status] || status;
    }

    updateUI() {
        // Update download count
        const activeCount = this.downloads.size;
        this.elements.downloadCount.textContent = activeCount;

        // Update status bar
        if (activeCount === 0) {
            this.elements.statusText.textContent = 'Ready to download';
            this.elements.statusDetails.textContent = '';
        } else {
            const downloadingCount = Array.from(this.downloads.values()).filter(d => d.status === 'downloading').length;
            const completeCount = Array.from(this.downloads.values()).filter(d => d.status === 'complete').length;
            
            this.elements.statusText.textContent = `${downloadingCount} downloading, ${completeCount} complete`;
            this.elements.statusDetails.textContent = `${activeCount} total`;
        }

        // Show empty state if no downloads
        if (activeCount === 0 && !this.elements.downloadsList.querySelector('.empty-state')) {
            this.elements.downloadsList.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📥</div>
                    <p>No downloads yet</p>
                    <p>Paste a URL and start downloading!</p>
                </div>
            `;
        }
    }

    showNotification(message, type = 'success') {
        const notification = this.elements.notification;
        notification.textContent = message;
        notification.className = `notification ${type}`;
        notification.classList.add('show');

        setTimeout(() => {
            notification.classList.remove('show');
        }, 3000);
    }

    saveFolder(folder) {
        localStorage.setItem('downbad_folder', folder);
    }

    loadSavedFolder() {
        const savedFolder = localStorage.getItem('downbad_folder');
        if (savedFolder) {
            this.elements.folder.value = savedFolder;
        }
    }

    async openFolder(folder) {
        try {
            const success = await window.electronAPI.openFolder(folder);
            if (success) {
                this.showNotification('Folder opened in Finder', 'success');
            } else {
                this.showNotification('Failed to open folder', 'error');
            }
        } catch (error) {
            this.showNotification('Failed to open folder', 'error');
        }
    }
}

// Global app instance
let app;

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    app = new DownBadApp();
});

// Global functions for HTML onclick handlers
function chooseFolder() {
    app.chooseFolder();
}

function pasteUrl() {
    app.pasteUrl();
}

function handleKeyPress(event) {
    app.handleKeyPress(event);
}

function startDownload() {
    app.startDownload();
} 