from __future__ import annotations

import os
import shutil
import subprocess
from typing import Callable

from amdl.utils import get_subprocess_startupinfo


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
            startupinfo=get_subprocess_startupinfo(),
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
    try:
        log(f"准备转换 {len(downloaded_files)} 个下载的文件")
        converted_count = 0

        if audio_format and audio_format != "保持原格式":
            for file_path in downloaded_files:
                if not file_path.endswith((".m4a", ".mp4")):
                    continue
                converted_path = os.path.splitext(file_path)[0] + f".{audio_format}"
                if os.path.exists(converted_path):
                    log(f"    跳过 {os.path.basename(file_path)} (目标文件已存在)")
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
                    try:
                        os.remove(file_path)
                        log(f"    已删除原文件 {os.path.basename(file_path)}")
                    except Exception as error:
                        log(f"    删除原文件失败 {os.path.basename(file_path)}: {str(error)}")
                else:
                    log(f"    转换失败 {os.path.basename(file_path)}")

        if video_format and video_format != "保持原格式":
            for file_path in downloaded_files:
                if not file_path.endswith((".mov", ".mp4")):
                    continue
                converted_path = os.path.splitext(file_path)[0] + f".{video_format}"
                if os.path.exists(converted_path):
                    log(f"    跳过 {os.path.basename(file_path)} (目标文件已存在)")
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
                    try:
                        os.remove(file_path)
                        log(f"    已删除原文件 {os.path.basename(file_path)}")
                    except Exception as error:
                        log(f"    删除原文件失败 {os.path.basename(file_path)}: {str(error)}")
                else:
                    log(f"    转换失败 {os.path.basename(file_path)}")

        log(f"格式转换完成，共转换 {converted_count} 个文件")
    except Exception as error:
        log(f"格式转换过程中发生错误: {str(error)}")
    return []