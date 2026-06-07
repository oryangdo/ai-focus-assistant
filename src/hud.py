"""OpenCV HUD overlays for the webcam focus session."""

import cv2

from src.gaze_tracker import GazeState, GazeStatus
from src.pomodoro import PomodoroTimer, SessionData
from src.risk_estimator import DistractionWarning, RiskEstimate

DASHBOARD_FONT = cv2.FONT_HERSHEY_SIMPLEX
DASHBOARD_MARGIN = 12


def draw_unified_dashboard(
    frame,
    *,
    timer: PomodoroTimer,
    phone_detected: bool,
    risk: RiskEstimate | None,
    gaze: GazeState,
    fps: float,
    object_count: int,
) -> None:
    """Draw the top-right session HUD."""
    font = DASHBOARD_FONT
    scale = 0.55
    thickness = 1
    line_height = 24
    pad = 12
    dot_radius = 6

    white = (255, 255, 255)
    gray = (160, 160, 160)
    green = (80, 200, 80)
    amber = (80, 180, 255)
    red = (80, 80, 255)
    dark_bg = (40, 40, 40)

    mode_color = green if timer.mode_str == "FOCUS" else amber
    phone_color = amber if phone_detected else gray

    if risk is None:
        risk_color = gray
        risk_text = "---"
    else:
        risk_text = risk.level_str
        if risk.level_str == "LOW":
            risk_color = green
        elif risk.level_str == "MEDIUM":
            risk_color = amber
        else:
            risk_color = red

    if gaze.status == GazeStatus.LOOKING_AWAY:
        gaze_text = "AWAY"
        gaze_color = amber if timer.mode_str == "FOCUS" else None
    elif gaze.status == GazeStatus.LOOKING_FORWARD:
        gaze_text = "FWD"
        gaze_color = green if timer.mode_str == "FOCUS" else None
    elif gaze.status == GazeStatus.CALIBRATING:
        gaze_text = "CAL"
        gaze_color = gray if timer.mode_str == "FOCUS" else None
    else:
        gaze_text = "NO FACE"
        gaze_color = gray if timer.mode_str == "FOCUS" else None

    rows = [
        (timer.mode_str, timer.time_remaining_str, mode_color),
        ("Phone", f"{timer.distraction_count} hits", phone_color if phone_detected else None),
        ("Gaze", f"{gaze_text} ({gaze.gaze_distraction_count})", gaze_color),
        ("Risk", risk_text, risk_color if timer.mode_str == "FOCUS" else None),
        ("FPS", f"{fps:.1f}", None),
        ("Objects", str(object_count), None),
    ]

    max_label_w = 0
    max_value_w = 0
    for label, value, _ in rows:
        (lw, _), _ = cv2.getTextSize(label, font, scale, thickness)
        (vw, _), _ = cv2.getTextSize(value, font, scale, thickness)
        max_label_w = max(max_label_w, lw)
        max_value_w = max(max_value_w, vw)

    col_gap = 20
    dot_space = dot_radius * 2 + 8
    panel_w = dot_space + max_label_w + col_gap + max_value_w + pad * 2
    panel_h = len(rows) * line_height + pad * 2

    _h_frame, w_frame = frame.shape[:2]
    x_right = w_frame - DASHBOARD_MARGIN
    x_left = x_right - panel_w
    y_top = DASHBOARD_MARGIN

    cv2.rectangle(frame, (x_left, y_top), (x_right, y_top + panel_h), dark_bg, -1)
    cv2.rectangle(frame, (x_left, y_top), (x_right, y_top + panel_h), (100, 100, 100), 1)

    cy = y_top + pad + line_height // 2 + 4
    for label, value, dot_color in rows:
        dot_x = x_left + pad + dot_radius
        if dot_color is not None:
            cv2.circle(frame, (dot_x, cy - 4), dot_radius, dot_color, -1)

        label_x = x_left + pad + dot_space
        cv2.putText(frame, label, (label_x, cy), font, scale, white, thickness, cv2.LINE_AA)

        (vw, _), _ = cv2.getTextSize(value, font, scale, thickness)
        value_x = x_right - pad - vw
        cv2.putText(frame, value, (value_x, cy), font, scale, gray, thickness, cv2.LINE_AA)

        cy += line_height


def draw_warning_banner(frame, warning: DistractionWarning) -> None:
    """Draw a bottom-centered proactive distraction warning."""
    font = DASHBOARD_FONT
    scale = 0.6
    thickness = 2
    pad = 10

    alert = warning.severity == "alert"
    bg = (40, 40, 80) if alert else (50, 50, 40)
    border = (80, 80, 255) if alert else (80, 180, 255)
    text_color = (220, 220, 255) if alert else (220, 220, 200)

    (tw, th), _ = cv2.getTextSize(warning.message, font, scale, thickness)
    h_frame, w_frame = frame.shape[:2]
    panel_w = tw + pad * 2
    panel_h = th + pad * 2
    x_left = (w_frame - panel_w) // 2
    y_top = h_frame - panel_h - DASHBOARD_MARGIN

    cv2.rectangle(frame, (x_left, y_top), (x_left + panel_w, y_top + panel_h), bg, -1)
    cv2.rectangle(frame, (x_left, y_top), (x_left + panel_w, y_top + panel_h), border, 2)
    cv2.putText(
        frame,
        warning.message,
        (x_left + pad, y_top + pad + th),
        font,
        scale,
        text_color,
        thickness,
        cv2.LINE_AA,
    )


def draw_session_summary(frame, session: SessionData) -> None:
    """Draw a centered session summary overlay."""
    font = DASHBOARD_FONT
    scale = 0.65
    thickness = 2
    line_height = 28
    pad = 16

    phone_mins, phone_secs = divmod(int(session.phone_visible_seconds), 60)
    phone_time_str = f"{phone_mins}:{phone_secs:02d}"
    gaze_mins, gaze_secs = divmod(int(session.gaze_away_seconds), 60)
    gaze_time_str = f"{gaze_mins}:{gaze_secs:02d}"

    lines = [
        "SESSION COMPLETE",
        f"Score: {session.focus_score}",
        f"Distractions: {session.distractions}",
        f"Phone Time: {phone_time_str}",
        f"Gaze Away: {gaze_time_str} ({session.gaze_distractions} events)",
    ]

    max_w = 0
    for line in lines:
        (tw, _), _ = cv2.getTextSize(line, font, scale, thickness)
        max_w = max(max_w, tw)

    panel_w = max_w + pad * 2
    panel_h = len(lines) * line_height + pad * 2

    h_frame, w_frame = frame.shape[:2]
    x_left = (w_frame - panel_w) // 2
    y_top = (h_frame - panel_h) // 2

    cv2.rectangle(frame, (x_left, y_top), (x_left + panel_w, y_top + panel_h), (40, 60, 40), -1)
    cv2.rectangle(frame, (x_left, y_top), (x_left + panel_w, y_top + panel_h), (80, 200, 80), 2)

    white = (255, 255, 255)
    green = (80, 200, 80)
    cy = y_top + pad + line_height - 6
    for i, line in enumerate(lines):
        (tw, _), _ = cv2.getTextSize(line, font, scale, thickness)
        tx = x_left + (panel_w - tw) // 2
        color = green if i == 0 else white
        cv2.putText(frame, line, (tx, cy), font, scale, color, thickness, cv2.LINE_AA)
        cy += line_height
