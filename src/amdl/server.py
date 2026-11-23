from __future__ import annotations

import json
import logging
import os
import socket
import sys
import shutil
import subprocess
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path

# ── Windows: ensure anyio uses asyncio backend ──────────────
if sys.platform == "win32":
    os.environ.setdefault("ANYIO_BACKEND", "asyncio")

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel, Field, field_validator, ValidationInfo

from amdl.enums import (
    CoverFormat,
    DownloadMode,
    MusicVideoCodec,
    SongCodec,
    SyncedLyricsFormat,
    UploadedVideoQuality,
)
from amdl.converter import _AUDIO_PRESETS, _VIDEO_PRESETS
from amdl import __version__
from amdl.task_manager import get_task_manager, TaskStatus
from amdl.dependency_manager import BIN_DIR, DATA_DIR, _SUBPROCESS_FLAGS
from amdl.dependency_manager import ensure_dependencies_async

logger = logging.getLogger("amdl.server")

# ── Path resolution（兼容 PyInstaller 打包） ───────────────
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys._MEIPASS)  # type: ignore[attr-defined]  (只读)
    FRONTEND_OUT = BASE_DIR / "frontend_out"
else:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    FRONTEND_OUT = BASE_DIR / "src" / "frontend" / "out"

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
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Allow overriding CORS origins via environment variable for production deployments.
# Defaults to ["*"] for local/desktop use; set AMDL_CORS_ORIGINS for stricter control.
_CORS_ORIGINS = os.environ.get("AMDL_CORS_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=False,
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
    mp4box_path: str = Field(default="MP4Box")
    download_mode: DownloadMode = Field(default=DownloadMode.YTDLP)
    codec_song: SongCodec = Field(default=SongCodec.AAC_WEB)
    codec_music_video: MusicVideoCodec = Field(default=MusicVideoCodec.H264)
    quality_post: UploadedVideoQuality = Field(default=UploadedVideoQuality.BEST, alias="quality_uploaded_video")
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

    model_config = {"populate_by_name": True}

    @field_validator("codec_song", mode="before")
    @classmethod
    def _coerce_song_codec(cls, v):
        if isinstance(v, str):
            v_clean = v.strip().lower().replace("_", "-")
            for c in SongCodec:
                if c.value.lower() == v_clean or c.name.lower() == v.strip().lower():
                    return c
        return v

    @field_validator("codec_music_video", mode="before")
    @classmethod
    def _coerce_mv_codec(cls, v):
        if isinstance(v, str):
            v_clean = v.strip().lower().replace("_", "-")
            for c in MusicVideoCodec:
                if c.value.lower() == v_clean or c.name.lower() == v.strip().lower():
                    return c
        return v

    @field_validator("download_mode", mode="before")
    @classmethod
    def _coerce_download_mode(cls, v):
        if isinstance(v, str):
            v_clean = v.strip().lower().replace("_", "-")
            for c in DownloadMode:
                if c.value.lower() == v_clean or c.name.lower() == v.strip().lower():
                    return c
        return v

    @field_validator("quality_post", mode="before")
    @classmethod
    def _coerce_quality_post(cls, v):
        if isinstance(v, str):
            v_clean = v.strip().lower()
            for c in UploadedVideoQuality:
                if c.value.lower() == v_clean or c.name.lower() == v.strip().lower():
                    return c
        return v

    @field_validator("synced_lyrics_format", mode="before")
    @classmethod
    def _coerce_synced_lyrics(cls, v):
        if isinstance(v, str):
            v_clean = v.strip().lower()
            for c in SyncedLyricsFormat:
                if c.value.lower() == v_clean or c.name.lower() == v.strip().lower():
                    return c
        return v

    @field_validator("cover_format", mode="before")
    @classmethod
    def _coerce_cover_format(cls, v):
        if isinstance(v, str):
            v_clean = v.strip().lower()
            for c in CoverFormat:
                if c.value.lower() == v_clean or c.name.lower() == v.strip().lower():
                    return c
        return v

    @field_validator("cookies_path")
    @classmethod
    def _validate_cookies(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("cookies_path must not be empty")
        v = v.strip()
        p = Path(v)
        if p.exists() and p.is_file():
            return str(p.resolve())
        candidate = DATA_DIR / v
        if candidate.exists() and candidate.is_file():
            return str(candidate.resolve())
        raise ValueError(f"Cookies file not found: {v}")

    @field_validator("wvd_path", "exclude_tags")
    @classmethod
    def _empty_str_to_none(cls, v: str | None) -> str | None:
        if v is None or not v.strip():
            return None
        return v.strip()

    @field_validator("truncate")
    @classmethod
    def _validate_truncate(cls, v: int | None) -> int | None:
        if v is not None and v <= 0:
            return None
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
            return None
        v = v.strip().lower()
        if not v:
            return None
        if v not in _AUDIO_PRESETS:
            raise ValueError(f"Unsupported audio format: {v}")
        return v

    @field_validator("video_format")
    @classmethod
    def _validate_video_fmt(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip().lower()
        if not v:
            return None
        if v not in _VIDEO_PRESETS:
            raise ValueError(f"Unsupported video format: {v}")
        return v

    @field_validator(
        "template_folder_album",
        "template_folder_compilation",
        "template_file_single_disc",
        "template_file_multi_disc",
        "template_folder_no_album",
        "template_file_no_album",
        "template_file_playlist",
        "template_date",
    )
    @classmethod
    def _validate_templates(cls, v: str, info: ValidationInfo) -> str:
        if not v or not v.strip():
            defaults = {
                "template_folder_album": "{album_artist}/{album}",
                "template_folder_compilation": "Compilations/{album}",
                "template_file_single_disc": "{track:02d} {title}",
                "template_file_multi_disc": "{disc}-{track:02d} {title}",
                "template_folder_no_album": "{artist}/Unknown Album",
                "template_file_no_album": "{title}",
                "template_file_playlist": "Playlists/{playlist_artist}/{playlist_title}",
                "template_date": "%Y-%m-%dT%H:%M:%SZ",
            }
            return defaults.get(info.field_name, v)
        return v


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = __version__


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
    parsing: dict | None = None
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
    """Find an executable, searching custom_path → PATH → BIN_DIR → Homebrew paths."""
    found_path: str | None = None

    if custom_path:
        custom_p = Path(custom_path).expanduser()
        if custom_p.exists() and custom_p.is_file():
            found_path = str(custom_p.resolve())
        else:
            found_path = shutil.which(custom_path)

    # 1) shutil.which — respects PATH (including BIN_DIR added above)
    if not found_path:
        found_path = shutil.which(name)

    # 2) BIN_DIR direct lookup (for cases where BIN_DIR isn't in PATH yet)
    if not found_path:
        ext = _KNOWN_EXTENSIONS.get(name, None) or ""
        candidate = BIN_DIR / f"{name}{ext}"
        if candidate.exists() and candidate.is_file():
            found_path = str(candidate.resolve())

    # 3) Homebrew fallback (macOS / Linux)
    if not found_path and sys.platform != "win32":
        for brew_dir in _HOMEBREW_PATHS:
            candidate = Path(brew_dir) / name
            if candidate.exists() and candidate.is_file():
                found_path = str(candidate.resolve())
                break

    if found_path and Path(found_path).exists():
        resolved = Path(found_path).resolve()
        version_line = None
        try:
            kwargs = {}
            if sys.platform == "win32":
                kwargs["creationflags"] = _SUBPROCESS_FLAGS
            result = subprocess.run(
                [str(resolved), "-version"] if name in ("ffmpeg", "MP4Box") else [str(resolved), "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                **kwargs,
            )
            out = result.stdout or result.stderr or ""
            version_line = out.split("\n")[0].strip() or None
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
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    existing: dict = {}
    if SETTINGS_FILE.exists():
        try:
            existing = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    existing.update(payload)
    tmp_file = SETTINGS_FILE.with_suffix(".tmp")
    tmp_file.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_file.replace(SETTINGS_FILE)
    return JSONResponse(content={"status": "ok"})



@app.get("/api/info", response_model=ApiInfoResponse, tags=["system"])
async def get_api_info():
    return ApiInfoResponse(
        api_version=__version__,
        supported_codecs_song=[{"value": c.value, "label": c.name} for c in SongCodec],
        supported_codecs_music_video=[{"value": c.value, "label": c.name} for c in MusicVideoCodec],
        supported_cover_formats=[{"value": c.value, "label": c.name} for c in CoverFormat],
        supported_download_modes=[{"value": c.value, "label": c.name} for c in DownloadMode],
        supported_audio_conversion_formats=list(_AUDIO_PRESETS.keys()),
        supported_video_conversion_formats=list(_VIDEO_PRESETS.keys()),
    )


# ── Update Checker ──────────────────────────────────────────
_UPDATE_CACHE: dict = {"time": 0.0, "data": None}


def _parse_version(ver_str: str) -> tuple[int, ...]:
    import re
    clean = re.sub(r"[^\d.]", "", ver_str)
    parts = []
    for p in clean.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            break
    return tuple(parts)


@app.get("/api/system/check-update", tags=["system"])
async def check_update(force: bool = False):
    import httpx
    now = time.time()
    if not force and _UPDATE_CACHE["data"] and (now - _UPDATE_CACHE["time"] < 600):
        return JSONResponse(content=_UPDATE_CACHE["data"])

    current_ver = __version__
    curr_tuple = _parse_version(current_ver)
    url = "https://api.github.com/repos/wenfeng110402/AppleMusic-Downloader/releases/latest"

    res_data = {
        "has_update": False,
        "current_version": current_ver,
        "latest_version": current_ver,
        "release_notes": "",
        "release_url": "https://github.com/wenfeng110402/AppleMusic-Downloader/releases",
    }

    try:
        async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
            resp = await client.get(
                url,
                headers={
                    "User-Agent": f"AppleMusicDownloader/{current_ver}",
                    "Accept": "application/vnd.github.v3+json",
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                tag = data.get("tag_name", "").lstrip("v")
                latest_tuple = _parse_version(tag)
                has_update = latest_tuple > curr_tuple
                res_data = {
                    "has_update": has_update,
                    "current_version": current_ver,
                    "latest_version": tag or current_ver,
                    "release_notes": data.get("body", ""),
                    "release_url": data.get("html_url", res_data["release_url"]),
                }
                _UPDATE_CACHE["time"] = now
                _UPDATE_CACHE["data"] = res_data
    except Exception as e:
        logger.debug("Failed to check for updates: %s", e)

    return JSONResponse(content=res_data)


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
    progress = _get_progress()
    for name in ("ffmpeg", "MP4Box", "N_m3u8DL-RE"):
        dep_item = _find_executable(name)
        if dep_item.found:
            progress[name] = {"status": "ok", "progress": 100, "error": ""}
    return {"dependencies": progress}


@app.delete("/api/temp", tags=["system"])
async def clean_temp():
    count = 0
    if TEMP_DIR.exists():
        for item in TEMP_DIR.iterdir():
            try:
                if item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
                else:
                    item.unlink(missing_ok=True)
                count += 1
            except Exception as e:
                logger.warning("Failed to remove temp item %s: %s", item, e)
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
async def cancel_task(task_id: str, delete: bool = False):
    tm = get_task_manager()
    task = tm.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    if delete or task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
        await tm.delete_task(task_id)
        return {"message": "Task removed", "task_id": task_id}

    await tm.cancel_task(task_id)
    return {"message": "Task cancelled", "task_id": task_id}


@app.delete("/api/tasks", tags=["tasks"])
async def clear_finished_tasks():
    tm = get_task_manager()
    count = await tm.clear_finished()
    return {"message": f"Cleared {count} finished tasks", "cleared_count": count}


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
            text = await websocket.receive_text()
            try:
                msg = json.loads(text)
                if isinstance(msg, dict) and msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except Exception:
                pass
    except WebSocketDisconnect:
        pass
    except Exception:
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
        content="<html><body>Frontend not built. Run: cd src/frontend && npm run build</body></html>",
        status_code=200,
    )


@app.get("/{full_path:path}", response_class=FileResponse)
async def serve_static(full_path: str):
    # API routes that were not matched above must return 404 JSON, never index.html
    if full_path.startswith("api/"):
        return JSONResponse({"detail": f"API endpoint not found: /{full_path}"}, status_code=404)

    file_path = (FRONTEND_OUT / full_path).resolve()
    root = FRONTEND_OUT.resolve()
    if file_path.is_relative_to(root) and file_path.exists() and file_path.is_file():
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

# ── single-instance lock ────────────────────────────────────
# Prevent multiple `run_desktop()` calls from spawning duplicate
# uvicorn processes and windows.
# Uses BOTH a threading lock (thread-safe) and a TCP port bind (process-safe).
_LOCK_PORT = 51_999
_LOCK_SOCKET: list[socket.socket | None] = [None]
_LOCK_THREAD = threading.Lock()


def _acquire_instance_lock() -> bool:
    with _LOCK_THREAD:
        if _LOCK_SOCKET[0] is not None:
            return False
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("127.0.0.1", _LOCK_PORT))
            s.listen(1)
            _LOCK_SOCKET[0] = s
            return True
        except OSError:
            return False


def _release_instance_lock() -> None:
    with _LOCK_THREAD:
        if _LOCK_SOCKET[0] is not None:
            try:
                _LOCK_SOCKET[0].close()
            except Exception:
                pass
            _LOCK_SOCKET[0] = None


def _is_port_available(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a port is available to bind on host."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False


def _find_free_port(start: int = 8000, max_attempts: int = 50, host: str = "127.0.0.1") -> int:
    """Find the first available port starting from *start* on *host*."""
    bind_host = host if host not in ("0.0.0.0", "::") else "0.0.0.0"
    for port in range(start, start + max_attempts):
        if _is_port_available(port, host=bind_host):
            return port
    return start  # give up, let caller handle potential bind error


def run_server(
    host: str = "127.0.0.1",
    port: int | None = None,
    log_level: str = "info",
    explicit_port: bool = False,
):
    import uvicorn

    if port is None:
        env_port = os.environ.get("PORT")
        if env_port and env_port.isdigit():
            port = int(env_port)
            explicit_port = True
        else:
            port = 8000

    if not explicit_port:
        original_port = port
        port = _find_free_port(port, host=host)
        if port != original_port:
            logger.info("Port %d in use — using port %d instead", original_port, port)
    else:
        bind_host = host if host not in ("0.0.0.0", "::") else "0.0.0.0"
        if not _is_port_available(port, host=bind_host):
            logger.warning(
                "Port %d on %s appears to be already in use or unavailable; uvicorn will attempt to bind",
                port,
                host,
            )

    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    uvicorn.run(app, host=host, port=int(port), log_level=log_level)


def run_desktop(host: str = "127.0.0.1", port: int | None = None):
    # Single-instance guard: only one desktop window allowed.
    if not _acquire_instance_lock():
        logger.warning("Another AMDL desktop instance is already running — skipping")
        return

    import webview

    if port is None:
        port = _find_free_port(8000, host=host)

    server_thread = threading.Thread(
        target=run_server,
        kwargs={"host": host, "port": port, "log_level": "info", "explicit_port": True},
        daemon=True,
    )
    server_thread.start()

    # Poll until server responds or timeout
    check_host = "127.0.0.1" if host in ("0.0.0.0", "::") else host
    for _ in range(40):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.25)
                if s.connect_ex((check_host, port)) == 0:
                    break
        except Exception:
            pass
        time.sleep(0.1)

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
    from amdl.cli import main
    main()