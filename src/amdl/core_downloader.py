"""Core download API — thin wrapper around gamdl's embedding API."""

from __future__ import annotations

import asyncio
import datetime
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import traceback
from collections.abc import AsyncIterator, Awaitable
from pathlib import Path
from typing import Callable, TypedDict
from urllib.parse import parse_qs, urlparse

# ── Python version guard ────────────────────────────────
_MIN_PYTHON = (3, 10)
if sys.version_info[:2] < _MIN_PYTHON:
    raise RuntimeError(f"Python {sys.version_info[0]}.{sys.version_info[1]} too old")

if sys.platform == "win32":
    os.environ.setdefault("ANYIO_BACKEND", "asyncio")

# ── gamdl imports ───────────────────────────────────────
from gamdl.api import AppleMusicApi
from gamdl.downloader import (
    AppleMusicBaseDownloader,
    AppleMusicDownloader,
    AppleMusicMusicVideoDownloader,
    AppleMusicSongDownloader,
    AppleMusicUploadedVideoDownloader,
    DownloadMode,
)
from gamdl.downloader.exceptions import (
    GamdlDownloaderMediaFileExistsError,
    GamdlDownloaderSyncedLyricsOnlyError,
)
from gamdl.downloader.types import DownloadItem
from gamdl.interface import (
    AppleMusicBaseInterface,
    AppleMusicInterface,
    AppleMusicMedia,
    AppleMusicMusicVideoInterface,
    AppleMusicSongInterface,
    AppleMusicUploadedVideoInterface,
    CoverFormat,
    MediaRating,
    MediaTags,
    MediaType,
    MusicVideoCodec,
    SongCodec,
    SyncedLyricsFormat,
    UploadedVideoQuality,
)
from gamdl.interface.exceptions import (
    GamdlInterfaceDecryptionNotAvailableError,
    GamdlInterfaceMediaNotStreamableError,
)
from gamdl.interface.types import DecryptionKeyAv

LogCallback = Callable[[str], None]


class PlaylistParseProgress(TypedDict):
    completed: int
    total: int | None
    current_title: str


ParseProgressCallback = Callable[[PlaylistParseProgress | None], Awaitable[None]]


async def iter_playlist_items(
    items: AsyncIterator[DownloadItem],
    url: str,
    report: ParseProgressCallback | None,
) -> AsyncIterator[DownloadItem]:
    """Observe playlist metadata resolution without altering gamdl's item stream."""
    url_info = AppleMusicInterface.get_url_info(url) if report else None
    if report is None or url_info is None or url_info.sub_id or not (
        url_info.type == "playlist" or url_info.library_type == "playlist"
    ):
        async for item in items:
            yield item
        return

    total = None
    resolved: set[int] = set()
    await report({"completed": 0, "total": total, "current_title": ""})
    async for item in items:
        media = item.media
        metadata = media.media_metadata or {}
        if metadata.get("type") in {"playlists", "library-playlists"} and not media.error:
            tracks = metadata.get("relationships", {}).get("tracks", {}).get("data")
            if tracks is not None:
                total = len(tracks)
                await report({"completed": 0, "total": total, "current_title": ""})
        elif media.playlist_metadata and media.index not in resolved:
            # Repeated songs occupy different positions in the same playlist.
            if not media.partial or media.error:
                resolved.add(media.index)
            await report({
                "completed": len(resolved),
                "total": total,
                "current_title": metadata.get("attributes", {}).get("name", ""),
            })
        yield item


# ── logger ──────────────────────────────────────────────
class _CallbackHandler(logging.Handler):
    def __init__(self, cb: LogCallback) -> None:
        super().__init__(logging.DEBUG)
        self.cb = cb
    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.cb(self.format(record))
        except Exception:
            self.handleError(record)

def _get_logger(name: str, level: str, cb: LogCallback | None) -> logging.Logger:
    log = logging.getLogger(name)
    log.setLevel(level)
    log.handlers.clear()
    h = _CallbackHandler(cb) if cb else logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter("%(message)s" if cb else "[%(levelname)s] %(message)s"))
    log.addHandler(h)
    return log


class _YtdlpLogger:
    """Forward yt-dlp diagnostics into the AMDL task log.

    yt-dlp sends retry and fragment messages through ``logger.debug`` even
    when ``quiet`` is enabled. Mapping those messages to INFO is important
    here: a fragment failure must remain visible instead of looking like a
    successful download.
    """

    def __init__(self, log: logging.Logger) -> None:
        self._log = log

    @staticmethod
    def _clean(message: object) -> str:
        return str(message).strip()

    def debug(self, message: object) -> None:
        text = self._clean(message)
        if not text or ("[download]" in text and "%" in text):
            return
        self._log.info("yt-dlp: %s", text.removeprefix("[debug] "))

    def info(self, message: object) -> None:
        self.debug(message)

    def warning(self, message: object) -> None:
        text = self._clean(message)
        if text:
            self._log.warning("yt-dlp: %s", text)

    def error(self, message: object) -> None:
        text = self._clean(message)
        if text:
            self._log.error("yt-dlp: %s", text)


