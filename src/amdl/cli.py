"""AMDL command-line interface."""

from __future__ import annotations

import sys

import click

from amdl import __version__


@click.group(invoke_without_command=True)
@click.version_option(__version__, prog_name="amdl")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """AppleMusic Downloader (amdl) — download songs, MVs, lyrics and more."""
    if ctx.invoked_subcommand is None and not ctx.args:
        click.echo(_HELP)


@cli.command("server")
@click.option("--host", default="127.0.0.1", show_default=True, help="Listen address.")
@click.option("--port", default=8000, show_default=True, type=int, help="Listen port.")
@click.option(
    "--log-level",
    default="info",
    show_default=True,
    type=click.Choice(["debug", "info", "warning", "error"], case_sensitive=False),
    help="Log level.",
)
def server_cmd(host: str, port: int, log_level: str) -> None:
    """Start the API server."""
    from amdl.server import run_server
    run_server(host=host, port=port, log_level=log_level)


@cli.command("desktop")
def desktop_cmd() -> None:
    """Launch the desktop app."""
    from amdl.server import run_desktop
    run_desktop()


def main() -> None:
    """AMDL entry point.

    Routes to:
      - ``amdl server`` / ``amdl --server`` → API server
      - ``amdl desktop`` / ``amdl --desktop`` → desktop GUI
      - ``amdl --gamdl-help`` → gamdl CLI full help
      - anything else (flags, URLs, options) → passthrough to gamdl CLI
    """
    args = sys.argv[1:]

    # ── backward-compat: --server / --desktop flags ──────────
    if args and args[0] == "--server":
        from amdl.server import run_server
        host, port, log_level = "127.0.0.1", 8000, "info"
        i = 1
        while i < len(args):
            if args[i] == "--host" and i + 1 < len(args):
                host = args[i + 1]; i += 2
            elif args[i] == "--port" and i + 1 < len(args):
                port = int(args[i + 1]); i += 2
            elif args[i] == "--log-level" and i + 1 < len(args):
                log_level = args[i + 1]; i += 2
            else:
                i += 1
        run_server(host=host, port=port, log_level=log_level)
        return

    if args and args[0] == "--desktop":
        from amdl.server import run_desktop
        run_desktop()
        return

    # ── sub-command style ──────────────────────────────────
    if args and args[0] in ("server", "desktop"):
        cli(args=args, standalone_mode=False)
        return

    # ── help / version / no args ─────────────────────────────
    if not args or args[0] in ("--help", "-h"):
        click.echo(_HELP)
        return

    if args and args[0] == "--version":
        cli(args=args, standalone_mode=False)
        return

    if args and args[0] == "-V":
        click.echo(f"amdl {__version__}")
        return

    if args and args[0] == "--gamdl-help":
        _passthrough_to_gamdl(["--help"])
        return

    # ── anything else (flags like -c, URLs, etc.) → passthrough to gamdl ──
    _passthrough_to_gamdl(args)


def _passthrough_to_gamdl(args: list[str]) -> None:
    """Forward arguments to gamdl CLI."""
    from gamdl.cli import cli as gamdl_cli

    original_downloader = gamdl_cli.AppleMusicDownloader
    original_argv = sys.argv

    class PlaylistProgressDownloader(original_downloader):
        async def get_download_item_from_url(self, url: str):
            from amdl.core_downloader import PlaylistParseProgress, iter_playlist_items

            log = gamdl_cli.logger.bind(action="Parsing")
            last_completed = 0

            async def report(progress: PlaylistParseProgress | None) -> None:
                nonlocal last_completed
                if progress is None:
                    return
                completed, total = progress["completed"], progress["total"]
                title = progress["current_title"]
                total_label = total if total is not None else "?"
                if completed > last_completed:
                    log.info(f'Parsed {completed}/{total_label}: "{title}"')
                elif title:
                    log.info(f'Resolving track {completed + 1}/{total_label}: "{title}"')
                elif total is None:
                    log.info("Fetching playlist information…")
                elif completed == 0:
                    log.info(f"Found {total} playlist tracks")
                last_completed = completed

            items = super().get_download_item_from_url(url)
            async for item in iter_playlist_items(items, url, report):
                yield item

    try:
        gamdl_cli.AppleMusicDownloader = PlaylistProgressDownloader
        sys.argv = ["gamdl", *args]
        gamdl_cli.main()
    finally:
        gamdl_cli.AppleMusicDownloader = original_downloader
        sys.argv = original_argv


_HELP = f"""\
AppleMusic Downloader (amdl) v{__version__}

Usage:
  amdl <urls...> [options]                   Download songs, albums, playlists, MVs
  amdl server [--host HOST] [--port PORT]    Start API server
  amdl desktop                               Launch desktop GUI application

Core Download Options:
  -c, --cookies-path PATH          Path to cookies.txt file (required)
  -o, --output-path PATH           Output directory (default: ./Apple Music)
  --codec-song CODEC               Song codec: aac-web, atmos, etc.
  --synced-lyrics-format FORMAT    Lyrics format: lrc, srt, ttml (default: lrc)
  --synced-lyrics-only             Only download synced lyrics without media
  --no-synced-lyrics               Skip downloading synced lyrics
  --save-cover                     Save cover art image to disk
  --cover-format FORMAT            Cover format: jpg, png, raw (default: jpg)
  --download-mode MODE             Download engine: ytdlp, nm3u8dlre
  -w, --overwrite                  Overwrite existing local files

Server Options:
  --host HOST                      Listen address (default: 127.0.0.1)
  --port PORT                      Listen port (default: 8000)
  --log-level LEVEL                Log level: debug, info, warning, error (default: info)

Examples:
  amdl -c cookies.txt "https://music.apple.com/us/album/..."
  amdl -c cookies.txt --synced-lyrics-format ttml "https://music.apple.com/..."
  amdl -c cookies.txt --synced-lyrics-only "https://music.apple.com/..."
  amdl server --host 0.0.0.0 --port 8000
  amdl desktop
  amdl --gamdl-help                Show full gamdl CLI options
"""