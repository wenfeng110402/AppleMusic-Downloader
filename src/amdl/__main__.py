"""python -m amdl → 启动 Flet GUI"""
from amdl.interface import main as gui_main
import flet as ft

ft.app(target=gui_main)
