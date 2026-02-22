import io
import os
import re
import sys
import traceback
from pathlib import Path

import amdl.cli
import platform
from PyQt6.QtCore import QThread, pyqtSignal

from amdl.gui_conversion import (
    convert_downloaded_files as shared_convert_downloaded_files,
    resolve_ffmpeg_executable,
)


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

        meipass_dir = getattr(sys, "_MEIPASS", None)
        if getattr(sys, "frozen", False):
            if meipass_dir:
                self.ffmpeg_exe = os.path.join(meipass_dir, "tools", "ffmpeg.exe")
            else:
                self.ffmpeg_exe = os.path.join(os.path.dirname(sys.executable), "tools", "ffmpeg.exe")
        else:
            self.ffmpeg_exe = "ffmpeg"

        fallback_paths = None
        if getattr(sys, "frozen", False):
            fallback_paths = [
                os.path.join(os.path.dirname(sys.executable), "tools", "ffmpeg.exe"),
                os.path.join(os.path.dirname(sys.executable), "ffmpeg.exe"),
                "ffmpeg",
                "ffmpeg.exe",
            ]
        self.ffmpeg_exe = resolve_ffmpeg_executable(self.ffmpeg_exe, fallback_paths)

        if not self.ffmpeg_exe:
            self.log_callback.emit(f"    警告: FFmpeg不可用: {self.ffmpeg_exe}")

    def run(self):
        try:
            success = True
            success_count = 0
            total = len(self.urls)

            self.log_callback.emit(f"开始下载 {total} 个项目...")
            self.downloaded_files = []

            for i, url in enumerate(self.urls, 1):
                self.log_callback.emit(f"正在处理 ({i}/{total}): {url}")

                args = [
                    "--cookies-path",
                    self.cookie_file,
                    url,
                ]

                if self.output_dir:
                    args.extend(["--output-path", self.output_dir])
                if self.download_options.get("overwrite"):
                    args.append("--overwrite")
                if self.download_options.get("disable_music_video_skip"):
                    args.append("--disable-music-video-skip")
                if self.download_options.get("save_playlist"):
                    args.append("--save-playlist")
                if self.download_options.get("synced_lyrics_only"):
                    args.append("--synced-lyrics-only")
                if self.download_options.get("no_synced_lyrics"):
                    args.append("--no-synced-lyrics")
                if self.download_options.get("read_urls_as_txt"):
                    args.append("--read-urls-as-txt")
                if self.download_options.get("no_exceptions"):
                    args.append("--no-exceptions")
                if self.download_options.get("codec_song"):
                    args.extend(["--codec-song", self.download_options.get("codec_song")])
                if self.download_options.get("codec_music_video"):
                    args.extend(["--codec-music-video", self.download_options.get("codec_music_video")])
                if self.download_options.get("quality_post"):
                    args.extend(["--quality-post", self.download_options.get("quality_post")])
                if self.download_options.get("download_mode"):
                    args.extend(["--download-mode", self.download_options.get("download_mode")])
                if self.download_options.get("remux_mode"):
                    args.extend(["--remux-mode", self.download_options.get("remux_mode")])
                if self.download_options.get("cover_format"):
                    args.extend(["--cover-format", self.download_options.get("cover_format")])
                if self.download_options.get("cover_size"):
                    args.extend(["--cover-size", str(self.download_options.get("cover_size"))])
                if self.download_options.get("truncate"):
                    args.extend(["--truncate", str(self.download_options.get("truncate"))])
                if self.download_options.get("synced_lyrics_format"):
                    args.extend(["--synced-lyrics-format", self.download_options.get("synced_lyrics_format")])

                log_stream = io.StringIO()

                try:
                    old_stdout = sys.stdout
                    old_stderr = sys.stderr
                    sys.stdout = log_stream
                    sys.stderr = log_stream

                    self.log_callback.emit(f"    传递给CLI的参数: {' '.join(args)}")
                    amdl.cli.main(args, standalone_mode=False)
                    success_count += 1
                    self.log_callback.emit("    下载完成!")
                except SystemExit as e:
                    if e.code == 0:
                        success_count += 1
                        self.log_callback.emit("    下载完成!")
                    else:
                        self.log_callback.emit(f"    下载失败! 错误代码: {e.code}")
                        success = False
                        log_output = log_stream.getvalue()
                        if log_output:
                            for line in log_output.splitlines():
                                if line.strip():
                                    self.log_callback.emit(line)
                except Exception as e:
                    self.log_callback.emit(f"    下载失败! 异常: {str(e)}")
                    success = False
                    log_output = log_stream.getvalue()
                    if log_output:
                        for line in log_output.splitlines():
                            if line.strip():
                                self.log_callback.emit(line)
                    self.log_callback.emit(f"    异常类型: {type(e).__name__}")
                    self.log_callback.emit(f"    堆栈跟踪: {traceback.format_exc()}")
                finally:
                    sys.stdout = old_stdout
                    sys.stderr = old_stderr

                    log_output = log_stream.getvalue()
                    if log_output:
                        for line in log_output.splitlines():
                            if line.strip():
                                self.log_callback.emit(line)
                                self.extract_downloaded_file_path(line)
                    else:
                        self.log_callback.emit("    没有捕获到日志输出")

                    progress = int((i / total) * 100)
                    self.progress_signal.emit(progress)

            audio_format = self.download_options.get("audio_format")
            video_format = self.download_options.get("video_format")

            self.log_callback.emit(f"准备转换 {len(self.downloaded_files)} 个下载的文件")
            for file_path in self.downloaded_files:
                self.log_callback.emit(f"  待转换文件: {file_path}")

            if (audio_format and audio_format != "保持原格式") or (video_format and video_format != "保持原格式"):
                self.log_callback.emit("开始执行格式转换...")
                self.convert_downloaded_files(audio_format, video_format)

            self.finished_signal.emit(success and success_count > 0)
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

    def extract_downloaded_file_path(self, log_line):
        patterns = [
            r"[Dd]ownload.*completed.*[:：]\s*(.+?\.(?:m4a|mp4|mov))",
            r"(?:已保存到|保存到|Saved to).*[:：]\s*(.+?\.(?:m4a|mp4|mov))",
            r"(?:已完成|完成).*[:：]\s*(.+?\.(?:m4a|mp4|mov))",
            r"([A-Za-z]:[/\\][^\s]*?\.(?:m4a|mp4|mov))(?:\s|$)",
        ]

        file_path = None
        for pat in patterns:
            m = re.search(pat, log_line)
            if not m:
                continue
            candidate = m.group(1).strip()
            if pat == patterns[-1]:
                if not ("saved" in log_line.lower() or "完成" in log_line or "success" in log_line.lower() or "Done" in log_line):
                    continue
            file_path = candidate
            break

        if file_path:
            if not os.path.isabs(file_path):
                file_path = os.path.abspath(file_path)
            if file_path not in self.downloaded_files:
                self.downloaded_files.append(file_path)
                self.log_callback.emit(f"    检测到下载文件: {file_path}")

        if "Done" in log_line and not self.downloaded_files and self.output_dir:
            try:
                media_files = []
                for ext in [".m4a", ".mp4", ".mov"]:
                    media_files.extend(Path(self.output_dir).rglob(f"*{ext}"))
                if media_files:
                    latest_file = max(media_files, key=lambda x: x.stat().st_mtime)
                    file_path = str(latest_file)
                    if file_path not in self.downloaded_files:
                        self.downloaded_files.append(file_path)
                        self.log_callback.emit(f"    检测到下载文件: {file_path}")
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
