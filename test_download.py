#!/usr/bin/env python3
"""
Test script to debug video download with detailed logging
"""

import yt_dlp
import sys
import os

def test_download(url):
    """Test download with detailed logging."""
    print(f"Testing download for: {url}")
    print("=" * 60)
    
    # First, get all available formats
    print("1. Getting available formats...")
    ydl_opts = {'quiet': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            
            print(f"Title: {info.get('title', 'Unknown')}")
            print(f"Total formats available: {len(formats)}")
            print()
            
            # Find video-only and audio-only formats
            video_formats = []
            audio_formats = []
            
            for fmt in formats:
                format_id = fmt.get('format_id', 'N/A')
                height = fmt.get('height', 0)
                width = fmt.get('width', 0)
                filesize = fmt.get('filesize', 'N/A')
                vcodec = fmt.get('vcodec', 'none')
                acodec = fmt.get('acodec', 'none')
                ext = fmt.get('ext', 'N/A')
                
                if vcodec != 'none' and acodec == 'none':
                    # Video-only format
                    video_formats.append((height, width, format_id, ext, filesize, fmt))
                elif vcodec == 'none' and acodec != 'none':
                    # Audio-only format
                    audio_formats.append((format_id, ext, filesize, fmt))
            
            # Sort video formats by height (highest first)
            video_formats.sort(key=lambda x: x[0], reverse=True)
            
            print("2. Available video-only formats:")
            print("-" * 50)
            for height, width, format_id, ext, filesize, fmt in video_formats[:10]:
                print(f"  {height}p ({width}x{height}) - {format_id} - {ext} - {filesize} bytes")
            
            print()
            print("3. Available audio-only formats:")
            print("-" * 50)
            for format_id, ext, filesize, fmt in audio_formats[:5]:
                print(f"  {format_id} - {ext} - {filesize} bytes")
            
            print()
            
            if video_formats and audio_formats:
                best_video_height = video_formats[0][0]
                best_video_id = video_formats[0][2]
                best_audio_id = audio_formats[0][0]
                
                print(f"4. Selected formats:")
                print(f"   Video: {best_video_height}p (format {best_video_id})")
                print(f"   Audio: format {best_audio_id}")
                print()
                
                # Test the download
                print("5. Testing download with selected formats...")
                download_opts = {
                    'format': f'{best_video_id}+{best_audio_id}',
                    'outtmpl': 'test_download_%(title)s.%(ext)s',
                    'merge_output_format': 'mp4',
                    'verbose': True
                }
                
                print(f"Download options: {download_opts}")
                print()
                
                with yt_dlp.YoutubeDL(download_opts) as download_ydl:
                    download_ydl.download([url])
                    
                print("6. Download completed!")
                
            else:
                print("ERROR: No video-only or audio-only formats found!")
                
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_download.py <youtube_url>")
        sys.exit(1)
    
    url = sys.argv[1]
    test_download(url) 