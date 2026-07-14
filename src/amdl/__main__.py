"""python -m amdl → 启动服务或桌面应用"""
import sys

# Ensure anyio uses the asyncio backend (avoids event-loop detection issues).
if sys.platform == "win32":
    import os as _os
    _os.environ.setdefault("ANYIO_BACKEND", "asyncio")

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