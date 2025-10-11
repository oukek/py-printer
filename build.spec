# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller配置文件
用于打包Flask服务应用
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files

# 获取项目根目录
project_root = os.path.dirname(os.path.abspath(SPEC))

# 收集所有数据文件
datas = []

# 收集Flask模板和静态文件（如果有的话）
datas += collect_data_files('flask')

# 收集项目中的配置文件和其他数据文件
datas += [
    (os.path.join(project_root, 'config.py'), '.'),
]

# 收集隐藏导入
hiddenimports = []
hiddenimports += [
    'flask', 'flask_cors', 'PIL', 'fitz', 'psutil',
    'werkzeug', 'jinja2', 'markupsafe', 'itsdangerous', 'click',
    'blinker'
]

# Windows特定的隐藏导入
if sys.platform == 'win32':
    hiddenimports += [
        'win32api', 'win32print', 'win32gui', 'win32con',
        'pywintypes'
    ]

# 分析配置
a = Analysis(
    ['app.py'],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'jupyter',
        'IPython',
        'pytest',
        'unittest',
        'doctest',
        'pdb',
        'turtle',
        'curses',
        'readline',
        'antigravity',
        'this',
        'webbrowser'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# 去重和过滤
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# 可执行文件配置
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='py-server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 保留控制台窗口以显示日志
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以添加图标文件路径
)