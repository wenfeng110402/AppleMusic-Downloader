"""python -m amdl → 启动服务或桌面应用"""
import asyncio
import sys

# Windows: use SelectorEventLoop to avoid "cannot create weak reference
# to NoneType" errors from httpx_retries + anyio on ProactorEventLoop.
if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

try:
    if "--server" in sys.argv:
        from amdl.server import run_server
        run_server()
    elif "--desktop" in sys.argv:
        from amdl.server import run_desktop
        run_desktop()
    else:
        from amdl.server import run_server
        run_server()
except RuntimeError as e:
    msg = str(e)
    print(f"FATAL: {msg}", file=sys.stderr)
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Python 版本不兼容",
            f"{msg}"
        )
        root.destroy()
    except ImportError:
        pass
    sys.exit(1)