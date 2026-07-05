import sys
from pathlib import Path


def resource_path(relative_path: str) -> str:
    """返回运行时资源的绝对路径。支持源码运行与 PyInstaller 打包后的 _MEIPASS。"""
    try:
        if getattr(sys, "frozen", False):
            base = getattr(sys, "_MEIPASS", Path(sys.executable).parent)
        else:
            base = Path(__file__).parent.parent
        return str(Path(base) / relative_path)
    except Exception:
        return relative_path


def prepend_tools_to_path(tool_dir_names: list[str] | None = None) -> None:
    """
    在运行时将可执行工具目录（例如 tools/）优先加入 PATH。

    - 在打包后的环境中，会优先查找 sys._MEIPASS 下的 tools 目录。
    - 在源码运行时，会查找项目根的 tools 目录和当前工作目录的 tools 目录。
    这样可以保证 subprocess 调用无需额外设置系统环境变量即可找到内置工具。
    """
    import os
    from pathlib import Path
    import sys


    candidates = []
    if tool_dir_names is None:
        tool_dir_names = ["tools"]

    # 构建 platform-specific 子目录候选，例如 tools/windows-x86_64, tools/linux-x86_64, tools/macos-arm64
    def platform_dir_names():
        import platform as _pl
        _sys = sys.platform
        machine = _pl.machine().lower()
        names = []
        if _sys.startswith("win"):
            arch = "x86_64" if "amd64" in machine or "x86_64" in machine else machine
            names.append(f"windows-{arch}")
            names.append("windows")
        elif _sys.startswith("linux"):
            arch = "x86_64" if "x86_64" in machine or "amd64" in machine else machine
            names.append(f"linux-{arch}")
            names.append("linux")
        elif _sys.startswith("darwin"):
            # macOS (darwin) -> use macos-arch
            arch = "arm64" if "arm64" in machine or "aarch64" in machine else "x86_64"
            names.append(f"macos-{arch}")
            names.append("macos")
        # generic fallback
        names.append("")
        return names

    platform_names = platform_dir_names()

    # 1) PyInstaller 解包目录
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            for pname in platform_names:
                for d in tool_dir_names:
                    p = Path(meipass) / (d if not pname else f"{d}/{pname}")
                    candidates.append(p)

    # 2) 项目根的 tools (包含 platform-specific 子目录)
    project_root = Path(__file__).parent.parent
    for pname in platform_names:
        for d in tool_dir_names:
            p = project_root / (d if not pname else Path(d) / pname)
            candidates.append(p)

    # 3) 当前工作目录的 tools (包含 platform-specific 子目录)
    for pname in platform_names:
        for d in tool_dir_names:
            p = Path.cwd() / (d if not pname else Path(d) / pname)
            candidates.append(p)

    # 将存在的目录按优先级加入 PATH 前端
    current_path = os.environ.get("PATH", "")
    normalized_path_entries = {
        os.path.normcase(os.path.normpath(x))
        for x in current_path.split(os.pathsep)
        if x
    }
    added = []
    for p in candidates:
        try:
            if p.exists() and p.is_dir():
                p_str = str(p)
                normalized_candidate = os.path.normcase(os.path.normpath(p_str))
                if normalized_candidate not in normalized_path_entries:
                    os.environ["PATH"] = p_str + os.pathsep + os.environ.get("PATH", "")
                    normalized_path_entries.add(normalized_candidate)
                    added.append(p_str)
        except Exception:
            continue

    # 可选：返回或记录已加入的路径，当前我们不返回值
    return
