from __future__ import annotations

import asyncio
import logging
import platform
import shutil
import subprocess
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Callable

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from amdl.core_downloader import download_urls
from amdl.enums import (
    CoverFormat,
    DownloadMode,
    MusicVideoCodec,
    SongCodec,
    SyncedLyricsFormat,
    UploadedVideoQuality,
)
from amdl.task_manager import get_task_manager

logger = logging.getLogger("amdl.server")

# ── 项目根目录 ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND_OUT = PROJECT_ROOT / "src" / "fronted" / "out"
TEMP_DIR = PROJECT_ROOT / "temp"


# ═══════════════════════════════════════════════════════════════
# Lifespan (startup / shutdown)
# ═══════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    tm = get_task_manager()
    tm.start()
    logger.info("AMDL server started")
    yield
    await tm.stop()
    logger.info("AMDL server stopped")


# ── FastAPI 应用 ──────────────────────────────────────────────
app = FastAPI(
    title="AMDL API",
    description="Apple Music Downloader API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS — 允许前端跨域调用（开发模式 + pywebview file:// 协议）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════
# 请求 / 响应模型
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
    quality_uploaded_video: UploadedVideoQuality = Field(default=UploadedVideoQuality.BEST)
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
# 辅助函数
# ═══════════════════════════════════════════════════════════════

def _build_log_callback() -> Callable[[str], None]:
    def _log(msg: str) -> None:
        logging.getLogger("amdl.api").info(msg)
    return _log


def _find_executable(name: str, custom_path: str | None = None) -> DependencyCheckItem:
    """Check if an executable exists in PATH or at custom_path."""
    target = custom_path or name
    found_path = shutil.which(target)

    if found_path and Path(found_path).exists():
        try:
            result = subprocess.run(
                [found_path, "-version"] if name == "ffmpeg"
                else [found_path, "--version"],
                capture_output=True, text=True, timeout=5,
            )
            version_line = (result.stdout or result.stderr).split("\n")[0]
        except Exception:
            version_line = None
        return DependencyCheckItem(name=name, found=True, path=str(Path(found_path).resolve()), version=version_line)

    return DependencyCheckItem(name=name, found=False)


# ═══════════════════════════════════════════════════════════════
# API 端点 — 系统
# ═══════════════════════════════════════════════════════════════

@app.get("/api/health", response_model=HealthResponse, tags=["system"])
async def health_check():
    return HealthResponse()


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
async def check_dependencies(ffmpeg_path: str = "", nm3u8dlre_path: str = ""):
    """Check required external dependencies (ffmpeg, N_m3u8DL-RE)."""
    deps = [
        _find_executable("ffmpeg", ffmpeg_path or None),
        _find_executable("N_m3u8DL-RE", nm3u8dlre_path or None),
    ]
    return DependencyCheckResponse(all_ok=all(d.found for d in deps), dependencies=deps)


@app.delete("/api/temp", tags=["system"])
async def clean_temp():
    """Clean the temp directory."""
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
# API 端点 — 任务队列
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
    return TaskListResponse(tasks=[TaskInfoResponse(**t.to_dict()) for t in tasks], total=len(tasks))


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
# WebSocket 实时进度
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
# 静态文件服务（Next.js 构建产物）— 用于 pywebview 桌面模式
# ═══════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index = FRONTEND_OUT / "index.html"
    if index.exists():
        return FileResponse(index)
    return HTMLResponse(content="<html><body>Frontend not built. Run: cd src/fronted && npm run build</body></html>", status_code=200)


@app.get("/{full_path:path}", response_class=FileResponse)
async def serve_static(full_path: str):
    file_path = FRONTEND_OUT / full_path
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    # SPA fallback: return index.html for client-side routing
    index = FRONTEND_OUT / "index.html"
    if index.exists():
        return FileResponse(index)
    return JSONResponse({"error": "Not found"}, status_code=404)


# ═══════════════════════════════════════════════════════════════
# 启动入口
# ═══════════════════════════════════════════════════════════════

def run_server(host: str = "127.0.0.1", port: int = 8000, log_level: str = "info"):
    """Start the AMDL server (used by CLI and pywebview)."""
    import uvicorn

    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    uvicorn.run(app, host=host, port=int(port), log_level=log_level)


def run_desktop():
    """Launch as desktop app using pywebview."""
    import webview

    host = "127.0.0.1"
    port = 8000

    # Start server in background thread
    import threading
    server_thread = threading.Thread(target=run_server, args=(host, port), daemon=True)
    server_thread.start()

    # Wait for server to be ready
    import time
    time.sleep(2)

    url = f"http://{host}:{port}"
    window = webview.create_window(
        title="Apple Music Downloader",
        url=url,
        width=1200,
        height=800,
        min_size=(800, 600),
        resizable=True,
    )
    webview.start(debug=False)


if __name__ == "__main__":
    import sys

    if "--desktop" in sys.argv:
        run_desktop()
    else:
        run_server()