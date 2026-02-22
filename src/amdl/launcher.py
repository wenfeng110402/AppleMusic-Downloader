import os
import sys
import traceback

from PyQt6.QtWidgets import QApplication
from qfluentwidgets import Theme, setTheme


def is_admin() -> bool:
    try:
        import ctypes

        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def request_admin_privileges() -> bool:
    """请求管理员权限并重新启动程序"""
    try:
        import ctypes
        import subprocess

        # 检查是否为PyInstaller打包的EXE
        is_frozen = getattr(sys, "frozen", False)
        
        if is_frozen:
            # PyInstaller EXE - 直接重启自身
            try:
                exe_path = sys.executable
                ctypes.windll.shell32.ShellExecuteW(
                    None,
                    "runas",
                    exe_path,
                    None,
                    None,
                    1,
                )
                return True
            except Exception as e:
                print(f"PyInstaller模式下请求权限失败: {e}")
                return False
        else:
            # 普通Python脚本
            script_path = os.path.abspath(__file__)
            
            try:
                # 首先尝试用ctypes（更稳定）
                ctypes.windll.shell32.ShellExecuteW(
                    None,
                    "runas",
                    sys.executable,
                    f'"{script_path}"',
                    None,
                    1,
                )
                return True
            except Exception:
                # 备用方案：PowerShell
                try:
                    subprocess.Popen(
                        f'powershell -Command "Start-Process python -ArgumentList \'{script_path}\' -Verb RunAs"',
                        shell=True
                    )
                    return True
                except Exception:
                    return False
        
    except Exception as e:
        print(f"请求管理员权限时出错: {e}")
        return False


def main():
    if not is_admin():
        print("请求管理员权限...")
        if request_admin_privileges():
            sys.exit(0)
        print("无法获取管理员权限，程序将退出")
        input("按回车键退出...")
        sys.exit(1)

    try:
        try:
            from amdl.utils import prepend_tools_to_path

            prepend_tools_to_path(["tools"])
        except Exception:
            pass

        from amdl.fluent_gui import FluentMainWindow

        app = QApplication(sys.argv)
        setTheme(Theme.AUTO)
        app.setApplicationName("AppleMusic Downloader")
        app.setApplicationVersion("3.1.0")

        window = FluentMainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"发生未捕获异常: {str(e)}")
        traceback.print_exc()
        input("按回车键退出...")
