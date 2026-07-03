# -*- mode: python ; coding: utf-8 -*-

import os

# 获取当前工作目录（项目根目录）
project_root = os.getcwd()

# Windows manifest — embed requireAdministrator
manifest_path = os.path.join(project_root, 'AppleMusicDownloader.exe.manifest')
if not os.path.exists(manifest_path):
    manifest_path = None

a = Analysis(
    ['src/amdl/launcher.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        (os.path.join(project_root, 'tools'), 'tools'),
        (os.path.join(project_root, 'icon.ico'), '.'),
        (os.path.join(project_root, 'LICENSE'), '.')
    ],
    hiddenimports=[
        'amdl',
        'amdl.launcher',
        'amdl.fluent_gui',
        'amdl.download_worker',
        'amdl.ui_builder',
        'amdl.settings_store',
        'amdl.i18n',
        'amdl.cli',
        'amdl.core_downloader',
        'amdl.enums',
        'amdl.utils',
        'amdl.gui_conversion',
        'gamdl',
        'gamdl.api',
        'gamdl.api.apple_music',
        'gamdl.api.itunes',
        'gamdl.api.wrapper',
        'gamdl.downloader',
        'gamdl.downloader.base',
        'gamdl.downloader.downloader',
        'gamdl.downloader.song',
        'gamdl.downloader.music_video',
        'gamdl.downloader.uploaded_video',
        'gamdl.downloader.amdecrypt',
        'gamdl.interface',
        'gamdl.interface.base',
        'gamdl.interface.interface',
        'gamdl.interface.song',
        'gamdl.interface.music_video',
        'gamdl.interface.uploaded_video',
        'qfluentwidgets',
        'httpx',
        'structlog',
        'PIL',
        'colorama',
        'click',
        'PyQt6',
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PySide2',
        'PySide6',
    ],
    manifest=manifest_path,
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)


exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='AppleMusicDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(project_root, 'icon.ico'),
)