"""OpenCV HUD overlays for the webcam focus session."""

from dataclasses import dataclass

import cv2

from src.gaze_tracker import GazeState, GazeStatus
from src.pomodoro import PomodoroTimer, SessionData
from src.risk_estimator import DistractionWarning, RiskEstimate

DASHBOARD_FONT = cv2.FONT_HERSHEY_SIMPLEX
DASHBOARD_MARGIN = 12


@dataclass
class SummaryOverlayLayout:
    """Clickable regions on the session summary overlay."""
    close_rect: tuple[int, int, int, int]
    dashboard_rect: tuple[int, int, int, int]


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

    if not timer.running and timer.mode_str == "FOCUS":
        timer_label = "READY"
        timer_value = "Press SPACE"
        timer_color = gray
    else:
        timer_label = timer.mode_str
        timer_value = timer.time_remaining_str
        timer_color = mode_color

    rows = [
        (timer_label, timer_value, timer_color),
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


def draw_home_screen(frame) -> None:
    """Draw the start screen shown before the user begins a focus session."""
    font = DASHBOARD_FONT
    title_scale = 0.9
    body_scale = 0.6
    thickness = 2
    line_height = 34
    pad = 20

    lines = [
        "AI Focus Assistant",
        "Press SPACE to start a focus session",
        "Press Q to quit",
    ]

    max_w = 0
    for i, line in enumerate(lines):
        scale = title_scale if i == 0 else body_scale
        (tw, _), _ = cv2.getTextSize(line, font, scale, thickness if i == 0 else 1)
        max_w = max(max_w, tw)

    panel_w = max_w + pad * 2
    panel_h = len(lines) * line_height + pad * 2

    h_frame, w_frame = frame.shape[:2]
    x_left = (w_frame - panel_w) // 2
    y_top = (h_frame - panel_h) // 2

    cv2.rectangle(frame, (x_left, y_top), (x_left + panel_w, y_top + panel_h), (35, 35, 45), -1)
    cv2.rectangle(frame, (x_left, y_top), (x_left + panel_w, y_top + panel_h), (120, 120, 180), 2)

    white = (255, 255, 255)
    accent = (180, 180, 255)
    cy = y_top + pad + line_height - 8
    for i, line in enumerate(lines):
        scale = title_scale if i == 0 else body_scale
        thick = thickness if i == 0 else 1
        (tw, _), _ = cv2.getTextSize(line, font, scale, thick)
        tx = x_left + (panel_w - tw) // 2
        color = accent if i == 0 else white
        cv2.putText(frame, line, (tx, cy), font, scale, color, thick, cv2.LINE_AA)
        cy += line_height


def _point_in_rect(x: int, y: int, rect: tuple[int, int, int, int]) -> bool:
    x1, y1, x2, y2 = rect
    return x1 <= x <= x2 and y1 <= y <= y2


def draw_session_summary(frame, session: SessionData) -> SummaryOverlayLayout:
    """Draw a centered session summary overlay with dismiss and dashboard actions."""
    font = DASHBOARD_FONT
    scale = 0.65
    thickness = 2
    line_height = 28
    pad = 16
    button_h = 34
    button_pad = 10

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
        "ESC to close",
    ]

    max_w = 0
    for line in lines:
        (tw, _), _ = cv2.getTextSize(line, font, scale, thickness)
        max_w = max(max_w, tw)

    dashboard_label = "Open Dashboard"
    (btn_tw, _), _ = cv2.getTextSize(dashboard_label, font, 0.55, 1)
    panel_w = max(max_w, btn_tw + button_pad * 2) + pad * 2
    panel_h = len(lines) * line_height + button_h + pad * 3

    h_frame, w_frame = frame.shape[:2]
    x_left = (w_frame - panel_w) // 2
    y_top = (h_frame - panel_h) // 2
    x_right = x_left + panel_w
    y_bottom = y_top + panel_h

    cv2.rectangle(frame, (x_left, y_top), (x_right, y_bottom), (40, 60, 40), -1)
    cv2.rectangle(frame, (x_left, y_top), (x_right, y_bottom), (80, 200, 80), 2)

    close_size = 18
    close_x2 = x_right - 8
    close_x1 = close_x2 - close_size
    close_y1 = y_top + 8
    close_y2 = close_y1 + close_size
    cv2.rectangle(frame, (close_x1, close_y1), (close_x2, close_y2), (60, 60, 60), -1)
    cv2.putText(
        frame,
        "X",
        (close_x1 + 4, close_y1 + 14),
        font,
        0.5,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )

    white = (255, 255, 255)
    green = (80, 200, 80)
    cy = y_top + pad + line_height - 6
    for i, line in enumerate(lines):
        (tw, _), _ = cv2.getTextSize(line, font, scale, thickness)
        tx = x_left + (panel_w - tw) // 2
        color = green if i == 0 else white
        cv2.putText(frame, line, (tx, cy), font, scale, color, thickness, cv2.LINE_AA)
        cy += line_height

    btn_y1 = y_bottom - pad - button_h
    btn_y2 = y_bottom - pad
    btn_x1 = x_left + pad
    btn_x2 = x_right - pad
    cv2.rectangle(frame, (btn_x1, btn_y1), (btn_x2, btn_y2), (50, 90, 50), -1)
    cv2.rectangle(frame, (btn_x1, btn_y1), (btn_x2, btn_y2), green, 2)
    btn_tx = btn_x1 + ((btn_x2 - btn_x1) - btn_tw) // 2
    btn_ty = btn_y1 + button_h - 10
    cv2.putText(
        frame,
        dashboard_label,
        (btn_tx, btn_ty),
        font,
        0.55,
        white,
        1,
        cv2.LINE_AA,
    )

    return SummaryOverlayLayout(
        close_rect=(close_x1, close_y1, close_x2, close_y2),
        dashboard_rect=(btn_x1, btn_y1, btn_x2, btn_y2),
    )


def summary_hit_test(
    x: int,
    y: int,
    layout: SummaryOverlayLayout,
) -> str | None:
    """Return 'close', 'dashboard', or None for a click on the summary overlay."""
    if _point_in_rect(x, y, layout.close_rect):
        return "close"
    if _point_in_rect(x, y, layout.dashboard_rect):
        return "dashboard"
    return None