def _ytdlp_options(log: logging.Logger) -> dict:
    """Return strict yt-dlp options for Apple Music HLS downloads."""
    return {
        "quiet": True,
        "no_warnings": True,
        "overwrites": True,
        "noprogress": True,
        "allow_unplayable_formats": True,
        # Match gamdl's proven fragment concurrency. Do NOT add
        # http_chunk_size: range-chunking on CENC HLS can cause
        # "Conflicting range" errors.
        "concurrent_fragment_downloads": 8,
        # yt-dlp's API defaults are too permissive for a lossless archive:
        # fragment_retries=0 and skip_unavailable_fragments=True can produce
        # a playable but truncated file that still returns success.
        "retries": 10,
        "fragment_retries": 10,
        "skip_unavailable_fragments": False,
        "continuedl": False,
        "logger": _YtdlpLogger(log),
    }


_DURATION_TOLERANCE_SECONDS = 2.0


def _expected_duration_seconds(media_metadata: object) -> float | None:
    """Extract Apple Music's catalog duration without trusting other fields."""
    if not isinstance(media_metadata, dict):
        return None
    attributes = media_metadata.get("attributes")
    if not isinstance(attributes, dict):
        return None
    value = attributes.get("durationInMillis")
    try:
        duration = float(value) / 1000.0
    except (TypeError, ValueError):
        return None
    return duration if duration > 0 else None


