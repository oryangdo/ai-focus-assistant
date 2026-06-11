# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for AI Focus Assistant (macOS standalone .app)."""

from pathlib import Path

from PyInstaller.utils.hooks import collect_all

block_cipher = None
project_root = Path(SPECPATH)

datas = []
binaries = []
hiddenimports = [
    "mediapipe.tasks.python.vision",
    "ultralytics",
]

for package in ("mediapipe", "ultralytics"):
    pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(package)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hiddenimports

face_model = project_root / "models" / "face_landmarker.task"
if face_model.is_file():
    datas.append((str(face_model), "models"))

yolo_weights = project_root / "yolov8s.pt"
if yolo_weights.is_file():
    datas.append((str(yolo_weights), "."))

a = Analysis(
    ["webcam_demo.py"],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["streamlit", "pandas"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AI Focus Assistant",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
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
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="AI Focus Assistant",
)

app = BUNDLE(
    coll,
    name="AI Focus Assistant.app",
    icon=None,
    bundle_identifier="com.oryangdo.ai-focus-assistant",
    info_plist={
        "NSCameraUsageDescription": (
            "AI Focus Assistant uses your camera to detect phone distractions "
            "and track focus during Pomodoro sessions."
        ),
        "CFBundleShortVersionString": "1.0.0",
    },
)
