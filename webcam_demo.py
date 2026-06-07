"""
Real-time object detection from your webcam using YOLO.

Detects all COCO classes and draws boxes/labels/scores like before.
Shows "PHONE DETECTED" only after repeated high-confidence phone frames.
Draws a small FPS + detection summary panel on top of the video.

Press 'q' to quit.
"""

import time
from collections import Counter

import cv2
from ultralytics import YOLO

from src.gaze_tracker import GazeState, GazeStatus, GazeTracker
from src.hud import draw_session_summary, draw_unified_dashboard, draw_warning_banner
from src.pomodoro import PomodoroTimer
from src.risk_estimator import RiskEstimator, RiskEstimate, DistractionWarning
from src.session_logger import ensure_sessions_csv, get_csv_path, log_session

# yolov8s = "small" — better accuracy than nano, still reasonable for webcam
MODEL_PATH = "yolov8s.pt"

# Minimum confidence for ANY box to be returned by YOLO (0.0–1.0).
DETECTION_CONFIDENCE_THRESHOLD = 0.60

# COCO dataset label for smartphones (used by default YOLO weights)
PHONE_CLASS_NAME = "cell phone"
PHONE_CONFIDENCE_THRESHOLD = 0.50
PHONE_STREAK_REQUIRED = 5
PHONE_STREAK_USE_DECAY = False
PHONE_STREAK_DECAY = 1

WINDOW_NAME = "YOLO Webcam"
FPS_SMOOTHING = 0.9
RISK_SAMPLE_INTERVAL = 30  # ~1 second at 30fps


