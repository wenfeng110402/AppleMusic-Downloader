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

if "--server" in sys.argv:
    from amdl.server import run_server
    run_server()
elif "--desktop" in sys.argv:
    from amdl.server import run_desktop
    run_desktop()
else:
    from amdl.server import run_server
    run_server()