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
import json
from typing import Dict, Any, List


class SimpleWebVideoDownloader:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("DownBad")
        self.root.geometry("600x700")  # Larger initial size for better visibility
        self.root.resizable(True, True)
        self.root.minsize(500, 600)  # Minimum window size
        
        # Configuration file path
        self.config_file = os.path.join(os.path.expanduser("~"), ".web_video_downloader_config.json")
        
        # Check for FFmpeg
        self.ffmpeg_available = self.check_ffmpeg()
        
        # Variables
        self.folder_path = tk.StringVar()
        self.url = tk.StringVar()
        self.download_video = tk.BooleanVar(value=True)  # Auto-select video
        self.download_audio = tk.BooleanVar(value=False)  # Audio optional
        self.progress_value = tk.DoubleVar()
        self.status_text = tk.StringVar(value="✨ Ready")
        
        # UI state
        self.downloading = False
        self.download_complete = False
        self.start_time = None
        
        # Multiple downloads tracking
        self.active_downloads: List[Dict[str, Any]] = []
        self.download_counter = 0
        
        # Load configuration
        self.load_config()
        
        # Setup modern theme
        self.setup_modern_theme()
        
        self.setup_ui()
        self.setup_bindings()
        
    def setup_ui(self):
        # Use light backgrounds and black text for all widgets
        bg = "#f0f0f0"
        fg = "black"
        entry_bg = "white"
        entry_fg = "black"

        self.root.configure(bg=bg)
        tk.Label(self.root, text="DownBad", font=("TkDefaultFont", 18, "bold"), bg=bg, fg=fg).pack(pady=(10, 10))

        tk.Label(self.root, text="Download Folder:", bg=bg, fg=fg).pack(anchor=tk.W, padx=10)
        folder_row = tk.Frame(self.root, bg=bg)
        folder_row.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.folder_entry = tk.Entry(folder_row, textvariable=self.folder_path, bg=entry_bg, fg=entry_fg)
        self.folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.browse_button = tk.Button(folder_row, text="Browse", command=self.browse_folder, bg=bg, fg=fg)
        self.browse_button.pack(side=tk.RIGHT, padx=(5, 0))

        tk.Label(self.root, text="Video URL:", bg=bg, fg=fg).pack(anchor=tk.W, padx=10)
        self.url_entry = tk.Entry(self.root, textvariable=self.url, bg=entry_bg, fg=entry_fg)
        self.url_entry.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.video_checkbox = tk.Checkbutton(self.root, text="Download Video", variable=self.download_video, bg=bg, fg=fg, selectcolor=bg, activebackground=bg, activeforeground=fg)
        self.video_checkbox.pack(anchor=tk.W, padx=10)
        self.audio_checkbox = tk.Checkbutton(self.root, text="Download Audio (MP3)", variable=self.download_audio, bg=bg, fg=fg, selectcolor=bg, activebackground=bg, activeforeground=fg)
        self.audio_checkbox.pack(anchor=tk.W, padx=10, pady=(0, 10))

        self.download_button = tk.Button(self.root, text="Start Download", command=self.start_download, bg=bg, fg=fg)
        self.download_button.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.status_label = tk.Label(self.root, textvariable=self.status_text, anchor=tk.W, bg=bg, fg=fg)
        self.status_label.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.open_folder_button = tk.Button(self.root, text="Open Folder", command=self.open_folder, state="disabled", bg=bg, fg=fg)
        self.open_folder_button.pack(anchor=tk.E, padx=10, pady=(0, 10))

        tk.Label(self.root, text="Active Downloads:", bg=bg, fg=fg).pack(anchor=tk.W, padx=10, pady=(10, 0))
        self.downloads_frame = tk.Frame(self.root, bg=bg)
        self.downloads_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
    def setup_bindings(self):
        """Set up keyboard shortcuts and bindings."""
        # Cmd+V for pasting into URL field
        self.root.bind('<Command-v>', lambda e: self.paste_url())
        
        # Return key in URL field triggers download
        self.url_entry.bind('<Return>', lambda e: self.start_download())
        
        # Track changes to enable/disable download button
        self.folder_path.trace_add('write', lambda *args: self.validate_inputs())
        self.url.trace_add('write', lambda *args: self.validate_inputs())
        
        # Add hover effects for buttons
        self.add_hover_effects()
        
    def add_hover_effects(self):
        """Add hover effects to buttons for better UX."""
        def on_enter(event):
            widget = event.widget
            if widget == self.download_button:
                widget.configure(bg='#4f46e5')
            elif widget == self.browse_button:
                widget.configure(bg='#4f46e5')
            elif widget == self.open_folder_button:
                widget.configure(bg='#4b5563')
                
        def on_leave(event):
            widget = event.widget
            if widget == self.download_button:
                widget.configure(bg='#6366f1')
            elif widget == self.browse_button:
                widget.configure(bg='#6366f1')
            elif widget == self.open_folder_button:
                widget.configure(bg='#374151')
        
        # Bind hover events
        for button in [self.download_button, self.browse_button, self.open_folder_button]:
            button.bind('<Enter>', on_enter)
            button.bind('<Leave>', on_leave)
        
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
            self.save_config()
            
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
        
        if url_valid and folder_valid:
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
            
    def add_download_item(self, download_id: int, url: str, download_video: bool, download_audio: bool):
        """Add a new download item to the UI with modern styling."""
        # Create download item container with rounded corners effect
        download_frame = tk.Frame(self.downloads_frame, 
                                 bg='#1e293b',
                                 relief=tk.FLAT,
                                 bd=0)
        download_frame.pack(fill=tk.X, pady=5, padx=5)
        
        # Add padding to download item content
        download_content = tk.Frame(download_frame, bg='#1e293b')
        download_content.pack(fill=tk.BOTH, expand=True, padx=15, pady=12)
        
        # Title and status row
        title_frame = tk.Frame(download_content, bg='#1e293b')
        title_frame.pack(fill=tk.X, pady=(0, 8))
        
        # Download ID and type indicator
        if download_video and download_audio:
            type_icon = "🎬🎵"
            type_text = "Video + Audio"
        elif download_video:
            type_icon = "🎬"
            type_text = "Video Only"
        else:
            type_icon = "🎵"
            type_text = "Audio Only"
            
        title_label = tk.Label(title_frame, 
                              text=f"{type_icon} Download #{download_id} ({type_text})",
                              font=('Arial', 11, 'bold'),
                              fg='#e8e8e8',
                              bg='#1e293b')
        title_label.pack(side=tk.LEFT)
        
        # Status and controls frame
        status_controls_frame = tk.Frame(title_frame, bg='#1e293b')
        status_controls_frame.pack(side=tk.RIGHT)
        
        # Cancel button
        cancel_button = tk.Button(status_controls_frame,
                                 text="❌",
                                 font=('Arial', 10),
                                 bg='#ef4444',
                                 fg='white',
                                 relief=tk.FLAT,
                                 bd=0,
                                 width=3,
                                 command=lambda: self.cancel_download(download_id),
                                 activebackground='#dc2626',
                                 activeforeground='white')
        cancel_button.pack(side=tk.RIGHT, padx=(8, 0))
        
        # Status indicator
        status_label = tk.Label(status_controls_frame, 
                               text="Starting...",
                               font=('Arial', 10),
                               fg='#6366f1',
                               bg='#1e293b')
        status_label.pack(side=tk.RIGHT, padx=(0, 8))
        
        # URL preview (truncated)
        url_preview = url[:60] + "..." if len(url) > 60 else url
        url_label = tk.Label(download_content,
                            text=url_preview,
                            font=('Arial', 9),
                            fg='#94a3b8',
                            bg='#1e293b',
                            anchor=tk.W)
        url_label.pack(fill=tk.X, pady=(0, 8))
        
        # Progress bar container
        progress_container = tk.Frame(download_content, bg='#1e293b')
        progress_container.pack(fill=tk.X, pady=(0, 4))
        
        # Progress bar
        progress_var = tk.DoubleVar()
        progress_bar = tk.Frame(progress_container, 
                               bg='#0f172a',
                               relief=tk.FLAT,
                               bd=0)
        progress_bar.pack(fill=tk.X)
        
        # Progress fill (will be updated)
        progress_fill = tk.Frame(progress_bar,
                                bg='#6366f1',
                                relief=tk.FLAT,
                                bd=0)
        progress_fill.pack(side=tk.LEFT, fill=tk.Y)
        
        # Progress percentage and ETA
        info_frame = tk.Frame(download_content, bg='#1e293b')
        info_frame.pack(fill=tk.X)
        
        percentage_label = tk.Label(info_frame,
                                   text="0%",
                                   font=('Arial', 9),
                                   fg='#6366f1',
                                   bg='#1e293b')
        percentage_label.pack(side=tk.LEFT)
        
        eta_label = tk.Label(info_frame,
                            text="",
                            font=('Arial', 9),
                            fg='#94a3b8',
                            bg='#1e293b')
        eta_label.pack(side=tk.RIGHT)
        
        download_info = {
            'id': download_id,
            'url': url,
            'download_video': download_video,
            'download_audio': download_audio,
            'frame': download_frame,
            'title_label': title_label,
            'status_label': status_label,
            'url_label': url_label,
            'progress_var': progress_var,
            'progress_fill': progress_fill,
            'percentage_label': percentage_label,
            'eta_label': eta_label,
            'cancel_button': cancel_button,
            'start_time': time.time(),
            'status': 'starting',
            'cancelled': False,  # Add cancellation flag
            'thread': None  # Will store thread reference
        }
        
        self.active_downloads.append(download_info)
        return download_info
        
    def remove_download_item(self, download_info: Dict[str, Any]):
        """Remove a download item from the UI."""
        if download_info in self.active_downloads:
            self.active_downloads.remove(download_info)
            download_info['frame'].destroy()
            # No need to reorder since we're using pack layout
            
    def update_download_progress(self, download_info: Dict[str, Any], percentage: float, status: str, eta_text: str = ""):
        """Update progress for a specific download with modern styling."""
        # Don't update if cancelled unless it's a cancellation status
        if download_info['cancelled'] and status.lower() not in ['cancelling', 'cancelled']:
            return
            
        download_info['progress_var'].set(percentage)
        download_info['status_label'].config(text=status)
        download_info['eta_label'].config(text=eta_text)
        download_info['percentage_label'].config(text=f"{percentage:.1f}%")
        download_info['status'] = status.lower()
        
        # Update progress bar fill with smooth animation
        progress_fill = download_info['progress_fill']
        progress_fill.pack_forget()  # Remove current fill
        
        # Calculate fill width based on percentage
        parent_width = progress_fill.master.winfo_width()
        if parent_width > 1:  # Ensure parent has been rendered
            fill_width = int((percentage / 100) * parent_width)
            progress_fill.configure(width=fill_width)
            progress_fill.pack(side=tk.LEFT, fill=tk.Y)
            
            # Add subtle animation effect
            if percentage > 0:
                progress_fill.configure(bg='#6366f1')
            if percentage == 100:
                progress_fill.configure(bg='#10b981')  # Green when complete
        
        # Update status color based on status with smooth transitions
        if status.lower() == 'finished':
            download_info['status_label'].config(fg='#10b981')  # Green
            download_info['title_label'].config(fg='#10b981')
        elif status.lower() == 'error':
            download_info['status_label'].config(fg='#ef4444')  # Red
            download_info['title_label'].config(fg='#ef4444')
        elif status.lower() in ['cancelling', 'cancelled']:
            download_info['status_label'].config(fg='#f59e0b')  # Orange
            download_info['title_label'].config(fg='#94a3b8')  # Gray
        elif status.lower() in ['downloading', 'post-processing']:
            download_info['status_label'].config(fg='#6366f1')  # Purple
            download_info['title_label'].config(fg='#e8e8e8')
        else:
            download_info['status_label'].config(fg='#f59e0b')  # Orange
            download_info['title_label'].config(fg='#e8e8e8')
        
        # Update overall status with emoji
        active_count = len([d for d in self.active_downloads if d['status'] in ['starting', 'downloading', 'post-processing']])
        if active_count > 0:
            self.status_text.set(f"🔄 Active downloads: {active_count}")
        else:
            self.status_text.set("✨ Ready")
        
    def create_progress_hook(self, download_info: Dict[str, Any]):
        """Create a progress hook for yt-dlp."""
        def progress_hook(d):
            # Check for cancellation
            if download_info['cancelled']:
                raise Exception("Download cancelled by user")
                
            if d['status'] == 'downloading':
                if 'total_bytes' in d and d['total_bytes']:
                    percentage = (d['downloaded_bytes'] / d['total_bytes']) * 100
                    
                    # Calculate ETA
                    if download_info['start_time'] and percentage > 0:
                        elapsed = time.time() - download_info['start_time']
                        if percentage > 0:
                            estimated_total = elapsed / (percentage / 100)
                            eta = estimated_total - elapsed
                            eta_text = f"ETA: {self.format_time(eta)}"
                        else:
                            eta_text = ""
                    else:
                        eta_text = ""
                    
                    self.root.after(0, lambda: self.update_download_progress(download_info, percentage, "Downloading...", eta_text))
                elif 'downloaded_bytes' in d:
                    self.root.after(0, lambda: self.update_download_progress(download_info, 0, "Downloading..."))
            elif d['status'] == 'finished':
                self.root.after(0, lambda: self.update_download_progress(download_info, 100, "Post-processing..."))
            elif d['status'] == 'error':
                self.root.after(0, lambda: self.update_download_progress(download_info, 0, "Error occurred"))
                
        return progress_hook
        
    def on_download_complete(self, download_info: Dict[str, Any]):
        """Called when download completes successfully."""
        self.root.after(0, lambda: self.update_download_progress(download_info, 100, "Finished"))
        
        # Enable open folder button if no active downloads
        active_count = len([d for d in self.active_downloads if d['status'] in ['starting', 'downloading', 'post-processing']])
        if active_count == 0:
            self.root.after(0, lambda: self.open_folder_button.config(state="normal"))
        
        # Remove the download item after a delay
        self.root.after(3000, lambda: self.remove_download_item(download_info))
        
    def on_download_error(self, error, download_info: Dict[str, Any]):
        """Called when download fails."""
        self.root.after(0, lambda: self.update_download_progress(download_info, 0, "Error"))
        self.root.after(0, lambda: messagebox.showerror("Download Failed", f"Download #{download_info['id']} failed: {str(error)}"))
        
        # Remove the download item after a delay
        self.root.after(3000, lambda: self.remove_download_item(download_info))
        
    def run_download(self, url: str, path: str, download_video: bool, download_audio: bool, download_info: Dict[str, Any]):
        """Run the actual download in a separate thread."""
        try:
            # Check for cancellation at the start
            if download_info['cancelled']:
                return
                
            # Get video info first
            info_ydl = yt_dlp.YoutubeDL({'quiet': True})
            info = info_ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown') if info else 'Unknown'
            
            # Check for cancellation after getting info
            if download_info['cancelled']:
                return
            
            # Create subfolder if downloading both video and audio
            if download_video and download_audio:
                safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                download_path = os.path.join(path, safe_title)
                os.makedirs(download_path, exist_ok=True)
            else:
                download_path = path
            
            # Download video if requested
            if download_video and not download_info['cancelled']:
                self.download_video_only(url, download_path, download_info)
            
            # Download audio if requested
            if download_audio and not download_info['cancelled']:
                self.download_audio_only(url, download_path, download_info)
                
            if not download_info['cancelled']:
                self.on_download_complete(download_info)
            
        except Exception as e:
            error_msg = str(e)
            if "cancelled by user" in error_msg.lower():
                # Don't show error for user cancellation
                return
            self.on_download_error(error_msg, download_info)
    
    def download_video_only(self, url: str, path: str, download_info: Dict[str, Any]):
        """Download highest quality video only."""
        # Check for cancellation
        if download_info['cancelled']:
            return
            
        ydl_opts = {
            'outtmpl': os.path.join(path, '%(title)s.%(ext)s'),
            'progress_hooks': [self.create_progress_hook(download_info)],
            'format': 'bestvideo',  # Get best video quality (any format)
        }
        
        # Set FFmpeg path if available
        ffmpeg_found = False
        if getattr(sys, 'frozen', False):
            bundle_dir = os.path.dirname(os.path.dirname(os.path.dirname(sys.executable)))
            ffmpeg_path = os.path.join(bundle_dir, 'Contents', 'Frameworks', 'ffmpeg')
            if os.path.exists(ffmpeg_path) and os.access(ffmpeg_path, os.X_OK):
                ydl_opts['ffmpeg_location'] = ffmpeg_path
                ffmpeg_found = True
                print(f"USING BUNDLED FFMPEG: {ffmpeg_path}")
            else:
                print(f"BUNDLED FFMPEG NOT FOUND OR NOT EXECUTABLE: {ffmpeg_path}")
        else:
            try:
                result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    ffmpeg_found = True
                    print("SYSTEM FFMPEG FOUND")
            except:
                pass
        
        # If FFmpeg is available, add post-processor to convert to MP4
        if ffmpeg_found:
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }]
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    
    def download_audio_only(self, url: str, path: str, download_info: Dict[str, Any]):
        """Download highest quality audio only."""
        # Check for cancellation
        if download_info['cancelled']:
            return
            
        ydl_opts = {
            'outtmpl': os.path.join(path, '%(title)s.%(ext)s'),
            'progress_hooks': [self.create_progress_hook(download_info)],
            'format': 'bestaudio',  # Get best audio quality
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'm4a',
                'preferredquality': '192',
            }],
        }
        
        # Set FFmpeg path if available
        if getattr(sys, 'frozen', False):
            bundle_dir = os.path.dirname(os.path.dirname(os.path.dirname(sys.executable)))
            ffmpeg_path = os.path.join(bundle_dir, 'Contents', 'Frameworks', 'ffmpeg')
            if os.path.exists(ffmpeg_path) and os.access(ffmpeg_path, os.X_OK):
                ydl_opts['ffmpeg_location'] = ffmpeg_path
                print(f"USING BUNDLED FFMPEG: {ffmpeg_path}")
            else:
                print(f"BUNDLED FFMPEG NOT FOUND OR NOT EXECUTABLE: {ffmpeg_path}")
        else:
            try:
                result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    print("SYSTEM FFMPEG FOUND")
            except:
                pass
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
    def start_download(self):
        """Start the download process."""
        url = self.url.get().strip()
        path = self.folder_path.get().strip()
        download_video = self.download_video.get()
        download_audio = self.download_audio.get()
        
        if not self.validate_url(url) or not self.validate_folder(path):
            messagebox.showerror("Invalid Input", "Please check your URL and folder selection.")
            return
            
        if not download_video and not download_audio:
            messagebox.showerror("Invalid Selection", "Please select at least video or audio to download.")
            return
            
        # Increment download counter
        self.download_counter += 1
        
        # Clear the URL field
        self.url.set("")
        
        # Disable open folder button while downloading
        self.open_folder_button.config(state="disabled")
        
        # Create download info and start download
        download_info = self.add_download_item(self.download_counter, url, download_video, download_audio)
        
        # Start download in background thread
        download_thread = threading.Thread(
            target=self.run_download,
            args=(url, path, download_video, download_audio, download_info),
            daemon=True
        )
        download_info['thread'] = download_thread  # Store thread reference
        download_thread.start()
        
    def open_folder(self):
        """Open the download folder in Finder."""
        folder = self.folder_path.get().strip()
        if folder and os.path.exists(folder):
            try:
                subprocess.call(["open", folder])
            except Exception as e:
                messagebox.showerror("Error", f"Could not open folder: {e}")
                
    def load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    if 'download_folder' in config:
                        self.folder_path.set(config['download_folder'])
        except Exception as e:
            print(f"Error loading config: {e}")
            
    def save_config(self):
        """Save configuration to file."""
        try:
            config = {
                'download_folder': self.folder_path.get()
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Error saving config: {e}")
            
    def setup_modern_theme(self):
        """Setup modern purple theme with custom styling."""
        # Configure the root window
        self.root.configure(bg='#1a1a2e')
        
        # Create custom styles
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('Purple.TFrame', background='#16213e')
        style.configure('Purple.TLabel', background='#16213e', foreground='#e8e8e8', font=('Arial', 10))
        style.configure('Purple.TButton', 
                       background='#8b5cf6', 
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       font=('Arial', 10, 'bold'))
        style.map('Purple.TButton',
                 background=[('active', '#7c3aed'), ('pressed', '#6d28d9')])
        
        style.configure('Purple.TEntry', 
                       fieldbackground='#0f172a',
                       foreground='#e8e8e8',
                       borderwidth=0,
                       focuscolor='#8b5cf6',
                       font=('Arial', 10))
        
        style.configure('Purple.TCheckbutton', 
                       background='#16213e',
                       foreground='#e8e8e8',
                       font=('Arial', 10))
        
        style.configure('Purple.Horizontal.TProgressbar',
                       background='#8b5cf6',
                       troughcolor='#0f172a',
                       borderwidth=0,
                       lightcolor='#8b5cf6',
                       darkcolor='#8b5cf6')
        
        # Configure the main window background
        self.root.configure(bg='#1a1a2e')
        
    def create_rounded_frame(self, parent, **kwargs):
        """Create a frame with rounded corners effect."""
        frame = tk.Frame(parent, **kwargs)
        # Add rounded corner effect using canvas if needed
        return frame
        
    def run(self):
        """Start the application."""
        self.root.mainloop()

    def check_ffmpeg(self):
        """Check if FFmpeg is available on the system."""
        try:
            # First check if we're running from a bundled app
            if getattr(sys, 'frozen', False):
                # Running in a bundle, check for bundled FFmpeg
                bundle_dir = os.path.dirname(sys.executable)
                
                # Check multiple possible locations for bundled FFmpeg
                ffmpeg_locations = [
                    os.path.join(bundle_dir, 'Contents', 'Frameworks', 'ffmpeg'),
                    os.path.join(bundle_dir, 'ffmpeg'),
                    os.path.join(bundle_dir, 'Contents', 'MacOS', 'ffmpeg'),
                    os.path.join(bundle_dir, 'Contents', 'Resources', 'ffmpeg')
                ]
                
                for ffmpeg_path in ffmpeg_locations:
                    if os.path.exists(ffmpeg_path):
                        return True
                
                return False
            else:
                # Running in development, check system FFmpeg
                result = subprocess.run(['ffmpeg', '-version'], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=5)
                return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False
            
    def show_ffmpeg_warning(self):
        """Show a warning dialog about FFmpeg not being available."""
        warning_text = """FFmpeg is not available on your system.

This app requires FFmpeg for video downloads and audio conversion. 

To install FFmpeg:
1. Install Homebrew (if not already installed): https://brew.sh
2. Run: brew install ffmpeg

Audio-only downloads may still work without FFmpeg."""
        
        messagebox.showwarning("FFmpeg Not Found", warning_text)

    def cancel_download(self, download_id: int):
        """Cancel a download."""
        for download_info in self.active_downloads:
            if download_info['id'] == download_id:
                # Set cancellation flag
                download_info['cancelled'] = True
                
                # Update UI immediately
                self.update_download_progress(download_info, 0, "Cancelling...")
                download_info['cancel_button'].config(state="disabled", bg='#6b7280')
                
                # Schedule removal after a short delay
                self.root.after(2000, lambda: self.remove_download_item(download_info))
                break


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