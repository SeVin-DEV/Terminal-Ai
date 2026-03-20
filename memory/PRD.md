# TermuxAI - AI-Powered Terminal Environment

## Product Overview
TermuxAI is a mobile-first coding and development environment powered by an AI agent. It provides a full Linux terminal (Termux-like) alongside an AI assistant that can see terminal activity, execute commands, and help with coding tasks.

## Core Features

### 1. First-Run Onboarding Wizard
- **Theme Selection**: 3 dark themes (Cyberpunk Void, Monokai Pro, Dracula)
- **AI Provider Config**: Support for OpenAI, Anthropic, Google Gemini, OpenAI-compatible endpoints, and Generic HTTP
- **Agent Customization**: Custom agent name and system prompt

### 2. Terminal Tab
- Full xterm.js terminal emulator connected to a real Linux PTY via WebSocket
- Special keys toolbar (ESC, TAB, CTRL, arrows) for mobile keyboard limitations
- CTRL shortcut panel (C, D, Z, L, A, E) for common terminal operations
- Shared terminal session between user and AI agent
- **Session Persistence**: Terminal buffer saved to MongoDB every 30 seconds and restored on startup

### 3. AI Agent Tab
- Chat interface with conversational AI powered by user's configured provider
- Terminal context awareness - AI sees recent terminal output
- Code block parsing with "Run" buttons to execute commands in terminal
- Auto-execute mode option for hands-free terminal automation
- Chat history persistence in MongoDB

### 4. File Browser Tab
- Full filesystem navigation with breadcrumb trail
- Directory listing with file type icons and sizes
- File viewer with syntax-aware display
- File editor with save functionality
- Create new files and folders via modal dialog
- Delete files/folders with confirmation
- Long-press to delete

### 5. Settings Tab
- Live theme switching
- AI provider reconfiguration
- Agent name and system prompt editing
- Auto-execute toggle
- API key management (secured, shows "saved" indicator)

### 6. APK Packaging
- `eas.json` configured with development, preview (APK), and production (AAB) profiles
- `app.json` configured with Android package name, permissions, and icons
- Build with: `cd frontend && eas build --platform android --profile preview`

## Architecture
- **Backend**: FastAPI with WebSocket support, PTY terminal management, AI provider proxy, file system API
- **Frontend**: Expo (React Native) with expo-router tabs, WebView/iframe xterm.js
- **Database**: MongoDB for config, chat history, terminal session persistence
- **Terminal**: Real Linux PTY shared via WebSocket to multiple clients

## AI Providers Supported
| Provider | Endpoint | Model Examples |
|----------|----------|----------------|
| OpenAI | api.openai.com/v1/chat/completions | gpt-4o, gpt-4-turbo |
| Anthropic | api.anthropic.com/v1/messages | claude-sonnet-4-20250514 |
| Google Gemini | generativelanguage.googleapis.com/v1beta | gemini-2.0-flash |
| OpenAI Compatible | Custom | Any OpenAI-format API |
| Generic HTTP | Custom | Any REST API |

## Tech Stack
- Expo SDK 54, React Native, TypeScript
- FastAPI, Python, Motor (async MongoDB)
- xterm.js 5.3.0 with WebSocket PTY bridge
- MongoDB for persistence

## APK Build Instructions
1. Install EAS CLI: `npm install -g eas-cli`
2. Login: `eas login`
3. Configure project: `eas build:configure`
4. Build APK: `eas build --platform android --profile preview`
5. Download APK from the build URL provided by EAS

## Self-Contained Termux Deployment
The app supports running entirely on a single Android device with Termux:

### Connection Flow
1. App launches → checks if backend is reachable at saved URL
2. If reachable → auto-routes to terminal/onboarding
3. If not → shows Connection Setup screen with:
   - **Local Mode**: Setup instructions for Termux + one-command auto-setup
   - **Remote Mode**: Enter URL for cloud/tunnel backend (Cloudflare, serveo, ngrok)

### Termux Auto-Setup (One Command)
```bash
curl -sSL https://your-backend-url/api/termux-setup | bash
```
This automatically:
- Installs Python, tmux
- Downloads server.py from the backend
- Creates start.sh / stop.sh / status.sh management scripts
- Configures tmux session with auto-restart on crash
- Enables termux-wake-lock to prevent sleep
- Optionally auto-starts on Termux boot (with Termux:Boot app)

### Backend Storage
- **Cloud**: Uses MongoDB (auto-detected via MONGO_URL env var)
- **Termux**: Uses JSON file storage (no MongoDB needed, fully self-contained)

### Server Management
- Start: `~/termuxai/start.sh` (tmux + wake-lock + auto-restart)
- Stop: `~/termuxai/stop.sh`
- Status: `~/termuxai/status.sh`
- View logs: `tmux attach -t termuxai`
