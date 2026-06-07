"""
Session logging module for saving focus session data to CSV.
"""

import csv
import shutil
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
    "gaze_distractions",
    "gaze_away_seconds",
]

# Defaults for columns added after older schema versions
CSV_DEFAULTS: dict[str, int | float] = {
    "peak_risk_score": 0,
    "avg_risk_score": 0,
    "gaze_distractions": 0,
    "gaze_away_seconds": 0.0,
}

# When rows were appended with extra values beyond a short header
TRAILING_EXTRA_COLUMNS = [
    "peak_risk_score",
    "avg_risk_score",
    "gaze_distractions",
    "gaze_away_seconds",
]


def get_csv_path() -> Path:
    """Get path to sessions CSV, creating data directory if needed."""
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir / "sessions.csv"


def _normalize_row(old_header: list[str], row: list[str]) -> dict[str, str]:
    """Map one CSV row onto the current schema."""
    record = {header: str(CSV_DEFAULTS.get(header, "")) for header in CSV_HEADERS}

    for header in CSV_HEADERS:
        if header in old_header:
            idx = old_header.index(header)
            if idx < len(row):
                record[header] = row[idx]

    if len(row) > len(old_header):
        extras = row[len(old_header):]
        for i, header in enumerate(TRAILING_EXTRA_COLUMNS):
            if header not in old_header and i < len(extras):
                record[header] = extras[i]

    return record


def ensure_sessions_csv(csv_path: Path | None = None) -> tuple[bool, list[str] | None]:
    """
    Ensure sessions.csv uses CSV_HEADERS.

    Migrates older files in place (with a .bak backup) when the header differs.
    Returns (migrated, previous_header).
    """
    csv_path = csv_path or get_csv_path()
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    if not csv_path.exists():
        with open(csv_path, "w", newline="") as f:
            csv.writer(f).writerow(CSV_HEADERS)
        return False, None

    with open(csv_path, newline="") as f:
        rows = list(csv.reader(f))

    if not rows:
        with open(csv_path, "w", newline="") as f:
            csv.writer(f).writerow(CSV_HEADERS)
        return False, None

    old_header = rows[0]
    if old_header == CSV_HEADERS:
        return False, None

    migrated_rows = []
    for row in rows[1:]:
        if not row or not any(cell.strip() for cell in row):
            continue
        record = _normalize_row(old_header, row)
        migrated_rows.append([record[header] for header in CSV_HEADERS])

    backup_path = csv_path.with_suffix(".csv.bak")
    shutil.copy2(csv_path, backup_path)

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADERS)
        writer.writerows(migrated_rows)

    return True, old_header


def log_session(session: SessionData) -> None:
    """Append a session row to the CSV file."""
    csv_path = get_csv_path()
    ensure_sessions_csv(csv_path)

    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            session.timestamp,
            session.duration_seconds,
            session.distractions,
            session.phone_visible_seconds,
            session.focus_score,
            session.peak_risk_score,
            session.avg_risk_score,
            session.gaze_distractions,
            session.gaze_away_seconds,
        ])
