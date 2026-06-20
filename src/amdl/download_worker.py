"""Download worker — calls core_downloader directly, no Click dependency."""

import os
import platform
import shutil
import sys
import time
import traceback
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from amdl.core_downloader import download_urls as core_download_urls
from amdl.enums import (
    CoverFormat,
    DownloadMode,
    MusicVideoCodec,
    PostQuality,
    RemuxMode,
    SongCodec,
    SyncedLyricsFormat,
)
from amdl.gui_conversion import (
    convert_downloaded_files as shared_convert_downloaded_files,
    resolve_ffmpeg_executable,
)

# ── GUI-string → Enum mapping ───────────────────────────────
_SONG_CODEC_MAP = {
    "aac-legacy": SongCodec.AAC_LEGACY,
    "atmos": SongCodec.ATMOS,
}
_MV_CODEC_MAP = {
    "h264": MusicVideoCodec.H264,
    "h265": MusicVideoCodec.H265,
}
_QUALITY_MAP = {
    "best": PostQuality.BEST,
    "ask": PostQuality.ASK,
}
_DL_MODE_MAP = {
    "ytdlp": DownloadMode.YTDLP,
    "nm3u8dlre": DownloadMode.NM3U8DLRE,
}
_REMUX_MAP = {
    "ffmpeg": RemuxMode.FFMPEG,
    "mp4box": RemuxMode.MP4BOX,
}
_COVER_MAP = {
    "jpg": CoverFormat.JPG,
    "png": CoverFormat.PNG,
}
_SYNCED_LYRICS_MAP = {
    "lrc": SyncedLyricsFormat.LRC,
    "srt": SyncedLyricsFormat.SRT,
    "ttml": SyncedLyricsFormat.TTML,
}


def _safe_enum(val: str | None, mapping: dict, default):
    """Convert a GUI string to an Enum, falling back to *default*."""
    if not val:
        return default
    return mapping.get(val, default)


