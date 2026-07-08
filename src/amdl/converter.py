from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable


def _get_startupinfo():
    """Windows 下隐藏命令行窗口，其他系统返回 None"""
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        return startupinfo
    return None


LogFunc = Callable[[str], None]


def resolve_ffmpeg_executable(
    preferred: str | None = None,
    fallback_paths: list[str] | None = None,
) -> str | None:
    candidates: list[str] = []
    if preferred:
        candidates.append(preferred)
    else:
        candidates.append("ffmpeg")
    if fallback_paths:
        candidates.extend(fallback_paths)

    for candidate in candidates:
        if not candidate:
            continue
        if os.path.isabs(candidate):
            if os.path.exists(candidate):
                return candidate
            continue
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
        if os.path.exists(candidate):
            return candidate
    return None


def _run_subprocess(cmd: list[str]) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            startupinfo=_get_startupinfo(),
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as error:
        return 1, "", str(error)


def convert_audio_file(
    source_path: str,
    target_path: str,
    target_format: str,
    ffmpeg_exe: str | None,
    log: LogFunc,
) -> bool:
    if not os.path.exists(source_path):
        log(f"    错误: 源文件不存在: {source_path}")
        return False
    if not ffmpeg_exe:
        log("    错误: FFmpeg不可用")
        return False

    target_format = target_format.lower()
    if target_format == "mp3":
        cmd = [
            ffmpeg_exe,
            "-y",
            "-i",
            source_path,
            "-c:a",
            "libmp3lame",
            "-b:a",
            "320k",
            "-c:v",
            "copy",
            "-map",
            "0:0",
            "-map",
            "0:1?",
            "-id3v2_version",
            "3",
            "-write_id3v1",
            "1",
            target_path,
        ]
    elif target_format == "flac":
        cmd = [
            ffmpeg_exe,
            "-y",
            "-i",
            source_path,
            "-c:a",
            "flac",
            "-compression_level",
            "8",
            "-c:v",
            "copy",
            "-map",
            "0:0",
            "-map",
            "0:1?",
            target_path,
        ]
    elif target_format == "wav":
        cmd = [
            ffmpeg_exe,
            "-y",
            "-i",
            source_path,
            "-c:a",
            "pcm_s16le",
            "-c:v",
            "copy",
            "-map",
            "0:0",
            "-map",
            "0:1?",
            target_path,
        ]
    elif target_format in ("aac", "m4a"):
        cmd = [
            ffmpeg_exe,
            "-y",
            "-i",
            source_path,
            "-c:a",
            "aac",
            "-b:a",
            "256k",
            "-c:v",
            "copy",
            "-map",
            "0:0",
            "-map",
            "0:1?",
            target_path,
        ]
    elif target_format == "ogg":
        cmd = [
            ffmpeg_exe,
            "-y",
            "-i",
            source_path,
            "-c:a",
            "libvorbis",
            "-q:a",
            "5",
            "-c:v",
            "copy",
            "-map",
            "0:0",
            "-map",
            "0:1?",
            target_path,
        ]
    elif target_format == "wma":
        cmd = [
            ffmpeg_exe,
            "-y",
            "-i",
            source_path,
            "-c:a",
            "wmav2",
            "-b:a",
            "192k",
            "-c:v",
            "copy",
            "-map",
            "0:0",
            "-map",
            "0:1?",
            target_path,
        ]
    else:
        cmd = [
            ffmpeg_exe,
            "-y",
            "-i",
            source_path,
            "-c:a",
            "aac",
            "-b:a",
            "256k",
            "-c:v",
            "copy",
            "-map",
            "0:0",
            "-map",
            "0:1?",
            target_path,
        ]

    log(f"    执行转换命令: {' '.join(cmd)}")
    code, stdout, stderr = _run_subprocess(cmd)
    if code == 0:
        if stdout:
            log(f"    FFmpeg输出: {stdout}")
        return True
    log(f"    FFmpeg错误: {stderr}")
    return False


def convert_video_file(
    source_path: str,
    target_path: str,
    target_format: str,
    ffmpeg_exe: str | None,
    log: LogFunc,
) -> bool:
    if not os.path.exists(source_path):
        log(f"    错误: 源文件不存在: {source_path}")
        return False
    if not ffmpeg_exe:
        log("    错误: FFmpeg不可用")
        return False

    target_format = target_format.lower()
    if target_format in ["mp4", "mov", "mkv"]:
        cmd = [ffmpeg_exe, "-y", "-i", source_path, "-c", "copy", target_path]
    elif target_format == "avi":
        cmd = [
            ffmpeg_exe,
            "-y",
            "-i",
            source_path,
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            target_path,
        ]
    elif target_format == "wmv":
        cmd = [
            ffmpeg_exe,
            "-y",
            "-i",
            source_path,
            "-c:v",
            "wmv2",
            "-c:a",
            "wmav2",
            target_path,
        ]
    elif target_format == "flv":
        cmd = [
            ffmpeg_exe,
            "-y",
            "-i",
            source_path,
            "-c:v",
            "flv",
            "-c:a",
            "aac",
            target_path,
        ]
    elif target_format == "webm":
        cmd = [
            ffmpeg_exe,
            "-y",
            "-i",
            source_path,
            "-c:v",
            "libvpx-vp9",
            "-c:a",
            "libopus",
            target_path,
        ]
    else:
        cmd = [ffmpeg_exe, "-y", "-i", source_path, "-c", "copy", target_path]

    log(f"    执行转换命令: {' '.join(cmd)}")
    code, stdout, stderr = _run_subprocess(cmd)
    if code == 0:
        if stdout:
            log(f"    FFmpeg输出: {stdout}")
        return True
    log(f"    FFmpeg错误: {stderr}")
    return False