def load_historical_stats() -> tuple[float, float, float, float]:
    """
    Load historical session averages from sessions.csv for risk baselines.

    Returns (avg_distractions, avg_phone_time, avg_gaze_distractions, avg_gaze_away_seconds).
    Missing CSV columns (older schema) default to 0. Falls back to sensible defaults
    when no file or rows exist.
    """
    import csv

    defaults = (2.0, 30.0, 0.5, 20.0)
    csv_path = get_csv_path()
    if not csv_path.exists():
        return defaults

    try:
        ensure_sessions_csv(csv_path)
        with open(csv_path, newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        if not rows:
            return defaults

        n = len(rows)
        avg_distractions = sum(int(r.get("distractions") or 0) for r in rows) / n
        avg_phone_time = sum(float(r.get("phone_visible_seconds") or 0) for r in rows) / n
        avg_gaze_distractions = sum(int(r.get("gaze_distractions") or 0) for r in rows) / n
        avg_gaze_away = sum(float(r.get("gaze_away_seconds") or 0) for r in rows) / n
        return avg_distractions, avg_phone_time, avg_gaze_distractions, avg_gaze_away
    except Exception:
        return defaults


def tally_detections(result, class_names: dict[int, str]) -> tuple[int, dict[str, int]]:
    """Total box count plus per-class totals for this frame."""
    if result.boxes is None or len(result.boxes) == 0:
        return 0, {}

    labels = [class_names[int(cid)] for cid in result.boxes.cls]
    counts = Counter(labels)
    total = sum(counts.values())
    sorted_counts = dict(sorted(counts.items()))
    return total, sorted_counts


def cell_phone_confidences(result, class_names: dict[int, str]) -> list[float]:
    """Confidence score for every box YOLO labeled as a cell phone (may be empty)."""
    if result.boxes is None or len(result.boxes) == 0:
        return []

    scores: list[float] = []
    for class_id, conf in zip(result.boxes.cls, result.boxes.conf, strict=True):
        if class_names[int(class_id)] == PHONE_CLASS_NAME:
            scores.append(float(conf))
    return scores


def frame_qualifies_for_phone_streak(phone_scores: list[float]) -> bool:
    """True if this frame has at least one cell phone at or above the threshold."""
    return any(score >= PHONE_CONFIDENCE_THRESHOLD for score in phone_scores)


def print_cell_phone_debug(phone_scores: list[float]) -> None:
    """Log raw phone confidences so you can compare real phones vs false positives."""
    if not phone_scores:
        return
    formatted = ", ".join(f"{s:.3f}" for s in phone_scores)
    print(f"cell phone confidence: [{formatted}]")


def update_risk_and_warnings(
    *,
    pomodoro: PomodoroTimer,
    risk_estimator: RiskEstimator,
    gaze: GazeState,
    gaze_tracker: GazeTracker,
    phone_detected: bool,
    phone_streak: int,
    risk_sample_counter: int,
    previous_risk_score: int | None,
    current_risk: RiskEstimate | None,
) -> tuple[RiskEstimate | None, DistractionWarning | None, int, int | None]:
    """Sample risk and evaluate proactive warnings during focus mode."""
    if pomodoro.mode_str != "FOCUS":
        return None, None, risk_sample_counter, None

    risk_sample_counter += 1
    if risk_sample_counter < RISK_SAMPLE_INTERVAL:
        return current_risk, None, risk_sample_counter, previous_risk_score

    risk_sample_counter = 0
    new_risk = risk_estimator.calculate(
        elapsed_seconds=pomodoro.elapsed_seconds,
        seconds_since_phone=pomodoro.seconds_since_phone,
        current_distractions=pomodoro.distraction_count,
        current_phone_time=pomodoro.phone_visible_seconds,
        current_gaze_distractions=pomodoro.gaze_distraction_count,
        current_gaze_away_seconds=pomodoro.gaze_away_seconds,
        is_looking_away=gaze.status == GazeStatus.LOOKING_AWAY,
        continuous_gaze_away_seconds=gaze.continuous_away_seconds,
        seconds_since_looking_forward=gaze_tracker.seconds_since_looking_forward,
    )
    pomodoro.record_risk_score(new_risk.score)
    warning = risk_estimator.evaluate_warning(
        new_risk,
        phone_detected=phone_detected,
        phone_streak=phone_streak,
        phone_streak_required=PHONE_STREAK_REQUIRED,
        previous_score=previous_risk_score,
        continuous_gaze_away_seconds=gaze.continuous_away_seconds,
        is_looking_away=gaze.status == GazeStatus.LOOKING_AWAY,
    )
    return new_risk, warning, risk_sample_counter, new_risk.score


def main() -> None:
    print(f"Loading YOLO model: {MODEL_PATH} ...")
    model = YOLO(MODEL_PATH)
    print("Model ready. Starting webcam.")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError(
            "Could not open webcam. Check that a camera is connected and "
            "no other app is using it exclusively."
        )

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)

    phone_streak = 0
    fps_smooth: float | None = None
    pomodoro = PomodoroTimer(auto_start=True)
    gaze_tracker = GazeTracker()
    phone_distraction_counted = False
    last_frame_time = time.monotonic()
    summary_until: float | None = None
    key_buffer = ""

    hist_distractions, hist_phone_time, hist_gaze_events, hist_gaze_away = (
        load_historical_stats()
    )
    risk_estimator = RiskEstimator(
        historical_avg_distractions=hist_distractions,
        historical_avg_phone_time=hist_phone_time,
        historical_avg_gaze_distractions=hist_gaze_events,
        historical_avg_gaze_away_seconds=hist_gaze_away,
    )
    current_risk: RiskEstimate | None = None
    previous_risk_score: int | None = None
    current_warning: DistractionWarning | None = None
    risk_sample_counter = 0
    gaze_state = GazeState(
        status=GazeStatus.NO_FACE,
        gaze_away_seconds=0.0,
        gaze_distraction_count=0,
        continuous_away_seconds=0.0,
    )

    try:
        while True:
            loop_start = time.monotonic()
            frame_delta = loop_start - last_frame_time
            last_frame_time = loop_start

            ok, frame = cap.read()
            if not ok:
                print("Failed to read frame from webcam.")
                break

            in_focus = pomodoro.mode_str == "FOCUS"
            gaze_state = gaze_tracker.update(frame, frame_delta, active=in_focus)
            if in_focus:
                pomodoro.sync_gaze_metrics(
                    gaze_state.gaze_away_seconds,
                    gaze_state.gaze_distraction_count,
                )

            results = model(
                frame,
                conf=DETECTION_CONFIDENCE_THRESHOLD,
                verbose=False,
            )
            result = results[0]
            object_count, _class_counts = tally_detections(result, model.names)
            annotated_frame = result.plot()

            phone_scores = cell_phone_confidences(result, model.names)
            print_cell_phone_debug(phone_scores)

            if frame_qualifies_for_phone_streak(phone_scores):
                phone_streak += 1
            else:
                if PHONE_STREAK_USE_DECAY:
                    phone_streak = max(0, phone_streak - PHONE_STREAK_DECAY)
                else:
                    phone_streak = 0

            phone_detected = phone_streak >= PHONE_STREAK_REQUIRED
            if phone_detected:
                if not phone_distraction_counted:
                    pomodoro.add_distraction()
                    phone_distraction_counted = True
                pomodoro.add_phone_time(frame_delta)
                pomodoro.mark_phone_detected()
            else:
                phone_distraction_counted = False

            session_data = pomodoro.update()
            if session_data is not None:
                log_session(session_data)
                summary_until = time.monotonic() + 5.0
                gaze_tracker.reset_session()
                print(
                    f"Session logged: score={session_data.focus_score}, "
                    f"distractions={session_data.distractions}, "
                    f"phone_time={session_data.phone_visible_seconds:.1f}s, "
                    f"gaze_away={session_data.gaze_away_seconds:.1f}s, "
                    f"gaze_events={session_data.gaze_distractions}, "
                    f"peak_risk={session_data.peak_risk_score}"
                )

            current_risk, current_warning, risk_sample_counter, previous_risk_score = (
                update_risk_and_warnings(
                    pomodoro=pomodoro,
                    risk_estimator=risk_estimator,
                    gaze=gaze_state,
                    gaze_tracker=gaze_tracker,
                    phone_detected=phone_detected,
                    phone_streak=phone_streak,
                    risk_sample_counter=risk_sample_counter,
                    previous_risk_score=previous_risk_score,
                    current_risk=current_risk,
                )
            )
            if pomodoro.mode_str != "FOCUS":
                current_risk = None
                current_warning = None
                previous_risk_score = None

            elapsed = max(time.monotonic() - loop_start, 1e-9)
            instant_fps = 1.0 / elapsed
            if fps_smooth is None:
                fps_smooth = instant_fps
            else:
                fps_smooth = FPS_SMOOTHING * fps_smooth + (1 - FPS_SMOOTHING) * instant_fps

            draw_unified_dashboard(
                annotated_frame,
                timer=pomodoro,
                phone_detected=phone_detected,
                risk=current_risk,
                gaze=gaze_state,
                fps=fps_smooth,
                object_count=object_count,
            )

            if current_warning is not None and in_focus:
                draw_warning_banner(annotated_frame, current_warning)

            if summary_until is not None:
                if time.monotonic() < summary_until:
                    last_session = pomodoro.last_session
                    if last_session is not None:
                        draw_session_summary(annotated_frame, last_session)
                else:
                    summary_until = None

            cv2.imshow(WINDOW_NAME, annotated_frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                session_data = pomodoro.get_current_session_data()
                if session_data is not None:
                    log_session(session_data)
                    print(
                        f"Session saved on quit: score={session_data.focus_score}, "
                        f"duration={session_data.duration_seconds:.0f}s, "
                        f"distractions={session_data.distractions}"
                    )
                break
            elif key != 255:
                key_buffer += chr(key)
                key_buffer = key_buffer[-7:]
                if key_buffer.lower() == "orlando":
                    session_data = pomodoro.end_session_early()
                    if session_data is not None:
                        log_session(session_data)
                        summary_until = time.monotonic() + 5.0
                        gaze_tracker.reset_session()
                        print(
                            f"Session ended early! score={session_data.focus_score}, "
                            f"distractions={session_data.distractions}, "
                            f"phone_time={session_data.phone_visible_seconds:.1f}s"
                        )
                    key_buffer = ""
    finally:
        gaze_tracker.close()
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
