#!/usr/bin/env python3
"""
Test script to debug yt-dlp format selection
"""

import yt_dlp
import sys
import os

def test_format_selection(url):
    """Test format selection for a given URL."""
    print(f"Testing URL: {url}")
    print("=" * 50)
    
    # First, get all available formats
    ydl_opts = {'quiet': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            
            print(f"Title: {info.get('title', 'Unknown')}")
            print(f"Total formats available: {len(formats)}")
            print()
            
            # Filter and sort formats by resolution
            video_formats = []
            audio_formats = []
            complete_formats = []
            
            for fmt in formats:
                format_id = fmt.get('format_id', 'N/A')
                ext = fmt.get('ext', 'N/A')
                height = fmt.get('height', 0)
                width = fmt.get('width', 0)
                filesize = fmt.get('filesize', 'N/A')
                vcodec = fmt.get('vcodec', 'none')
                acodec = fmt.get('acodec', 'none')
                
                if vcodec != 'none' and acodec != 'none':
                    # This is a complete video+audio format
                    complete_formats.append((height, width, format_id, ext, filesize, fmt))
                elif vcodec != 'none':
                    # Video only
                    video_formats.append((height, width, format_id, ext, filesize, fmt))
                elif acodec != 'none':
                    # Audio only
                    audio_formats.append((format_id, ext, filesize, fmt))
            
            # Sort by height (highest first)
            video_formats.sort(key=lambda x: x[0], reverse=True)
            complete_formats.sort(key=lambda x: x[0], reverse=True)
            
            print("Video-only formats:")
            print("-" * 40)
            for height, width, format_id, ext, filesize, fmt in video_formats[:10]:
                print(f"  {height}p ({width}x{height}) - {format_id} - {ext} - {filesize} bytes")
            
            print()
            print("Complete video formats (video + audio):")
            print("-" * 40)
            for height, width, format_id, ext, filesize, fmt in complete_formats:
                print(f"  {height}p ({width}x{height}) - {format_id} - {ext} - {filesize} bytes")
            
            print()
            print("Audio-only formats:")
            print("-" * 40)
            for format_id, ext, filesize, fmt in audio_formats[:5]:
                print(f"  {format_id} - {ext} - {filesize} bytes")
            
            print()
            
            # Test different format strings
            test_formats = [
                'best',
                'bestvideo+bestaudio',
                'bestvideo[height>=1080]+bestaudio',
                'bestvideo[height>=720]+bestaudio',
                'bestvideo[height>=360]+bestaudio',
                'bestvideo+bestaudio/best'
            ]
            
            print("Testing format selection:")
            print("-" * 40)
            
            for format_str in test_formats:
                print(f"\nTesting format: {format_str}")
                try:
                    test_opts = {'format': format_str, 'quiet': True}
                    with yt_dlp.YoutubeDL(test_opts) as test_ydl:
                        # Get the selected format info
                        selected_info = test_ydl.extract_info(url, download=False)
                        selected_formats = selected_info.get('requested_formats', [selected_info])
                        
                        for fmt in selected_formats:
                            height = fmt.get('height', 'N/A')
                            format_id = fmt.get('format_id', 'N/A')
                            ext = fmt.get('ext', 'N/A')
                            print(f"  Selected: {height}p - {format_id} - {ext}")
                            
                except Exception as e:
                    print(f"  Error: {e}")
                        
        except Exception as e:
            print(f"Error extracting info: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_formats.py <youtube_url>")
        sys.exit(1)
    
    url = sys.argv[1]
    test_format_selection(url) 