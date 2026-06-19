"""Core download API — pure Python, no Click/terminal dependencies.

Can be called from:
- CLI (click → core_downloader)
- GUI (QThread → core_downloader)
"""

from __future__ import annotations

import base64
import logging
import re
import sys
import time
from pathlib import Path
from typing import Callable, Optional

from .apple_music_api import AppleMusicApi
from .constants import X_NOT_FOUND_STRING
from .downloader import Downloader
from .downloader_music_video import DownloaderMusicVideo
from .downloader_post import DownloaderPost
from .downloader_song import DownloaderSong
from .downloader_song_legacy import DownloaderSongLegacy
from .enums import (
    CoverFormat,
    DownloadMode,
    MusicVideoCodec,
    PostQuality,
    RemuxMode,
    SongCodec,
    SyncedLyricsFormat,
)
from .itunes_api import ItunesApi

# ── legacy codecs that use webplayback + ffmpeg -decryption_key ──
LEGACY_CODECS = (SongCodec.AAC_LEGACY,)

# ── type aliases ──────────────────────────────────────────────
LogCallback = Callable[[str], None]


# ── in-memory logger that pipes to a GUI/text callback ───────
class CallbackHandler(logging.Handler):
    """logging Handler that emits formatted records to a callback."""

    def __init__(self, callback: LogCallback, level=logging.DEBUG) -> None:
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
        # Use a simple formatter without ANSI codes
        handler.setFormatter(
            logging.Formatter("[%(levelname)s] %(message)s")
        )
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
    mp4decrypt_path: str = "mp4decrypt",
    ffmpeg_path: str = "ffmpeg",
    mp4box_path: str = "MP4Box",
    # optional – modes
    download_mode: DownloadMode = DownloadMode.YTDLP,
    remux_mode: RemuxMode = RemuxMode.FFMPEG,
    # optional – codec / format
    codec_song: SongCodec = SongCodec.AAC_LEGACY,
    codec_music_video: MusicVideoCodec = MusicVideoCodec.H264,
    quality_post: PostQuality = PostQuality.BEST,
    synced_lyrics_format: SyncedLyricsFormat = SyncedLyricsFormat.LRC,
    cover_format: CoverFormat = CoverFormat.JPG,
    cover_size: int = 1200,
    truncate: int | None = None,
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
    """Download tracks from Apple Music URLs.

    Returns the number of errors encountered (0 = success).
    """
    logger = _setup_logger("amdl.core", log_level, log_callback)

    # ── normalize path types (callers may pass str, e.g. from GUI) ─
    temp_path = Path(temp_path)
    output_path = Path(output_path)
    if wvd_path is not None:
        wvd_path = Path(wvd_path)

    # ── expand txt files ─────────────────────────────────────
    if read_urls_as_txt:
        expanded: list[str] = []
        for u in urls:
            p = Path(u)
            if p.exists():
                expanded.extend(p.read_text(encoding="utf-8").splitlines())
            else:
                expanded.append(u)
        urls = expanded

    # ── initialise API objects ───────────────────────────────
    apple_music_api = AppleMusicApi(cookies_path, language=language)
    itunes_api = ItunesApi(apple_music_api.storefront, apple_music_api.language)

    downloader = Downloader(
        apple_music_api,
        itunes_api,
        output_path=output_path,
        temp_path=temp_path,
        wvd_path=wvd_path,
        nm3u8dlre_path=nm3u8dlre_path,
        mp4decrypt_path=mp4decrypt_path,
        ffmpeg_path=ffmpeg_path,
        mp4box_path=mp4box_path,
        download_mode=download_mode,
        remux_mode=remux_mode,
        cover_format=cover_format,
        template_folder_album=template_folder_album,
        template_folder_compilation=template_folder_compilation,
        template_file_single_disc=template_file_single_disc,
        template_file_multi_disc=template_file_multi_disc,
        template_folder_no_album=template_folder_no_album,
        template_file_no_album=template_file_no_album,
        template_file_playlist=template_file_playlist,
        template_date=template_date,
        exclude_tags=exclude_tags,
        cover_size=cover_size,
        truncate=truncate,
    )

    downloader_song = DownloaderSong(downloader, codec_song, synced_lyrics_format)
    downloader_song_legacy = DownloaderSongLegacy(downloader, codec_song)
    downloader_music_video = DownloaderMusicVideo(downloader, codec_music_video)
    downloader_post = DownloaderPost(downloader, quality_post)

    # ── tool validation ──────────────────────────────────────
    skip_mv = False
    if not synced_lyrics_only:
        if wvd_path is not None and not Path(wvd_path).exists():
            logger.critical(X_NOT_FOUND_STRING.format(".wvd file", wvd_path))
            return 1
        logger.debug("Setting up CDM")
        downloader.set_cdm()

        if not downloader.ffmpeg_path_full and (
            remux_mode == RemuxMode.FFMPEG or download_mode == DownloadMode.NM3U8DLRE
        ):
            logger.critical(X_NOT_FOUND_STRING.format("ffmpeg", ffmpeg_path))
            return 1
        if not downloader.mp4box_path_full and remux_mode == RemuxMode.MP4BOX:
            logger.critical(X_NOT_FOUND_STRING.format("MP4Box", mp4box_path))
            return 1
        if not downloader.mp4decrypt_path_full:
            logger.critical(X_NOT_FOUND_STRING.format("mp4decrypt", mp4decrypt_path))
            return 1
        if download_mode == DownloadMode.NM3U8DLRE and not downloader.nm3u8dlre_path_full:
            logger.critical(X_NOT_FOUND_STRING.format("N_m3u8DL-RE", nm3u8dlre_path))
            return 1
        if not downloader.mp4decrypt_path_full:
            logger.warning(
                X_NOT_FOUND_STRING.format("mp4decrypt", mp4decrypt_path)
                + ", music videos will not be downloaded"
            )
            skip_mv = True
        else:
            skip_mv = False

    # ── main URL loop ────────────────────────────────────────
    error_count = 0
    total_urls = len(urls)

    for url_index, url in enumerate(urls, start=1):
        logger.info(f'Checking "{url}"')
        try:
            url_info = downloader.get_url_info(url)
            download_queue = downloader.get_download_queue(url_info)
            tracks_meta = download_queue.tracks_metadata
        except Exception as e:
            error_count += 1
            logger.error(f'Failed to check "{url}": {e}', exc_info=not no_exceptions)
            continue

        total_tracks = len(tracks_meta)
        for track_index, track_metadata in enumerate(tracks_meta, start=1):
            try:
                remuxed_path = None
                playlist_track = (
                    track_index if download_queue.playlist_attributes else None
                )
                title = track_metadata["attributes"].get("name", "unknown")
                logger.info(f'Downloading "{title}"')

                if not track_metadata["attributes"].get("playParams"):
                    logger.warning("Track is not streamable, skipping")
                    continue

                ttype = track_metadata["type"]

                # skip conditions
                if synced_lyrics_only and ttype != "songs":
                    logger.warning("Track is not downloadable (synced-lyrics-only mode), skipping")
                    continue
                if ttype == "music-videos" and skip_mv:
                    logger.warning("Music video skipped (mp4decrypt missing)")
                    continue
                if ttype == "music-videos" and url_info.type == "album" and not disable_music_video_skip:
                    logger.warning("Music video in album skipped (use --disable-music-video-skip)")
                    continue

                # ── SONGS ──────────────────────────────────
                if ttype == "songs":
                    lyrics = downloader_song.get_lyrics(track_metadata)
                    webplayback = apple_music_api.get_webplayback(track_metadata["id"])
                    tags = downloader_song.get_tags(webplayback, lyrics.unsynced)
                    if playlist_track:
                        tags = {
                            **tags,
                            **downloader.get_playlist_tags(
                                download_queue.playlist_attributes, playlist_track
                            ),
                        }
                    final_path = downloader.get_final_path(tags, ".m4a")
                    lyrics_synced_path = downloader_song.get_lyrics_synced_path(final_path)
                    cover_url = downloader.get_cover_url(track_metadata)
                    cover_ext = downloader.get_cover_file_extension(cover_url)
                    cover_path = (
                        downloader_song.get_cover_path(final_path, cover_ext)
                        if cover_ext
                        else None
                    )

                    if synced_lyrics_only:
                        pass
                    elif final_path.exists() and not overwrite:
                        logger.warning(f'Song already exists at "{final_path}", skipping')
                    elif codec_song in LEGACY_CODECS:
                        # ── LEGACY PATH (v2.4.2 compat) ──────────────
                        # Uses webplayback-only stream selection and
                        # ffmpeg -decryption_key for single-step decrypt+remux.
                        # This avoids mp4decrypt + -c copy issues with
                        # fragmented MP4 streams.
                        stream_info = downloader_song_legacy.get_stream_info(webplayback)
                        if not stream_info.stream_url or not stream_info.widevine_pssh:
                            logger.warning(
                                "Song is not downloadable or not available in the chosen codec, skipping"
                            )
                            continue

                        decryption_key = downloader_song_legacy.get_decryption_key(
                            stream_info.widevine_pssh, track_metadata["id"]
                        )
                        enc_path = downloader_song.get_encrypted_path(track_metadata["id"])
                        dec_path = downloader_song.get_decrypted_path(track_metadata["id"])
                        remuxed_path = downloader_song.get_remuxed_path(track_metadata["id"])

                        logger.debug(f'Downloading to "{enc_path}"')
                        downloader.download(enc_path, stream_info.stream_url)
                        logger.debug(f'Remuxing to "{remuxed_path}"')
                        downloader_song_legacy.remux(
                            enc_path, dec_path, remuxed_path, decryption_key,
                        )
                    else:
                        stream_info = downloader_song.get_stream_info(track_metadata, webplayback)
                        if not stream_info.stream_url or not stream_info.widevine_pssh:
                            logger.warning(
                                "Song is not downloadable or not available in the chosen codec, skipping"
                            )
                            continue

                        # DRM-protected: download → decrypt → remux
                        decryption_key = downloader.get_decryption_key(
                            stream_info.widevine_pssh, track_metadata["id"]
                        )
                        enc_path = downloader_song.get_encrypted_path(track_metadata["id"])
                        dec_path = downloader_song.get_decrypted_path(track_metadata["id"])
                        remuxed_path = downloader_song.get_remuxed_path(track_metadata["id"])

                        logger.debug(f'Downloading to "{enc_path}"')
                        downloader.download(enc_path, stream_info.stream_url)
                        logger.debug(f'Decrypting to "{dec_path}"')

                        # CENC streams (data: URI) use the raw KID as-is
                        cenc_kid = None
                        if stream_info.widevine_pssh.startswith("data:"):
                            raw = base64.b64decode(stream_info.widevine_pssh.split(",")[-1])
                            cenc_kid = raw.hex()

                        downloader_song.decrypt(
                            enc_path, dec_path, decryption_key,
                            cenc_kid=cenc_kid,
                        )
                        logger.debug(f'Remuxing to "{remuxed_path}"')
                        downloader_song.remux(dec_path, remuxed_path, stream_info.codec)

                    # synced lyrics
                    if no_synced_lyrics or not lyrics.synced:
                        pass
                    elif lyrics_synced_path.exists() and not overwrite:
                        logger.debug(f'Synced lyrics already exists at "{lyrics_synced_path}", skipping')
                    else:
                        logger.debug(f'Saving synced lyrics to "{lyrics_synced_path}"')
                        downloader_song.save_lyrics_synced(lyrics_synced_path, lyrics.synced)

                # ── MUSIC VIDEOS ───────────────────────────
                elif ttype == "music-videos":
                    mv_id_alt = downloader_music_video.get_music_video_id_alt(track_metadata)
                    itunes_page = itunes_api.get_itunes_page("music-video", mv_id_alt)

                    if mv_id_alt == track_metadata["id"]:
                        stream_url = downloader_music_video.get_stream_url_from_itunes_page(itunes_page)
                    else:
                        webplayback = apple_music_api.get_webplayback(track_metadata["id"])
                        stream_url = downloader_music_video.get_stream_url_from_webplayback(webplayback)

                    m3u8_data = downloader_music_video.get_m3u8_master_data(stream_url)
                    tags = downloader_music_video.get_tags(mv_id_alt, itunes_page, track_metadata)
                    if playlist_track:
                        tags = {
                            **tags,
                            **downloader.get_playlist_tags(
                                download_queue.playlist_attributes, playlist_track
                            ),
                        }
                    final_path = downloader.get_final_path(tags, ".m4v")
                    cover_url = downloader.get_cover_url(track_metadata)
                    cover_ext = downloader.get_cover_file_extension(cover_url)
                    cover_path = (
                        downloader_music_video.get_cover_path(final_path, cover_ext)
                        if cover_ext
                        else None
                    )

                    if final_path.exists() and not overwrite:
                        logger.warning(f'Music video already exists at "{final_path}", skipping')
                    else:
                        si_video, si_audio = (
                            downloader_music_video.get_stream_info_video(m3u8_data),
                            downloader_music_video.get_stream_info_audio(m3u8_data),
                        )
                        key_video = downloader.get_decryption_key(si_video.widevine_pssh, track_metadata["id"])
                        key_audio = downloader.get_decryption_key(si_audio.widevine_pssh, track_metadata["id"])

                        enc_v = downloader_music_video.get_encrypted_path_video(track_metadata["id"])
                        enc_a = downloader_music_video.get_encrypted_path_audio(track_metadata["id"])
                        dec_v = downloader_music_video.get_decrypted_path_video(track_metadata["id"])
                        dec_a = downloader_music_video.get_decrypted_path_audio(track_metadata["id"])
                        remuxed_path = downloader_music_video.get_remuxed_path(track_metadata["id"])

                        logger.debug(f'Downloading video to "{enc_v}"')
                        downloader.download(enc_v, si_video.stream_url)
                        logger.debug(f'Downloading audio to "{enc_a}"')
                        downloader.download(enc_a, si_audio.stream_url)
                        logger.debug(f'Decrypting video to "{dec_v}"')
                        downloader_music_video.decrypt(enc_v, key_video, dec_v)
                        logger.debug(f'Decrypting audio to "{dec_a}"')
                        downloader_music_video.decrypt(enc_a, key_audio, dec_a)
                        logger.debug(f'Remuxing to "{remuxed_path}"')
                        downloader_music_video.remux(
                            dec_v, dec_a, remuxed_path, si_video.codec, si_audio.codec
                        )

                # ── POST VIDEOS ────────────────────────────
                elif ttype == "uploaded-videos":
                    stream_url = downloader_post.get_stream_url(track_metadata)
                    tags = downloader_post.get_tags(track_metadata)
                    final_path = downloader.get_final_path(tags, ".m4v")
                    cover_url = downloader.get_cover_url(track_metadata)
                    cover_ext = downloader.get_cover_file_extension(cover_url)
                    cover_path = (
                        downloader_music_video.get_cover_path(final_path, cover_ext)
                        if cover_ext
                        else None
                    )

                    if final_path.exists() and not overwrite:
                        logger.warning(f'Post video already exists at "{final_path}", skipping')
                    else:
                        remuxed_path = downloader_post.get_post_temp_path(track_metadata["id"])
                        logger.debug(f'Downloading to "{remuxed_path}"')
                        downloader.download_ytdlp(remuxed_path, stream_url)

                # ── cover + tags (common to all types) ──────
                if synced_lyrics_only or not save_cover or cover_path is None:
                    pass
                elif cover_path.exists() and not overwrite:
                    logger.debug(f'Cover already exists at "{cover_path}", skipping')
                else:
                    logger.debug(f'Saving cover to "{cover_path}"')
                    downloader.save_cover(cover_path, cover_url)

                if remuxed_path:
                    logger.debug("Applying tags")
                    downloader.apply_tags(remuxed_path, tags, cover_url)
                    logger.debug(f'Moving to "{final_path}"')
                    downloader.move_to_output_path(remuxed_path, final_path)

                if (
                    not synced_lyrics_only
                    and save_playlist
                    and download_queue.playlist_attributes
                ):
                    pl_path = downloader.get_playlist_file_path(tags)
                    logger.debug(f'Updating M3U8 playlist from "{pl_path}"')
                    downloader.update_playlist_file(pl_path, final_path, playlist_track)

            except Exception as e:
                error_count += 1
                logger.error(
                    f'Failed to download "{title}": {e}',
                    exc_info=not no_exceptions,
                )
            finally:
                if temp_path.exists():
                    logger.debug(f'Cleaning up "{temp_path}"')
                    downloader.cleanup_temp_path()

            # progress callback
            if progress_callback:
                progress_callback(track_index, total_tracks)

    logger.info(f"Done ({error_count} error(s))")
    return error_count
