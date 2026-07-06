# AMDL API Guide

Base URL: `http://127.0.0.1:8000`

---

## System

### GET /api/health

Health check.

**Response:**
```json
{
  "status": "ok",
  "version": "2.0.0"
}
```

---

### GET /api/info

Get supported options for dynamic rendering.

**Response:**
```json
{
  "api_version": "2.0.0",
  "supported_codecs_song": [
    {"value": "AAC_WEB", "label": "AAC_WEB"},
    {"value": "AAC_ALAC", "label": "AAC_ALAC"},
    {"value": "AAC_256K", "label": "AAC_256K"}
  ],
  "supported_codecs_music_video": [...],
  "supported_cover_formats": [...],
  "supported_download_modes": [...],
  "supported_audio_conversion_formats": ["mp3","flac","wav","aac","m4a","ogg","alac"],
  "supported_video_conversion_formats": ["mp4","mov","mkv","avi","webm"]
}
```

---

### GET /api/dependencies

Check external dependencies (ffmpeg, N_m3u8DL-RE).

**Query params:**

| Param | Type | Default | Description |
|---|---|---|---|
| `ffmpeg_path` | string | `""` | Custom ffmpeg path |
| `nm3u8dlre_path` | string | `""` | Custom N_m3u8DL-RE path |

**Response:**
```json
{
  "all_ok": true,
  "dependencies": [
    {
      "name": "ffmpeg",
      "found": true,
      "path": "/opt/homebrew/bin/ffmpeg",
      "version": "ffmpeg version 7.0 ..."
    },
    {
      "name": "N_m3u8DL-RE",
      "found": false,
      "path": null,
      "version": null
    }
  ]
}
```

---

### DELETE /api/temp

Clean the temp directory.

**Response:**
```json
{"message": "Cleaned 15 items from temp directory"}
```

---

## Tasks

### POST /api/tasks

Submit a download task.

**Request body:**

```json
{
  "urls": ["https://music.apple.com/us/album/xxx"],
  "cookies_path": "/path/to/cookies.txt",

  "output_path": "./Apple Music",
  "temp_path": "./temp",
  "ffmpeg_path": "ffmpeg",
  "nm3u8dlre_path": "N_m3u8DL-RE",

  "download_mode": "YTDLP",
  "codec_song": "AAC_WEB",
  "codec_music_video": "H264",
  "quality_uploaded_video": "BEST",
  "synced_lyrics_format": "LRC",
  "cover_format": "JPG",
  "cover_size": 1200,

  "audio_format": null,
  "video_format": null,

  "overwrite": false,
  "save_cover": false,
  "save_playlist": false,
  "no_synced_lyrics": false,
  "language": "en-US"
}
```

**Required fields:** `urls`, `cookies_path`

**Optional fields with defaults shown above.** Omit or pass `null` for defaults.

**Enum values:**

| Field | Options |
|---|---|
| `download_mode` | `YTDLP`, `FFMPEG` |
| `codec_song` | See `/api/info` |
| `codec_music_video` | See `/api/info` |
| `cover_format` | `JPG`, `PNG`, `WEBP`, `TIFF` |
| `audio_format` | `mp3`, `flac`, `wav`, `aac`, `m4a`, `ogg`, `alac`, or `null` |
| `video_format` | `mp4`, `mov`, `mkv`, `avi`, `webm`, or `null` |

**Response:**
```json
{
  "task_id": "task-abc123",
  "status": "pending",
  "message": "Task submitted"
}
```

---

### GET /api/tasks

List all tasks (newest first).

**Response:**
```json
{
  "tasks": [
    {
      "id": "task-abc123",
      "status": "running",
      "progress": {"completed": 3, "total": 10, "percent": 30.0},
      "error_count": 0,
      "message": "Downloading track 4 of 10 ...",
      "created_at": "2026-07-05T12:00:00Z",
      "updated_at": "2026-07-05T12:01:15Z",
      "urls": ["https://music.apple.com/us/album/xxx"]
    }
  ],
  "total": 1
}
```

**Task status values:** `pending`, `running`, `completed`, `failed`, `cancelled`

---

### GET /api/tasks/{task_id}

Get details of a specific task.

**Response:** Same as single task object in list response above.

**Error (404):**
```json
{"detail": "Task not found: task-xxx"}
```

---

### DELETE /api/tasks/{task_id}

Cancel a pending or running task.

**Response:**
```json
{"message": "Task cancelled", "task_id": "task-abc123"}
```

**Error (404):**
```json
{"detail": "Task not found or finished: task-xxx"}
```

---

## WebSocket

### WS /api/ws/{task_id}

Real-time download progress stream.

Connect after submitting a task via `POST /api/tasks`.

**Messages received from server:**

```json
// Initial state on connect
{"type": "subscribed", "task_id": "task-abc123", "status": "pending", "progress": {...}}

// Progress update
{"type": "progress", "completed": 5, "total": 10, "percent": 50.0}

// Status change
{"type": "status", "status": "completed", "message": "Done"}

// Error
{"type": "error", "message": "Task not found"}
```

**Messages sent by client:**

```json
// Keep-alive ping
{"type": "ping"}

// Server responds
{"type": "pong"}
```

---

## Static Files (Desktop Mode)

When running in desktop mode (`--desktop`), the API also serves the Next.js frontend build:

| Route | Serves |
|---|---|
| `GET /` | `src/fronted/out/index.html` |
| `GET /*` | `src/fronted/out/*` (SPA fallback) |

No separate frontend dev server needed.

---

## Quick Start

```bash
# Terminal 1: Start backend
python src/amdl/server.py

# Or start as desktop app (requires npm run build first)
python src/amdl/server.py --desktop

# Test health
curl http://127.0.0.1:8000/api/health

# Check dependencies
curl http://127.0.0.1:8000/api/dependencies

# Submit a download task
curl -X POST http://127.0.0.1:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"urls":["https://music.apple.com/us/album/xxx"],"cookies_path":"/path/to/cookies.txt"}'

# List tasks
curl http://127.0.0.1:8000/api/tasks

# Cancel a task
curl -X DELETE http://127.0.0.1:8000/api/tasks/task-abc123

# Clean temp
curl -X DELETE http://127.0.0.1:8000/api/temp
```