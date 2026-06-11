"""
Analytics script for focus session history.

Reads session history from Application Support, calculates statistics,
prints a summary, and generates charts saved to the user reports folder.

Run with: .venv/bin/python -m src.analytics
"""

import csv
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from src.paths import reports_dir
from src.session_logger import CSV_HEADERS, ensure_sessions_csv, get_csv_path


DATA_FILE = get_csv_path()
REPORTS_DIR = reports_dir()

ROLLING_WINDOW = 5


def load_sessions() -> list[dict]:
    """Load sessions from CSV file."""
    if not DATA_FILE.exists():
        return []

    ensure_sessions_csv(DATA_FILE)

    sessions = []
    with open(DATA_FILE, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sessions.append({
                "timestamp": row.get("timestamp", ""),
                "duration_seconds": float(row.get("duration_seconds") or 0),
                "distractions": int(row.get("distractions") or 0),
                "phone_visible_seconds": float(row.get("phone_visible_seconds") or 0),
                "focus_score": int(row.get("focus_score") or 0),
                "peak_risk_score": int(row.get("peak_risk_score") or 0),
                "avg_risk_score": int(row.get("avg_risk_score") or 0),
                "gaze_distractions": int(row.get("gaze_distractions") or 0),
                "gaze_away_seconds": float(row.get("gaze_away_seconds") or 0),
            })
    return sessions


def sessions_have_risk_data(sessions: list[dict]) -> bool:
    """True if any session has recorded risk scores."""
    return any(s["peak_risk_score"] > 0 or s["avg_risk_score"] > 0 for s in sessions)


def sessions_have_gaze_data(sessions: list[dict]) -> bool:
    """True if any session has recorded gaze metrics."""
    return any(s["gaze_away_seconds"] > 0 or s["gaze_distractions"] > 0 for s in sessions)


def calculate_stats(sessions: list[dict]) -> dict:
    """Calculate summary statistics from sessions."""
    if not sessions:
        return {}
    
    total_sessions = len(sessions)
    total_focus_time = sum(s["duration_seconds"] for s in sessions)
    total_phone_time = sum(s["phone_visible_seconds"] for s in sessions)
    total_distractions = sum(s["distractions"] for s in sessions)
    scores = [s["focus_score"] for s in sessions]
    
    stats = {
        "total_sessions": total_sessions,
        "total_focus_time_seconds": total_focus_time,
        "total_focus_time_hours": total_focus_time / 3600,
        "average_focus_score": sum(scores) / len(scores),
        "average_distractions": total_distractions / total_sessions,
        "average_phone_time": total_phone_time / total_sessions,
        "total_phone_time_seconds": total_phone_time,
        "best_score": max(scores),
        "worst_score": min(scores),
    }

    if sessions_have_gaze_data(sessions):
        stats["average_gaze_distractions"] = (
            sum(s["gaze_distractions"] for s in sessions) / total_sessions
        )
        stats["average_gaze_away_seconds"] = (
            sum(s["gaze_away_seconds"] for s in sessions) / total_sessions
        )
        stats["total_gaze_away_seconds"] = sum(s["gaze_away_seconds"] for s in sessions)

    return stats


# ─────────────────────────────────────────────────────────────
# TREND CALCULATIONS
# ─────────────────────────────────────────────────────────────

def calculate_trend(values: list[float]) -> tuple[float, str]:
    """
    Calculate linear trend slope and direction.
    Returns (slope, arrow) where arrow is ↑, ↓, or →.
    """
    if len(values) < 2:
        return 0.0, "→"
    
    x = np.arange(len(values))
    slope, _ = np.polyfit(x, values, 1)
    
    threshold = 0.5
    if slope > threshold:
        return slope, "↑"
    elif slope < -threshold:
        return slope, "↓"
    else:
        return slope, "→"


def calculate_trends(sessions: list[dict]) -> dict:
    """Calculate trends for key metrics."""
    if len(sessions) < 2:
        return {}
    
    scores = [s["focus_score"] for s in sessions]
    phone_times = [s["phone_visible_seconds"] for s in sessions]
    distractions = [s["distractions"] for s in sessions]
    
    score_slope, score_arrow = calculate_trend(scores)
    phone_slope, phone_arrow = calculate_trend(phone_times)
    dist_slope, dist_arrow = calculate_trend(distractions)
    
    result = {
        "score_trend": score_arrow,
        "score_slope": score_slope,
        "phone_trend": phone_arrow,
        "phone_slope": phone_slope,
        "distraction_trend": dist_arrow,
        "distraction_slope": dist_slope,
    }

    if sessions_have_gaze_data(sessions):
        gaze_away = [s["gaze_away_seconds"] for s in sessions]
        gaze_events = [float(s["gaze_distractions"]) for s in sessions]
        gaze_away_slope, gaze_away_arrow = calculate_trend(gaze_away)
        gaze_event_slope, gaze_event_arrow = calculate_trend(gaze_events)
        result.update({
            "gaze_away_trend": gaze_away_arrow,
            "gaze_away_slope": gaze_away_slope,
            "gaze_distraction_trend": gaze_event_arrow,
            "gaze_distraction_slope": gaze_event_slope,
        })

    return result


def calculate_risk_trends(sessions: list[dict]) -> dict:
    """Calculate trends for peak and average risk scores."""
    if len(sessions) < 2 or not sessions_have_risk_data(sessions):
        return {}

    peak_scores = [float(s["peak_risk_score"]) for s in sessions]
    avg_scores = [float(s["avg_risk_score"]) for s in sessions]

    peak_slope, peak_arrow = calculate_trend(peak_scores)
    avg_slope, avg_arrow = calculate_trend(avg_scores)

    return {
        "peak_risk_trend": peak_arrow,
        "peak_risk_slope": peak_slope,
        "avg_risk_trend": avg_arrow,
        "avg_risk_slope": avg_slope,
    }


def calculate_risk_stats(sessions: list[dict]) -> dict:
    """Summary statistics for risk scores."""
    if not sessions_have_risk_data(sessions):
        return {}

    peak_scores = [s["peak_risk_score"] for s in sessions]
    avg_scores = [s["avg_risk_score"] for s in sessions]

    return {
        "average_peak_risk": sum(peak_scores) / len(peak_scores),
        "average_avg_risk": sum(avg_scores) / len(avg_scores),
        "highest_peak_risk": max(peak_scores),
        "lowest_avg_risk": min(avg_scores),
    }


# ─────────────────────────────────────────────────────────────
# ROLLING AVERAGES
# ─────────────────────────────────────────────────────────────

def calculate_rolling_averages(sessions: list[dict], window: int = ROLLING_WINDOW) -> dict:
    """Calculate rolling averages for the last N sessions."""
    if not sessions:
        return {}
    
    recent = sessions[-window:]
    
    return {
        "rolling_score": sum(s["focus_score"] for s in recent) / len(recent),
        "rolling_phone_time": sum(s["phone_visible_seconds"] for s in recent) / len(recent),
        "rolling_distractions": sum(s["distractions"] for s in recent) / len(recent),
        "window_size": len(recent),
    }


# ─────────────────────────────────────────────────────────────
# PERSONAL RECORDS
# ─────────────────────────────────────────────────────────────

def calculate_distraction_free_streak(sessions: list[dict]) -> int:
    """Find the longest streak of consecutive sessions with 0 distractions."""
    if not sessions:
        return 0
    
    max_streak = 0
    current_streak = 0
    
    for s in sessions:
        if s["distractions"] == 0:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0
    
    return max_streak


def calculate_personal_records(sessions: list[dict]) -> dict:
    """Calculate personal records from all sessions."""
    if not sessions:
        return {}
    
    return {
        "highest_score": max(s["focus_score"] for s in sessions),
        "longest_session_seconds": max(s["duration_seconds"] for s in sessions),
        "lowest_phone_time": min(s["phone_visible_seconds"] for s in sessions),
        "distraction_free_streak": calculate_distraction_free_streak(sessions),
    }


# ─────────────────────────────────────────────────────────────
# TIME OF DAY ANALYSIS
# ─────────────────────────────────────────────────────────────

def get_time_bucket(timestamp: str) -> str:
    """Categorize timestamp into time-of-day bucket."""
    try:
        dt = datetime.fromisoformat(timestamp)
        hour = dt.hour
    except ValueError:
        return "unknown"
    
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 21:
        return "evening"
    else:
        return "night"


def analyze_time_of_day(sessions: list[dict]) -> dict[str, dict]:
    """Analyze performance by time of day."""
    buckets: dict[str, list[int]] = {
        "morning": [],
        "afternoon": [],
        "evening": [],
        "night": [],
    }
    
    for s in sessions:
        bucket = get_time_bucket(s["timestamp"])
        if bucket in buckets:
            buckets[bucket].append(s["focus_score"])
    
    result = {}
    for bucket, scores in buckets.items():
        if scores:
            result[bucket] = {
                "avg_score": sum(scores) / len(scores),
                "count": len(scores),
            }
    
    return result


def format_time_mmss(seconds: float) -> str:
    """Format seconds as MM:SS."""
    mins, secs = divmod(int(seconds), 60)
    return f"{mins}:{secs:02d}"


def print_summary(
    stats: dict,
    trends: dict,
    rolling: dict,
    records: dict,
    time_of_day: dict,
    risk_trends: dict | None = None,
    risk_stats: dict | None = None,
) -> None:
    """Print a clean terminal summary with all analytics."""
    if not stats:
        print("No session data found.")
        print(f"Run some focus sessions first. Data will be saved to {DATA_FILE}")
        return
    
    print()
    print("═" * 47)
    print("           FOCUS SESSION ANALYTICS")
    print("═" * 47)
    print(f"  Total Sessions:          {stats['total_sessions']}")
    print(f"  Total Focus Time:        {stats['total_focus_time_hours']:.1f} hours")
    print(f"  Average Focus Score:     {stats['average_focus_score']:.1f}")
    print(
        "    (100 − phone time ratio×50 − phone hits×5 "
        "− gaze events×2 − gaze-away ratio×25, clamped 0–100)"
    )
    print(f"  Average Distractions:    {stats['average_distractions']:.1f} per session")
    print(f"  Total Phone Time:        {format_time_mmss(stats['total_phone_time_seconds'])}")
    print(f"  Best Session Score:      {stats['best_score']}")
    print(f"  Worst Session Score:     {stats['worst_score']}")
    
    # Trends
    if trends:
        print()
        print("─" * 17 + " TRENDS " + "─" * 17)
        score_label = "improving" if trends["score_trend"] == "↑" else "declining" if trends["score_trend"] == "↓" else "stable"
        phone_label = "improving" if trends["phone_trend"] == "↓" else "worsening" if trends["phone_trend"] == "↑" else "stable"
        dist_label = "improving" if trends["distraction_trend"] == "↓" else "worsening" if trends["distraction_trend"] == "↑" else "stable"
        print(f"  Focus Score:       {trends['score_trend']} {score_label}")
        print(f"  Phone Time:        {trends['phone_trend']} {phone_label}")
        print(f"  Distractions:      {trends['distraction_trend']} {dist_label}")

    if risk_stats:
        print()
        print("─" * 15 + " RISK STATS " + "─" * 15)
        print(f"  Avg Peak Risk:       {risk_stats['average_peak_risk']:.1f}")
        print(f"  Avg Session Risk:    {risk_stats['average_avg_risk']:.1f}")
        print(f"  Highest Peak Risk:   {risk_stats['highest_peak_risk']:.0f}")

    if risk_trends:
        print()
        print("─" * 14 + " RISK TRENDS " + "─" * 14)
        peak_label = (
            "worsening" if risk_trends["peak_risk_trend"] == "↑"
            else "improving" if risk_trends["peak_risk_trend"] == "↓"
            else "stable"
        )
        avg_label = (
            "worsening" if risk_trends["avg_risk_trend"] == "↑"
            else "improving" if risk_trends["avg_risk_trend"] == "↓"
            else "stable"
        )
        print(f"  Peak Risk:         {risk_trends['peak_risk_trend']} {peak_label}")
        print(f"  Avg Risk:          {risk_trends['avg_risk_trend']} {avg_label}")

    if stats.get("average_gaze_away_seconds") is not None:
        print()
        print("─" * 15 + " GAZE STATS " + "─" * 15)
        print(f"  Avg Gaze Away:       {format_time_mmss(stats['average_gaze_away_seconds'])}")
        print(f"  Avg Gaze Events:     {stats['average_gaze_distractions']:.1f} per session")
        print(f"  Total Gaze Away:     {format_time_mmss(stats['total_gaze_away_seconds'])}")

    if trends.get("gaze_away_trend"):
        print()
        print("─" * 14 + " GAZE TRENDS " + "─" * 14)
        away_label = (
            "worsening" if trends["gaze_away_trend"] == "↑"
            else "improving" if trends["gaze_away_trend"] == "↓"
            else "stable"
        )
        event_label = (
            "worsening" if trends["gaze_distraction_trend"] == "↑"
            else "improving" if trends["gaze_distraction_trend"] == "↓"
            else "stable"
        )
        print(f"  Gaze Away Time:    {trends['gaze_away_trend']} {away_label}")
        print(f"  Gaze Distractions: {trends['gaze_distraction_trend']} {event_label}")
    
    # Rolling averages
    if rolling and rolling.get("window_size", 0) >= 2:
        print()
        print("─" * 12 + f" ROLLING AVG ({rolling['window_size']}) " + "─" * 12)
        print(f"  Recent Score:      {rolling['rolling_score']:.1f}  (overall: {stats['average_focus_score']:.1f})")
        print(f"  Recent Phone:      {rolling['rolling_phone_time']:.1f}s (overall: {stats['average_phone_time']:.1f}s)")
        print(f"  Recent Distract:   {rolling['rolling_distractions']:.1f}  (overall: {stats['average_distractions']:.1f})")
    
    # Personal records
    if records:
        print()
        print("─" * 13 + " PERSONAL RECORDS " + "─" * 13)
        print(f"  Highest Score:           {records['highest_score']}")
        print(f"  Longest Session:         {format_time_mmss(records['longest_session_seconds'])}")
        print(f"  Lowest Phone Time:       {format_time_mmss(records['lowest_phone_time'])}")
        print(f"  Distraction-Free Streak: {records['distraction_free_streak']} sessions")
    
    # Time of day
    if time_of_day:
        print()
        print("─" * 14 + " TIME OF DAY " + "─" * 14)
        for bucket in ["morning", "afternoon", "evening", "night"]:
            if bucket in time_of_day:
                data = time_of_day[bucket]
                print(f"  {bucket.capitalize():12} {data['avg_score']:.1f} avg ({data['count']} sessions)")
    
    print("═" * 47)


def generate_charts(sessions: list[dict], time_of_day: dict) -> None:
    """Generate and save charts to reports/."""
    if not sessions:
        return
    
    REPORTS_DIR.mkdir(exist_ok=True)
    
    session_nums = list(range(1, len(sessions) + 1))
    scores = [s["focus_score"] for s in sessions]
    distractions = [s["distractions"] for s in sessions]
    phone_times = [s["phone_visible_seconds"] for s in sessions]
    
    # Chart style
    plt.style.use("seaborn-v0_8-darkgrid")
    
    # 1. Focus Score over sessions (line chart)
    plt.figure(figsize=(8, 4))
    plt.plot(session_nums, scores, marker="o", linewidth=2, color="#4CAF50")
    plt.fill_between(session_nums, scores, alpha=0.3, color="#4CAF50")
    plt.xlabel("Session")
    plt.ylabel("Focus Score")
    plt.title("Focus Score Over Sessions")
    plt.ylim(0, 105)
    plt.xticks(session_nums)
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "focus_score.png", dpi=100)
    plt.close()
    
    # 2. Distractions per session (bar chart)
    plt.figure(figsize=(8, 4))
    plt.bar(session_nums, distractions, color="#FF9800", edgecolor="#E65100")
    plt.xlabel("Session")
    plt.ylabel("Distractions")
    plt.title("Distractions Per Session")
    plt.xticks(session_nums)
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "distractions.png", dpi=100)
    plt.close()
    
    # 3. Phone visible time per session (bar chart)
    plt.figure(figsize=(8, 4))
    plt.bar(session_nums, phone_times, color="#2196F3", edgecolor="#1565C0")
    plt.xlabel("Session")
    plt.ylabel("Phone Time (seconds)")
    plt.title("Phone Visible Time Per Session")
    plt.xticks(session_nums)
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "phone_time.png", dpi=100)
    plt.close()
    
    # 4. Trends with trend lines (3 subplots)
    if len(sessions) >= 2:
        fig, axes = plt.subplots(1, 3, figsize=(12, 4))
        x = np.array(session_nums)
        
        # Focus score trend
        ax = axes[0]
        ax.plot(x, scores, marker="o", color="#4CAF50", label="Score")
        z = np.polyfit(x, scores, 1)
        p = np.poly1d(z)
        ax.plot(x, p(x), "--", color="#2E7D32", linewidth=2, label="Trend")
        ax.set_xlabel("Session")
        ax.set_ylabel("Score")
        ax.set_title("Focus Score Trend")
        ax.set_ylim(0, 105)
        ax.legend()
        
        # Phone time trend
        ax = axes[1]
        ax.plot(x, phone_times, marker="o", color="#2196F3", label="Phone Time")
        z = np.polyfit(x, phone_times, 1)
        p = np.poly1d(z)
        ax.plot(x, p(x), "--", color="#1565C0", linewidth=2, label="Trend")
        ax.set_xlabel("Session")
        ax.set_ylabel("Seconds")
        ax.set_title("Phone Time Trend")
        ax.legend()
        
        # Distraction trend
        ax = axes[2]
        ax.plot(x, distractions, marker="o", color="#FF9800", label="Distractions")
        z = np.polyfit(x, distractions, 1)
        p = np.poly1d(z)
        ax.plot(x, p(x), "--", color="#E65100", linewidth=2, label="Trend")
        ax.set_xlabel("Session")
        ax.set_ylabel("Count")
        ax.set_title("Distraction Trend")
        ax.legend()
        
        plt.tight_layout()
        plt.savefig(REPORTS_DIR / "trends.png", dpi=100)
        plt.close()
    
    # 5. Time of day chart
    if time_of_day:
        buckets = ["morning", "afternoon", "evening", "night"]
        bucket_scores = []
        bucket_labels = []
        bucket_counts = []
        
        for b in buckets:
            if b in time_of_day:
                bucket_labels.append(b.capitalize())
                bucket_scores.append(time_of_day[b]["avg_score"])
                bucket_counts.append(time_of_day[b]["count"])
        
        if bucket_labels:
            plt.figure(figsize=(8, 4))
            colors = ["#FFC107", "#FF9800", "#FF5722", "#3F51B5"][:len(bucket_labels)]
            bars = plt.bar(bucket_labels, bucket_scores, color=colors, edgecolor="#333")
            plt.xlabel("Time of Day")
            plt.ylabel("Average Focus Score")
            plt.title("Performance by Time of Day")
            plt.ylim(0, 105)
            
            # Add count labels on bars
            for bar, count in zip(bars, bucket_counts):
                plt.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 2,
                    f"n={count}",
                    ha="center",
                    fontsize=9,
                )
            
            plt.tight_layout()
            plt.savefig(REPORTS_DIR / "time_of_day.png", dpi=100)
            plt.close()
    
    # 6. Rolling average chart
    if len(sessions) >= ROLLING_WINDOW:
        plt.figure(figsize=(8, 4))
        
        # Calculate rolling averages for each point
        rolling_scores = []
        for i in range(len(sessions)):
            window_start = max(0, i - ROLLING_WINDOW + 1)
            window = sessions[window_start:i + 1]
            avg = sum(s["focus_score"] for s in window) / len(window)
            rolling_scores.append(avg)
        
        plt.plot(session_nums, scores, marker="o", alpha=0.5, color="#4CAF50", label="Actual")
        plt.plot(session_nums, rolling_scores, linewidth=3, color="#1B5E20", label=f"Rolling Avg ({ROLLING_WINDOW})")
        plt.xlabel("Session")
        plt.ylabel("Focus Score")
        plt.title("Focus Score with Rolling Average")
        plt.ylim(0, 105)
        plt.legend()
        plt.tight_layout()
        plt.savefig(REPORTS_DIR / "rolling_avg.png", dpi=100)
        plt.close()

    # 7. Risk trends (peak + average per session)
    if len(sessions) >= 1 and sessions_have_risk_data(sessions):
        peak_risk = [s["peak_risk_score"] for s in sessions]
        avg_risk = [s["avg_risk_score"] for s in sessions]

        plt.figure(figsize=(8, 4))
        plt.plot(session_nums, peak_risk, marker="o", linewidth=2, color="#F44336", label="Peak Risk")
        plt.plot(session_nums, avg_risk, marker="s", linewidth=2, color="#FF5722", label="Avg Risk")
        plt.axhline(y=33, color="#4CAF50", linestyle="--", alpha=0.5, label="LOW/MEDIUM")
        plt.axhline(y=66, color="#FF9800", linestyle="--", alpha=0.5, label="MEDIUM/HIGH")
        plt.xlabel("Session")
        plt.ylabel("Risk Score")
        plt.title("Distraction Risk Over Sessions")
        plt.ylim(0, 105)
        plt.xticks(session_nums)
        plt.legend()
        plt.tight_layout()
        plt.savefig(REPORTS_DIR / "risk_trends.png", dpi=100)
        plt.close()

        if len(sessions) >= 2:
            fig, axes = plt.subplots(1, 2, figsize=(10, 4))
            x = np.array(session_nums)

            for ax, values, title, color in [
                (axes[0], peak_risk, "Peak Risk Trend", "#C62828"),
                (axes[1], avg_risk, "Average Risk Trend", "#E64A19"),
            ]:
                ax.plot(x, values, marker="o", color=color, label="Risk")
                z = np.polyfit(x, values, 1)
                p = np.poly1d(z)
                ax.plot(x, p(x), "--", color=color, alpha=0.7, linewidth=2, label="Trend")
                ax.set_xlabel("Session")
                ax.set_ylabel("Score")
                ax.set_title(title)
                ax.set_ylim(0, 105)
                ax.legend()

            plt.tight_layout()
            plt.savefig(REPORTS_DIR / "risk_trend_lines.png", dpi=100)
            plt.close()

    if len(sessions) >= 1 and sessions_have_gaze_data(sessions):
        gaze_away = [s["gaze_away_seconds"] for s in sessions]
        gaze_events = [s["gaze_distractions"] for s in sessions]

        fig, axes = plt.subplots(1, 2, figsize=(10, 4))
        axes[0].bar(session_nums, gaze_away, color="#9C27B0", edgecolor="#6A1B9A")
        axes[0].set_xlabel("Session")
        axes[0].set_ylabel("Seconds")
        axes[0].set_title("Gaze Away Time per Session")
        axes[0].set_xticks(session_nums)

        axes[1].bar(session_nums, gaze_events, color="#673AB7", edgecolor="#4527A0")
        axes[1].set_xlabel("Session")
        axes[1].set_ylabel("Events")
        axes[1].set_title("Gaze Distractions per Session")
        axes[1].set_xticks(session_nums)

        plt.tight_layout()
        plt.savefig(REPORTS_DIR / "gaze_metrics.png", dpi=100)
        plt.close()
    
    print(f"  Charts saved to {REPORTS_DIR}/")
    print()


def main() -> None:
    """Run analytics."""
    sessions = load_sessions()
    
    # Calculate all analytics
    stats = calculate_stats(sessions)
    trends = calculate_trends(sessions)
    rolling = calculate_rolling_averages(sessions)
    records = calculate_personal_records(sessions)
    time_of_day = analyze_time_of_day(sessions)
    risk_trends = calculate_risk_trends(sessions)
    risk_stats = calculate_risk_stats(sessions)
    
    # Output
    print_summary(
        stats, trends, rolling, records, time_of_day,
        risk_trends=risk_trends or None,
        risk_stats=risk_stats or None,
    )
    generate_charts(sessions, time_of_day)


if __name__ == "__main__":
    main()
