"""Task queue manager — manages download task queue, execution, and WebSocket progress push.

Architecture:
  POST /api/tasks → queue → worker thread → download_urls(progress_callback)
                                                      │
                                                      ▼
                                              asyncio.run_coroutine_threadsafe()
                                                      │
                                                      ▼
                                              WebSocket.send_json() → Flutter
"""

from __future__ import annotations

import atexit
import asyncio
import logging
import threading
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from fastapi import WebSocket

# Lazy import: core_downloader does a Python version guard at import time.
try:
    from amdl.core_downloader import _download_urls_async
except Exception as _import_err:
    _download_urls_async = _import_err  # type: ignore[assignment]

# ── Global singleton ─────────────────────────────────────────
_task_manager: TaskManager | None = None


def get_task_manager() -> TaskManager:
    """Get the global TaskManager singleton."""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager


def _atexit_cleanup() -> None:
    """Ensure worker task is cancelled on interpreter shutdown."""
    tm = _task_manager
    if tm and tm._worker_task and not tm._worker_task.done():
        try:
            tm._worker_task.cancel()
        except Exception:
            pass


# ── Task status enum ─────────────────────────────────────────

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ── A single download task ───────────────────────────────────

class DownloadTask:
    """Represents a single download task."""

    def __init__(self, task_id: str, kwargs: dict):
        self.id = task_id
        self.kwargs = kwargs  # arguments to pass to download_urls
        self.status = TaskStatus.PENDING
        self.progress: tuple[int, int] = (0, 0)  # (completed, total)
        self.error_count: int = 0
        self.message: str = ""
        self.logs: list[str] = []
        self._logs_lock = threading.Lock()
        self.created_at: str = datetime.now(timezone.utc).isoformat()
        self.updated_at: str = self.created_at
        self.cancelled: bool = False
        self.websockets: list[WebSocket] = []  # WebSocket clients subscribed to this task
        self._future: asyncio.Task | None = None

    def append_log(self, msg: str) -> None:
        """Thread-safe log append."""
        with self._logs_lock:
            self.logs.append(msg)

    def get_logs(self) -> list[str]:
        """Thread-safe log read."""
        with self._logs_lock:
            return list(self.logs)

    def to_dict(self) -> dict:
        completed, total = self.progress
        return {
            "id": self.id,
            "status": self.status.value,
            "progress": {
                "completed": completed,
                "total": total,
                "percent": round(completed / total * 100, 1) if total > 0 else 0,
            },
            "error_count": self.error_count,
            "message": self.message,
            "logs": self.get_logs(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "urls": self.kwargs.get("urls", []),
        }


# ── Task queue manager ───────────────────────────────────────

class TaskManager:
    """Manages the download task queue, executes tasks sequentially, and pushes progress via WebSocket."""

    def __init__(self, max_concurrent: int = 1):
        self._tasks: dict[str, DownloadTask] = {}
        # asyncio primitives are lazily created in start() — NOT here —
        # to avoid "cannot create weak reference to 'NoneType' object"
        # when __init__ runs outside an active event loop.
        self._queue: asyncio.Queue[str] | None = None
        self._semaphore: asyncio.Semaphore | None = None
        self._worker_task: asyncio.Task | None = None
        self._lock = threading.Lock()
        self._max_concurrent = max_concurrent

    # ── Lifecycle ────────────────────────────────────────

    def start(self) -> None:
        """Start the background worker. Call on FastAPI startup."""
        loop = asyncio.get_running_loop()
        # Create asyncio objects HERE (inside the running loop) so that
        # internal weakrefs to the loop are always valid.
        self._queue = asyncio.Queue()
        self._semaphore = asyncio.Semaphore(self._max_concurrent)
        self._worker_task = loop.create_task(self._worker_loop())
        atexit.register(_atexit_cleanup)

    async def stop(self) -> None:
        """Stop the background worker. Call on FastAPI shutdown."""
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        for task in self._tasks.values():
            for ws in task.websockets:
                try:
                    await ws.close()
                except Exception:
                    pass
            task.websockets.clear()

    # ── Task submission ──────────────────────────────────

    async def submit(self, kwargs: dict) -> str:
        """Submit a download task and return the task_id."""
        assert self._queue is not None, "TaskManager.start() must be called first"
        task_id = str(uuid.uuid4())
        task = DownloadTask(task_id, kwargs)
        with self._lock:
            self._tasks[task_id] = task
        await self._queue.put(task_id)
        return task_id

    # ── Task queries ─────────────────────────────────────

    def get_task(self, task_id: str) -> DownloadTask | None:
        with self._lock:
            return self._tasks.get(task_id)

    def list_tasks(self) -> list[DownloadTask]:
        with self._lock:
            return sorted(
                self._tasks.values(),
                key=lambda t: t.created_at,
                reverse=True,
            )

    # ── Task cancellation ────────────────────────────────

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task. PENDING tasks are cancelled immediately; RUNNING tasks are marked for cancellation."""
        task = self.get_task(task_id)
        if not task:
            return False
        if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
            return False
        task.cancelled = True
        task.status = TaskStatus.CANCELLED
        task.message = "已取消"
        task.updated_at = datetime.now(timezone.utc).isoformat()
        if task._future and not task._future.done():
            task._future.cancel()
        await self._broadcast_status(task)
        return True

    # ── Background worker loop ───────────────────────────

    async def _worker_loop(self):
        assert self._queue is not None and self._semaphore is not None
        while True:
            task_id = await self._queue.get()
            task = self.get_task(task_id)
            if not task or task.cancelled:
                self._queue.task_done()
                continue

            async with self._semaphore:
                if task.cancelled:
                    self._queue.task_done()
                    continue

                task.status = TaskStatus.RUNNING
                task.updated_at = datetime.now(timezone.utc).isoformat()
                await self._broadcast_status(task)

                task._future = asyncio.ensure_future(self._execute_download(task_id))
                try:
                    await task._future
                except asyncio.CancelledError:
                    task.status = TaskStatus.CANCELLED
                    task.message = "已取消"
                    task.updated_at = datetime.now(timezone.utc).isoformat()
                    await self._broadcast_status(task)
                except Exception as e:
                    task.status = TaskStatus.FAILED
                    task.message = str(e)
                    task.updated_at = datetime.now(timezone.utc).isoformat()
                    await self._broadcast_status(task)
                finally:
                    self._queue.task_done()

    async def _execute_download(self, task_id: str) -> None:
        """Execute download directly in uvicorn's event loop — no threads."""
        task = self.get_task(task_id)
        if not task or task.cancelled:
            return

        if not callable(_download_urls_async):
            msg = str(_download_urls_async)
            task.status = TaskStatus.FAILED
            task.message = msg
            task.logs.append(f"[FATAL] {msg}")
            task.updated_at = datetime.now(timezone.utc).isoformat()
            await self._broadcast_status(task)
            return

        async def on_progress(completed: int, total: int):
            if task.cancelled:
                raise asyncio.CancelledError("Task cancelled")
            task.progress = (completed, total)
            await self._broadcast_progress(task_id, completed, total)

        def on_log(msg: str):
            task.append_log(msg)
            logging.getLogger("amdl.task").info(f"[{task_id[:8]}] {msg}")

        from amdl.dependency_manager import DATA_DIR as _data_dir
        kwargs: dict = task.kwargs.copy()

        for key in ("cookies_path", "output_path", "temp_path"):
            val = kwargs.get(key)
            if isinstance(val, str):
                p = Path(val)
                kwargs[key] = p if p.is_absolute() else _data_dir / val

        wvd = kwargs.get("wvd_path")
        if isinstance(wvd, str) and wvd:
            p = Path(wvd)
            kwargs["wvd_path"] = p if p.is_absolute() else _data_dir / p

        try:
            err_count = await _download_urls_async(
                urls=kwargs.get("urls", []),
                cookies_path=kwargs["cookies_path"],
                output_path=kwargs.get("output_path", Path("./Apple Music")),
                temp_path=kwargs.get("temp_path", Path("./temp")),
                wvd_path=kwargs.get("wvd_path"),
                nm3u8dlre_path=kwargs.get("nm3u8dlre_path", "N_m3u8DL-RE"),
                ffmpeg_path=kwargs.get("ffmpeg_path", "ffmpeg"),
                download_mode=kwargs.get("download_mode"),
                codec_song=kwargs.get("codec_song"),
                codec_music_video=kwargs.get("codec_music_video"),
                quality_post=kwargs.get("quality_post"),
                synced_lyrics_format=kwargs.get("synced_lyrics_format"),
                cover_format=kwargs.get("cover_format"),
                cover_size=kwargs.get("cover_size", 1200),
                truncate=kwargs.get("truncate"),
                audio_format=kwargs.get("audio_format"),
                video_format=kwargs.get("video_format"),
                template_folder_album=kwargs.get("template_folder_album"),
                template_folder_compilation=kwargs.get("template_folder_compilation"),
                template_file_single_disc=kwargs.get("template_file_single_disc"),
                template_file_multi_disc=kwargs.get("template_file_multi_disc"),
                template_folder_no_album=kwargs.get("template_folder_no_album"),
                template_file_no_album=kwargs.get("template_file_no_album"),
                template_file_playlist=kwargs.get("template_file_playlist"),
                template_date=kwargs.get("template_date"),
                exclude_tags=kwargs.get("exclude_tags"),
                overwrite=kwargs.get("overwrite", False),
                save_cover=kwargs.get("save_cover", False),
                save_playlist=kwargs.get("save_playlist", False),
                synced_lyrics_only=kwargs.get("synced_lyrics_only", False),
                no_synced_lyrics=kwargs.get("no_synced_lyrics", False),
                disable_music_video_skip=kwargs.get("disable_music_video_skip", False),
                read_urls_as_txt=kwargs.get("read_urls_as_txt", False),
                no_exceptions=False,
                language=kwargs.get("language", "en-US"),
                log_callback=on_log,
                log_level=kwargs.get("log_level", "INFO"),
                progress_callback=on_progress,
            )
        except asyncio.CancelledError:
            raise

        if not task.cancelled:
            task.error_count = err_count
            completed_count, _ = task.progress
            task.status = (
                TaskStatus.COMPLETED
                if completed_count > 0 or err_count == 0
                else TaskStatus.FAILED
            )
            task.message = (
                "全部完成" if err_count == 0
                else f"部分完成（{err_count} 个错误）" if completed_count > 0
                else f"全部失败（{err_count} 个错误）"
            )
            task.updated_at = datetime.now(timezone.utc).isoformat()
            await self._broadcast_status(task)

    # ── WebSocket broadcasting ──────────────────────────

    async def _broadcast_progress(self, task_id: str, completed: int, total: int):
        task = self.get_task(task_id)
        if not task:
            return
        message = {
            "type": "progress",
            "task_id": task_id,
            "completed": completed,
            "total": total,
            "percent": round(completed / total * 100, 1) if total > 0 else 0,
        }
        await self._send_to_subscribers(task, message)

    async def _broadcast_status(self, task: DownloadTask):
        completed, total = task.progress[0], task.progress[1]
        message = {
            "type": "status",
            "task_id": task.id,
            "status": task.status.value,
            "progress": {
                "completed": completed,
                "total": total,
                "percent": round(completed / total * 100, 1) if total > 0 else 0,
            },
            "error_count": task.error_count,
            "message": task.message,
            "logs": task.get_logs(),
            "updated_at": task.updated_at,
        }
        await self._send_to_subscribers(task, message)

    async def _send_to_subscribers(self, task: DownloadTask, message: dict):
        """Send a message to all WebSocket clients subscribed to this task. Clean up dead connections."""
        dead: list[WebSocket] = []
        for ws in task.websockets:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            try:
                task.websockets.remove(ws)
            except ValueError:
                pass

    # ── WebSocket subscription management ───────────────

    async def subscribe(self, task_id: str, ws: WebSocket) -> bool:
        """Subscribe a WebSocket client to a task's progress updates. Returns False if the task doesn't exist."""
        task = self.get_task(task_id)
        if not task:
            return False
        task.websockets.append(ws)
        # Send current state immediately
        try:
            completed, total = task.progress
            await ws.send_json({
                "type": "subscribed",
                "task_id": task_id,
                "status": task.status.value,
                "progress": {
                    "completed": completed,
                    "total": total,
                    "percent": round(completed / total * 100, 1) if total > 0 else 0,
                },
                "error_count": task.error_count,
                "message": task.message,
            })
        except Exception:
            pass
        return True

    async def unsubscribe(self, task_id: str, ws: WebSocket):
        task = self.get_task(task_id)
        if task and ws in task.websockets:
            try:
                task.websockets.remove(ws)
            except ValueError:
                pass
