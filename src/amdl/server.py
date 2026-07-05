from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Callable

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
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


# ═══════════════════════════════════════════════════════════════
# Lifespan (startup / shutdown)
# ═══════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the task manager worker on startup, clean up on shutdown."""
    tm = get_task_manager()
    tm.start()
    yield
    await tm.stop()


# ── FastAPI 应用 ──────────────────────────────────────────────
app = FastAPI(
    title="AMDL API",
    description="Apple Music Downloader API — a download service for Apple Music",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ═══════════════════════════════════════════════════════════════
# 请求 / 响应模型
# ═══════════════════════════════════════════════════════════════

class DownloadRequest(BaseModel):
    # ── 必填 ──────────────────────────────────────────────
    urls: list[str] = Field(
        ...,
        min_length=1,
        description="Apple Music link list (supports songs, albums, playlists, artists, music videos)",
        examples=[
            ["https://music.apple.com/us/album/xxx"],
            ["https://music.apple.com/us/album/xxx/123", "https://music.apple.com/us/album/yyy/456"],
        ],
    )
    cookies_path: str = Field(
        ...,
        description="Netscape formatted cookies.txt file absolute path",
        examples=["/path/to/cookies.txt"],
    )

    # ── 路径 ──────────────────────────────────────────────
    output_path: str = Field(
        default="./Apple Music",
        description="Download output directory",
    )
    temp_path: str = Field(
        default="./temp",
        description="Temporary file path",
    )
    wvd_path: str | None = Field(
        default=None,
        description="WVD file path (for Widevine decryption)",
    )

    # ── 二进制工具路径 ────────────────────────────────────
    nm3u8dlre_path: str = Field(
        default="N_m3u8DL-RE",
        description="N_m3u8DL-RE executable path",
    )
    ffmpeg_path: str = Field(
        default="ffmpeg",
        description="ffmpeg executable path",
    )

    # ── 下载模式 ──────────────────────────────────────────
    download_mode: DownloadMode = Field(
        default=DownloadMode.YTDLP,
        description="Download mode: YTDLP or FFmpeg",
    )

    # ── 编码 / 格式 ───────────────────────────────────────
    codec_song: SongCodec = Field(
        default=SongCodec.AAC_WEB,
        description="Song audio encoding format",
    )
    codec_music_video: MusicVideoCodec = Field(
        default=MusicVideoCodec.H264,
        description="Music video encoding format",
    )
    quality_uploaded_video: UploadedVideoQuality = Field(
        default=UploadedVideoQuality.BEST,
        description="Uploaded video quality",
    )
    synced_lyrics_format: SyncedLyricsFormat = Field(
        default=SyncedLyricsFormat.LRC,
        description="Synced lyrics format",
    )
    cover_format: CoverFormat = Field(
        default=CoverFormat.JPG,
        description="Cover image format",
    )
    cover_size: int = Field(
        default=1200,
        ge=50,
        le=5000,
        description="Cover image size (pixels)",
    )
    truncate: int | None = Field(
        default=None,
        ge=0,
        description="Truncate file name length (character count), null=do not truncate",
    )

    # ── 格式转换 ──────────────────────────────────────────
    audio_format: str | None = Field(
        default=None,
        description="Output audio format conversion (e.g. mp3/flac/wav/aac/ogg/alac), null=do not convert",
    )
    video_format: str | None = Field(
        default=None,
        description="Output video format conversion (e.g. mp4/mkv/avi/webm), null=do not convert",
    )

    # ── 模板 ──────────────────────────────────────────────
    template_folder_album: str = Field(
        default="{album_artist}/{album}",
        description="Album folder naming template",
    )
    template_folder_compilation: str = Field(
        default="Compilations/{album}",
        description="Compilation folder naming template",
    )
    template_file_single_disc: str = Field(
        default="{track:02d} {title}",
        description="Single-disc file naming template",
    )
    template_file_multi_disc: str = Field(
        default="{disc}-{track:02d} {title}",
        description="Multi-disc file naming template",
    )
    template_folder_no_album: str = Field(
        default="{artist}/Unknown Album",
        description="Folder naming template when no album info is available",
    )
    template_file_no_album: str = Field(
        default="{title}",
        description="File naming template when no album info is available",
    )
    template_file_playlist: str = Field(
        default="Playlists/{playlist_artist}/{playlist_title}",
        description="Playlist file naming template",
    )
    template_date: str = Field(
        default="%Y-%m-%dT%H:%M:%SZ",
        description="Date tag format",
    )
    exclude_tags: str | None = Field(
        default=None,
        description="Exclude tags list (comma-separated, e.g. 'all,comment,copyright')",
    )

    # ── 布尔开关 ──────────────────────────────────────────
    overwrite: bool = Field(
        default=False,
        description="Overwrite existing files",
    )
    save_cover: bool = Field(
        default=False,
        description="Save cover file",
    )
    save_playlist: bool = Field(
        default=False,
        description="Save playlist file",
    )
    synced_lyrics_only: bool = Field(
        default=False,
        description="Only download synced lyrics",
    )
    no_synced_lyrics: bool = Field(
        default=False,
        description="Do not download synced lyrics",
    )
    disable_music_video_skip: bool = Field(
        default=False,
        description="Disable music video skip",
    )
    read_urls_as_txt: bool = Field(
        default=False,
        description="Read urls as a .txt file, and read links from it",
    )

    # ── API ───────────────────────────────────────────────
    language: str = Field(
        default="en-US",
        description="Apple Music API language",
    )

    log_level: str = Field(
        default="INFO",
        description="Log level (DEBUG/INFO/WARNING/CRITICAL)",
    )

    # ── 校验 ──────────────────────────────────────────────
    @field_validator("cookies_path")
    @classmethod
    def _validate_cookies_path(cls, v: str) -> str:
        p = Path(v)
        if not p.exists():
            raise ValueError(f"Cookies file does not exist: {v}")
        if not p.is_file():
            raise ValueError(f"Cookies path is not a file: {v}")
        return v

    @field_validator("log_level")
    @classmethod
    def _validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"Invalid log level: {v}，available options: {', '.join(sorted(allowed))}")
        return v.upper()

    @field_validator("audio_format")
    @classmethod
    def _validate_audio_format(cls, v: str | None) -> str | None:
        if v is None:
            return v
        allowed = {"mp3", "flac", "wav", "aac", "m4a", "ogg", "wma", "alac"}
        if v.lower() not in allowed:
            raise ValueError(
                f"Supported audio format not supported: {v}，available options: {', '.join(sorted(allowed))}"
            )
        return v.lower()

    @field_validator("video_format")
    @classmethod
    def _validate_video_format(cls, v: str | None) -> str | None:
        if v is None:
            return v
        allowed = {"mp4", "mov", "mkv", "avi", "wmv", "flv", "webm"}
        if v.lower() not in allowed:
            raise ValueError(
                f"Supported video format not supported: {v}，available options: {', '.join(sorted(allowed))}"
            )
        return v.lower()