def convert_downloaded_files(
    downloaded_files: list[str],
    audio_format: str,
    video_format: str,
    ffmpeg_exe: str | None,
    log: LogFunc,
) -> list[str]:
    result_files: list[str] = []
    try:
        log(f"准备转换 {len(downloaded_files)} 个下载的文件")
        converted_count = 0

        if audio_format and audio_format != "keep original":
            for file_path in downloaded_files:
                if not file_path.endswith((".m4a", ".mp4")):
                    result_files.append(file_path)
                    continue
                converted_path = os.path.splitext(file_path)[0] + f".{audio_format}"
                if os.path.exists(converted_path):
                    log(f"    跳过 {os.path.basename(file_path)} (目标文件已存在)")
                    result_files.append(converted_path)
                    continue
                if convert_audio_file(
                    file_path,
                    converted_path,
                    audio_format,
                    ffmpeg_exe,
                    log,
                ):
                    converted_count += 1
                    log(f"    成功转换 {os.path.basename(file_path)} 为 {audio_format}")
                    result_files.append(converted_path)
                    try:
                        os.remove(file_path)
                        log(f"    已删除原文件 {os.path.basename(file_path)}")
                    except Exception as error:
                        log(f"    删除原文件失败 {os.path.basename(file_path)}: {str(error)}")
                else:
                    log(f"    转换失败 {os.path.basename(file_path)}")
                    result_files.append(file_path)

        if video_format and video_format != "keep original":
            for file_path in list(result_files):
                if not file_path.endswith((".mov", ".mp4")):
                    continue
                converted_path = os.path.splitext(file_path)[0] + f".{video_format}"
                if os.path.exists(converted_path):
                    log(f"    跳过 {os.path.basename(file_path)} (目标文件已存在)")
                    result_files.append(converted_path)
                    continue
                if convert_video_file(
                    file_path,
                    converted_path,
                    video_format,
                    ffmpeg_exe,
                    log,
                ):
                    converted_count += 1
                    log(f"    成功转换 {os.path.basename(file_path)} 为 {video_format}")
                    result_files.append(converted_path)
                    try:
                        os.remove(file_path)
                        log(f"    已删除原文件 {os.path.basename(file_path)}")
                    except Exception as error:
                        log(f"    删除原文件失败 {os.path.basename(file_path)}: {str(error)}")
                else:
                    log(f"    转换失败 {os.path.basename(file_path)}")
                    result_files.append(file_path)
        log(f"格式转换完成，共转换 {converted_count} 个文件")
    except Exception as error:
        log(f"格式转换过程中发生错误: {str(error)}")
    return result_files


def convert_directory(
    output_dir: str,
    audio_format: str | None,
    video_format: str | None,
    ffmpeg_exe: str | None,
    log: LogFunc,
) -> list[str]:
    """扫描目录下所有 .m4a/.m4v/.mp4/.mov 文件，批量转换格式。

    Args:
        output_dir: 输出目录路径。
        audio_format: 目标音频格式（如 "mp3", "flac"），None=不转。
        video_format: 目标视频格式（如 "mp4", "mkv"），None=不转。
        ffmpeg_exe: FFmpeg 可执行文件路径。
        log: 日志回调。

    Returns:
        转换后的文件路径列表。
    """
    if not ffmpeg_exe:
        log("    错误: FFmpeg 不可用，无法转换格式")
        return []

    files = []
    audio_exts = (".m4a", ".mp4")
    video_exts = (".mp4", ".mov", ".m4v")

    for ext in set(audio_exts + video_exts):
        for fpath in Path(output_dir).rglob(f"*{ext}"):
            fp = str(fpath)
            if fp not in files:
                files.append(fp)

    if not files:
        log("    未找到需要转换的文件")
        return []

    return convert_downloaded_files(files, audio_format or "keep original", video_format or "keep original", ffmpeg_exe, log)


def convert_file_list(
    files: list[Path],
    audio_format: str | None,
    video_format: str | None,
    ffmpeg_exe: str,
    log: LogFunc,
) -> list[str]:
    """Convert only files from current download task, not the whole directory."""
    if not ffmpeg_exe:
        log("    Error: FFmpeg not available, conversion skipped")
        return []

    if not files:
        return []

    converted: list[str] = []
    audio_exts = (".m4a", ".mp4")
    video_exts = (".mp4", ".mov", ".m4v")

    for path in files:
        if not path.exists():
            continue
        ext = path.suffix.lower()
        if audio_format and ext in audio_exts:
            log(f"    Converting {path.name} to {audio_format}...")
            target = str(path.with_suffix(f".{audio_format}"))
            ok = convert_audio_file(str(path), target, audio_format, ffmpeg_exe, log)
            if ok:
                converted.append(target)
                log(f"    Done: {target}")
        elif video_format and ext in video_exts:
            log(f"    Converting {path.name} to {video_format}...")
            target = str(path.with_suffix(f".{video_format}"))
            ok = convert_video_file(str(path), target, video_format, ffmpeg_exe, log)
            if ok:
                converted.append(target)
                log(f"    Done: {target}")

    if converted:
        log(f"Conversion complete: {len(converted)} file(s) converted")
    else:
        log("No files were converted")
    return converted