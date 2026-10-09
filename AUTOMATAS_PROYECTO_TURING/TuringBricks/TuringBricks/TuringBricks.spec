# -*- mode: python ; coding: utf-8 -*-
# Archivo de PyInstaller para crear el ejecutable de Turing Bricks.
# Uso:  python -m PyInstaller --noconfirm --clean TuringBricks.spec
import sys
from PyInstaller.utils.hooks import collect_all

datas = [("assets", "assets")]
binaries, hiddenimports = [], []
for pkg in ("ursina", "panda3d", "panda3d_gltf", "screeninfo", "pyperclip", "PIL"):
    try:
        d, b, h = collect_all(pkg)
        datas += d; binaries += b; hiddenimports += h
    except Exception:
        pass

a = Analysis(["main.py"], pathex=[], binaries=binaries, datas=datas, hiddenimports=hiddenimports,
             hookspath=[], runtime_hooks=[], excludes=["tkinter", "matplotlib", "numpy", "cv2", "imageio", "imageio_ffmpeg", "lxml", "scipy", "pandas", "IPython"], noarchive=False)
pyz = PYZ(a.pure)
icon = "assets/icon.ico" if sys.platform.startswith("win") else None
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="TuringBricks", debug=False, strip=False, upx=False,
          console=False, icon=icon)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="TuringBricks")