class DownloadResponse(BaseModel):
    success: bool = Field(..., description="Whether all downloads completed successfully")
    error_count: int = Field(..., description="Number of errors that occurred")
    total_urls: int = Field(..., description="Total number of URLs provided")
    message: str = Field(..., description="Description of the result")


class TaskSubmitResponse(BaseModel):
    task_id: str = Field(..., description="Task ID for tracking progress")
    status: str = Field(..., description="Initial task status")
    message: str = Field(..., description="Description")


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
    """API 信息及支持的枚举值列表，供前端动态渲染选项。"""
    api_version: str
    supported_codecs_song: list[dict[str, str]]
    supported_codecs_music_video: list[dict[str, str]]
    supported_cover_formats: list[dict[str, str]]
    supported_synced_lyrics_formats: list[dict[str, str]]
    supported_uploaded_video_qualities: list[dict[str, str]]
    supported_download_modes: list[dict[str, str]]
    supported_audio_conversion_formats: list[str]
    supported_video_conversion_formats: list[str]
    template_variables: list[str]


class HealthResponse(BaseModel):
    status: str = Field(..., description="Service status, always 'ok'")
    version: str = Field(..., description="API version")


# ═══════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════

def _build_log_callback() -> Callable[[str], None]:
    """构造一个将日志写入 logging 的回调。"""
    def _log(msg: str) -> None:
        logging.getLogger("amdl.api").info(msg)
    return _log


