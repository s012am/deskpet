# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['pet.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('pets', 'pets'),
    ],
    hiddenimports=[
        'PyQt6.QtWidgets',
        'PyQt6.QtGui',
        'PyQt6.QtCore',
        'objc',
        'AppKit',
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
    [],
    exclude_binaries=True,
    name='DesktopPet',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DesktopPet',
)
app = BUNDLE(
    coll,
    name='DesktopPet.app',
    icon=None,
    bundle_identifier='com.desktoppet.app',
    info_plist={
        'NSHighResolutionCapable': True,
        'LSUIElement': True,
    },
)
