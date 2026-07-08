"""python -m amdl → 启动服务或桌面应用"""
import sys

if "--server" in sys.argv:
    from amdl.server import run_server
    run_server()
elif "--desktop" in sys.argv:
    from amdl.server import run_desktop
    run_desktop()
else:
    from amdl.server import run_server
    run_server()