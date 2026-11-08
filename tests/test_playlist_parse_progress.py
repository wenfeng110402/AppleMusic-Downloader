from __future__ import annotations

import asyncio
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from gamdl.cli import cli as gamdl_cli
from gamdl.downloader import AppleMusicDownloader
from gamdl.downloader.types import DownloadItem
from gamdl.interface import AppleMusicInterface
from structlog.testing import capture_logs

from amdl import cli, core_downloader, server, task_manager
from amdl.task_manager import DownloadTask, TaskManager, TaskStatus

PLAYLIST_URL = "https://music.apple.com/us/playlist/test/pl.1234567890abcdef1234567890abcdef"


def playlist_downloader() -> AppleMusicDownloader:
    repeated = {"id": "123", "type": "songs", "attributes": {"name": "Repeat"}}
    unavailable = {"id": "456", "type": "songs", "attributes": {"name": "Unavailable"}}

    async def get_playlist(media_id):
        return {"data": [{
            "type": "playlists",
            "relationships": {"tracks": {"data": [repeated], "next": "/next"}},
        }]}

    async def get_extended_api_data(next_uri, href_uri):
        return {"data": [repeated, unavailable]}

    async def get_media(media):
        yield media
        if media.media_id == "456":
            raise ValueError("Unavailable")
        media.partial = False
        yield media

    async def get_download_item(media):
        return DownloadItem(media)

    base = SimpleNamespace(apple_music_api=SimpleNamespace(
        get_playlist=get_playlist, get_extended_api_data=get_extended_api_data,
    ))
    song = SimpleNamespace(base=base, get_media=get_media)
    base.interface = AppleMusicInterface(song, None, None)
    song_downloader = SimpleNamespace(base=base, get_download_item=get_download_item)
    return AppleMusicDownloader(song_downloader, None, None)


class PlaylistParseTests(unittest.IsolatedAsyncioTestCase):
    async def test_counts_paginated_entries_including_repeats_and_unavailable_tracks(self):
        updates = []

        async def report(progress):
            updates.append(progress)

        items = [
            item async for item in core_downloader.iter_playlist_items(
                playlist_downloader().get_download_item_from_url(PLAYLIST_URL),
                PLAYLIST_URL, report,
            )
        ]
        self.assertEqual([item.media.media_id for item in items[1:]], [
            "123", "123", "123", "123", "456", "456",
        ])
        self.assertEqual(
            [(p["completed"], p["total"], p["current_title"]) for p in updates],
            [
                (0, None, ""), (0, 3, ""),
                (0, 3, "Repeat"), (1, 3, "Repeat"),
                (1, 3, "Repeat"), (2, 3, "Repeat"),
                (2, 3, "Unavailable"), (3, 3, "Unavailable"),
            ],
        )

    async def test_task_exposes_parsing_in_rest_and_websocket_without_changing_download_count(self):
        manager = TaskManager()
        task = DownloadTask("playlist", {"urls": [PLAYLIST_URL], "cookies_path": "cookies.txt"})
        task.status = TaskStatus.RUNNING
        manager._tasks[task.id] = task
        messages = []

        async def send_json(message):
            messages.append(message)

        async def download(**kwargs):
            progress = {"completed": 1, "total": 3, "current_title": "Repeat"}
            report = kwargs.get("parse_progress_callback")
            self.assertIsNotNone(report, "Tasks must receive metadata progress from the downloader")
            await report(progress)
            snapshot = await server.get_task(task.id)
            self.assertEqual(snapshot.model_dump()["parsing"], progress)
            self.assertEqual(snapshot.progress["completed"], 0)
            await manager.subscribe(task.id, SimpleNamespace(send_json=send_json))
            self.assertEqual(messages[-1]["parsing"], progress)
            await report(None)
            await kwargs["progress_callback"](1, 3)
            return 2

        await manager.subscribe(task.id, SimpleNamespace(send_json=send_json))
        with (
            patch.object(task_manager, "_download_urls_async", download),
            patch.object(server, "get_task_manager", return_value=manager),
        ):
            await manager._execute_download(task.id)
            snapshot = await server.get_task(task.id)

        self.assertEqual(snapshot.status, "completed")
        self.assertEqual(snapshot.progress["completed"], 1)
        self.assertIsNone(snapshot.model_dump()["parsing"])
        self.assertTrue(any(
            m["type"] == "parsing" and m["parsing"] is not None for m in messages
        ))
        self.assertTrue(any(
            m["type"] == "parsing" and m["parsing"] is None for m in messages
        ))


class CliPlaylistParseTests(unittest.TestCase):
    def test_passthrough_logs_playlist_progress_and_restores_gamdl(self):
        async def consume_playlist():
            configured_class = gamdl_cli.AppleMusicDownloader
            sample = playlist_downloader()
            sample.__class__ = configured_class
            return [item async for item in sample.get_download_item_from_url(PLAYLIST_URL)]

        original_argv = ["amdl", "-c", "cookies.txt", PLAYLIST_URL]

        def gamdl_main():
            self.assertEqual(sys.argv, ["gamdl", "-c", "cookies.txt", PLAYLIST_URL])
            self.assertEqual(len(asyncio.run(consume_playlist())), 7)

        with (
            patch.object(sys, "argv", original_argv),
            patch.object(gamdl_cli, "main", gamdl_main),
            capture_logs() as logs,
        ):
            cli.main()
            messages = [entry["event"] for entry in logs]
            self.assertIn('Resolving track 1/3: "Repeat"', messages)
            self.assertIn('Parsed 3/3: "Unavailable"', messages)
            self.assertIs(sys.argv, original_argv)
        self.assertIs(gamdl_cli.AppleMusicDownloader, AppleMusicDownloader)
