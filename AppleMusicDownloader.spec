# -*- mode: python ; coding: utf-8 -*-

import os

# 获取当前工作目录（项目根目录）
project_root = os.getcwd()

a = Analysis(
    ['src/amdl/fluent_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        (os.path.join(project_root, 'tools'), 'tools'),
        (os.path.join(project_root, 'icon.ico'), '.'),
        (os.path.join(project_root, 'LICENSE'), '.')
    ],
    hiddenimports=[
        'qfluentwidgets', 
        'yt_dlp', 
        'mutagen', 
        'm3u8', 
        'PIL', 
        'pywidevine', 
        'InquirerPy', 
        'colorama',
        'click',
        'requests',
        'urllib3',
        'certifi',
        'charset_normalizer',
        'idna',
        'yaml',
        'termcolor',
        'PyQt6',
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'ffmpeg'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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