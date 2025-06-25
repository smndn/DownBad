# -*- mode: python ; coding: utf-8 -*-
import os
import subprocess
import shutil

block_cipher = None

# Find FFmpeg binary
def find_ffmpeg():
    """Find FFmpeg binary on the system."""
    try:
        # Try to find ffmpeg using which command
        result = subprocess.run(['which', 'ffmpeg'], capture_output=True, text=True)
        if result.returncode == 0:
            ffmpeg_path = result.stdout.strip()
            if os.path.exists(ffmpeg_path):
                return ffmpeg_path
    except:
        pass
    
    # Common FFmpeg locations on macOS
    common_paths = [
        '/opt/homebrew/bin/ffmpeg',
        '/usr/local/bin/ffmpeg',
        '/usr/bin/ffmpeg'
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            return path
    
    return None

# Get FFmpeg binary path
ffmpeg_path = find_ffmpeg()
binaries = []

temp_ffmpeg = None
if ffmpeg_path:
    print(f"Found FFmpeg at: {ffmpeg_path}")
    # Copy FFmpeg to a temp location with correct permissions
    temp_ffmpeg = os.path.abspath("ffmpeg_bundled")
    shutil.copy(ffmpeg_path, temp_ffmpeg)
    os.chmod(temp_ffmpeg, 0o755)
    binaries.append((temp_ffmpeg, 'Contents/Frameworks'))
else:
    print("Warning: FFmpeg not found. The app may not work properly for video downloads.")

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=binaries,
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DownBad',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DownBad',
)

app = BUNDLE(
    coll,
    name='DownBad.app',
    icon='app_icon.icns',
    bundle_identifier='com.downbad.app',
    info_plist={
        'CFBundleName': 'DownBad',
        'CFBundleDisplayName': 'DownBad',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleIdentifier': 'com.downbad.app',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.13.0',
        'NSRequiresAquaSystemAppearance': False,
    },
) 