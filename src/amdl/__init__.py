"""AppleMusic Downloader (amdl) — core package."""

import asyncio
import sys

# Windows: must be set at package level, before any submodule imports gamdl.
# gamdl's httpx_retries + anyio is incompatible with ProactorEventLoop.
if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

__version__ = "2.4.9"
