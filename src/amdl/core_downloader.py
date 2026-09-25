"""Core download API — thin wrapper around gamdl's embedding API."""

from __future__ import annotations

import asyncio
import datetime
import logging
import os
import re
import shutil
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Callable

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

        media.cover = await song_iface.base.get_cover(media.media_metadata)
        media.lyrics = await song_iface.get_lyrics(media.media_metadata)

        playback = None
        webplayback = None
        try:
            if song_iface.base.wrapper_api:
                playback = (
                    await song_iface.base.wrapper_api.get_playback(media.media_id)
                    if not media.is_library else None
                )
                webplayback = (
                    await song_iface.base.apple_music_api.get_webplayback(media.media_id, media.is_library)
                    if media.is_library or any(codec.is_web for codec in song_iface.codec_priority) else None
                )
            else:
                webplayback = await song_iface.base.apple_music_api.get_webplayback(media.media_id, media.is_library)
        except Exception as e:
            log.debug("webplayback query failed for %s: %s", media.media_id, e)

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

        with YoutubeDL(
            {
                "quiet": True,
                "no_warnings": True,
                "overwrites": True,
                "noprogress": True,
                "allow_unplayable_formats": True,
                "concurrent_fragment_downloads": 4,
                "retries": 10,
                "fragment_retries": 10,
                "file_access_retries": 5,
                "buffersize": 1024 * 64,
                "http_chunk_size": 10485760,
            }
        ) as ydl:
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
    log.info("AppleMusicDownloader ready, starting parse...")

    # ── parse → download ────────────────────────────────
    items: list = []
    errors = 0
    for url in urls:
        log.info('Parsing "%s"', url)
        try:
            async for it in dl.get_download_item_from_url(url):
                items.append(it)
        except Exception as e:
            errors += 1
            log.error('Failed to parse "%s": %s', url, e, exc_info=not no_exceptions)

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
        log.info('Downloading "%s"', title)
        max_retries = 3
        for attempt in range(1, max_retries + 1):
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
