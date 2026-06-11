"""
Application path resolution for development, macOS launchers, and PyInstaller builds.

Read-only assets (models) resolve from the project or bundle root.
User data (CSV, charts, caches) lives under Application Support.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.request import urlretrieve

APP_NAME = "AI Focus Assistant"

YOLO_MODEL_FILENAME = "yolov8s.pt"
FACE_LANDMARKER_FILENAME = "face_landmarker.task"
FACE_LANDMARKER_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "face_landmarker/face_landmarker/float16/1/face_landmarker.task"
)


def is_frozen() -> bool:
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def bundle_dir() -> Path:
    """Root for bundled read-only assets."""
    if is_frozen():
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def user_support_dir() -> Path:
    """Writable per-user application directory."""
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support" / APP_NAME
    elif sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home())) / APP_NAME
    else:
        base = Path.home() / ".local" / "share" / APP_NAME
    base.mkdir(parents=True, exist_ok=True)
    return base


def data_dir() -> Path:
    path = user_support_dir() / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def reports_dir() -> Path:
    path = user_support_dir() / "reports"
    path.mkdir(parents=True, exist_ok=True)
    return path


def cache_dir() -> Path:
    path = user_support_dir() / "cache"
    path.mkdir(parents=True, exist_ok=True)
    return path


def models_cache_dir() -> Path:
    """User-writable model cache (runtime downloads when not bundled)."""
    return cache_dir()


def ensure_runtime_dirs() -> None:
    """Create all user-writable directories before a session starts."""
    data_dir()
    reports_dir()
    models_cache_dir()


def resource_path(*parts: str) -> Path:
    return bundle_dir().joinpath(*parts)


def _first_existing(candidates: list[Path]) -> Path | None:
    for path in candidates:
        if path.is_file():
            return path
    return None


def ensure_yolo_model() -> Path:
    """Return path to YOLO weights, downloading into user cache if needed."""
    existing = _first_existing([
        resource_path(YOLO_MODEL_FILENAME),
        models_cache_dir() / YOLO_MODEL_FILENAME,
        bundle_dir() / YOLO_MODEL_FILENAME,
    ])
    if existing is not None:
        return existing

    dest = models_cache_dir() / YOLO_MODEL_FILENAME
    try:
        print(f"Downloading YOLO weights to {dest} ...")
        from ultralytics.utils.downloads import attempt_download_asset

        downloaded = attempt_download_asset(YOLO_MODEL_FILENAME, dir=models_cache_dir())
        return Path(downloaded)
    except Exception as exc:
        raise RuntimeError(
            f"Could not download {YOLO_MODEL_FILENAME}. "
            "Check your internet connection and try again."
        ) from exc


def ensure_face_landmarker_model() -> Path:
    """Return path to the MediaPipe face landmarker model."""
    existing = _first_existing([
        resource_path("models", FACE_LANDMARKER_FILENAME),
        models_cache_dir() / FACE_LANDMARKER_FILENAME,
        bundle_dir() / "models" / FACE_LANDMARKER_FILENAME,
    ])
    if existing is not None:
        return existing

    dest = models_cache_dir() / FACE_LANDMARKER_FILENAME
    try:
        print(f"Downloading face landmarker model to {dest} ...")
        urlretrieve(FACE_LANDMARKER_URL, dest)
        print("Face landmarker model ready.")
        return dest
    except Exception as exc:
        raise RuntimeError(
            f"Could not download {FACE_LANDMARKER_FILENAME}. "
            "Check your internet connection and try again."
        ) from exc
