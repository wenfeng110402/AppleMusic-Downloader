import json
import time
import sys
import subprocess
import colorama
import requests
from urllib.parse import unquote, quote


def color_text(text: str, color) -> str:
    return color + text + colorama.Style.RESET_ALL


def normalize_url(url: str) -> str:
    """
    标准化 URL，解码特殊字符以便正则表达式匹配。
    
    Args:
        url: 原始 URL，可能包含 URL 编码的特殊字符
        
    Returns:
        解码后的 URL
    """
    # URL 解码，处理像 %20 这样的编码字符
    decoded_url = unquote(url)
    return decoded_url


def sanitize_filename(filename: str) -> str:
    """
    清理文件名中的非法字符，确保可以安全地用作文件系统路径。
    
    Args:
        filename: 原始文件名
        
    Returns:
        清理后的文件名
    """
    import re
    # Windows 和其他系统中的非法文件名字符
    illegal_chars = r'[\\/:*?"<>|;]'
    # 用下划线替换非法字符
    sanitized = re.sub(illegal_chars, '_', filename)
    # 移除控制字符
    sanitized = ''.join(char for char in sanitized if ord(char) >= 32)
    # 移除前导和尾随空格/点号
    sanitized = sanitized.strip('. ')
    return sanitized


def raise_response_exception(response):
    # 构建详细的错误信息
    error_details = {
        "url": response.url,
        "status_code": response.status_code,
        "response_text": response.text,
        "request_headers": dict(response.request.headers),
        "response_headers": dict(response.headers)
    }
    
    
def get_subprocess_startupinfo():
    """
    获取用于隐藏命令行窗口的 startupinfo 配置
    
    Returns:
        subprocess.STARTUPINFO: 配置了隐藏窗口的 startupinfo 对象，在非 Windows 系统上返回 None
    """
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        return startupinfo
    return None


def resource_path(relative_path: str) -> str:
    """
    返回运行时资源的绝对路径。支持源码运行与 PyInstaller 打包后的 _MEIPASS。

    :param relative_path: 相对于项目根或 _MEIPASS 的相对路径，例如 "tools/ffmpeg.exe"
    :return: 资源的绝对路径字符串
    """
    try:
        from pathlib import Path
        import sys

        if getattr(sys, "frozen", False):
            base = getattr(sys, "_MEIPASS", Path(sys.executable).parent)
        else:
            # project root (gamdl is package dir, so go up one level)
            base = Path(__file__).parent.parent

        return str(Path(base) / relative_path)
    except Exception:
        # 回退到相对路径
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
    added = []
    for p in candidates:
        try:
            if p.exists() and p.is_dir():
                p_str = str(p)
                if p_str not in os.environ.get("PATH", ""):
                    os.environ["PATH"] = p_str + os.pathsep + os.environ.get("PATH", "")
                    added.append(p_str)
        except Exception:
            continue

    # 可选：返回或记录已加入的路径，当前我们不返回值
    return