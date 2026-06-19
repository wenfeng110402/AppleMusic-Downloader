from __future__ import annotations

import inspect
import json
import logging
from enum import Enum
from pathlib import Path

import click
import colorama

from . import __version__
from .apple_music_api import AppleMusicApi
from .constants import *
from .custom_formatter import CustomFormatter
from .downloader import Downloader
from .downloader_music_video import DownloaderMusicVideo
from .downloader_post import DownloaderPost
from .downloader_song import DownloaderSong
from .enums import CoverFormat, DownloadMode, MusicVideoCodec, PostQuality, RemuxMode, SongCodec, SyncedLyricsFormat
from .itunes_api import ItunesApi
apple_music_api_sig = inspect.signature(AppleMusicApi.__init__)
downloader_sig = inspect.signature(Downloader.__init__)
downloader_song_sig = inspect.signature(DownloaderSong.__init__)
downloader_music_video_sig = inspect.signature(DownloaderMusicVideo.__init__)
downloader_post_sig = inspect.signature(DownloaderPost.__init__)


def get_param_string(param: click.Parameter) -> str:
    if isinstance(param.default, Enum):
        return param.default.value
    elif isinstance(param.default, Path):
        return str(param.default)
    elif param.default is None:
        return ""
    else:
        return str(param.default)


def write_default_config_file(ctx: click.Context):
    ctx.params["config_path"].parent.mkdir(parents=True, exist_ok=True)
    config_file = {
        param.name: get_param_string(param)
        for param in ctx.command.params
        if param.name not in EXCLUDED_CONFIG_FILE_PARAMS
    }
    ctx.params["config_path"].write_text(json.dumps(config_file, indent=4))


_CONFIG_MIGRATIONS = {
    "codec_song": {"aac": "aac-legacy"},
    "codec_music_video": {},
    "quality_post": {},
}


def _migrate_config(config_file: dict) -> None:
    """Migrate deprecated config values to current enum values in-place."""
    for key, mapping in _CONFIG_MIGRATIONS.items():
        old_val = config_file.get(key)
        if old_val in mapping:
            config_file[key] = mapping[old_val]


def load_config_file(
    ctx: click.Context,
    param: click.Parameter,
    no_config_file: bool,
) -> click.Context:
    if no_config_file:
        return ctx
    legacy_config_path = Path.home() / ".gamdl" / "config.json"
    if (
        not ctx.params["config_path"].exists()
        and legacy_config_path.exists()
        and ctx.params["config_path"] != legacy_config_path
    ):
        ctx.params["config_path"].parent.mkdir(parents=True, exist_ok=True)
        ctx.params["config_path"].write_text(legacy_config_path.read_text())
    if not ctx.params["config_path"].exists():
        write_default_config_file(ctx)
    config_file = dict(json.loads(ctx.params["config_path"].read_text()))
    # Backward compatibility for renamed/deprecated config values
    _migrate_config(config_file)
    for param in ctx.command.params:
        if (
            config_file.get(param.name) is not None
            and not ctx.get_parameter_source(param.name)
            == click.core.ParameterSource.COMMANDLINE
        ):
            ctx.params[param.name] = param.type_cast_value(ctx, config_file[param.name])
    return ctx


