"""Launch the Streamlit dashboard in the user's default browser."""

from __future__ import annotations

import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

PORT = 8501
DASHBOARD_URL = f"http://127.0.0.1:{PORT}"
HEALTH_URL = f"{DASHBOARD_URL}/_stcore/health"


def is_dashboard_running() -> bool:
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=1) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def launch_dashboard() -> bool:
    """Start Streamlit if needed and open the dashboard in the default browser."""
    try:
        import streamlit  # noqa: F401
    except ImportError:
        return False

    if is_dashboard_running():
        webbrowser.open(DASHBOARD_URL)
        return True

    project_root = Path(__file__).resolve().parent.parent
    log_file = Path.home() / "Library" / "Logs" / "AI Focus Assistant" / "dashboard.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    with open(log_file, "a", encoding="utf-8") as log:
        subprocess.Popen(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                str(project_root / "src" / "dashboard.py"),
                "--server.headless",
                "true",
                f"--server.port={PORT}",
                "--browser.gatherUsageStats",
                "false",
            ],
            cwd=project_root,
            stdout=log,
            stderr=log,
            start_new_session=True,
        )

    for _ in range(40):
        if is_dashboard_running():
            webbrowser.open(DASHBOARD_URL)
            return True
        time.sleep(0.25)

    return False
