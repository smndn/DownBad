#!/bin/bash

# DownBad v2.0 Installation Script
echo "🚀 Installing DownBad v2.0 to Applications folder..."

# Detect architecture
ARCH=$(uname -m)
if [[ "$ARCH" == "arm64" ]]; then
    APP_PATH="dist/mac-arm64/DownBad.app"
    echo "📱 Detected Apple Silicon (ARM64)"
else
    APP_PATH="dist/mac/DownBad.app"
    echo "💻 Detected Intel (x64)"
fi

# Check if app exists
if [[ ! -d "$APP_PATH" ]]; then
    echo "❌ Error: $APP_PATH not found."
    echo "💡 Please run 'npm run build-mac' first to build the app."
    exit 1
fi

# Check if FFmpeg is bundled
FFMPEG_PATH="$APP_PATH/Contents/Resources/ffmpeg"
if [[ ! -f "$FFMPEG_PATH" ]]; then
    echo "⚠️  Warning: FFmpeg not found in bundled app. Audio downloads may not work."
else
    echo "✅ FFmpeg is bundled and ready for audio processing"
fi

# Check if Python environment is bundled
VENV_PATH="$APP_PATH/Contents/Resources/venv"
if [[ ! -d "$VENV_PATH" ]]; then
    echo "⚠️  Warning: Python virtual environment not found in bundled app."
else
    echo "✅ Python environment is bundled"
fi

# Copy to Applications
echo "📂 Copying DownBad.app to /Applications..."
sudo cp -r "$APP_PATH" /Applications/

# Set permissions
echo "🔐 Setting permissions..."
sudo chown -R $(whoami):staff /Applications/DownBad.app
sudo chmod -R 755 /Applications/DownBad.app

# Make sure FFmpeg is executable
if [[ -f "/Applications/DownBad.app/Contents/Resources/ffmpeg" ]]; then
    sudo chmod +x "/Applications/DownBad.app/Contents/Resources/ffmpeg"
    echo "✅ FFmpeg permissions set"
fi

echo ""
echo "🎉 DownBad v2.0 has been successfully installed!"
echo "📍 Location: /Applications/DownBad.app"
echo "🎯 Features:"
echo "   • Beautiful purple-themed UI"
echo "   • Multiple concurrent downloads"
echo "   • Real-time progress tracking"
echo "   • Video and audio merging"
echo "   • High-quality downloads"
echo ""
echo "💡 You can now:"
echo "   • Find DownBad in your Applications folder"
echo "   • Launch it from Spotlight (Cmd+Space, type 'DownBad')"
echo "   • Add it to your Dock"
echo ""
echo "🗑️  To uninstall: Simply delete DownBad.app from Applications folder" 