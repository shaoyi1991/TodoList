# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['c:\\Users\\Administrator\\Desktop\\Coze插件\\TodoList\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('c:\\Users\\Administrator\\Desktop\\Coze插件\\TodoList\\todo.ico', '.'), ('todo_data.json', '.')],
    hiddenimports=['win32com.client'],
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
    name='TodoListV1.3.251212',
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
    icon=['c:\\Users\\Administrator\\Desktop\\Coze插件\\TodoList\\todo.ico'],
)