# ── thread ──────────────────────────────────────────────────
class DownloadThread(QThread):
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool)

    def __init__(self, urls, cookie_file, output_dir, download_options, log_callback):
        super().__init__()
        self.urls = urls
        self.cookie_file = cookie_file
        self.output_dir = output_dir
        self.download_options = download_options
        self.downloaded_files = []
        self.log_callback = log_callback
        self._stop_requested = False

        # Resolve ffmpeg path (cross-platform)
        self.ffmpeg_exe = "ffmpeg"
        meipass_dir = getattr(sys, "_MEIPASS", None)
        if getattr(sys, "frozen", False):
            self.ffmpeg_exe = os.path.join(
                meipass_dir or os.path.dirname(sys.executable),
                "tools",
                "ffmpeg",
            )

        fallback_paths = [
            shutil.which("ffmpeg"),
            shutil.which("ffmpeg.exe"),
        ]
        base_dirs = [
            getattr(sys, "_MEIPASS", None) or "",
            os.path.dirname(sys.executable)
            if getattr(sys, "frozen", False)
            else os.getcwd(),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."),
        ]
        for bd in base_dirs:
            for name in ("ffmpeg", "ffmpeg.exe"):
                p = os.path.join(bd, "tools", name)
                if os.path.exists(p):
                    fallback_paths.append(p)

        self.ffmpeg_exe = resolve_ffmpeg_executable(self.ffmpeg_exe, fallback_paths)
        if not self.ffmpeg_exe:
            self.log_callback.emit("    警告: FFmpeg不可用")

    def run(self):
        try:
            total = len(self.urls)
            self.log_callback.emit(f"开始下载 {total} 个项目...")
            self.downloaded_files = []

            if self._stop_requested:
                self.log_callback.emit("下载已被用户停止")
                self.finished_signal.emit(False)
                return

            # ── build kwargs for core_downloader ──────────────
            opts = self.download_options
            cookies_path = Path(self.cookie_file)
            output_path = Path(self.output_dir) if self.output_dir else Path.cwd()

            # Map GUI strings to proper enums
            codec_song = _safe_enum(opts.get("codec_song"), _SONG_CODEC_MAP, SongCodec.AAC_LEGACY)
            codec_mv = _safe_enum(opts.get("codec_music_video"), _MV_CODEC_MAP, MusicVideoCodec.H264)
            quality = _safe_enum(opts.get("quality_post"), _QUALITY_MAP, PostQuality.BEST)
            dl_mode = _safe_enum(opts.get("download_mode"), _DL_MODE_MAP, DownloadMode.YTDLP)
            remux = _safe_enum(opts.get("remux_mode"), _REMUX_MAP, RemuxMode.FFMPEG)
            cover_fmt = _safe_enum(opts.get("cover_format"), _COVER_MAP, CoverFormat.JPG)
            synced_fmt = _safe_enum(
                opts.get("synced_lyrics_format"), _SYNCED_LYRICS_MAP, SyncedLyricsFormat.LRC
            )

            cover_size = opts.get("cover_size", 1200)
            truncate = opts.get("truncate")
            temp_path = opts.get("temp_path") or "./temp"
            wvd_path = opts.get("wvd_path") or None

            kwargs = dict(
                urls=self.urls,
                cookies_path=cookies_path,
                output_path=output_path,
                temp_path=temp_path,
                wvd_path=Path(wvd_path) if wvd_path else None,
                codec_song=codec_song,
                codec_music_video=codec_mv,
                quality_post=quality,
                synced_lyrics_format=synced_fmt,
                download_mode=dl_mode,
                remux_mode=remux,
                cover_format=cover_fmt,
                cover_size=cover_size,
                truncate=truncate if truncate and truncate > 0 else None,
                overwrite=opts.get("overwrite", False),
                save_cover=opts.get("save_cover", False),
                save_playlist=opts.get("save_playlist", False),
                synced_lyrics_only=opts.get("synced_lyrics_only", False),
                no_synced_lyrics=opts.get("no_synced_lyrics", False),
                disable_music_video_skip=opts.get("disable_music_video_skip", False),
                read_urls_as_txt=opts.get("read_urls_as_txt", False),
                no_exceptions=opts.get("no_exceptions", True),
                log_callback=self.log_callback.emit,
                log_level="DEBUG",
                progress_callback=self._on_progress,
            )

            # template overrides (only if non-empty)
            for gui_key, core_key in [
                ("template_folder_album", "template_folder_album"),
                ("template_folder_compilation", "template_folder_compilation"),
                ("template_file_single_disc", "template_file_single_disc"),
                ("template_file_multi_disc", "template_file_multi_disc"),
            ]:
                val = opts.get(gui_key)
                if val:
                    kwargs[core_key] = val

            # ── record start time BEFORE download ──────────────
            download_start_time = time.time()

            # ── run core downloader (no Click, no terminal I/O) ──
            error_count = core_download_urls(**kwargs)

            # ── collect files for conversion ──────────────────
            # Use download_start_time so that ANY file created/modified
            # during the entire download process is captured.
            if self.output_dir:
                self._collect_new_files(download_start_time)

            # ── format conversion (post-processing) ───────────
            audio_format = opts.get("audio_format")
            video_format = opts.get("video_format")
            if (audio_format and audio_format != "keep original") or (
                video_format and video_format != "keep original"
            ):
                self.log_callback.emit("开始执行格式转换...")
                self.convert_downloaded_files(audio_format, video_format)

            self.progress_signal.emit(100)
            self.finished_signal.emit(error_count == 0)

        except MemoryError:
            self.log_callback.emit("内存不足错误: 下载过程中发生内存不足")
            self.log_callback.emit("请尝试以下解决方案:")
            self.log_callback.emit("1. 关闭其他占用内存的程序")
            self.log_callback.emit("2. 减少同时下载的项目数量")
            self.log_callback.emit("3. 使用更低的封面尺寸设置")
            self.finished_signal.emit(False)
        except TimeoutError:
            self.log_callback.emit("操作超时: 下载过程中发生超时")
            self.log_callback.emit("请检查网络连接是否正常")
            self.finished_signal.emit(False)
        except PermissionError as e:
            self.log_callback.emit(f"权限错误: 无法访问文件或目录 - {str(e)}")
            self.log_callback.emit("请确保有权限访问指定的文件和目录")
            self.finished_signal.emit(False)
        except Exception as e:
            self.log_callback.emit(f"下载过程中发生未知错误: {str(e)}\n{traceback.format_exc()}")
            try:
                uname_info = platform.uname()
            except Exception:
                uname_info = "N/A"
            self.log_callback.emit(f"Python版本: {sys.version}")
            self.log_callback.emit(f"操作系统: {os.name}")
            self.log_callback.emit(f"系统信息: {uname_info}")
            self.finished_signal.emit(False)

    def _on_progress(self, current: int, total: int):
        """Called by core_downloader for each completed track."""
        if total > 0:
            pct = int((current / total) * 100)
            self.progress_signal.emit(pct)

    def _collect_new_files(self, since: float):
        """Collect all media files created/modified since the given timestamp."""
        try:
            for ext in (".m4a", ".mp4", ".mov"):
                for media_file in Path(self.output_dir).rglob(f"*{ext}"):
                    try:
                        if media_file.stat().st_mtime >= since:
                            fp = str(media_file)
                            if fp not in self.downloaded_files:
                                self.downloaded_files.append(fp)
                                self.log_callback.emit(f"    检测到下载文件: {fp}")
                    except OSError:
                        pass
        except Exception as e:
            self.log_callback.emit(f"    检测下载文件时出错: {str(e)}")

    def convert_downloaded_files(self, audio_format, video_format):
        self.downloaded_files = shared_convert_downloaded_files(
            self.downloaded_files,
            audio_format,
            video_format,
            self.ffmpeg_exe,
            self.log_callback.emit,
        )

    def stop(self):
        """Request the download thread to stop after current track."""
        self._stop_requested = True
