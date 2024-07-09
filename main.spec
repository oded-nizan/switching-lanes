# -*- mode: python ; coding: utf-8 -*-

import sys
import os

# Add project root to the path
project_root = os.path.abspath(os.path.dirname(__name__))
sys.path.insert(0, project_root)

a = Analysis(
    ['src/main.py'],
    pathex=[project_root],  # Ensure the root path is included
    binaries=[],
    datas=[
        ('src/resources/background.jpg', 'resources'),
        ('src/resources/obstacle.png', 'resources'),
        ('src/resources/player.png', 'resources'),
        ('src/resources/projectile.png', 'resources'),
        ('src/database.db', 'src')
    ],
    hiddenimports=[],
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
    [],
    exclude_binaries=True,
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='motorbike.ico',  # Ensure this is a string
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='main'
)
