from __future__ import annotations

import unittest
from unittest.mock import patch

from amdl import task_manager as task_manager_module
from amdl.task_manager import DownloadTask, TaskManager, TaskStatus


class TaskResultTests(unittest.IsolatedAsyncioTestCase):
    async def test_playlist_with_successes_and_errors_is_partial(self) -> None:
        manager = TaskManager()
        task = DownloadTask(
            "playlist-task",
            {
                "urls": ["https://music.apple.com/test-playlist"],
                "cookies_path": "cookies.txt",
            },
        )
        manager._tasks[task.id] = task

        async def partial_download(**kwargs) -> int:
            await kwargs["progress_callback"](9, 10)
            return 1

        with patch.object(task_manager_module, "_download_urls_async", partial_download):
            await manager._execute_download(task.id)

        self.assertEqual(task.status, TaskStatus.COMPLETED)
        self.assertEqual(task.message, "部分完成（1 个错误）")


if __name__ == "__main__":
    unittest.main()