# ═══════════════════════════════════════════════════════════════
# API 端点 — 系统
# ═══════════════════════════════════════════════════════════════

@app.get("/api/health", response_model=HealthResponse, tags=["system"])
async def health_check():
    """健康检查端点。"""
    return HealthResponse(status="ok", version="2.0.0")


@app.get("/api/info", response_model=ApiInfoResponse, tags=["system"])
async def get_api_info():
    """获取 API 支持的选项列表，供前端动态渲染下拉菜单。"""
    return ApiInfoResponse(
        api_version="2.0.0",
        supported_codecs_song=[
            {"value": c.value, "label": c.name} for c in SongCodec
        ],
        supported_codecs_music_video=[
            {"value": c.value, "label": c.name} for c in MusicVideoCodec
        ],
        supported_cover_formats=[
            {"value": c.value, "label": c.name} for c in CoverFormat
        ],
        supported_synced_lyrics_formats=[
            {"value": c.value, "label": c.name} for c in SyncedLyricsFormat
        ],
        supported_uploaded_video_qualities=[
            {"value": c.value, "label": c.name} for c in UploadedVideoQuality
        ],
        supported_download_modes=[
            {"value": c.value, "label": c.name} for c in DownloadMode
        ],
        supported_audio_conversion_formats=[
            "mp3", "flac", "wav", "aac", "m4a", "ogg", "wma", "alac",
        ],
        supported_video_conversion_formats=[
            "mp4", "mov", "mkv", "avi", "wmv", "flv", "webm",
        ],
        template_variables=[
            "{album_artist}", "{album}", "{artist}", "{title}",
            "{track}", "{disc}", "{track:02d}", "{disc-}{track:02d}",
            "{playlist_artist}", "{playlist_title}", "{playlist_track}",
            "{date}", "{genre}", "{composer}", "{year}",
        ],
    )


# ═══════════════════════════════════════════════════════════════
# API 端点 — 任务队列
# ═══════════════════════════════════════════════════════════════

@app.post(
    "/api/tasks",
    response_model=TaskSubmitResponse,
    tags=["tasks"],
    summary="Submit a download task",
    description="Submit an Apple Music download task. Returns a task_id immediately. "
    "Track progress via WebSocket at /api/ws/{task_id}.",
)
async def submit_task(request: DownloadRequest):
    """Submit a download task to the queue. Returns immediately with a task_id."""
    tm = get_task_manager()
    task_id = await tm.submit(request.model_dump())
    return TaskSubmitResponse(
        task_id=task_id,
        status="pending",
        message=f"Task submitted. Connect to /api/ws/{task_id} for real-time progress.",
    )


@app.get(
    "/api/tasks",
    response_model=TaskListResponse,
    tags=["tasks"],
    summary="List all tasks",
    description="Get all download tasks, sorted by creation time (newest first).",
)
async def list_tasks():
    """Get all tasks (newest first)."""
    tm = get_task_manager()
    tasks = tm.list_tasks()
    return TaskListResponse(
        tasks=[TaskInfoResponse(**t.to_dict()) for t in tasks],
        total=len(tasks),
    )


@app.get(
    "/api/tasks/{task_id}",
    response_model=TaskInfoResponse,
    tags=["tasks"],
    summary="Get task details",
    description="Get the status and progress of a specific task.",
)
async def get_task(task_id: str):
    """Get details of a specific task."""
    tm = get_task_manager()
    task = tm.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    return TaskInfoResponse(**task.to_dict())


@app.delete(
    "/api/tasks/{task_id}",
    tags=["tasks"],
    summary="Cancel a task",
    description="Cancel a pending or running task.",
)
async def cancel_task(task_id: str):
    """Cancel a task."""
    tm = get_task_manager()
    ok = await tm.cancel_task(task_id)
    if not ok:
        raise HTTPException(
            status_code=404,
            detail=f"Task not found or already finished: {task_id}",
        )
    return {"message": "Task cancelled", "task_id": task_id}


