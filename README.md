# DownBad - Simple Web Video Downloader

A minimal Python application for downloading YouTube videos and audio files with a clean, modern interface.

## Features

- **Simple Interface**: Clean Tkinter-based UI with ttk widgets
- **YouTube Support**: Download videos from YouTube URLs
- **Audio Extraction**: Option to download audio-only as MP3
- **Progress Tracking**: Real-time download progress with percentage and ETA
- **Folder Selection**: Choose your download destination
- **Keyboard Shortcuts**: ⌘V to paste URLs, Return to start download
- **Threading**: Non-blocking downloads that keep the UI responsive
- **MP4 Format**: Downloads videos in MP4 format (not MKV)

## Requirements

- Python 3.11 or higher
- macOS (designed for macOS, may work on other platforms)
- Internet connection for downloads

## Installation

1. **Clone or download this repository**
   ```bash
   git clone <repository-url>
   cd WebVideoDownloader
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Start the application**
   ```bash
   python app.py
   ```

2. **Select a download folder**
   - Click the "📂" button to browse and select a folder
   - The folder must exist and be writable

3. **Enter a YouTube URL**
   - Paste or type a YouTube video URL
   - Supports both `youtube.com` and `youtu.be` links
   - Use ⌘V to paste from clipboard

4. **Choose download type**
   - **Unchecked**: Download best quality video + audio (MP4)
   - **Checked**: Download audio-only and convert to MP3

5. **Start download**
   - Click "Download" or press Return in the URL field
   - Monitor progress in the progress bar with ETA
   - Check status messages for current operation

6. **Access your files**
   - After successful download, click "Open Folder" to view in Finder
   - Files are named using the video title

## Building macOS App

To create a standalone macOS app that can be launched from Launchpad:

1. **Install PyInstaller** (if not already installed)
   ```bash
   pip install pyinstaller
   ```

2. **Build the app**
   ```bash
   ./build_app.sh
   ```
   
   Or manually:
   ```bash
   pyinstaller WebVideoDownloader.spec
   ```

3. **Install to Applications** (optional)
   ```bash
   cp -R "dist/Simple Web Video Downloader.app" /Applications/
   ```

The app will be created in the `dist/` folder and can be moved to your Applications folder for easy access from Launchpad.

## Keyboard Shortcuts

- **⌘V**: Paste clipboard content into URL field
- **Return**: Start download (when URL and folder are valid)

## File Naming

- **Video files**: `%(title)s.%(ext)s` (MP4 format)
- **Audio files**: `%(title)s.%(ext)s` (converted to .mp3)

## Error Handling

The application includes comprehensive error handling:
- Invalid URLs or folders
- Network connectivity issues
- Download failures
- File system permission problems

Error messages are displayed in dialog boxes with details.

## Technical Details

- **UI Framework**: Tkinter with ttk widgets for modern appearance
- **Download Engine**: yt-dlp Python API
- **Threading**: Background downloads to maintain UI responsiveness
- **Progress Tracking**: Real-time updates via yt-dlp progress hooks
- **Audio Conversion**: FFmpeg integration through yt-dlp
- **Format**: MP4 video format with M4A audio

## Troubleshooting

### Common Issues

1. **"Download Failed" errors**
   - Check your internet connection
   - Verify the YouTube URL is valid and accessible
   - Ensure you have write permissions to the selected folder

2. **Audio conversion issues**
   - Audio-only downloads require FFmpeg
   - yt-dlp will attempt to download FFmpeg automatically
   - If issues persist, install FFmpeg manually

3. **Permission errors**
   - Make sure the selected folder exists and is writable
   - Check macOS security settings for the application

4. **Tkinter Import Error**
   - If you see `ModuleNotFoundError: No module named '_tkinter'`, your Python installation doesn't include Tkinter
   - **Solution for macOS with Homebrew**:
     ```bash
     brew install python-tk
     # Then recreate your virtual environment:
     rm -rf venv
     /opt/homebrew/bin/python3 -m venv venv
     source venv/bin/activate
     pip install -r requirements.txt
     ```
   - **Alternative**: Use the system Python instead of Homebrew Python

### FFmpeg Installation (if needed)

If you encounter audio conversion issues, install FFmpeg:

```bash
# Using Homebrew
brew install ffmpeg

# Or download from https://ffmpeg.org/download.html
```

## Development

### Project Structure
```
WebVideoDownloader/
├── app.py                    # Main application
├── requirements.txt          # Python dependencies
├── WebVideoDownloader.spec   # PyInstaller configuration
├── build_app.sh             # Build script for macOS app
└── README.md                # This file
```

### Running from Source
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Future Enhancements

- Support for additional video platforms
- Batch download capabilities
- Custom quality selection
- Download history
- Custom app icon
- Auto-updates

## License

This project is open source. Feel free to modify and distribute according to your needs.

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests. 
