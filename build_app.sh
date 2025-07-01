#!/bin/bash

# DownBad - Build Script for macOS (Electron Version)
echo "Building DownBad Electron App for macOS..."

# Navigate to Electron directory
cd DownBad-electron

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf dist build

# Copy FFmpeg to resources
echo "Copying FFmpeg to resources..."
mkdir -p resources
cp ../ffmpeg_bundled resources/ffmpeg
chmod +x resources/ffmpeg

# Build the app
echo "Building app with Electron Builder..."
npm run build

# Check if build was successful
if [ -d "dist/mac-arm64/DownBad.app" ]; then
    echo "✅ Build successful!"
    echo "App location: dist/mac-arm64/DownBad.app"
    
    # Install to Applications automatically
    echo "Installing to Applications..."
    cp -R "dist/mac-arm64/DownBad.app" /Applications/
    echo "✅ App installed to Applications folder!"
    echo "You can now launch it from Launchpad or Applications folder."
elif [ -d "dist/mac/DownBad.app" ]; then
    echo "✅ Build successful!"
    echo "App location: dist/mac/DownBad.app"
    
    # Install to Applications automatically
    echo "Installing to Applications..."
    cp -R "dist/mac/DownBad.app" /Applications/
    echo "✅ App installed to Applications folder!"
    echo "You can now launch it from Launchpad or Applications folder."
else
    echo "❌ Build failed!"
    exit 1
fi 