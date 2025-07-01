#!/usr/bin/env python3
"""
Command-line interface for DownBad downloads.
Called by the Electron frontend.
"""

import sys
import os
import subprocess
import yt_dlp
import ssl

def main():
    if len(sys.argv) < 3:
        print("Usage: python download_cli.py <url> <folder> [video] [audio]")
        sys.exit(1)
    
    url = sys.argv[1]
    folder = sys.argv[2]
    download_video = 'video' in sys.argv[3:]
    download_audio = 'audio' in sys.argv[3:]
    
    if not download_video and not download_audio:
        print("Error: Must specify at least 'video' or 'audio'")
        sys.exit(1)
    
    print(f"Starting download...")
    print(f"URL: {url}")
    print(f"Folder: {folder}")
    print(f"Video: {download_video}, Audio: {download_audio}")
    
    try:
        # Get video info with SSL fix for macOS
        info_ydl_opts = {
            'quiet': True,
            'no_check_certificate': True,  # Fix for macOS SSL issues
        }
        info_ydl = yt_dlp.YoutubeDL(info_ydl_opts)
        info = info_ydl.extract_info(url, download=False)
        title = info.get('title', 'Unknown') if info else 'Unknown'
        print(f"Title: {title}")
        
        # Create safe filename for folder (only if downloading both video and audio)
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        
        if download_video and download_audio:
            # Create folder for both video and audio
            download_path = os.path.join(folder, safe_title)
            os.makedirs(download_path, exist_ok=True)
        else:
            # Use the main folder directly for single downloads
            download_path = folder
        
        # Download video
        if download_video:
            print("Stage: Starting video download...")
            
            # First, get available formats to debug
            info_ydl_opts = {
                'quiet': True,
                'no_check_certificate': True,
            }
            info_ydl = yt_dlp.YoutubeDL(info_ydl_opts)
            info = info_ydl.extract_info(url, download=False)
            
            print("Stage: Available video formats:")
            if info and 'formats' in info:
                for f in info['formats']:
                    if f.get('vcodec') != 'none':
                        print(f"Stage: - {f.get('format_id', 'N/A')}: {f.get('ext', 'N/A')} {f.get('resolution', 'N/A')} {f.get('vcodec', 'N/A')}")
            else:
                print("Stage: Could not get format information")
            
            # Choose format more carefully
            ydl_opts = {
                'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
                'format': 'bestvideo[ext=mp4][vcodec^=avc]/bestvideo[ext=mp4]/bestvideo',  # Prefer H.264 MP4
                'no_check_certificate': True,  # Fix for macOS SSL issues
            }
            
            print("Stage: Downloading highest quality H.264 MP4 available...")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            print("Stage: Video download complete!")
            
            # Check what was actually downloaded
            print("Stage: Checking downloaded file...")
            if os.path.exists(download_path):
                for filename in os.listdir(download_path):
                    if filename.lower().endswith('.mp4'):
                        file_path = os.path.join(download_path, filename)
                        print(f"Stage: Downloaded file: {filename}")
                        
                        # Check if it's actually a valid MP4
                        try:
                            import subprocess
                            ffmpeg_path = get_ffmpeg_path()
                            if ffmpeg_path:
                                probe_cmd = [ffmpeg_path, '-i', file_path]
                                result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
                                if result.returncode == 0:
                                    print(f"Stage: File analysis: {result.stderr}")
                                else:
                                    print(f"Stage: ⚠️ File may be corrupted or not a valid MP4")
                        except Exception as e:
                            print(f"Stage: Error analyzing file: {str(e)}")
        
        # Download audio
        if download_audio:
            print("Stage: Starting audio download...")
            ydl_opts = {
                'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
                'format': 'bestaudio',  # Get best audio quality - matches original app
                'no_check_certificate': True,  # Fix for macOS SSL issues
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'm4a',
                    'preferredquality': '192',
                }],
            }
            
            # Set FFmpeg path if available
            ffmpeg_path = get_ffmpeg_path()
            if ffmpeg_path:
                ydl_opts['ffmpeg_location'] = ffmpeg_path
                print("Stage: Audio will be converted to M4A format")
            else:
                print("Stage: FFmpeg not found - audio will be downloaded in original format")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            print("Stage: Audio download complete!")
        
        # Final summary
        print("Stage: Download Summary:")
        print(f"Stage: Download path: {download_path}")
        if os.path.exists(download_path):
            final_files = os.listdir(download_path)
            print(f"Stage: Final files in directory: {final_files}")
            for file in final_files:
                file_path = os.path.join(download_path, file)
                if os.path.isfile(file_path):
                    size = os.path.getsize(file_path)
                    print(f"Stage: - {file} ({size / (1024*1024):.1f} MB)")
        else:
            print(f"Stage: ❌ Download path not found: {download_path}")
        
        print("All downloads completed successfully!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

def check_ffmpeg():
    """Check if FFmpeg is available."""
    try:
        # Check bundled FFmpeg first (for packaged app)
        if getattr(sys, 'frozen', False):
            # Running in a packaged app
            resources_path = os.path.join(os.path.dirname(sys.executable), '..', 'Resources')
            bundled_ffmpeg = os.path.join(resources_path, 'ffmpeg')
            if os.path.exists(bundled_ffmpeg) and os.access(bundled_ffmpeg, os.X_OK):
                return True
        
        # Check system FFmpeg
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except:
        return False

def get_ffmpeg_path():
    """Get FFmpeg path if available."""
    try:
        # Check bundled FFmpeg first (for packaged app)
        if getattr(sys, 'frozen', False):
            # Running in a packaged app
            resources_path = os.path.join(os.path.dirname(sys.executable), '..', 'Resources')
            bundled_ffmpeg = os.path.join(resources_path, 'ffmpeg')
            if os.path.exists(bundled_ffmpeg) and os.access(bundled_ffmpeg, os.X_OK):
                return bundled_ffmpeg
        
        # Check for system FFmpeg
        result = subprocess.run(['which', 'ffmpeg'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    return None

if __name__ == "__main__":
    main() 