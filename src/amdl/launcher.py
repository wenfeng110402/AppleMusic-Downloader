#!/usr/bin/env python
"""Cross-platform application launcher for AppleMusic Downloader GUI."""

import os
import sys
import traceback


# Ensure amdl is importable
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


# ---- Windows admin elevation (no-op on macOS/Linux) ----
def _ensure_admin_windows():
    """On Windows: request admin elevation if not already running as admin.
    Returns True if we should proceed with GUI, False if we relaunched."""
    if sys.platform != "win32":
        return True  # not Windows, nothing to do

    try:
        import ctypes
        if ctypes.windll.shell32.IsUserAnAdmin():
            return True  # already admin
    except Exception:
        return True  # can't check, proceed anyway

    # Not admin — relaunch self with runas verb
    try:
        ctypes.windll.shell32.ShellExecuteW(
            None,                     # hwnd
            "runas",                  # operation
            sys.executable,           # file
            " ".join(f'"{a}"' for a in sys.argv),  # parameters
            None,                     # directory
            1,                        # SW_SHOWNORMAL
        )
    except Exception:
        pass
    return False  # original process exits


def main():
    """Launch the GUI application (with admin elevation on Windows)."""
    if not _ensure_admin_windows():
        sys.exit(0)

    try:
        from PyQt6.QtWidgets import QApplication
        from qfluentwidgets import Theme, setTheme

        from amdl.fluent_gui import FluentMainWindow

        app = QApplication(sys.argv)
        setTheme(Theme.AUTO)
        app.setApplicationName("AppleMusic Downloader")
        app.setApplicationVersion("2.4.2")

        window = FluentMainWindow()
        window.show()

        sys.exit(app.exec())

    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        input("Press Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    main()