# ═══════════════════════════════════════════════════════════════
# API 端点 — 实时进度 (WebSocket)
# ═══════════════════════════════════════════════════════════════

@app.websocket("/api/ws/{task_id}")
async def task_progress_ws(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for real-time download progress.

    Connect to /api/ws/{task_id} after submitting a task.
    You will receive JSON messages:
      - {"type":"subscribed", ...} — initial state on connect
      - {"type":"progress", "completed":3, "total":10, "percent":30.0} — progress update
      - {"type":"status", "status":"completed", ...} — status change
    """
    tm = get_task_manager()
    await websocket.accept()

    ok = await tm.subscribe(task_id, websocket)
    if not ok:
        await websocket.send_json({
            "type": "error",
            "message": f"Task not found: {task_id}",
        })
        await websocket.close(code=1008)
        return

    try:
        # Keep connection alive, listen for client-side disconnect
        while True:
            data = await websocket.receive_text()
            # Client can send {"type":"ping"} to keep alive
            if data == '{"type":"ping"}':
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        await tm.unsubscribe(task_id, websocket)


# ═══════════════════════════════════════════════════════════════
# API 端点 — 简单下载（同步等待，兼容旧版）
# ═══════════════════════════════════════════════════════════════

@app.post(
    "/api/download",
    response_model=DownloadResponse,
    tags=["download"],
    summary="Download Apple Music Content (sync)",
    description="Download Apple Music content synchronously. "
    "For real-time progress, use /api/tasks instead.",
)
async def download(request: DownloadRequest):
    """下载 Apple Music 内容（同步等待）。推荐使用 /api/tasks 异步队列。"""
    log_callback = _build_log_callback()

    try:
        err_count = await asyncio.to_thread(
            download_urls,
            urls=request.urls,
            cookies_path=Path(request.cookies_path),
            output_path=Path(request.output_path),
            temp_path=Path(request.temp_path),
            wvd_path=Path(request.wvd_path) if request.wvd_path else None,
            nm3u8dlre_path=request.nm3u8dlre_path,
            ffmpeg_path=request.ffmpeg_path,
            download_mode=request.download_mode,
            codec_song=request.codec_song,
            codec_music_video=request.codec_music_video,
            quality_post=request.quality_uploaded_video,
            synced_lyrics_format=request.synced_lyrics_format,
            cover_format=request.cover_format,
            cover_size=request.cover_size,
            truncate=request.truncate,
            audio_format=request.audio_format,
            video_format=request.video_format,
            template_folder_album=request.template_folder_album,
            template_folder_compilation=request.template_folder_compilation,
            template_file_single_disc=request.template_file_single_disc,
            template_file_multi_disc=request.template_file_multi_disc,
            template_folder_no_album=request.template_folder_no_album,
            template_file_no_album=request.template_file_no_album,
            template_file_playlist=request.template_file_playlist,
            template_date=request.template_date,
            exclude_tags=request.exclude_tags,
            overwrite=request.overwrite,
            save_cover=request.save_cover,
            save_playlist=request.save_playlist,
            synced_lyrics_only=request.synced_lyrics_only,
            no_synced_lyrics=request.no_synced_lyrics,
            disable_music_video_skip=request.disable_music_video_skip,
            read_urls_as_txt=request.read_urls_as_txt,
            language=request.language,
            log_callback=log_callback,
            log_level=request.log_level,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"download error occurred: {e}",
        )

    return DownloadResponse(
        success=err_count == 0,
        error_count=err_count,
        total_urls=len(request.urls),
        message=(
            "全部下载完成"
            if err_count == 0
            else f"download completed, total {err_count} errors"
        ),
    )


# ═══════════════════════════════════════════════════════════════
# 全局异常处理器
# ═══════════════════════════════════════════════════════════════

@app.exception_handler(Exception)
async def global_exception_handler(request: Any, exc: Exception) -> JSONResponse:
    """全局异常处理器，确保所有异常都返回 JSON。"""
    return JSONResponse(
        status_code=500,
        content={"detail": f"server error: {exc}"},
    )