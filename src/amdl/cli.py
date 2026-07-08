from __future__ import annotations
import sys


def main():
    """AMDL entry point.

    Usage:
        amdl --server [--host HOST] [--port PORT]   # 启动 API 服务
        amdl --desktop                                # 启动桌面应用
        amdl <gamdl args...>                          # 透传 gamdl 命令行
    """
    args = sys.argv[1:] if len(sys.argv) > 1 else []

    # ── API 服务模式 ──────────────────────────────────────────
    if args and args[0] == "--server":
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
    if args and args[0] == "--desktop":
        from amdl.server import run_desktop

        run_desktop()
        return

    # ── 默认：透传给 gamdl ────────────────────────────────────
    from gamdl.cli.cli import main as gamdl_main

    sys.argv = ["gamdl", *args]
    gamdl_main()
    