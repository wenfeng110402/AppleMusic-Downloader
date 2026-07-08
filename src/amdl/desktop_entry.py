"""PyInstaller entry point for the desktop application bundle.

This script is the target for PyInstaller when building
standalone executables for Windows, macOS, and Linux.
"""
from amdl.server import run_desktop

if __name__ == "__main__":
    run_desktop()
