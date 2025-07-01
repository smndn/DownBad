# DownBad v2 (Electron)

This is the Electron-based version of DownBad.

## Features
- Modern, cross-platform UI (HTML/JS/React-ready)
- Calls your Python backend for video downloads

## Getting Started

### 1. Install dependencies
```
cd DownBad-electron
npm install
```

### 2. Run the app
```
npm start
```

### 3. Build for production
```
npm run build
```

## Python Backend
- The Electron app will call your Python scripts (e.g., `app.py`) using Node's `child_process`.
- Make sure your Python venv is set up and dependencies are installed.

## Structure
- `main.js` - Electron main process
- `renderer.js` - UI logic (vanilla JS, can be replaced with React)
- `index.html` - UI layout
- `package.json` - Project config

---

**You can now build a beautiful, robust UI and keep your Python download logic!** 