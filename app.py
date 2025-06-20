#!/usr/bin/env python3
"""
Simple Web Video Downloader
A minimal Python application for downloading YouTube videos and audio.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import subprocess
import os
import sys
import yt_dlp
import re
import time
from typing import Dict, Any


class SimpleWebVideoDownloader:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Simple Web Video Downloader")
        self.root.geometry("420x280")  # Increased height for ETA
        self.root.resizable(False, False)
        
        # Variables
        self.folder_path = tk.StringVar()
        self.url = tk.StringVar()
        self.audio_only = tk.BooleanVar()
        self.progress_value = tk.DoubleVar()
        self.status_text = tk.StringVar(value="Idle")
        
        # UI state
        self.downloading = False
        self.download_complete = False
        self.start_time = None
        
        self.setup_ui()
        self.setup_bindings()
        
    def setup_ui(self):
        """Create the user interface."""
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Folder selection
        ttk.Label(main_frame, text="Folder:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        folder_frame = ttk.Frame(main_frame)
        folder_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_path, width=35)
        self.folder_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        self.browse_button = ttk.Button(folder_frame, text="📂", width=3, command=self.browse_folder)
        self.browse_button.grid(row=0, column=1, padx=(5, 0))
        
        # URL input
        ttk.Label(main_frame, text="URL:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        self.url_entry = ttk.Entry(main_frame, textvariable=self.url, width=40)
        self.url_entry.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Audio-only checkbox
        self.audio_checkbox = ttk.Checkbutton(
            main_frame, 
            text="Audio-only (MP3)", 
            variable=self.audio_only
        )
        self.audio_checkbox.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(0, 15))
        
        # Download button
        self.download_button = ttk.Button(
            main_frame, 
            text="Download", 
            command=self.start_download
        )
        self.download_button.grid(row=5, column=0, columnspan=2, pady=(0, 15))
        
        # Progress section
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(progress_frame, text="Progress").grid(row=0, column=0, sticky=tk.W)
        self.progress_label = ttk.Label(progress_frame, text="0 %")
        self.progress_label.grid(row=0, column=1, sticky=tk.E)
        
        self.progress_bar = ttk.Progressbar(
            progress_frame, 
            variable=self.progress_value, 
            mode='determinate',
            length=300
        )
        self.progress_bar.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # ETA display
        self.eta_label = ttk.Label(progress_frame, text="")
        self.eta_label.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(2, 0))
        
        # Status
        self.status_label = ttk.Label(main_frame, textvariable=self.status_text)
        self.status_label.grid(row=7, column=0, columnspan=2, sticky=tk.W, pady=(10, 15))
        
        # Open folder button
        self.open_folder_button = ttk.Button(
            main_frame, 
            text="Open Folder", 
            command=self.open_folder,
            state="disabled"
        )
        self.open_folder_button.grid(row=8, column=0, columnspan=2)
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        folder_frame.columnconfigure(0, weight=1)
        progress_frame.columnconfigure(0, weight=1)
        
    def setup_bindings(self):
        """Set up keyboard shortcuts and bindings."""
        # Cmd+V for pasting into URL field
        self.root.bind('<Command-v>', lambda e: self.paste_url())
        
        # Return key in URL field triggers download
        self.url_entry.bind('<Return>', lambda e: self.start_download())
        
        # Track changes to enable/disable download button
        self.folder_path.trace_add('write', lambda *args: self.validate_inputs())
        self.url.trace_add('write', lambda *args: self.validate_inputs())
        
    def paste_url(self):
        """Paste clipboard content into URL field."""
        try:
            clipboard_content = self.root.clipboard_get()
            self.url.set(clipboard_content)
        except tk.TclError:
            pass  # Clipboard might be empty or contain non-text data
            
    def browse_folder(self):
        """Open folder browser dialog."""
        folder = filedialog.askdirectory(
            title="Select Download Folder",
            initialdir=os.path.expanduser("~/Downloads")
        )
        if folder:
            self.folder_path.set(folder)
            
    def validate_url(self, url: str) -> bool:
        """Basic URL validation for YouTube links."""
        if not url.startswith('http'):
            return False
        return 'youtube.com' in url or 'youtu.be' in url
        
    def validate_folder(self, folder: str) -> bool:
        """Validate that folder exists and is writable."""
        if not folder:
            return False
        return os.path.exists(folder) and os.access(folder, os.W_OK)
        
    def validate_inputs(self, *args):
        """Validate all inputs and update download button state."""
        url_valid = self.validate_url(self.url.get().strip())
        folder_valid = self.validate_folder(self.folder_path.get().strip())
        
        if url_valid and folder_valid and not self.downloading:
            self.download_button.config(state="normal")
        else:
            self.download_button.config(state="disabled")
            
    def format_time(self, seconds):
        """Format seconds into human readable time."""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
            
    def create_progress_hook(self):
        """Create a progress hook for yt-dlp."""
        def progress_hook(d):
            if d['status'] == 'downloading':
                if 'total_bytes' in d and d['total_bytes']:
                    percentage = (d['downloaded_bytes'] / d['total_bytes']) * 100
                    
                    # Calculate ETA
                    if self.start_time and percentage > 0:
                        elapsed = time.time() - self.start_time
                        if percentage > 0:
                            estimated_total = elapsed / (percentage / 100)
                            eta = estimated_total - elapsed
                            eta_text = f"ETA: {self.format_time(eta)}"
                        else:
                            eta_text = ""
                    else:
                        eta_text = ""
                    
                    self.root.after(0, lambda: self.update_progress(percentage, "Downloading...", eta_text))
                elif 'downloaded_bytes' in d:
                    self.root.after(0, lambda: self.update_status("Downloading..."))
            elif d['status'] == 'finished':
                self.root.after(0, lambda: self.update_status("Post-processing..."))
            elif d['status'] == 'error':
                self.root.after(0, lambda: self.update_status("Error occurred"))
                
        return progress_hook
        
    def update_progress(self, percentage: float, status: str, eta_text: str = ""):
        """Update progress bar, status, and ETA."""
        self.progress_value.set(percentage)
        self.progress_label.config(text=f"{percentage:.1f} %")
        self.status_text.set(status)
        self.eta_label.config(text=eta_text)
        
    def update_status(self, status: str):
        """Update status text."""
        self.status_text.set(status)
        
    def reset_ui(self):
        """Reset UI to initial state."""
        self.downloading = False
        self.progress_value.set(0)
        self.progress_label.config(text="0 %")
        self.status_text.set("Idle")
        self.eta_label.config(text="")
        self.validate_inputs()
        
    def on_download_complete(self):
        """Called when download completes successfully."""
        self.root.after(0, lambda: self.update_progress(100, "Finished"))
        self.root.after(0, lambda: self.open_folder_button.config(state="normal"))
        self.download_complete = True
        self.downloading = False
        self.validate_inputs()
        
    def on_download_error(self, error):
        """Called when download fails."""
        self.root.after(0, lambda: self.update_status("Error"))
        self.root.after(0, lambda: messagebox.showerror("Download Failed", str(error)))
        self.reset_ui()
        
    def run_download(self, url: str, path: str, audio_only: bool):
        """Run the actual download in a separate thread."""
        ydl_opts = {
            'outtmpl': os.path.join(path, '%(title)s.%(ext)s'),
            'progress_hooks': [self.create_progress_hook()],
        }
        
        if audio_only:
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '0',
            }]
        else:
            # Force MP4 format for video downloads
            ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            ydl_opts['merge_output_format'] = 'mp4'
            
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.on_download_complete()
        except Exception as e:
            self.on_download_error(e)
            
    def start_download(self):
        """Start the download process."""
        if self.downloading:
            return
            
        url = self.url.get().strip()
        path = self.folder_path.get().strip()
        audio_only = self.audio_only.get()
        
        if not self.validate_url(url) or not self.validate_folder(path):
            messagebox.showerror("Invalid Input", "Please check your URL and folder selection.")
            return
            
        self.downloading = True
        self.download_complete = False
        self.start_time = time.time()
        self.open_folder_button.config(state="disabled")
        self.update_status("Starting download...")
        self.validate_inputs()
        
        # Start download in background thread
        download_thread = threading.Thread(
            target=self.run_download,
            args=(url, path, audio_only),
            daemon=True
        )
        download_thread.start()
        
    def open_folder(self):
        """Open the download folder in Finder."""
        folder = self.folder_path.get().strip()
        if folder and os.path.exists(folder):
            try:
                subprocess.call(["open", folder])
            except Exception as e:
                messagebox.showerror("Error", f"Could not open folder: {e}")
                
    def run(self):
        """Start the application."""
        self.root.mainloop()


def main():
    """Main entry point."""
    try:
        app = SimpleWebVideoDownloader()
        app.run()
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 