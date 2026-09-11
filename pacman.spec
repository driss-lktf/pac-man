# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Pac-Man game.

Build a standalone executable with::

    pyinstaller pacman.spec

The resulting binary is placed in ``dist/pac-man``. The ``config.json`` file
and the assigned ``mazegenerator`` package are bundled alongside the code.
"""

block_cipher = None

a = Analysis(
    ['pac-man.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('config.json', '.'),
        ('mazegenerator', 'mazegenerator'),
    ],
    hiddenimports=['mazegenerator'],
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
    name='pac-man',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
