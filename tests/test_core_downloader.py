from __future__ import annotations

import asyncio
import json
import logging
import unittest
from unittest.mock import patch

from amdl import core_downloader


class _FakePlaylistApi:
    def __init__(self, pages: dict[str, dict]) -> None:
        self.pages = pages
        self.requested: list[tuple[str, dict]] = []

    async def _amp_request(self, path: str, params: dict) -> dict:
        self.requested.append((path, params))
        return self.pages[path]


class YtdlpOptionsTests(unittest.TestCase):
    def test_fragment_failures_are_not_silently_skipped(self) -> None:
        log = logging.getLogger("test.ytdlp")
        options = core_downloader._ytdlp_options(log)

        self.assertEqual(options["retries"], 10)
        self.assertEqual(options["fragment_retries"], 10)
        self.assertFalse(options["skip_unavailable_fragments"])
        self.assertFalse(options["continuedl"])
        self.assertIsInstance(options["logger"], core_downloader._YtdlpLogger)


class DurationValidationTests(unittest.TestCase):
    def test_catalog_duration_is_read_from_duration_in_millis(self) -> None:
        metadata = {"attributes": {"durationInMillis": 125_812}}

        self.assertAlmostEqual(
            core_downloader._expected_duration_seconds(metadata),
            125.812,
        )

    def test_truncated_file_is_rejected_and_removed(self) -> None:
        log = logging.getLogger("test.duration")
        with (
            patch.object(core_downloader, "_probe_media_duration", return_value=65.953),
            patch("pathlib.Path.unlink") as unlink,
        ):
            with self.assertRaisesRegex(RuntimeError, "incomplete media detected"):
                core_downloader._validate_media_duration(
                    "Campfire Song.m4a",
                    125.812,
                    "ffprobe",
                    log,
                )

        unlink.assert_called_once_with(missing_ok=True)

    def test_duration_within_tolerance_is_accepted(self) -> None:
        log = logging.getLogger("test.duration")
        with patch.object(core_downloader, "_probe_media_duration", return_value=69.1):
            core_downloader._validate_media_duration(
                "track.m4a",
                69.063,
                "ffprobe",
                log,
            )

    def test_probe_parses_ffprobe_output(self) -> None:
        completed = type(
            "Completed",
            (),
            {
                "returncode": 0,
                "stdout": json.dumps(
                    {
                        "streams": [{"duration": "125.812000"}],
                        "format": {"duration": "125.812000"},
                    }
                ),
                "stderr": "",
            },
        )()
        with patch.object(core_downloader.subprocess, "run", return_value=completed):
            duration = core_downloader._probe_media_duration("track.m4a", "ffprobe")

        self.assertAlmostEqual(duration, 125.812)

    def test_unverifiable_duration_is_an_error(self) -> None:
        log = logging.getLogger("test.duration")
        with patch.object(core_downloader, "_probe_media_duration", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "could not verify duration"):
                core_downloader._validate_media_duration(
                    "track.m4a",
                    125.812,
                    "ffprobe",
                    log,
                )


class PlaylistPaginationTests(unittest.TestCase):
    def test_all_next_pages_are_loaded_and_track_count_is_checked(self) -> None:
        first_page = {
            "data": [
                {
                    "id": "pl.1",
                    "type": "playlists",
                    "attributes": {"trackCount": 3},
                    "relationships": {
                        "tracks": {
                            "data": [{"id": "1", "type": "songs"}],
                            "next": "/v1/catalog/us/playlists/pl.1/tracks?offset=1&limit=2",
                        }
                    },
                }
            ]
        }
        api = _FakePlaylistApi(
            {
                "/v1/catalog/us/playlists/pl.1/tracks": {
                    "data": [
                        {"id": "2", "type": "songs"},
                        {"id": "3", "type": "songs"},
                    ],
                    "next": None,
                }
            }
        )

        asyncio.run(
            core_downloader._load_all_playlist_tracks(
                api,
                first_page,
                logging.getLogger("test.playlist"),
            )
        )

        tracks = first_page["data"][0]["relationships"]["tracks"]
        self.assertEqual([track["id"] for track in tracks["data"]], ["1", "2", "3"])
        self.assertIsNone(tracks["next"])
        self.assertEqual(
            api.requested,
            [
                (
                    "/v1/catalog/us/playlists/pl.1/tracks",
                    {"offset": "1", "limit": "2"},
                )
            ],
        )

    def test_short_playlist_fails_instead_of_marking_success(self) -> None:
        first_page = {
            "data": [
                {
                    "id": "pl.short",
                    "type": "playlists",
                    "attributes": {"trackCount": 150},
                    "relationships": {
                        "tracks": {
                            "data": [{"id": "1", "type": "songs"}],
                            "next": None,
                        }
                    },
                }
            ]
        }

        with self.assertRaisesRegex(RuntimeError, "loaded 1 of 150"):
            asyncio.run(
                core_downloader._load_all_playlist_tracks(
                    _FakePlaylistApi({}),
                    first_page,
                    logging.getLogger("test.playlist"),
                )
            )

    def test_repeated_cursor_fails_instead_of_looping_forever(self) -> None:
        next_uri = "/v1/catalog/us/playlists/pl.loop/tracks?offset=1"
        first_page = {
            "data": [
                {
                    "id": "pl.loop",
                    "type": "playlists",
                    "relationships": {
                        "tracks": {
                            "data": [{"id": "1", "type": "songs"}],
                            "next": next_uri,
                        }
                    },
                }
            ]
        }

        with self.assertRaisesRegex(RuntimeError, "cursor repeated"):
            asyncio.run(
                core_downloader._load_all_playlist_tracks(
                    _FakePlaylistApi(
                        {
                            "/v1/catalog/us/playlists/pl.loop/tracks": {
                                "data": [],
                                "next": next_uri,
                            }
                        }
                    ),
                    first_page,
                    logging.getLogger("test.playlist"),
                )
            )


if __name__ == "__main__":
    unittest.main()
