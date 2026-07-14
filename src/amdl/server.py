from __future__ import annotations

import json
import logging
import os
import sys
import shutil
import subprocess
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path

# ── Windows: hide cmd window for subprocess calls ───────────
if sys.platform == "win32":
    _SUBPROCESS_FLAGS = subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
else:
    _SUBPROCESS_FLAGS = 0

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel, Field, field_validator

from amdl.enums import (
    CoverFormat,
    DownloadMode,
    MusicVideoCodec,
    SongCodec,
    SyncedLyricsFormat,
    UploadedVideoQuality,
)
from amdl.task_manager import get_task_manager
from amdl.dependency_manager import BIN_DIR, DATA_DIR
from amdl.dependency_manager import ensure_dependencies_async

logger = logging.getLogger("amdl.server")

# ── Path resolution（兼容 PyInstaller 打包） ───────────────
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys._MEIPASS)  # type: ignore[attr-defined]  (只读)
    FRONTEND_OUT = BASE_DIR / "frontend_out"
else:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    FRONTEND_OUT = BASE_DIR / "src" / "fronted" / "out"

# DATA_DIR / TEMP_DIR / SETTINGS_FILE — 统一从 dependency_manager 获取
TEMP_DIR = DATA_DIR / "temp"
SETTINGS_FILE = DATA_DIR / "settings.json"


def _add_bin_to_path() -> None:
    """Add BIN_DIR to PATH so shutil.which can find bundled binaries."""
    bin_str = str(BIN_DIR)
    current = os.environ.get("PATH", "")
    if bin_str not in current:
        os.environ["PATH"] = f"{bin_str}{os.pathsep}{current}"


_add_bin_to_path()

# ── 图标：根据平台自动选择 ────────────────────────────────
import platform as _platform
if _platform.system() == "Darwin":
    ICON_FILE = BASE_DIR / "icon.icns"
elif _platform.system() == "Windows":
    ICON_FILE = BASE_DIR / "icon.ico"
else:
    ICON_FILE = BASE_DIR / "icon.png"


# ═══════════════════════════════════════════════════════════════
# Lifespan
# ═══════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    tm = get_task_manager()
    tm.start()
    # Auto-download missing dependencies in background
    ensure_dependencies_async()
    logger.info("AMDL server started")
    yield
    await tm.stop()
    logger.info("AMDL server stopped")


# ═══════════════════════════════════════════════════════════════
# FastAPI app
# ═══════════════════════════════════════════════════════════════

