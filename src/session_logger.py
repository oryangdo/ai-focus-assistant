"""
Session logging module for saving focus session data to CSV.
"""

import csv
from pathlib import Path

from src.pomodoro import SessionData


CSV_HEADERS = [
    "timestamp",
    "duration_seconds",
    "distractions",
    "phone_visible_seconds",
    "focus_score",
    "peak_risk_score",
    "avg_risk_score",
]


def get_csv_path() -> Path:
    """Get path to sessions CSV, creating data directory if needed."""
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir / "sessions.csv"


def log_session(session: SessionData) -> None:
    """Append a session row to the CSV file."""
    csv_path = get_csv_path()
    file_exists = csv_path.exists()
    
    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(CSV_HEADERS)
        writer.writerow([
            session.timestamp,
            session.duration_seconds,
            session.distractions,
            session.phone_visible_seconds,
            session.focus_score,
            session.peak_risk_score,
            session.avg_risk_score,
        ])