def _probe_media_duration(path: str | Path, ffprobe_path: str) -> float | None:
    """Read the audio stream duration, falling back to container duration."""
    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0  # type: ignore[attr-defined]
    try:
        result = subprocess.run(
            [
                ffprobe_path,
                "-v", "error",
                "-select_streams", "a:0",
                "-show_entries", "stream=duration:format=duration",
                "-of", "json",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=60,
            creationflags=creationflags,
        )
        if result.returncode != 0:
            return None
        probe = json.loads(result.stdout)
        values = [
            stream.get("duration")
            for stream in probe.get("streams", [])
            if isinstance(stream, dict)
        ]
        values.append(probe.get("format", {}).get("duration"))
        duration = next(
            (float(value) for value in values if value not in (None, "N/A")),
            None,
        )
    except (OSError, ValueError, TypeError, json.JSONDecodeError, subprocess.SubprocessError):
        return None
    return duration if duration is not None and duration > 0 else None


def _validate_media_duration(
    path: str | Path,
    expected_seconds: float | None,
    ffprobe_path: str,
    log: logging.Logger,
) -> None:
    """Reject a staged file when its actual duration is clearly too short."""
    if expected_seconds is None:
        return

    actual_seconds = _probe_media_duration(path, ffprobe_path)
    if actual_seconds is None:
        raise RuntimeError(
            f'could not verify duration for "{Path(path).name}": '
            f"ffprobe ({ffprobe_path}) is unavailable or the file is unreadable"
        )

    difference = actual_seconds - expected_seconds
    if abs(difference) > _DURATION_TOLERANCE_SECONDS:
        Path(path).unlink(missing_ok=True)
        raise RuntimeError(
            f'incomplete media detected for "{Path(path).name}": '
            f"actual {actual_seconds:.3f}s, expected {expected_seconds:.3f}s "
            f"(difference {difference:+.3f}s, tolerance {_DURATION_TOLERANCE_SECONDS:.1f}s)"
        )

    log.info('Duration verified "%s": %.3fs (expected %.3fs)', Path(path).name, actual_seconds, expected_seconds)


def _resolve_ffprobe(ffmpeg_path: str) -> str:
    """Prefer ffprobe next to the configured ffmpeg, then use PATH."""
    ffmpeg = Path(ffmpeg_path)
    if ffmpeg.name.lower() in {"ffmpeg", "ffmpeg.exe"}:
        sibling = ffmpeg.with_name("ffprobe.exe" if sys.platform == "win32" else "ffprobe")
        if sibling.exists():
            return str(sibling)
    return _resolve_bin("ffprobe")


def _playlist_track_count(playlist: dict) -> int | None:
    """Return Apple Music's advertised playlist track count."""
    try:
        value = playlist["attributes"]["trackCount"]
        count = int(value)
    except (KeyError, TypeError, ValueError):
        return None
    return count if count >= 0 else None


async def _fetch_playlist_page(api: AppleMusicApi, next_uri: str) -> dict:
    """Fetch one ``next`` page using the exact URI supplied by Apple."""
    parsed = urlparse(next_uri)
    raw_params = parse_qs(parsed.query, keep_blank_values=True)
    params = {
        key: values[0] if len(values) == 1 else values
        for key, values in raw_params.items()
    }
    if not parsed.path:
        raise RuntimeError(f"Invalid playlist next URI: {next_uri}")
    return await api._amp_request(parsed.path, params)


async def _load_all_playlist_tracks(
    api: AppleMusicApi,
    playlist_response: dict,
    log: logging.Logger,
) -> None:
    """Hydrate every track page before gamdl creates per-track download tasks.

    Apple may cap the first *catalog* request at 100 tracks even when a larger
    ``limit[tracks]`` is requested. gamdl 3.9.1 has an implicit loop, but this
    explicit version uses Apple's exact ``next`` URI, detects cursor loops and
    verifies the advertised ``trackCount``. Without that final check, a failed
    second page can silently look like a successful short playlist download.
    """
    data = playlist_response.get("data") if isinstance(playlist_response, dict) else None
    if not data or not isinstance(data[0], dict):
        return

    playlist = data[0]
    relationships = playlist.get("relationships")
    tracks_relation = relationships.get("tracks") if isinstance(relationships, dict) else None
    if not isinstance(tracks_relation, dict):
        return

    tracks = tracks_relation.get("data")
    if not isinstance(tracks, list):
        tracks = []
        tracks_relation["data"] = tracks

    expected = _playlist_track_count(playlist)
    log.info(
        'Playlist "%s": first page has %d tracks (expected total: %s)',
        playlist.get("id", "?"),
        len(tracks),
        expected if expected is not None else "unknown",
    )

    next_uri = tracks_relation.get("next")
    seen_cursors: set[str] = set()
    page_number = 1
    while next_uri:
        if next_uri in seen_cursors:
            raise RuntimeError(f"Playlist pagination cursor repeated: {next_uri}")
        seen_cursors.add(next_uri)

        page = await _fetch_playlist_page(api, next_uri)
        page_tracks = page.get("data", []) if isinstance(page, dict) else []
        if not isinstance(page_tracks, list):
            raise RuntimeError(f"Invalid playlist page payload at page {page_number + 1}")

        tracks.extend(page_tracks)
        page_number += 1
        next_uri = page.get("next")
        log.info(
            'Playlist "%s": loaded page %d, %d tracks so far',
            playlist.get("id", "?"),
            page_number,
            len(tracks),
        )

    # Keep gamdl's implicit pagination loop from requesting the same pages again.
    tracks_relation["next"] = None

    if expected is not None and len(tracks) != expected:
        raise RuntimeError(
            f'playlist pagination incomplete for "{playlist.get("id", "?")}": '
            f"loaded {len(tracks)} of {expected} tracks after {page_number} page(s)"
        )

    log.info(
        'Playlist "%s": pagination complete, %d/%s tracks loaded',
        playlist.get("id", "?"),
        len(tracks),
        expected if expected is not None else "?",
    )


def _install_playlist_pagination(api: AppleMusicApi, log: logging.Logger) -> None:
    """Wrap both catalog and library playlist requests with full pagination."""
    original_catalog = api.get_playlist
    original_library = api.get_library_playlist

    async def catalog_with_all_tracks(*args, **kwargs):
        response = await original_catalog(*args, **kwargs)
        await _load_all_playlist_tracks(api, response, log)
        return response

    async def library_with_all_tracks(*args, **kwargs):
        response = await original_library(*args, **kwargs)
        await _load_all_playlist_tracks(api, response, log)
        return response

    api.get_playlist = catalog_with_all_tracks  # type: ignore[method-assign]
    api.get_library_playlist = library_with_all_tracks  # type: ignore[method-assign]


# ── binary resolver ─────────────────────────────────────
def _resolve_bin(name: str) -> str:
    p = shutil.which(name)
    if p:
        return p
    from amdl.dependency_manager import BIN_DIR
    c = BIN_DIR / name
    if c.exists():
        return str(c)
    if getattr(sys, "frozen", False):
        mp = Path(getattr(sys, "_MEIPASS", "")) / "bin" / name
        if mp.exists():
            return str(mp)
    for d in ["/opt/homebrew/bin", "/usr/local/bin", str(Path.home() / ".local" / "bin")]:
        c = Path(d) / name
        if c.exists():
            return str(c)
    return name


def _format_ttml(raw_ttml: str) -> str:
    """Format TTML XML cleanly while strictly preserving spaces between words and keeping <p> on one line.

    gamdl's default minidom.parseString().toprettyxml() breaks mixed content inside <p>, converting spaces
    between <span> tags into newlines and tabs ('\\n\\t\\t\\t\\t \\n\\t\\t\\t\\t'), which causes standard TTML
    parsers (AMLL, Lyricify, Salt Player) to strip the whitespace and render all words glued together without spaces.
    """
    if not raw_ttml or not isinstance(raw_ttml, str):
        return raw_ttml

    xml_str = raw_ttml.strip()
    if xml_str.startswith("<?xml"):
        xml_str = re.sub(r"^\<\?xml.*?\?\>\s*", "", xml_str, flags=re.DOTALL)

    # Separate elements so placeholders and structural blocks each start on a new line
    xml_str = re.sub(r"(<p\b)", r"\n\1", xml_str)
    xml_str = re.sub(r"(</p>)", r"\1\n", xml_str)
    xml_str = re.sub(r"(<div\b)", r"\n\1\n", xml_str)
    xml_str = re.sub(r"(</div>)", r"\n\1\n", xml_str)

    p_placeholders: list[str] = []

    def _clean_p(match: re.Match) -> str:
        p_content = match.group(0)
        # Normalize any whitespace or newline sequence between </span> and <span to exactly one space
        p_content = re.sub(r"</span>\s+<span", "</span> <span", p_content)
        # Remove any leading whitespace directly after <p ...>
        p_content = re.sub(r"(<p\b[^>]*>)\s+", r"\1", p_content)
        # Remove any trailing whitespace directly before </p>
        p_content = re.sub(r"\s+(</p>)", r"\1", p_content)
        idx = len(p_placeholders)
        p_placeholders.append(p_content)
        return f"___TTML_P_PLACEHOLDER_{idx}___"

    protected = re.sub(r"<p\b[^>]*>.*?</p>", _clean_p, xml_str, flags=re.DOTALL)

    text_placeholders: list[str] = []

    def _clean_text(match: re.Match) -> str:
        t_content = match.group(0).strip()
        idx = len(text_placeholders)
        text_placeholders.append(t_content)
        return f"___TTML_TEXT_PLACEHOLDER_{idx}___"

    protected = re.sub(r"<text\b[^>]*>.*?</text>", _clean_text, protected, flags=re.DOTALL)

    # Format structural tags with indentation
    protected = re.sub(r">\s*<", ">\n<", protected)

    lines = protected.splitlines()
    indent = 0
    formatted_lines: list[str] = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("</"):
            indent = max(0, indent - 1)

        formatted_lines.append("  " * indent + line)

        if line.startswith("<") and not line.startswith("</") and not line.endswith("/>"):
            if "</" not in line:
                indent += 1

    result = "\n".join(formatted_lines)

    for i, p in enumerate(p_placeholders):
        result = result.replace(f"___TTML_P_PLACEHOLDER_{i}___", p)
    for i, t in enumerate(text_placeholders):
        result = result.replace(f"___TTML_TEXT_PLACEHOLDER_{i}___", t)

    return '<?xml version="1.0" encoding="utf-8"?>\n' + result


# ── sync entry point ────────────────────────────────────
def download_urls(**kwargs) -> int:
    """Synchronous entry point for download_urls.

    Creates a new event loop appropriate for the platform.
    On Windows, ProactorEventLoop is used (supports subprocesses & async IO).
    """
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_download_urls_async(**kwargs))
    finally:
        loop.close()


