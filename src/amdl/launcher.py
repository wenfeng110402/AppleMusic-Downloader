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
    try:
        import ctypes

        if getattr(sys, "frozen", False):
            executable = sys.executable
            script_path = executable
        else:
            executable = sys.executable
            script_path = os.path.abspath(__file__)

        ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            executable,
            f'"{script_path}"' if not getattr(sys, "frozen", False) else "",
            None,
            1,
        )
        return True
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
            from .utils import prepend_tools_to_path

            prepend_tools_to_path(["tools"])
        except Exception:
            pass

        from .fluent_gui import FluentMainWindow

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
