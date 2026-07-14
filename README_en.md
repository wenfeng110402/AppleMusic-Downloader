# AppleMusic Downloader

![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/wenfeng110402/AppleMusic-Downloader/total?style=social&logo=GitHub)

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](https://github.com/wenfeng110402/AppleMusic-Downloader)
![GitHub License](https://img.shields.io/github/license/wenfeng110402/AppleMusic-Downloader?style=social)

- [Chinese README](README.md)

---

AppleMusic Downloader is a powerful Apple Music download tool that supports downloading songs, music videos, lyrics, and cover art.

The project offers three usage modes:

| Mode | Use Case |
|------|----------|
| **CLI** | Terminal users, install via `pip install applemusic-dl` |
| **API Server** | Developers, integrate download capabilities into your own apps |
| **Desktop App** | General users, download the packaged installer and run |

---

## Acknowledgments

This project uses code from [gamdl (Glomatico's Apple Music Downloader)](https://github.com/glomatico/gamdl) and [yt-dlp](https://github.com/yt-dlp/yt-dlp). We sincerely thank all contributors to gamdl and yt-dlp for their outstanding work in the open-source community.

---

## Table of Contents

- [Installation](#installation)
  - [Method 1: pip install (recommended)](#method-1-pip-install-recommended)
  - [Method 2: Desktop installer](#method-2-desktop-installer-windows-only)
  - [Method 3: From source](#method-3-from-source)
- [CLI Usage](#cli-usage)
- [API Server Deployment](#api-server-deployment)
  - [Starting the API Server](#starting-the-api-server)
  - [API Endpoints](#api-endpoints)
  - [API Client Examples](#api-client-examples)
- [Frontend Deployment](#frontend-deployment)
  - [Frontend Features](#frontend-features)
  - [Development Mode](#development-mode)
  - [Production Mode](#production-mode)
- [Desktop App](#desktop-app)
- [Requirements](#requirements)
- [Supported Link Types](#supported-link-types)
- [Project Structure](#project-structure)
- [Disclaimer](#disclaimer)

---

## Installation

### Method 1: pip install (recommended)

```bash
pip install applemusic-dl
```

Use the `amdl` command directly after installation:

```bash
amdl --help
```

For desktop GUI mode, install with desktop dependencies:

```bash
pip install applemusic-dl[desktop]
```

### Method 2: Desktop installer (Windows only)

1. Download the latest installer from the [Releases](https://github.com/wenfeng110402/AppleMusic-Downloader/releases) page
2. Run `AppleMusicDownloader_Setup.exe` and follow the prompts
3. Find "Apple Music Downloader" in your Start menu

### Method 3: From source

```bash
git clone https://github.com/wenfeng110402/AppleMusic-Downloader.git
cd AppleMusic-Downloader
pip install -r requirements.txt
pip install -e .
```

---

## CLI Usage

```bash
# View help
amdl --help

# Download a single track
amdl -c /path/to/cookies.txt "https://music.apple.com/us/album/left-and-right/1630451412?i=1630451413"

# Download an entire album
amdl -c /path/to/cookies.txt "https://music.apple.com/us/album/left-and-right/1630451412"

# Specify output directory
amdl -c /path/to/cookies.txt -o "./My Music" "https://music.apple.com/..."

# Specify codec and audio format
amdl -c /path/to/cookies.txt --codec-song aac-256k --audio-format mp3 "https://music.apple.com/..."
```

---

## API Server Deployment

The project includes a built-in FastAPI backend that can be deployed independently as an API service.

### Starting the API Server

```bash
# Start after installation
python -m amdl --server

# Custom port
python -m amdl --server --port 8080

# Allow external access (use a reverse proxy in production)
python -m amdl --server --host 0.0.0.0 --port 8000
```

Visit `http://127.0.0.1:8000/docs` for the interactive API documentation (Swagger UI).

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/info` | Get supported codecs, formats, etc. |
| GET | `/api/dependencies` | Check external dependencies (ffmpeg, N_m3u8DL-RE) |
| POST | `/api/tasks` | Submit a download task |
| GET | `/api/tasks` | List all tasks |
| GET | `/api/tasks/{task_id}` | Get task details |
| DELETE | `/api/tasks/{task_id}` | Cancel a task |
| WebSocket | `/api/ws/{task_id}` | Real-time download progress |
| GET | `/api/settings` | Read user preferences |
| POST | `/api/settings` | Save user preferences |
| DELETE | `/api/temp` | Clean temp directory |

See [docs/api.md](docs/api.md) for detailed API documentation.

### API Client Examples

**Python client:**

```python
import requests

# Submit a download task
resp = requests.post("http://127.0.0.1:8000/api/tasks", json={
    "urls": ["https://music.apple.com/us/album/left-and-right/1630451412?i=1630451413"],
    "cookies_path": "/path/to/cookies.txt",
    "output_path": "./Apple Music"
})
task = resp.json()
print(f"Task ID: {task['task_id']}")

# Poll for task status
import time
while True:
    status = requests.get(f"http://127.0.0.1:8000/api/tasks/{task['task_id']}").json()
    print(f"Status: {status['status']}, Progress: {status['progress']}")
    if status["status"] in ("completed", "failed", "cancelled"):
        break
    time.sleep(3)
```

**curl client:**

```bash
# Submit a task
curl -X POST http://127.0.0.1:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://music.apple.com/us/album/left-and-right/1630451412"],
    "cookies_path": "/path/to/cookies.txt"
  }'

# Query task status
curl http://127.0.0.1:8000/api/tasks/<task_id>
```

**WebSocket real-time progress (Python):**

```python
import asyncio
import websockets
import json

async def listen_progress(task_id: str):
    uri = f"ws://127.0.0.1:8000/api/ws/{task_id}"
    async with websockets.connect(uri) as ws:
        # Send ping to keep alive
        await ws.send(json.dumps({"type": "ping"}))
        async for msg in ws:
            data = json.loads(msg)
            print(f"Progress: {data}")
            if data.get("type") == "completed":
                break

asyncio.run(listen_progress("your-task-id"))
```

---

## Frontend Deployment

The project includes a Next.js-based web frontend that can be deployed independently.

### Frontend Features

The web frontend provides a complete graphical interface, including:

- **Bilingual UI (i18n)** — Switch between Chinese and English with one click
- **Dark/Light themes** — CSS variable driven, toggle between modes
- **Backend status indicator** — Real-time green/red dot in the sidebar
- **Download form** — Multi-URL input, file browser selector (native dialog in desktop mode)
- **Audio format selection** — Support MP3/FLAC/WAV/AAC conversion
- **Persistent settings** — Auto-save to backend on every change, survives page refresh
- **Download queue** — Real-time task list, progress bars, auto-refresh (3s interval)
- **Task logs** — Expandable detailed runtime logs for each task
- **Dependency check** — One-click verification of FFmpeg / N_m3u8DL-RE etc.
- **Dark-themed UI** — Frosted glass质感, immersive dark design

### Development Mode

```bash
cd src/fronted
npm install
npm run dev
```

In development mode, the frontend runs on `http://localhost:3000` with API requests proxied to `http://127.0.0.1:8000`.

Start the backend simultaneously:

```bash
python -m amdl --server
```

### Production Mode

```bash
cd src/fronted
npm install
npm run build
```

Build output is in `src/fronted/out/`, deployable to any static file server (Nginx, Caddy, etc.).

**Nginx configuration example:**

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend static files
    root /path/to/src/fronted/out;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # API reverse proxy to backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Docker deployment:**

```bash
# Backend
docker run -d --name amdl-api \
  -p 8000:8000 \
  -v /path/to/cookies.txt:/cookies.txt \
  -v /path/to/output:/output \
  --restart unless-stopped \
  python:3.10-slim \
  sh -c "pip install applemusic-dl && python -m amdl --server --host 0.0.0.0"

# Frontend (serve static files with Nginx)
docker run -d --name amdl-frontend \
  -p 80:80 \
  -v /path/to/src/fronted/out:/usr/share/nginx/html \
  --restart unless-stopped \
  nginx:alpine
```

---

## Desktop App

In desktop mode, the backend service and frontend Web UI are integrated in a single window:

```bash
# Launch desktop app
python -m amdl --desktop

# Or simply launch (auto-detect)
python -m amdl
```

The desktop app is built on pywebview and works on Windows, macOS, and Linux.

> **🐧 Linux users**: pywebview on Linux requires Qt WebEngine. Before launching desktop mode, install the system dependencies:
> ```bash
> sudo apt update && sudo apt install -y python3-pyqt5 python3-pyqt5.qtwebengine libqt5webkit5-dev
> pip install pywebview[qt]
> ```

> **🍎 macOS users**: Files downloaded from Releases are flagged with a quarantine attribute by macOS. Remove it before first launch:
>
> **.app (Desktop app)**:  
> ```bash
> xattr -d com.apple.quarantine /Applications/AppleMusicDownloader.app
> ```
> Or right-click → Open (instead of double-clicking), then click "Open" in the dialog.
>
> If you see "is damaged and can't be opened", run this command and retry:
> ```bash
> sudo xattr -rd com.apple.quarantine /Applications/AppleMusicDownloader.app
> ```
>

## Requirements

### Required

- Python 3.10 or higher
- A valid Apple Music subscription
- Netscape-format cookies file
- FFmpeg

**Obtaining a cookies file:**

- Firefox users: Use the [Export Cookies](https://addons.mozilla.org/firefox/addon/export-cookies-txt/) extension
- Chromium users: Use the [Open Cookies.txt](https://chromewebstore.google.com/detail/open-cookiestxt/gdocmgbfkjnnpapoeobnolbbkoibbcif) extension

**Installing FFmpeg:**

- macOS: `brew install ffmpeg`
- Linux: `apt install ffmpeg` / `pacman -S ffmpeg`
- Windows: Download from [ffmpeg.org](https://ffmpeg.org/)

### Optional

- [MP4Box](https://gpac.io/downloads/gpac-nightly-builds/): Alternative remux mode
- [N_m3u8DL-RE](https://github.com/nilaoda/N_m3u8DL-RE/releases/latest): Alternative download mode

---

## Supported Link Types

- Singles
- Albums
- Playlists
- Music Videos
- Artist Profiles
- Post Videos

> **💡 About codec selection**: When selecting Atmos or AC3 in the settings, the downloader will automatically fall back to AAC stereo if the track is not available in the selected format. Not all songs have Atmos/AC3 versions (typically only songs released after 2021). Only tracks marked with "Dolby Atmos" in Apple Music support Atmos downloads.

---

## Project Structure

```
AppleMusic-Downloader/
├── src/
│   ├── amdl/              # Python backend package
│   │   ├── server.py      # FastAPI server entry point
│   │   ├── cli.py         # CLI entry point
│   │   ├── core_downloader.py  # Core download logic
│   │   ├── task_manager.py     # Task queue management
│   │   ├── converter.py        # Format conversion
│   │   └── ...
│   └── fronted/           # Next.js frontend
│       ├── app/
│       │   ├── components/  # Frontend components
│       │   ├── service.tsx  # API client wrapper
│       │   └── i18n.tsx     # Internationalization
│       └── next.config.ts
├── docs/
│   └── api.md             # API documentation
├── pyproject.toml          # Package configuration
├── requirements.txt
└── README.md
```

---

## Disclaimer

This tool is for educational and research purposes only. Any use that violates laws or infringes on the rights of others is strictly prohibited.

1. This project does not directly provide or store any copyrighted content. Users must independently provide valid credentials (e.g., a valid Apple Music subscription and cookies file) to use its features.
2. The development team assumes no responsibility for how users use this tool. Any legal or copyright disputes arising from its use are the sole responsibility of the user.
3. This project is implemented based on code from [gamdl](https://github.com/glomatico/gamdl) and [yt-dlp](https://github.com/yt-dlp/yt-dlp) and is not directly affiliated with the original projects' authors. If there are any objections, please contact us for assistance.
4. Users must ensure compliance with local laws and regulations when using this tool.

By using this tool, you agree to comply with all applicable laws and assume full responsibility for your actions.