# ══════════════════════════════════════════════════════════
# async entry point
# ══════════════════════════════════════════════════════════
async def _download_urls_async(
    *,
    urls: list[str],
    cookies_path: Path,
    output_path: Path = Path("./Apple Music"),
    temp_path: Path = Path("./temp"),
    wvd_path: Path | None = None,
    nm3u8dlre_path: str = "N_m3u8DL-RE",
    ffmpeg_path: str = "ffmpeg",
    download_mode: DownloadMode = DownloadMode.YTDLP,
    codec_song: SongCodec = SongCodec.AAC_WEB,
    codec_music_video: MusicVideoCodec = MusicVideoCodec.H264,
    quality_post: UploadedVideoQuality = UploadedVideoQuality.BEST,
    synced_lyrics_format: SyncedLyricsFormat = SyncedLyricsFormat.LRC,
    cover_format: CoverFormat = CoverFormat.JPG,
    cover_size: int = 1200,
    truncate: int | None = None,
    audio_format: str | None = None,
    video_format: str | None = None,
    template_folder_album: str = "{album_artist}/{album}",
    template_folder_compilation: str = "Compilations/{album}",
    template_file_single_disc: str = "{track:02d} {title}",
    template_file_multi_disc: str = "{disc}-{track:02d} {title}",
    template_folder_no_album: str = "{artist}/Unknown Album",
    template_file_no_album: str = "{title}",
    template_file_playlist: str = "Playlists/{playlist_artist}/{playlist_title}",
    template_date: str = "%Y-%m-%dT%H:%M:%SZ",
    exclude_tags: str | None = None,
    overwrite: bool = False,
    save_cover: bool = False,
    save_playlist: bool = False,
    synced_lyrics_only: bool = False,
    no_synced_lyrics: bool = False,
    disable_music_video_skip: bool = False,
    read_urls_as_txt: bool = False,
    no_exceptions: bool = True,
    language: str = "en-US",
    log_callback: LogCallback | None = None,
    log_level: str = "INFO",
    progress_callback: Callable[[int, int], None] | None = None,
    parse_progress_callback: ParseProgressCallback | None = None,
) -> int:
    log = _get_logger("amdl.core", log_level, log_callback)
    log.info("System: Python %s.%s.%s | Platform: %s | EventLoop: %s",
             sys.version_info.major, sys.version_info.minor, sys.version_info.micro,
             sys.platform, type(asyncio.get_running_loop()).__name__)

    # ── PATH: Finder/Explorer launch has minimal env ────
    for d in ["/opt/homebrew/bin", "/usr/local/bin", str(Path.home() / ".local/bin")]:
        if d not in os.environ.get("PATH", ""):
            os.environ["PATH"] = f"{d}{os.pathsep}{os.environ.get('PATH', '')}"

    # ── absolute paths ──────────────────────────────────
    temp_path = temp_path.resolve()
    output_path = output_path.resolve()
    cookies_path = cookies_path.resolve()
    if wvd_path:
        wvd_path = wvd_path.resolve()

    # ── txt expansion ───────────────────────────────────
    if read_urls_as_txt:
        _u: list[str] = []
        for u in urls:
            p = Path(u)
            _u.extend(p.read_text("utf-8").splitlines() if p.exists() else [u])
        urls = _u

    # ── deduplicate urls while preserving order ────────
    seen_urls: set[str] = set()
    deduped_urls: list[str] = []
    for u in urls:
        clean_u = u.strip()
        if clean_u and clean_u not in seen_urls:
            seen_urls.add(clean_u)
            deduped_urls.append(clean_u)
    urls = deduped_urls

    exclude_list = [t.strip().lower() for t in (exclude_tags or "").split(",") if t.strip()]

    # ── API client ──────────────────────────────────────
    try:
        api = await AppleMusicApi.create_from_netscape_cookies(str(cookies_path), language=language)
    except Exception as e:
        log.critical(f"API init failed: {e}"); return 1

    if not api.active_subscription:
        log.critical("No active subscription"); return 1

    # Apple's first playlist page can be capped at 100 even when a larger
    # limit is requested. Ensure all pages are loaded before gamdl fans out.
    _install_playlist_pagination(api, log)

    # ── gamdl interface ─────────────────────────────────
    log.info("Creating AppleMusicBaseInterface...")
    base_iface = await AppleMusicBaseInterface.create(
        apple_music_api=api, cover_format=cover_format, cover_size=cover_size,
        wvd_path=str(wvd_path) if wvd_path else None,
    )
    log.info("AppleMusicBaseInterface created, building AppleMusicInterface...")
    song_priority = [codec_song]
    for c in (SongCodec.AAC_WEB, SongCodec.AAC_HE_WEB):
        if c not in song_priority:
            song_priority.append(c)

    song_iface = AppleMusicSongInterface(
        base=base_iface,
        synced_lyrics_format=synced_lyrics_format,
        codec_priority=song_priority,
        skip_stream_info=synced_lyrics_only,
    )

    # ── fix TTML formatting: prevent minidom from mutilating spaces between words ──
    _orig_internal_get_lyrics = song_iface._get_lyrics

    def _safe_internal_get_lyrics(lyrics_ttml: str):
        lyrics = _orig_internal_get_lyrics(lyrics_ttml)
        if lyrics and lyrics.synced and synced_lyrics_format == SyncedLyricsFormat.TTML:
            lyrics.synced = _format_ttml(lyrics_ttml)
        return lyrics

    song_iface._get_lyrics = _safe_internal_get_lyrics

    # ── enhance lyrics fetch: retrieve syllable-level and translated TTML ──
    _orig_get_lyrics = song_iface.get_lyrics

    async def _enhanced_get_lyrics(song_metadata: dict):
        song_id = song_metadata.get("id")
        if not song_id or song_metadata.get("attributes", {}).get("playParams", {}).get("isLibrary"):
            return await _orig_get_lyrics(song_metadata)

        if not song_metadata.get("attributes", {}).get("hasLyrics"):
            return None

        # 1. Try Apple Music Sing / syllable-lyrics endpoint for word-level & translated TTML
        if synced_lyrics_format == SyncedLyricsFormat.TTML:
            try:
                res = await api._amp_request(
                    f"/v1/catalog/{api.storefront}/songs/{song_id}/syllable-lyrics",
                    params={"l": language, "extend": "ttmlLocalizations"},
                )
                if res and "data" in res and len(res["data"]) > 0:
                    attrs = res["data"][0].get("attributes", {})
                    # When extend=ttmlLocalizations is passed, Apple returns the full syllable-timed
                    # and translated TTML in attrs["ttmlLocalizations"].
                    # Without extend, base syllable TTML is in attrs["ttml"].
                    raw_ttml = attrs.get("ttmlLocalizations") or attrs.get("ttml")
                    if isinstance(raw_ttml, dict):
                        lang_key = None
                        for k in raw_ttml.keys():
                            if k.lower() in language.lower() or language.lower() in k.lower():
                                lang_key = k
                                break
                        if not lang_key and "zh-Hans" in raw_ttml:
                            lang_key = "zh-Hans"
                        raw_ttml = raw_ttml.get(lang_key) or next(iter(raw_ttml.values()), None)

                    if raw_ttml and isinstance(raw_ttml, str):
                        log.info('Retrieved syllable/translated TTML for song %s', song_id)
                        return song_iface._get_lyrics(raw_ttml)
            except Exception as err:
                log.debug("Syllable-lyrics unavailable for %s: %s; falling back to standard lyrics", song_id, err)

        # 2. Fall back to standard catalog lyrics
        return await _orig_get_lyrics(song_metadata)

    song_iface.get_lyrics = _enhanced_get_lyrics

    # ── enhance get_media: safe webplayback tags & graceful catalog fallback ──
    async def _safe_get_media(media: AppleMusicMedia):
        if not media.media_metadata:
            media.media_metadata = (
                await (
                    song_iface.base.apple_music_api.get_library_song(media.media_id)
                    if media.is_library
                    else song_iface.base.apple_music_api.get_song(media.media_id)
                )
            )["data"][0]

        if media.media_metadata.get("attributes", {}).get("playParams", {}).get("isLibrary"):
            catalog_metadata = song_iface.base.get_catalog_metadata_from_library(media.media_metadata)
            if catalog_metadata:
                media.media_id = catalog_metadata["id"]
                media.is_library = False
                media.media_metadata = catalog_metadata

        yield media

        if not song_iface.base.is_media_streamable(media.media_metadata):
            raise GamdlInterfaceMediaNotStreamableError(media_id=media.media_id)

        if media.playlist_metadata:
            media.playlist_tags = song_iface.base.get_playlist_tags(media.playlist_metadata, media.index)

        async def _fetch_cover():
            try:
                return await song_iface.base.get_cover(media.media_metadata)
            except Exception as e:
                log.debug("cover fetch failed for %s: %s", media.media_id, e)
                return None

        async def _fetch_lyrics():
            if no_synced_lyrics:
                return None
            try:
                return await song_iface.get_lyrics(media.media_metadata)
            except Exception as e:
                log.debug("lyrics fetch failed for %s: %s", media.media_id, e)
                return None

        async def _fetch_playback():
            p, wp = None, None
            try:
                if song_iface.base.wrapper_api:
                    p = (
                        await song_iface.base.wrapper_api.get_playback(media.media_id)
                        if not media.is_library else None
                    )
                    wp = (
                        await song_iface.base.apple_music_api.get_webplayback(media.media_id, media.is_library)
                        if media.is_library or any(codec.is_web for codec in song_iface.codec_priority) else None
                    )
                else:
                    wp = await song_iface.base.apple_music_api.get_webplayback(media.media_id, media.is_library)
            except Exception as e:
                log.debug("webplayback query failed for %s: %s", media.media_id, e)
            return p, wp

        cover_res, lyrics_res, (playback, webplayback) = await asyncio.gather(
            _fetch_cover(),
            _fetch_lyrics(),
            _fetch_playback(),
        )
        media.cover = cover_res
        media.lyrics = lyrics_res

        tags_extracted = False
        if playback and isinstance(playback.get("songList"), list) and playback["songList"]:
            try:
                media.tags = await song_iface.base.get_tags_from_asset_info(
                    playback["songList"][0]["assets"][0]["metadata"],
                    media.lyrics.unsynced if media.lyrics else None,
                    song_iface.use_album_date,
                )
                tags_extracted = True
            except Exception as e:
                log.debug("Failed extracting tags from playback: %s", e)

        if not tags_extracted and webplayback and isinstance(webplayback.get("songList"), list) and webplayback["songList"]:
            try:
                media.tags = await song_iface.base.get_tags_from_asset_info(
                    webplayback["songList"][0]["assets"][0]["metadata"],
                    media.lyrics.unsynced if media.lyrics else None,
                    song_iface.use_album_date,
                )
                tags_extracted = True
            except Exception as e:
                log.debug("Failed extracting tags from webplayback: %s", e)

        if not tags_extracted:
            # Fall back to creating tags directly from catalog metadata so songList is never required
            attrs = media.media_metadata.get("attributes", {})
            rel_date = None
            if attrs.get("releaseDate"):
                try:
                    rel_date = datetime.datetime.strptime(attrs["releaseDate"], "%Y-%m-%d")
                except Exception:
                    pass
            media.tags = MediaTags(
                album=attrs.get("albumName"),
                album_artist=attrs.get("albumArtistName") or attrs.get("artistName"),
                album_id=None,
                album_sort=None,
                artist=attrs.get("artistName", "Unknown Artist"),
                artist_id=None,
                artist_sort=None,
                comment=None,
                compilation=False,
                composer=attrs.get("composerName"),
                composer_id=None,
                composer_sort=None,
                copyright=attrs.get("copyright"),
                date=rel_date,
                disc=attrs.get("discNumber", 1),
                disc_total=1,
                gapless=False,
                genre=attrs.get("genreNames", ["Unknown"])[0] if attrs.get("genreNames") else "Unknown",
                genre_id=None,
                lyrics=media.lyrics.unsynced if media.lyrics else None,
                media_type=MediaType.SONG,
                rating=MediaRating.EXPLICIT if attrs.get("contentRating") == "explicit" else MediaRating.CLEAN,
                storefront=None,
                title=attrs.get("name", "Unknown Title"),
                title_id=int(media.media_id) if str(media.media_id).isdigit() else 0,
                title_sort=None,
                track=attrs.get("trackNumber", 1),
                track_total=1,
                xid=attrs.get("isrc"),
            )

        if not song_iface.skip_stream_info:
            media.stream_info = await song_iface.get_stream_info(
                media.media_id,
                media.is_library,
                webplayback,
                playback,
            )
            if media.stream_info.audio_track.drm_free:
                pass
            elif (
                not song_iface.base.wrapper_api
                and not media.stream_info.audio_track.widevine_pssh
            ) or (
                song_iface.base.wrapper_api
                and not media.stream_info.audio_track.fairplay_key
                and not media.stream_info.audio_track.use_cenc
            ):
                raise GamdlInterfaceDecryptionNotAvailableError(media_id=media.media_id)
            elif media.stream_info.audio_track.widevine_pssh:
                media.decryption_key = DecryptionKeyAv(
                    audio_track=await song_iface.base.get_decryption_key(
                        media.stream_info.audio_track.widevine_pssh,
                        media.media_id,
                    )
                )

        media.partial = False
        yield media

    song_iface.get_media = _safe_get_media

    mv_priority = [codec_music_video]
    for c in (MusicVideoCodec.H265, MusicVideoCodec.H264):
        if c not in mv_priority:
            mv_priority.append(c)

    iface = AppleMusicInterface(
        song=song_iface,
        music_video=AppleMusicMusicVideoInterface(base=base_iface, codec_priority=mv_priority),
        uploaded_video=AppleMusicUploadedVideoInterface(base=base_iface, quality=quality_post),
    )
    log.info("AppleMusicInterface ready")

    # ── gamdl downloader ────────────────────────────────
    _ff_path = _resolve_bin("ffmpeg")
    _nm_path = _resolve_bin(Path(nm3u8dlre_path).name) if "/" not in str(nm3u8dlre_path) else nm3u8dlre_path

    base_dl = AppleMusicBaseDownloader(
        interface=iface, output_path=str(output_path), temp_path=str(temp_path),
        nm3u8dlre_path=_nm_path, ffmpeg_path=_ff_path, download_mode=download_mode,
        album_folder_template=template_folder_album,
        compilation_folder_template=template_folder_compilation,
        no_album_folder_template=template_folder_no_album,
        playlist_folder_template=template_file_playlist,
        single_disc_file_template=template_file_single_disc,
        multi_disc_file_template=template_file_multi_disc,
        no_album_file_template=template_file_no_album,
        playlist_file_template="{playlist_title}",
        date_tag_template=template_date, exclude_tags=exclude_list,
        **({"truncate": truncate} if truncate is not None else {}),
    )

    # ── override download: run everything in threads, never via asyncio
    # subprocess — Windows SelectorEventLoop (forced for httpx compat)
    # raises NotImplementedError on create_subprocess_exec.
    _use_nm3u8 = download_mode == DownloadMode.NM3U8DLRE

    def _ytdlp_download_sync(stream_url: str, dl_path: str) -> None:
        # Mirrors gamdl's _download_ytdlp_process, but in-process:
        # avoids multiprocessing (broken under PyInstaller without
        # freeze_support) and `sys.executable -m yt_dlp` (frozen exe
        # would relaunch AMDL itself).
        #
        # Delete any stale/empty file first — yt-dlp's HlsFD will
        # report "has already been downloaded" and return 0 bytes if
        # it finds an existing file at dl_path (even a 0-byte one).
        _p = Path(dl_path)
        if _p.exists():
            _p.unlink()
        from yt_dlp import YoutubeDL
        from yt_dlp.downloader.hls import HlsFD
        from yt_dlp.downloader.http import HttpFD

        with YoutubeDL(_ytdlp_options(log)) as ydl:
            if stream_url.split("?")[0].endswith(".m3u8"):
                success, _ = HlsFD(ydl, ydl.params).download(
                    dl_path, {"url": stream_url, "ext": "mp4", "protocol": "m3u8"}
                )
                if not success:
                    raise RuntimeError("yt-dlp HLS download failed")
            else:
                success, _ = HttpFD(ydl, ydl.params).download(dl_path, {"url": stream_url})
                if not success:
                    raise RuntimeError("yt-dlp HTTP download failed")

    def _nm3u8_download_sync(stream_url: str, dl_path: str) -> None:
        p = Path(dl_path)
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0  # type: ignore[attr-defined]
        result = subprocess.run(
            [
                base_dl.full_nm3u8dlre_path or _nm_path,
                stream_url,
                "--binary-merge", "--no-log", "--log-level", "off",
                "--ffmpeg-binary-path", base_dl.full_ffmpeg_path or _ff_path,
                "--save-name", p.stem,
                "--save-dir", str(p.parent),
                "--tmp-dir", str(p.parent),
            ],
            capture_output=True, text=True, creationflags=creationflags,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"N_m3u8DL-RE failed ({result.returncode}): {(result.stderr or result.stdout or '')[:200]}"
            )

    async def _download(stream_url: str, dl_path: str) -> None:
        Path(dl_path).parent.mkdir(parents=True, exist_ok=True)
        if _use_nm3u8 and stream_url.split("?")[0].endswith(".m3u8"):
            await asyncio.to_thread(_nm3u8_download_sync, stream_url, dl_path)
        else:
            await asyncio.to_thread(_ytdlp_download_sync, stream_url, dl_path)
        if not Path(dl_path).exists():
            raise RuntimeError(f"Download produced no file: {dl_path}")

    base_dl.download_stream = _download  # type: ignore[assignment]

    log.info("Creating AppleMusicDownloader...")
    dl = AppleMusicDownloader(
        song=AppleMusicSongDownloader(base=base_dl),
        music_video=AppleMusicMusicVideoDownloader(base=base_dl),
        uploaded_video=AppleMusicUploadedVideoDownloader(base=base_dl),
        overwrite=overwrite, save_cover=save_cover, save_playlist=save_playlist,
        no_synced_lyrics=no_synced_lyrics, synced_lyrics_only=synced_lyrics_only,
    )

    # gamdl moves the staged file to its final path in _final_processing().
    # Validate first so an incomplete file can never be reported as complete.
    # Keep the default implementation used by gamdl when overwrite=False, but
    # allow the retry below to replace a failed existing file.
    _original_final_processing = dl._final_processing
    _ffprobe_path = _resolve_ffprobe(base_dl.full_ffmpeg_path or _ff_path)

    async def _final_processing_impl(item) -> None:
        staged_path = Path(item.staged_path) if item.staged_path else None
        if staged_path and staged_path.exists() and item.final_path:
            expected = _expected_duration_seconds(item.media.media_metadata)
            _validate_media_duration(staged_path, expected, _ffprobe_path, log)
        await _original_final_processing(item)

    dl._final_processing = _final_processing_impl  # type: ignore[method-assign]
    log.info("AppleMusicDownloader ready, starting parse...")

    # ── parse → download ────────────────────────────────
    items: list = []
    errors = 0
    for url in urls:
        log.info('Parsing "%s"', url)
        try:
            async for item in iter_playlist_items(
                dl.get_download_item_from_url(url), url, parse_progress_callback,
            ):
                items.append(item)
        except Exception as e:
            errors += 1
            log.error('Failed to parse "%s": %s', url, e, exc_info=not no_exceptions)
        if parse_progress_callback:
            await parse_progress_callback(None)

    total = len(items) or 1
    completed = 0
    done_files: list[str] = []

    seen_media_ids: set[str] = set()
    for item in items:
        if item.media.error:
            # Deduplicate error items (gamdl can yield them multiple times)
            media_id = getattr(item.media, "media_id", None) or getattr(item, "uuid_", None)
            if media_id:
                if media_id in seen_media_ids:
                    continue
                seen_media_ids.add(media_id)

            errors += 1
            m = item.media.media_metadata
            n = m.get("attributes", {}).get("name", "?") if isinstance(m, dict) else "?"
            log.error('Skip "%s": %s', n, item.media.error)
            continue

        if item.media.partial or not item.final_path:
            continue

        title = item.media.media_metadata.get("attributes", {}).get("name", "?") if isinstance(item.media.media_metadata, dict) else "?"
        replace_invalid_existing = False
        if not overwrite and not synced_lyrics_only and Path(item.final_path).exists():
            expected = _expected_duration_seconds(item.media.media_metadata)
            try:
                _validate_media_duration(item.final_path, expected, _ffprobe_path, log)
            except RuntimeError as e:
                if Path(item.final_path).exists():
                    errors += 1
                    log.error('Existing "%s" cannot be verified; not treating it as successful: %s', title, e)
                    continue
                log.warning('Existing "%s" failed duration validation (%s); downloading again', title, e)
                replace_invalid_existing = True
            else:
                log.info('Existing "%s" passed duration validation', title)

        log.info('Downloading "%s"', title)
        max_retries = 3
        try:
            if replace_invalid_existing:
                Path(item.final_path).unlink(missing_ok=True)
            await dl.download(item)
            completed += 1
            done_files.append(str(item.final_path))
            if progress_callback:
                r = progress_callback(completed, total)
                if asyncio.iscoroutine(r):
                    await r
            continue
        except GamdlDownloaderSyncedLyricsOnlyError:
            completed += 1
            if item.synced_lyrics_path:
                done_files.append(str(item.synced_lyrics_path))
            log.info('Synced lyrics saved for "%s"', title)
            if progress_callback:
                r = progress_callback(completed, total)
                if asyncio.iscoroutine(r):
                    await r
            continue
        except GamdlDownloaderMediaFileExistsError:
            completed += 1
            log.info('Skipped "%s": exists', title)
            if progress_callback:
                r = progress_callback(completed, total)
                if asyncio.iscoroutine(r):
                    await r
            continue
        except Exception as first_error:
            log.warning('First attempt failed for "%s": %s', title, first_error)
            await asyncio.sleep(1.5)

        for attempt in range(2, max_retries + 1):
            try:
                await dl.download(item)
                completed += 1
                done_files.append(str(item.final_path))
                if progress_callback:
                    r = progress_callback(completed, total)
                    if asyncio.iscoroutine(r):
                        await r
                break
            except GamdlDownloaderSyncedLyricsOnlyError:
                completed += 1
                if item.synced_lyrics_path:
                    done_files.append(str(item.synced_lyrics_path))
                log.info('Synced lyrics saved for "%s"', title)
                if progress_callback:
                    r = progress_callback(completed, total)
                    if asyncio.iscoroutine(r):
                        await r
                break
            except GamdlDownloaderMediaFileExistsError:
                completed += 1
                log.info('Skipped "%s": exists', title)
                if progress_callback:
                    r = progress_callback(completed, total)
                    if asyncio.iscoroutine(r):
                        await r
                break
            except Exception as e:
                if attempt < max_retries:
                    log.warning('Retrying "%s" (attempt %d/%d) after error: %s', title, attempt, max_retries, e)
                    await asyncio.sleep(1.5)
                    continue
                errors += 1
                log.error('Failed "%s": %s\n%s', title, e, traceback.format_exc())

    # ── format conversion ───────────────────────────────
    if (audio_format or video_format) and done_files and not synced_lyrics_only:
        try:
            from amdl.converter import convert_file_list, resolve_ffmpeg_executable
            exe = resolve_ffmpeg_executable(ffmpeg_path)
            if exe:
                media_files = [Path(p) for p in done_files if not p.endswith((".ttml", ".lrc"))]
                if media_files:
                    log.info("Converting…")
                    convert_file_list(media_files, audio_format, video_format, exe,
                                      log_callback or (lambda m: None))
        except Exception as e:
            log.error("Conversion failed: %s", e, exc_info=not no_exceptions)

    log.info("Done (%d error(s))", errors)
    return errors
