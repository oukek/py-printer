# -*- mode: python ; coding: utf-8 -*-

import sys
import platform

block_cipher = None

a = Analysis(
    ['printer_info.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'win32con',
        'win32print',
        'win32ui',
        'PIL.ImageWin',
        'fitz',
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

# 根据操作系统设置不同的可执行文件名和配置
if platform.system() == 'Windows':
    exe_name = 'printer-tool.exe'
    # Windows特定配置
    console = True  # 启用控制台窗口，便于查看JSON输出
    argv_emulation = False
    codesign_identity = None
    entitlements_file = None
else:
    exe_name = 'printer-tool'
    # macOS/Linux配置
    console = True  # 启用控制台窗口，便于查看JSON输出
    argv_emulation = True
    codesign_identity = None
    entitlements_file = None

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=exe_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=console,
    disable_windowed_traceback=False,
    argv_emulation=argv_emulation,
    target_arch=None,  # 让PyInstaller自动检测架构
    codesign_identity=codesign_identity,
    entitlements_file=entitlements_file,
)