@click.command(name="amdl")
@click.help_option("-h", "--help")
@click.version_option(__version__, "-v", "--version")
# CLI specific options
@click.argument(
    "urls",
    nargs=-1,
    type=str,
    required=True,
)
@click.option(
    "--disable-music-video-skip",
    is_flag=True,
    help="Don't skip downloading music videos in albums/playlists.",
)
@click.option(
    "--save-cover",
    "-s",
    is_flag=True,
    help="Save cover as a separate file.",
)
@click.option(
    "--overwrite",
    is_flag=True,
    help="Overwrite existing files.",
)
@click.option(
    "--read-urls-as-txt",
    "-r",
    is_flag=True,
    help="Interpret URLs as paths to text files containing URLs separated by newlines",
)
@click.option(
    "--save-playlist",
    is_flag=True,
    help="Save a M3U8 playlist file when downloading a playlist.",
)
@click.option(
    "--synced-lyrics-only",
    is_flag=True,
    help="Download only the synced lyrics.",
)
@click.option(
    "--no-synced-lyrics",
    is_flag=True,
    help="Don't download the synced lyrics.",
)
@click.option(
    "--config-path",
    type=Path,
    default=Path.home() / ".amdl" / "config.json",
    help="Path to config file.",
)
@click.option(
    "--log-level",
    type=str,
    default="INFO",
    help="Log level.",
)
@click.option(
    "--no-exceptions",
    is_flag=True,
    help="Don't print exceptions.",
)
# API specific options
@click.option(
    "--cookies-path",
    "-c",
    type=Path,
    default=apple_music_api_sig.parameters["cookies_path"].default,
    help="Path to .txt cookies file.",
)
@click.option(
    "--language",
    "-l",
    type=str,
    default=apple_music_api_sig.parameters["language"].default,
    help="Metadata language as an ISO-2A language code (don't always work for videos).",
)
# Downloader specific options
@click.option(
    "--output-path",
    "-o",
    type=Path,
    default=downloader_sig.parameters["output_path"].default,
    help="Path to output directory.",
)
@click.option(
    "--temp-path",
    type=Path,
    default=downloader_sig.parameters["temp_path"].default,
    help="Path to temporary directory.",
)
@click.option(
    "--wvd-path",
    type=Path,
    default=downloader_sig.parameters["wvd_path"].default,
    help="Path to .wvd file.",
)
@click.option(
    "--nm3u8dlre-path",
    type=str,
    default=downloader_sig.parameters["nm3u8dlre_path"].default,
    help="Path to N_m3u8DL-RE binary.",
)
@click.option(
    "--mp4decrypt-path",
    type=str,
    default=downloader_sig.parameters["mp4decrypt_path"].default,
    help="Path to mp4decrypt binary.",
)
@click.option(
    "--ffmpeg-path",
    type=str,
    default=downloader_sig.parameters["ffmpeg_path"].default,
    help="Path to FFmpeg binary.",
)
@click.option(
    "--mp4box-path",
    type=str,
    default=downloader_sig.parameters["mp4box_path"].default,
    help="Path to MP4Box binary.",
)
@click.option(
    "--download-mode",
    type=DownloadMode,
    default=downloader_sig.parameters["download_mode"].default,
    help="Download mode.",
)
@click.option(
    "--remux-mode",
    type=RemuxMode,
    default=downloader_sig.parameters["remux_mode"].default,
    help="Remux mode.",
)
@click.option(
    "--cover-format",
    type=CoverFormat,
    default=downloader_sig.parameters["cover_format"].default,
    help="Cover format.",
)
@click.option(
    "--template-folder-album",
    type=str,
    default=downloader_sig.parameters["template_folder_album"].default,
    help="Template folder for tracks that are part of an album.",
)
@click.option(
    "--template-folder-compilation",
    type=str,
    default=downloader_sig.parameters["template_folder_compilation"].default,
    help="Template folder for tracks that are part of a compilation album.",
)
@click.option(
    "--template-file-single-disc",
    type=str,
    default=downloader_sig.parameters["template_file_single_disc"].default,
    help="Template file for the tracks that are part of a single-disc album.",
)
@click.option(
    "--template-file-multi-disc",
    type=str,
    default=downloader_sig.parameters["template_file_multi_disc"].default,
    help="Template file for the tracks that are part of a multi-disc album.",
)
@click.option(
    "--template-folder-no-album",
    type=str,
    default=downloader_sig.parameters["template_folder_no_album"].default,
    help="Template folder for the tracks that are not part of an album.",
)
@click.option(
    "--template-file-no-album",
    type=str,
    default=downloader_sig.parameters["template_file_no_album"].default,
    help="Template file for the tracks that are not part of an album.",
)
@click.option(
    "--template-file-playlist",
    type=str,
    default=downloader_sig.parameters["template_file_playlist"].default,
    help="Template file for the M3U8 playlist.",
)
@click.option(
    "--template-date",
    type=str,
    default=downloader_sig.parameters["template_date"].default,
    help="Date tag template.",
)
@click.option(
    "--exclude-tags",
    type=str,
    default=downloader_sig.parameters["exclude_tags"].default,
    help="Comma-separated tags to exclude.",
)
@click.option(
    "--cover-size",
    type=int,
    default=downloader_sig.parameters["cover_size"].default,
    help="Cover size.",
)
@click.option(
    "--truncate",
    type=int,
    default=downloader_sig.parameters["truncate"].default,
    help="Maximum length of the file/folder names.",
)
# DownloaderSong specific options
@click.option(
    "--codec-song",
    type=SongCodec,
    default=downloader_song_sig.parameters["codec"].default,
    help="Song codec.",
)
@click.option(
    "--synced-lyrics-format",
    type=SyncedLyricsFormat,
    default=downloader_song_sig.parameters["synced_lyrics_format"].default,
    help="Synced lyrics format.",
)
# DownloaderMusicVideo specific options
@click.option(
    "--codec-music-video",
    type=MusicVideoCodec,
    default=downloader_music_video_sig.parameters["codec"].default,
    help="Music video codec.",
)
# DownloaderPost specific options
@click.option(
    "--quality-post",
    type=PostQuality,
    default=downloader_post_sig.parameters["quality"].default,
    help="Post video quality.",
)
# This option should always be last
@click.option(
    "--no-config-file",
    "-n",
    is_flag=True,
    callback=load_config_file,
    help="Do not use a config file.",
)
def main(
    urls: list[str],
    disable_music_video_skip: bool,
    save_cover: bool,
    overwrite: bool,
    read_urls_as_txt: bool,
    save_playlist: bool,
    synced_lyrics_only: bool,
    no_synced_lyrics: bool,
    config_path: Path,
    log_level: str,
    no_exceptions: bool,
    cookies_path: Path,
    language: str,
    output_path: Path,
    temp_path: Path,
    wvd_path: Path,
    nm3u8dlre_path: str,
    mp4decrypt_path: str,
    ffmpeg_path: str,
    mp4box_path: str,
    download_mode: DownloadMode,
    remux_mode: RemuxMode,
    cover_format: CoverFormat,
    template_folder_album: str,
    template_folder_compilation: str,
    template_file_single_disc: str,
    template_file_multi_disc: str,
    template_folder_no_album: str,
    template_file_no_album: str,
    template_file_playlist: str,
    template_date: str,
    exclude_tags: str,
    cover_size: int,
    truncate: int,
    codec_song: SongCodec,
    synced_lyrics_format: SyncedLyricsFormat,
    codec_music_video: MusicVideoCodec,
    quality_post: PostQuality,
    no_config_file: bool,
):
    colorama.just_fix_windows_console()
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(CustomFormatter())
    logger.addHandler(stream_handler)
    logger.info("Starting Amdl")

    # cookies prompt (terminal-specific, keep here)
    while not cookies_path.exists():
        cookies_path_str = click.prompt(
            X_NOT_FOUND_STRING.format("Cookies file", cookies_path.absolute())
            + ". Move it to that location or drag and drop it here. Then, press enter to continue",
            default=str(cookies_path),
            show_default=False,
        )
        cookies_path = Path(cookies_path_str.strip('"'))

    # delegate all real work to the core module
    from .core_downloader import download_urls as _core_download

    _core_download(
        urls=urls,
        cookies_path=cookies_path,
        output_path=output_path,
        temp_path=temp_path,
        wvd_path=wvd_path,
        nm3u8dlre_path=nm3u8dlre_path,
        mp4decrypt_path=mp4decrypt_path,
        ffmpeg_path=ffmpeg_path,
        mp4box_path=mp4box_path,
        download_mode=download_mode,
        remux_mode=remux_mode,
        codec_song=codec_song,
        codec_music_video=codec_music_video,
        quality_post=quality_post,
        synced_lyrics_format=synced_lyrics_format,
        cover_format=cover_format,
        cover_size=cover_size,
        truncate=truncate,
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
        log_callback=lambda msg: logger.info(msg),
        log_level=log_level,
    )
