# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

python_path = r'C:\Users\micha\AppData\Local\Programs\Python\Python313\Lib\site-packages'

a = Analysis(
    ['launcher.py'],
    pathex=[python_path],
    binaries=[],
    datas=[
        ('logout.py', '.'),
        ('stashscroll.py', '.'),
        ('npcap_detector.py', '.'),
        ('poe_commands.py', '.'),
        ('update_checker.py', '.'),
    ],
    hiddenimports=[
        'win32api',
        'win32con',
        'win32process',
        'win32gui',
        'psutil',
        'pynput',
        'pynput.keyboard',
        'pynput.mouse',
        'keyboard',
        'scapy',
        'scapy.all',
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'winreg',
        'ctypes',
        'subprocess',
        'logging',
        'threading',
        'time',
        'requests',
        'packaging',
        'packaging.version',
        're',
        'json',
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

pyz = PYZ(
    a.pure, 
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PoE Tools',
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
    icon='NONE',
    uac_admin=True,
) 