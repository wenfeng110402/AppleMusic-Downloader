"""Core download API — thin wrapper around gamdl's embedding API.

Can be called from:
- CLI (click → core_downloader)
- GUI (QThread → core_downloader)

All Apple Music API / download / decryption / tagging is handled by gamdl.
applemusic-dl adds: logging callback, progress callback, and post-download format conversion.
"""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Callable

# ── Python version guard ────────────────────────────────
_MIN_PYTHON = (3, 10)
_pyver = sys.version_info[:2]

if _pyver < _MIN_PYTHON:
    raise RuntimeError(
        f"Python {_pyver[0]}.{_pyver[1]} is too old. "
        f"Requires Python {_MIN_PYTHON[0]}.{_MIN_PYTHON[1]}+"
    )

# ── anyio backend hint (Windows) ────────────────────────
# Ensure anyio explicitly uses the asyncio backend on Windows,
# avoiding issues with event loop detection (sniffio) when
# using a non-default event loop policy.
if sys.platform == "win32":
    import os as _os
    _os.environ.setdefault("ANYIO_BACKEND", "asyncio")

from gamdl.api import AppleMusicApi
from gamdl.downloader import (
    AppleMusicBaseDownloader,
    AppleMusicDownloader,
    AppleMusicMusicVideoDownloader,
    AppleMusicSongDownloader,
    AppleMusicUploadedVideoDownloader,
    DownloadMode,
)
from gamdl.downloader.exceptions import GamdlDownloaderMediaFileExistsError
from gamdl.interface import (
    AppleMusicBaseInterface,
    AppleMusicInterface,
    AppleMusicMusicVideoInterface,
    AppleMusicSongInterface,
    AppleMusicUploadedVideoInterface,
    CoverFormat,
    MusicVideoCodec,
    SongCodec,
    SyncedLyricsFormat,
    UploadedVideoQuality,
)

# ── type aliases ──────────────────────────────────────────────
LogCallback = Callable[[str], None]


# ── in-memory logger that pipes to a GUI/text callback ───────
class CallbackHandler(logging.Handler):
    """logging Handler that emits formatted records to a callback."""

    def __init__(self, callback: LogCallback, level: int = logging.DEBUG) -> None:
        super().__init__(level)
        self.callback = callback

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self.callback(msg)
        except Exception:
            self.handleError(record)


