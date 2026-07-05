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

import asyncio
import logging
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from fastapi import WebSocket

from amdl.core_downloader import download_urls

# ── Global singleton ─────────────────────────────────────────
_task_manager: TaskManager | None = None


def get_task_manager() -> TaskManager:
    """Get the global TaskManager singleton."""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager


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
        self.created_at: str = datetime.now(timezone.utc).isoformat()
        self.updated_at: str = self.created_at
        self.cancelled: bool = False
        self.websockets: list[WebSocket] = []  # WebSocket clients subscribed to this task

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
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "urls": self.kwargs.get("urls", []),
        }


# ── Task queue manager ───────────────────────────────────────

class TaskManager:
    """Manages the download task queue, executes tasks sequentially, and pushes progress via WebSocket."""

    def __init__(self, max_concurrent: int = 1):
        self._tasks: dict[str, DownloadTask] = {}
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._max_concurrent = max_concurrent
        self._loop: asyncio.AbstractEventLoop | None = None
        self._worker_task: asyncio.Task | None = None
        self._thread_pool = ThreadPoolExecutor(max_workers=max_concurrent)
        self._lock = threading.Lock()

    # ── Lifecycle ────────────────────────────────────────

    def start(self, loop: asyncio.AbstractEventLoop | None = None):
        """Start the background worker coroutine. Call this on FastAPI startup."""
        self._loop = loop or asyncio.get_event_loop()
        self._worker_task = self._loop.create_task(self._worker_loop())

    async def stop(self):
        """Stop the background worker. Call this on FastAPI shutdown."""
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        self._thread_pool.shutdown(wait=False)
        # Close all remaining WebSocket connections
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
        await self._broadcast_status(task)
        return True

    # ── Background worker loop ───────────────────────────

    async def _worker_loop(self):
        """Continuously pick tasks from the queue and execute them in a thread pool."""
        while True:
            task_id = await self._queue.get()
            task = self.get_task(task_id)
            if not task or task.cancelled:
                self._queue.task_done()
                continue

            # Mark as RUNNING
            task.status = TaskStatus.RUNNING
            task.updated_at = datetime.now(timezone.utc).isoformat()
            await self._broadcast_status(task)

            loop = asyncio.get_running_loop()
            try:
                await loop.run_in_executor(
                    self._thread_pool,
                    self._execute_download,
                    task_id,
                )
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.message = f"Internal error: {e}"
                task.updated_at = datetime.now(timezone.utc).isoformat()
                await self._broadcast_status(task)
            finally:
                self._queue.task_done()

    def _execute_download(self, task_id: str):
        """Execute the download in a worker thread (no async code here)."""
        task = self.get_task(task_id)
        if not task or task.cancelled:
            return

        # ── Build progress callback ──────────────────────
        def on_progress(completed: int, total: int):
            """Called by core_downloader.download_urls from the worker thread."""
            if task.cancelled:
                raise InterruptedError("Task cancelled")
            task.progress = (completed, total)
            # Bridge: worker thread → event loop → WebSocket
            if self._loop and not self._loop.is_closed():
                asyncio.run_coroutine_threadsafe(
                    self._broadcast_progress(task_id, completed, total),
                    self._loop,
                )

        # ── Build log callback ───────────────────────────
        def on_log(msg: str):
            logging.getLogger("amdl.task").info(f"[{task_id[:8]}] {msg}")

        # ── Execute download ─────────────────────────────
        try:
            kwargs = task.kwargs.copy()
            kwargs["progress_callback"] = on_progress
            kwargs["log_callback"] = on_log
            kwargs["no_exceptions"] = True  # always handle internally

            # Convert string paths to Path objects
            for key in ("cookies_path", "output_path", "temp_path"):
                val = kwargs.get(key)
                if isinstance(val, str):
                    kwargs[key] = Path(val)

            wvd = kwargs.get("wvd_path")
            if isinstance(wvd, str):
                kwargs["wvd_path"] = Path(wvd) if wvd else None

            err_count = download_urls(**kwargs)

            if not task.cancelled:
                task.error_count = err_count
                task.status = TaskStatus.COMPLETED
                task.message = "全部完成" if err_count == 0 else f"完成（{err_count} 个错误）"
                task.updated_at = datetime.now(timezone.utc).isoformat()

        except InterruptedError:
            task.status = TaskStatus.CANCELLED
            task.message = "已取消"
            task.updated_at = datetime.now(timezone.utc).isoformat()
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.message = str(e)
            task.updated_at = datetime.now(timezone.utc).isoformat()
            logging.getLogger("amdl.task").error(
                f"[{task_id[:8]}] Download failed: {e}", exc_info=True
            )

        # Broadcast final status to subscribers
        if self._loop and not self._loop.is_closed():
            asyncio.run_coroutine_threadsafe(
                self._broadcast_status(task),
                self._loop,
            )

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
        message = {
            "type": "status",
            "task_id": task.id,
            "status": task.status.value,
            "progress": {
                "completed": task.progress[0],
                "total": task.progress[1],
            },
            "error_count": task.error_count,
            "message": task.message,
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