app = FastAPI(
    title="AMDL API",
    description="Apple Music Downloader API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════
# Models
# ═══════════════════════════════════════════════════════════════

class DownloadRequest(BaseModel):
    urls: list[str] = Field(..., min_length=1)
    cookies_path: str = Field(...)
    output_path: str = Field(default="./Apple Music")
    temp_path: str = Field(default="./temp")
    wvd_path: str | None = Field(default=None)
    nm3u8dlre_path: str = Field(default="N_m3u8DL-RE")
    ffmpeg_path: str = Field(default="ffmpeg")
    download_mode: DownloadMode = Field(default=DownloadMode.YTDLP)
    codec_song: SongCodec = Field(default=SongCodec.AAC_WEB)
    codec_music_video: MusicVideoCodec = Field(default=MusicVideoCodec.H264)
    quality_post: UploadedVideoQuality = Field(default=UploadedVideoQuality.BEST)
    synced_lyrics_format: SyncedLyricsFormat = Field(default=SyncedLyricsFormat.LRC)
    cover_format: CoverFormat = Field(default=CoverFormat.JPG)
    cover_size: int = Field(default=1200, ge=50, le=5000)
    truncate: int | None = Field(default=None, ge=0)
    audio_format: str | None = Field(default=None)
    video_format: str | None = Field(default=None)
    template_folder_album: str = Field(default="{album_artist}/{album}")
    template_folder_compilation: str = Field(default="Compilations/{album}")
    template_file_single_disc: str = Field(default="{track:02d} {title}")
    template_file_multi_disc: str = Field(default="{disc}-{track:02d} {title}")
    template_folder_no_album: str = Field(default="{artist}/Unknown Album")
    template_file_no_album: str = Field(default="{title}")
    template_file_playlist: str = Field(default="Playlists/{playlist_artist}/{playlist_title}")
    template_date: str = Field(default="%Y-%m-%dT%H:%M:%SZ")
    exclude_tags: str | None = Field(default=None)
    overwrite: bool = Field(default=False)
    save_cover: bool = Field(default=False)
    save_playlist: bool = Field(default=False)
    synced_lyrics_only: bool = Field(default=False)
    no_synced_lyrics: bool = Field(default=False)
    disable_music_video_skip: bool = Field(default=False)
    read_urls_as_txt: bool = Field(default=False)
    language: str = Field(default="en-US")
    log_level: str = Field(default="INFO")

    @field_validator("cookies_path")
    @classmethod
    def _validate_cookies(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("cookies_path must not be empty")
        v = v.strip()
        p = Path(v)
        if not p.exists():
            raise ValueError(f"Cookies file not found: {v}")
        if not p.is_file():
            raise ValueError(f"Not a file: {v}")
        return v

    @field_validator("log_level")
    @classmethod
    def _validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"Invalid log level: {v}, options: {', '.join(sorted(allowed))}")
        return v.upper()

    @field_validator("audio_format")
    @classmethod
    def _validate_audio_fmt(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if v.lower() not in {"mp3", "flac", "wav", "aac", "m4a", "ogg", "wma", "alac"}:
            raise ValueError(f"Unsupported format: {v}")
        return v.lower()

    @field_validator("video_format")
    @classmethod
    def _validate_video_fmt(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if v.lower() not in {"mp4", "mov", "mkv", "avi", "wmv", "flv", "webm"}:
            raise ValueError(f"Unsupported format: {v}")
        return v.lower()


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "2.0.0"


class DependencyCheckItem(BaseModel):
    name: str
    found: bool
    path: str | None = None
    version: str | None = None


class DependencyCheckResponse(BaseModel):
    all_ok: bool
    dependencies: list[DependencyCheckItem]


class TaskSubmitResponse(BaseModel):
    task_id: str
    status: str
    message: str


class TaskInfoResponse(BaseModel):
    id: str
    status: str
    progress: dict
    error_count: int
    message: str
    logs: list[str] = Field(default_factory=list)
    created_at: str
    updated_at: str
    urls: list[str]


class TaskListResponse(BaseModel):
    tasks: list[TaskInfoResponse]
    total: int


class ApiInfoResponse(BaseModel):
    api_version: str
    supported_codecs_song: list[dict[str, str]]
    supported_codecs_music_video: list[dict[str, str]]
    supported_cover_formats: list[dict[str, str]]
    supported_download_modes: list[dict[str, str]]
    supported_audio_conversion_formats: list[str]
    supported_video_conversion_formats: list[str]


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

# ── well-known fallback paths per platform ──────────────────
_HOMEBREW_PATHS: list[str] = [
    "/opt/homebrew/bin",   # Apple Silicon
    "/usr/local/bin",       # Intel Mac
    "/home/linuxbrew/.linuxbrew/bin",
]

_KNOWN_EXTENSIONS: dict[str, str | None] = {
    "N_m3u8DL-RE": ".exe" if sys.platform == "win32" else None,
    "MP4Box": ".exe" if sys.platform == "win32" else None,
    "ffmpeg": ".exe" if sys.platform == "win32" else None,
}


def _find_executable(name: str, custom_path: str | None = None) -> DependencyCheckItem:
    """Find an executable, searching PATH → BIN_DIR → Homebrew paths."""
    target = custom_path or name

    # 1) shutil.which — respects PATH (including BIN_DIR added above)
    found_path = shutil.which(target)

    # 2) BIN_DIR direct lookup (for cases where BIN_DIR isn't in PATH yet)
    if not found_path:
        ext = _KNOWN_EXTENSIONS.get(name, None) or ""
        candidate = BIN_DIR / f"{target}{ext}"
        if candidate.exists():
            found_path = str(candidate)

    # 3) Homebrew fallback (macOS / Linux)
    if not found_path and sys.platform != "win32":
        for brew_dir in _HOMEBREW_PATHS:
            candidate = Path(brew_dir) / target
            if candidate.exists():
                found_path = str(candidate)
                break

    if found_path and Path(found_path).exists():
        resolved = Path(found_path).resolve()
        try:
            result = subprocess.run(
                [str(resolved), "-version"] if name in ("ffmpeg", "MP4Box") else [str(resolved), "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=_SUBPROCESS_FLAGS,
            )
            version_line = (result.stdout or result.stderr).split("\n")[0]
        except Exception:
            version_line = None
        return DependencyCheckItem(
            name=name,
            found=True,
            path=str(resolved),
            version=version_line,
        )

    return DependencyCheckItem(name=name, found=False)


# ═══════════════════════════════════════════════════════════════
# API — System
# ═══════════════════════════════════════════════════════════════

@app.get("/api/health", response_model=HealthResponse, tags=["system"])
async def health_check():
    return HealthResponse()

@app.get("/api/settings", tags=["system"])
async def get_settings():
    if SETTINGS_FILE.exists():
        try:
            return JSONResponse(content=json.loads(SETTINGS_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass
    return JSONResponse(content={})


@app.post("/api/settings", tags=["system"])
async def save_settings(payload: dict):
    # 读取已有设置，做合并而非覆盖
    existing: dict = {}
    if SETTINGS_FILE.exists():
        try:
            existing = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    existing.update(payload)
    SETTINGS_FILE.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    return JSONResponse(content={"status": "ok"})



@app.get("/api/info", response_model=ApiInfoResponse, tags=["system"])
async def get_api_info():
    return ApiInfoResponse(
        api_version="2.0.0",
        supported_codecs_song=[{"value": c.value, "label": c.name} for c in SongCodec],
        supported_codecs_music_video=[{"value": c.value, "label": c.name} for c in MusicVideoCodec],
        supported_cover_formats=[{"value": c.value, "label": c.name} for c in CoverFormat],
        supported_download_modes=[{"value": c.value, "label": c.name} for c in DownloadMode],
        supported_audio_conversion_formats=["mp3", "flac", "wav", "aac", "m4a", "ogg", "alac"],
        supported_video_conversion_formats=["mp4", "mov", "mkv", "avi", "webm"],
    )


@app.get("/api/dependencies", response_model=DependencyCheckResponse, tags=["system"])
async def check_dependencies(ffmpeg_path: str = "", nm3u8dlre_path: str = "", mp4box_path: str = ""):
    deps = [
        _find_executable("ffmpeg", ffmpeg_path or None),
        _find_executable("MP4Box", mp4box_path or None),
        _find_executable("N_m3u8DL-RE", nm3u8dlre_path or None),
    ]
    return DependencyCheckResponse(all_ok=all(d.found for d in deps), dependencies=deps)


@app.get("/api/dependencies/download-progress", tags=["system"])
async def dep_download_progress():
    """Get the progress of auto-downloading missing dependencies."""
    from amdl.dependency_manager import get_progress as _get_progress
    return {"dependencies": _get_progress()}


@app.delete("/api/temp", tags=["system"])
async def clean_temp():
    count = 0
    if TEMP_DIR.exists():
        for item in TEMP_DIR.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
            count += 1
    return {"message": f"Cleaned {count} items from temp directory"}


# ═══════════════════════════════════════════════════════════════
# API — Tasks
# ═══════════════════════════════════════════════════════════════

@app.post("/api/tasks", response_model=TaskSubmitResponse, tags=["tasks"])
async def submit_task(request: DownloadRequest):
    tm = get_task_manager()
    task_id = await tm.submit(request.model_dump())
    return TaskSubmitResponse(task_id=task_id, status="pending", message="Task submitted")


@app.get("/api/tasks", response_model=TaskListResponse, tags=["tasks"])
async def list_tasks():
    tm = get_task_manager()
    tasks = tm.list_tasks()
    return TaskListResponse(
        tasks=[TaskInfoResponse(**t.to_dict()) for t in tasks],
        total=len(tasks),
    )


@app.get("/api/tasks/{task_id}", response_model=TaskInfoResponse, tags=["tasks"])
async def get_task(task_id: str):
    tm = get_task_manager()
    task = tm.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    return TaskInfoResponse(**task.to_dict())


@app.delete("/api/tasks/{task_id}", tags=["tasks"])
async def cancel_task(task_id: str):
    tm = get_task_manager()
    ok = await tm.cancel_task(task_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Task not found or finished: {task_id}")
    return {"message": "Task cancelled", "task_id": task_id}


# ═══════════════════════════════════════════════════════════════
# WebSocket
# ═══════════════════════════════════════════════════════════════

@app.websocket("/api/ws/{task_id}")
async def task_progress_ws(websocket: WebSocket, task_id: str):
    tm = get_task_manager()
    await websocket.accept()

    ok = await tm.subscribe(task_id, websocket)
    if not ok:
        await websocket.send_json({"type": "error", "message": f"Task not found: {task_id}"})
        await websocket.close(code=1008)
        return

    try:
        while True:
            data = await websocket.receive_text()
            if data == '{"type":"ping"}':
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        await tm.unsubscribe(task_id, websocket)


# ═══════════════════════════════════════════════════════════════
# Static files (Next.js build output for pywebview)
# ═══════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index = FRONTEND_OUT / "index.html"
    if index.exists():
        return FileResponse(index)
    return HTMLResponse(
        content="<html><body>Frontend not built. Run: cd src/fronted && npm run build</body></html>",
        status_code=200,
    )


@app.get("/{full_path:path}", response_class=FileResponse)
async def serve_static(full_path: str):
    file_path = FRONTEND_OUT / full_path
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    index = FRONTEND_OUT / "index.html"
    if index.exists():
        return FileResponse(index)
    return JSONResponse({"error": "Not found"}, status_code=404)


# ═══════════════════════════════════════════════════════════════
# pywebview desktop API
# ═══════════════════════════════════════════════════════════════

class PywebviewApi:
    def __init__(self, window_ref: list):
        self._window_ref = window_ref

    def open_file(self, **kwargs) -> str | None:
        import webview
        from webview import FileDialog

        result = self._window_ref[0].create_file_dialog(
            FileDialog.OPEN,
            file_types=("Text files (*.txt)", "All files (*.*)"),
        )
        return result[0] if result else None

    def open_folder(self, **kwargs) -> str | None:
        import webview
        from webview import FileDialog

        result = self._window_ref[0].create_file_dialog(
            FileDialog.FOLDER,
        )
        return result[0] if result else None

    def save_file(self, **kwargs) -> str | None:
        import webview
        from webview import FileDialog

        result = self._window_ref[0].create_file_dialog(
            FileDialog.SAVE,
            file_types=("All files (*.*)",),
        )
        return result[0] if result else None


# ═══════════════════════════════════════════════════════════════
# Entry points
# ═══════════════════════════════════════════════════════════════

def _find_free_port(start: int = 8000, max_attempts: int = 20) -> int:
    """Find the first available port starting from *start*."""
    import socket
    for port in range(start, start + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start  # give up, let uvicorn fail with the original port


def run_server(host: str = "127.0.0.1", port: int = 8000, log_level: str = "info"):
    import uvicorn

    port = _find_free_port(port)
    if port != 8000:
        logger.info("Port 8000 in use — using port %d instead", port)

    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    uvicorn.run(app, host=host, port=int(port), log_level=log_level)


def run_desktop():
    import webview

    host = "127.0.0.1"
    port = _find_free_port(8000)

    server_thread = threading.Thread(target=run_server, args=(host, port), daemon=True)
    server_thread.start()
    time.sleep(2)

    url = f"http://{host}:{port}"
    window_ref: list = []
    api = PywebviewApi(window_ref)

    kwargs: dict = dict(
        title="Apple Music Downloader",
        url=url,
        width=1200,
        height=800,
        min_size=(800, 600),
        resizable=True,
        js_api=api,
    )

    # 设置窗口图标（pywebview >= 6.0 才支持 icon 参数）
    if ICON_FILE.exists():
        try:
            _v = tuple(int(x) for x in getattr(webview, "__version__", "0").split(".")[:2])
        except Exception:
            _v = (0, 0)
        if _v >= (6, 0):
            kwargs["icon"] = str(ICON_FILE)

    window = webview.create_window(**kwargs)
    window_ref.append(window)
    webview.start(debug=False)


if __name__ == "__main__":
    import sys

    if "--desktop" in sys.argv:
        run_desktop()
    else:
        run_server()