def _setup_logger(
    name: str,
    level: str = "INFO",
    callback: LogCallback | None = None,
) -> logging.Logger:
    """Configure a logger; routes to callback if given, else stdout."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()

    if callback:
        handler = CallbackHandler(callback)
        handler.setFormatter(logging.Formatter("%(message)s"))
    else:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(handler)
    return logger


# ── main download orchestrator ───────────────────────────────
def download_urls(
    *,
    # required
    urls: list[str],
    cookies_path: Path,
    # optional – paths
    output_path: Path = Path("./Apple Music"),
    temp_path: Path = Path("./temp"),
    wvd_path: Path | None = None,
    # optional – binaries
    nm3u8dlre_path: str = "N_m3u8DL-RE",
    ffmpeg_path: str = "ffmpeg",
    # optional – modes
    download_mode: DownloadMode = DownloadMode.YTDLP,
    # optional – codec / format
    codec_song: SongCodec = SongCodec.AAC_WEB,
    codec_music_video: MusicVideoCodec = MusicVideoCodec.H264,
    quality_post: UploadedVideoQuality = UploadedVideoQuality.BEST,
    synced_lyrics_format: SyncedLyricsFormat = SyncedLyricsFormat.LRC,
    cover_format: CoverFormat = CoverFormat.JPG,
    cover_size: int = 1200,
    truncate: int | None = None,
    # optional – conversion
    audio_format: str | None = None,
    video_format: str | None = None,
    # optional – templates
    template_folder_album: str = "{album_artist}/{album}",
    template_folder_compilation: str = "Compilations/{album}",
    template_file_single_disc: str = "{track:02d} {title}",
    template_file_multi_disc: str = "{disc}-{track:02d} {title}",
    template_folder_no_album: str = "{artist}/Unknown Album",
    template_file_no_album: str = "{title}",
    template_file_playlist: str = "Playlists/{playlist_artist}/{playlist_title}",
    template_date: str = "%Y-%m-%dT%H:%M:%SZ",
    exclude_tags: str | None = None,
    # optional – booleans
    overwrite: bool = False,
    save_cover: bool = False,
    save_playlist: bool = False,
    synced_lyrics_only: bool = False,
    no_synced_lyrics: bool = False,
    disable_music_video_skip: bool = False,
    read_urls_as_txt: bool = False,
    no_exceptions: bool = True,
    # optional – API
    language: str = "en-US",
    # optional – logging (if not provided, writes to stdout)
    log_callback: LogCallback | None = None,
    log_level: str = "INFO",
    # optional – progress tracking
    progress_callback: Callable[[int, int], None] | None = None,
) -> int:
    """Download tracks from Apple Music URLs via gamdl.

    Returns the number of errors encountered (0 = success).

    Note: mp4decrypt_path, mp4box_path, and remux_mode are no longer needed
    as gamdl handles everything internally.
    """
    if sys.platform == "win32":
        # On Windows, httpx_retries + anyio can have event loop compatibility
        # issues on certain Python versions. Try SelectorEventLoop first,
        # fall back to ProactorEventLoop if needed.
        _loop_types = [asyncio.SelectorEventLoop, asyncio.ProactorEventLoop]
        _last_exc = None
        for _loop_cls in _loop_types:
            try:
                _loop = _loop_cls()
                try:
                    return _loop.run_until_complete(_download_urls_async(
                        urls=urls,
                        cookies_path=cookies_path,
                        output_path=output_path,
                        temp_path=temp_path,
                        wvd_path=wvd_path,
                        nm3u8dlre_path=nm3u8dlre_path,
                        ffmpeg_path=ffmpeg_path,
                        download_mode=download_mode,
                        codec_song=codec_song,
                        codec_music_video=codec_music_video,
                        quality_post=quality_post,
                        synced_lyrics_format=synced_lyrics_format,
                        cover_format=cover_format,
                        cover_size=cover_size,
                        truncate=truncate,
                        audio_format=audio_format,
                        video_format=video_format,
                        template_folder_album=template_folder_album,
                        template_folder_compilation=template_folder_compilation,
                        template_file_single_disc=template_file_single_disc,
                        template_file_multi_disc=template_file_multi_disc,
                        template_folder_no_album=template_folder_no_album,
                        template_file_no_album=template_file_no_album,
                        template_file_playlist=template_file_playlist,
                        template_date=template_date,
                        exclude_tags=exclude_tags,
                        overwrite=overwrite,
                        save_cover=save_cover,
                        save_playlist=save_playlist,
                        synced_lyrics_only=synced_lyrics_only,
                        no_synced_lyrics=no_synced_lyrics,
                        disable_music_video_skip=disable_music_video_skip,
                        read_urls_as_txt=read_urls_as_txt,
                        no_exceptions=no_exceptions,
                        language=language,
                        log_callback=log_callback,
                        log_level=log_level,
                        progress_callback=progress_callback,
                    ))
                finally:
                    _loop.close()
            except TypeError as _e:
                msg = str(_e)
                if "weak reference" in msg:
                    _last_exc = _e
                    continue  # try next loop type
                raise
        # Both loop types failed — raise the last weakref error
        raise RuntimeError(
            f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} "
            f"on Windows is not fully compatible with httpx_retries.\n"
            f"Please downgrade to Python 3.10 or 3.11, "
            f"or use WSL (Windows Subsystem for Linux)."
        ) from _last_exc

    # macOS / Linux — use explicit event loop instead of asyncio.run() to avoid
    # interfering with uvicorn's running event loop when called from a thread pool.
    _loop = asyncio.new_event_loop()
    try:
        return _loop.run_until_complete(
            _download_urls_async(
                urls=urls,
                cookies_path=cookies_path,
                output_path=output_path,
                temp_path=temp_path,
                wvd_path=wvd_path,
                nm3u8dlre_path=nm3u8dlre_path,
                ffmpeg_path=ffmpeg_path,
                download_mode=download_mode,
                codec_song=codec_song,
                codec_music_video=codec_music_video,
                quality_post=quality_post,
                synced_lyrics_format=synced_lyrics_format,
                cover_format=cover_format,
                cover_size=cover_size,
                truncate=truncate,
                audio_format=audio_format,
                video_format=video_format,
                template_folder_album=template_folder_album,
                template_folder_compilation=template_folder_compilation,
                template_file_single_disc=template_file_single_disc,
                template_file_multi_disc=template_file_multi_disc,
                template_folder_no_album=template_folder_no_album,
                template_file_no_album=template_file_no_album,
                template_file_playlist=template_file_playlist,
                template_date=template_date,
                exclude_tags=exclude_tags,
                overwrite=overwrite,
                save_cover=save_cover,
                save_playlist=save_playlist,
                synced_lyrics_only=synced_lyrics_only,
                no_synced_lyrics=no_synced_lyrics,
                disable_music_video_skip=disable_music_video_skip,
                read_urls_as_txt=read_urls_as_txt,
                no_exceptions=no_exceptions,
                language=language,
                log_callback=log_callback,
                log_level=log_level,
                progress_callback=progress_callback,
            )
        )
    finally:
        _loop.close()


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
    """Async implementation of download_urls using gamdl embedding API."""
    logger = _setup_logger("amdl.core", log_level, log_callback)
    logger.info(
        f"System: Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} "
        f"| Platform: {sys.platform} "
        f"| EventLoop: {type(asyncio.get_running_loop()).__name__}"
    )

    # ── normalize & resolve path types ───────────────────
    # Resolve to absolute paths to prevent CWD-dependent failures
    # when gamdl's Rust ammuxer runs in a thread pool (asyncio.to_thread).
    temp_path = Path(temp_path).resolve()
    output_path = Path(output_path).resolve()
    cookies_path = cookies_path.resolve()
    if wvd_path is not None:
        wvd_path = wvd_path.resolve()

    # ── expand txt files ─────────────────────────────────
    if read_urls_as_txt:
        expanded: list[str] = []
        for u in urls:
            p = Path(u)
            if p.exists():
                expanded.extend(p.read_text(encoding="utf-8").splitlines())
            else:
                expanded.append(u)
        urls = expanded

    # ── parse exclude_tags ───────────────────────────────
    exclude_tags_list: list[str] = []
    if exclude_tags:
        exclude_tags_list = [t.strip().lower() for t in exclude_tags.split(",") if t.strip()]

    # ── initialise gamdl API ─────────────────────────────
    try:
        apple_music_api = await AppleMusicApi.create_from_netscape_cookies(
            cookies_path=str(cookies_path),
            language=language,
        )
    except TypeError as e:
        msg = str(e)
        if "weak reference" in msg and sys.platform == "win32":
            logger.critical(
                f"Failed to initialise AppleMusic API: {e}\n"
                f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} "
                f"on Windows needs SelectorEventLoop but ProactorEventLoop is active.\n"
                f"Restart the application — the event loop policy should be set automatically."
            )
        else:
            logger.critical(f"Failed to initialise AppleMusic API: {e}")
        return 1
    except Exception as e:
        logger.critical(f"Failed to initialise AppleMusic API: {e}")
        return 1

    if not apple_music_api.active_subscription:
        logger.critical("No active Apple Music subscription found — cannot download")
        return 1

    # ── build gamdl interface stack ──────────────────────
    base_interface = await AppleMusicBaseInterface.create(
        apple_music_api=apple_music_api,
        cover_format=cover_format,
        cover_size=cover_size,
        wvd_path=str(wvd_path) if wvd_path else None,
    )

    song_interface = AppleMusicSongInterface(
        base=base_interface,
        synced_lyrics_format=synced_lyrics_format,
        codec_priority=[codec_song],
    )
    music_video_interface = AppleMusicMusicVideoInterface(
        base=base_interface,
        codec_priority=[codec_music_video],
    )
    uploaded_video_interface = AppleMusicUploadedVideoInterface(
        base=base_interface,
        quality=quality_post,
    )

    interface = AppleMusicInterface(
        song=song_interface,
        music_video=music_video_interface,
        uploaded_video=uploaded_video_interface,
    )

    # ── build gamdl downloader stack ─────────────────────
    base_downloader = AppleMusicBaseDownloader(
        interface=interface,
        output_path=str(output_path),
        temp_path=str(temp_path),
        nm3u8dlre_path=nm3u8dlre_path,
        ffmpeg_path=ffmpeg_path,
        download_mode=download_mode,
        album_folder_template=template_folder_album,
        compilation_folder_template=template_folder_compilation,
        no_album_folder_template=template_folder_no_album,
        playlist_folder_template=template_file_playlist,
        single_disc_file_template=template_file_single_disc,
        multi_disc_file_template=template_file_multi_disc,
        no_album_file_template=template_file_no_album,
        playlist_file_template="{playlist_title}",
        date_tag_template=template_date,
        exclude_tags=exclude_tags_list,
    )

    # truncate=None = 不截断（gamdl 默认），传 0 会导致标题全空
    # 所以只在有值时传递
    _dl_kwargs: dict[str, object] = dict(
        interface=interface,
        output_path=str(output_path),
        temp_path=str(temp_path),
        nm3u8dlre_path=nm3u8dlre_path,
        ffmpeg_path=ffmpeg_path,
        download_mode=download_mode,
        album_folder_template=template_folder_album,
        compilation_folder_template=template_folder_compilation,
        no_album_folder_template=template_folder_no_album,
        playlist_folder_template=template_file_playlist,
        single_disc_file_template=template_file_single_disc,
        multi_disc_file_template=template_file_multi_disc,
        no_album_file_template=template_file_no_album,
        playlist_file_template="{playlist_title}",
        date_tag_template=template_date,
        exclude_tags=exclude_tags_list,
    )
    if truncate is not None:
        _dl_kwargs["truncate"] = truncate
    base_downloader = AppleMusicBaseDownloader(**_dl_kwargs)  # type: ignore[arg-type]

    # ── patch: replace gamdl's multiprocess-based download with direct yt-dlp ──
    # gamdl 3.8.3 uses multiprocessing.Process for yt-dlp downloads, which fails
    # silently inside PyInstaller bundles (fork issues on macOS).  We bypass it
    # with an async subprocess call so the file is guaranteed to be on disk.
    _dl_mode = download_mode
    _silent = False  # base_downloader.silent is not directly exposed

    async def _patched_download_stream(
        stream_url: str,
        download_path: str,
    ) -> None:
        Path(download_path).parent.mkdir(parents=True, exist_ok=True)
        is_m3u8 = stream_url.split("?")[0].endswith(".m3u8")
        use_nm3u8 = _dl_mode == DownloadMode.NM3U8DLRE and is_m3u8

        if use_nm3u8:
            # N_m3u8DL-RE mode — delegate to gamdl's existing subprocess impl
            await base_downloader._download_nm3u8dlre(stream_url, download_path)
        else:
            # yt-dlp via subprocess (bypasses gamdl's multiprocessing.Process)
            args = [
                "yt-dlp",
                "--quiet", "--no-warnings",
                "--allow-unplayable-formats",
                "--concurrent-fragments", "8",
                "-o", download_path,
                stream_url,
            ]
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            _, stderr = await proc.communicate()
            if proc.returncode != 0:
                err = stderr.decode(errors="replace") if stderr else "unknown error"
                raise RuntimeError(f"yt-dlp failed (exit {proc.returncode}): {err}")
            # yt-dlp may write to a temp file and rename; verify the final file
            if not Path(download_path).exists():
                raise RuntimeError(
                    f"yt-dlp did not produce {download_path} "
                    f"(exit {proc.returncode})"
                )

    base_downloader.download_stream = _patched_download_stream  # type: ignore[assignment]

    song_downloader = AppleMusicSongDownloader(base=base_downloader)
    mv_downloader = AppleMusicMusicVideoDownloader(base=base_downloader)
    uv_downloader = AppleMusicUploadedVideoDownloader(base=base_downloader)

    downloader = AppleMusicDownloader(
        song=song_downloader,
        music_video=mv_downloader,
        uploaded_video=uv_downloader,
        overwrite=overwrite,
        save_cover=save_cover,
        save_playlist=save_playlist,
        no_synced_lyrics=no_synced_lyrics,
        synced_lyrics_only=synced_lyrics_only,
    )

    # ── collect all download items first for progress ────
    all_items: list = []
    error_count = 0
    for url in urls:
        logger.info(f'Parsing "{url}"')
        try:
            async for item in downloader.get_download_item_from_url(url):
                all_items.append(item)
        except Exception as e:
            error_count += 1
            logger.error(f'Failed to parse "{url}": {e}', exc_info=not no_exceptions)
            continue

    total_tracks = len(all_items) if all_items else 1
    error_count = 0
    completed = 0
    completed_files: list[str] = []

    # ── download each item ───────────────────────────────
    for item in all_items:
        if item.media.error:
            error_count += 1
            meta = item.media.media_metadata
            name = meta.get("attributes", {}).get("name", "unknown") if isinstance(meta, dict) else "unknown"
            logger.error(f'Failed to process "{name}": {item.media.error}', exc_info=not no_exceptions)
            continue

        if item.media.partial or not item.final_path:
            continue

        meta = item.media.media_metadata
        title = meta.get("attributes", {}).get("name", "unknown") if isinstance(meta, dict) else "unknown"
        logger.info(f'Downloading "{title}"')

        try:
            await downloader.download(item)
            completed += 1
            completed_files.append(str(item.final_path))
            if progress_callback:
                progress_callback(completed, total_tracks)
        except GamdlDownloaderMediaFileExistsError:        
            completed += 1
            logger.info(f'Skipped "{title}": file already exists')
            if progress_callback:
                progress_callback(completed, total_tracks)
        except Exception as e:
            error_count += 1
            tb = traceback.format_exc()
            logger.error(f'Failed to download "{title}": {e}')
            logger.error(f'Traceback:\n{tb}')

    # ── format conversion (post-processing) ────────────
    if audio_format or video_format:
        if completed_files:
            try:
                from amdl.converter import convert_file_list, resolve_ffmpeg_executable
                exe = resolve_ffmpeg_executable(ffmpeg_path)
                if exe:
                    logger.info("Starting format conversion...")
                    convert_file_list(
                        [Path(p) for p in completed_files],
                        audio_format,
                        video_format,
                        exe,
                        logger.info if log_callback else (lambda m: None),
                    )
            except Exception as e:
                logger.error(f"Format conversion failed: {e}", exc_info=not no_exceptions)

    logger.info(f"Done ({error_count} error(s))")
    return error_count