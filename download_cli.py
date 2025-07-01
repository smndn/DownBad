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
import tempfile

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
        
        # Create safe filename
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        
        # If downloading both video and audio, merge them
        if download_video and download_audio:
            print("Downloading video and audio for merging...")
            merge_video_audio(url, folder, safe_title)
        else:
            # Download separately as before
            download_path = folder
            
            # Download video
            if download_video:
                print("Downloading video...")
                ydl_opts = {
                    'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
                    'format': 'bestvideo',  # Get best video quality (no audio) - matches original app
                    'no_check_certificate': True,  # Fix for macOS SSL issues
                }
                
                # Check for FFmpeg and add post-processor if available
                if check_ffmpeg():
                    ydl_opts['postprocessors'] = [{
                        'key': 'FFmpegVideoConvertor',
                        'preferedformat': 'mp4',
                    }]
                    # Set FFmpeg path
                    ffmpeg_path = get_ffmpeg_path()
                    if ffmpeg_path:
                        ydl_opts['ffmpeg_location'] = ffmpeg_path
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                print("Video download complete!")
            
            # Download audio
            if download_audio:
                print("Downloading audio...")
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
                if check_ffmpeg():
                    ffmpeg_path = get_ffmpeg_path()
                    if ffmpeg_path:
                        ydl_opts['ffmpeg_location'] = ffmpeg_path
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                print("Audio download complete!")
        
        print("All downloads completed successfully!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

def merge_video_audio(url, folder, safe_title):
    """Download video and audio separately, then merge them with FFmpeg."""
    if not check_ffmpeg():
        print("Error: FFmpeg is required for merging video and audio but was not found.")
        sys.exit(1)
    
    # Create temporary directory for intermediate files
    with tempfile.TemporaryDirectory() as temp_dir:
        print("Downloading video track...")
        
        # Download video (no audio)
        video_opts = {
            'outtmpl': os.path.join(temp_dir, 'video.%(ext)s'),
            'format': 'bestvideo',
            'no_check_certificate': True,
        }
        
        with yt_dlp.YoutubeDL(video_opts) as ydl:
            ydl.download([url])
        
        print("Downloading audio track...")
        
        # Download audio
        audio_opts = {
            'outtmpl': os.path.join(temp_dir, 'audio.%(ext)s'),
            'format': 'bestaudio',
            'no_check_certificate': True,
        }
        
        with yt_dlp.YoutubeDL(audio_opts) as ydl:
            ydl.download([url])
        
        # Find the downloaded files
        video_file = None
        audio_file = None
        
        for file in os.listdir(temp_dir):
            if file.startswith('video.'):
                video_file = os.path.join(temp_dir, file)
            elif file.startswith('audio.'):
                audio_file = os.path.join(temp_dir, file)
        
        if not video_file or not audio_file:
            print("Error: Could not find downloaded video or audio files.")
            sys.exit(1)
        
        print("Merging video and audio...")
        
        # Output file path
        output_file = os.path.join(folder, f"{safe_title}.mp4")
        
        # Use FFmpeg to merge video and audio
        ffmpeg_path = get_ffmpeg_path()
        if not ffmpeg_path:
            ffmpeg_path = 'ffmpeg'  # Use system ffmpeg
        
        merge_cmd = [
            ffmpeg_path,
            '-i', video_file,
            '-i', audio_file,
            '-c:v', 'copy',  # Copy video stream without re-encoding
            '-c:a', 'aac',   # Encode audio as AAC
            '-y',            # Overwrite output file if it exists
            output_file
        ]
        
        try:
            result = subprocess.run(merge_cmd, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                print(f"Successfully merged video and audio: {output_file}")
            else:
                print(f"FFmpeg error: {result.stderr}")
                sys.exit(1)
        except subprocess.TimeoutExpired:
            print("Error: FFmpeg merge operation timed out.")
            sys.exit(1)
        except Exception as e:
            print(f"Error running FFmpeg: {e}")
            sys.exit(1)

def check_ffmpeg():
    """Check if FFmpeg is available."""
    try:
        # Check bundled FFmpeg first
        if getattr(sys, 'frozen', False):
            bundle_dir = os.path.dirname(os.path.dirname(os.path.dirname(sys.executable)))
            ffmpeg_path = os.path.join(bundle_dir, 'Contents', 'Frameworks', 'ffmpeg')
            if os.path.exists(ffmpeg_path) and os.access(ffmpeg_path, os.X_OK):
                return True
        
        # Check system FFmpeg
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except:
        return False

def get_ffmpeg_path():
    """Get FFmpeg path if available."""
    try:
        # Check bundled FFmpeg first
        if getattr(sys, 'frozen', False):
            bundle_dir = os.path.dirname(os.path.dirname(os.path.dirname(sys.executable)))
            ffmpeg_path = os.path.join(bundle_dir, 'Contents', 'Frameworks', 'ffmpeg')
            if os.path.exists(ffmpeg_path) and os.access(ffmpeg_path, os.X_OK):
                return ffmpeg_path
        
        # Try to find system FFmpeg
        result = subprocess.run(['which', 'ffmpeg'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    return None

if __name__ == "__main__":
    main() 