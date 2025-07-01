#!/bin/bash

# DownBad Installation Script
echo "🚀 Installing DownBad to Applications folder..."

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
    echo "❌ Error: $APP_PATH not found. Please run 'npm run build-mac' first."
    exit 1
fi

# Copy to Applications
echo "📂 Copying DownBad.app to /Applications..."
sudo cp -r "$APP_PATH" /Applications/

# Set permissions
echo "🔐 Setting permissions..."
sudo chown -R $(whoami):staff /Applications/DownBad.app
sudo chmod -R 755 /Applications/DownBad.app

echo "✅ DownBad has been installed to /Applications!"
echo "🎉 You can now find DownBad in your Applications folder or Launchpad."
echo ""
echo "To uninstall, simply delete DownBad.app from Applications folder." 