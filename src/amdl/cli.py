from __future__ import annotations
import asyncio
import sys

# Windows: use SelectorEventLoop to avoid "cannot create weak reference
# to NoneType" errors from httpx_retries + anyio on ProactorEventLoop.
if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

_HELP = """\
AppleMusic Downloader (amdl) v2.4.6

Usage:
  amdl --server [options]     Start API server
  amdl --desktop              Launch desktop app
  amdl <gamdl args...>        Pass through to gamdl CLI

Server options:
  --host HOST        Listen address (default: 127.0.0.1)
  --port PORT        Listen port (default: 8000)
  --log-level LEVEL  Log level: DEBUG, INFO, WARNING, ERROR (default: INFO)

Examples:
  amdl --server --host 0.0.0.0 --port 8000
  amdl --desktop
  amdl -c /path/to/cookies.txt "https://music.apple.com/..."
  amdl --help
"""


def main():
    """AMDL entry point.

    Usage:
        amdl --server [--host HOST] [--port PORT]   # 启动 API 服务
        amdl --desktop                                # 启动桌面应用
        amdl <gamdl args...>                          # 透传 gamdl 命令行
    """
    args = sys.argv[1:] if len(sys.argv) > 1 else []

    # ── 帮助信息 ──────────────────────────────────────────────
    if not args or args[0] in ("--help", "-h"):
        print(_HELP)
        return

    # ── API 服务模式 ──────────────────────────────────────────
    if args[0] == "--server":
        from amdl.server import run_server

        # 解析 --host / --port（如果有的话）
        host = "127.0.0.1"
        port = 8000
        log_level = "info"
        i = 1
        while i < len(args):
            if args[i] == "--host" and i + 1 < len(args):
                host = args[i + 1]
                i += 2
            elif args[i] == "--port" and i + 1 < len(args):
                port = int(args[i + 1])
                i += 2
            elif args[i] == "--log-level" and i + 1 < len(args):
                log_level = args[i + 1]
                i += 2
            else:
                i += 1
        run_server(host=host, port=port, log_level=log_level)
        return

    # ── 桌面模式 ──────────────────────────────────────────────
    if args[0] == "--desktop":
        from amdl.server import run_desktop

        run_desktop()
        return

    # ── 默认：透传给 gamdl ────────────────────────────────────
    from gamdl.cli.cli import main as gamdl_main

    sys.argv = ["gamdl", *args]
    gamdl_main()
    