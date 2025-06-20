#!/bin/bash

# DownBad - Build Script for macOS
echo "Building DownBad for macOS..."

# Activate virtual environment
source venv/bin/activate

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist

# Build the app
echo "Building app with PyInstaller..."
pyinstaller WebVideoDownloader.spec

# Check if build was successful
if [ -d "dist/DownBad.app" ]; then
    echo "✅ Build successful!"
    echo "App location: dist/DownBad.app"
    
    # Ask if user wants to install to Applications
    read -p "Install to Applications folder? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Installing to Applications..."
        cp -R "dist/DownBad.app" /Applications/
        echo "✅ App installed to Applications folder!"
        echo "You can now launch it from Launchpad or Applications folder."
    fi
else
    echo "❌ Build failed!"
    exit 1
fi 