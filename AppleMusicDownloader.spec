# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

added_files = [
    ('gamdl/*', 'gamdl'),
    ('icon.ico', '.'),
    ('LICENSE', '.'),
    ('tools/N_m3u8DL-RE.exe', 'tools'),
    ('tools/ffmpeg.exe', 'tools'),
    ('tools/mp4box.exe', 'tools'),
    ('tools/mp4decrypt.exe', 'tools'),
]

a = Analysis(
    ['gamdl/fluent_gui.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'gamdl',
        'gamdl.cli',
        'gamdl.fluent_gui',
        'gamdl.fluent_main_window',
        'gamdl.main_window',
        'click',
        'colorama',
        'InquirerPy',
        'm3u8',
        'mutagen',
        'PIL',
        'pywidevine',
        'yt_dlp',
        'PyQt6',
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
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
    icon='icon.ico'
)