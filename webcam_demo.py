"""
Real-time object detection from your webcam using YOLO.

Detects all COCO classes and draws boxes/labels/scores like before.
Shows "PHONE DETECTED" only after repeated high-confidence phone frames.
Draws a small FPS + detection summary panel on top of the video.

To run, paste:
cd /Users/orlandoyang/Downloads/summer_project
source .venv/bin/activate
python src/webcam_demo.py

Press 'q' to quit.
"""

import time
from collections import Counter

import cv2
from ultralytics import YOLO

from src.pomodoro import PomodoroTimer

# yolov8s = "small" — better accuracy than nano, still reasonable for webcam
MODEL_PATH = "yolov8s.pt"

# Minimum confidence for ANY box to be returned by YOLO (0.0–1.0).
# Below this score, predictions are discarded before drawing / HUD / phone checks.
# Raising this trims weak guesses (e.g. background mistaken for something rare)
# without banning specific class names like "refrigerator".
DETECTION_CONFIDENCE_THRESHOLD = 0.60

# Optional future hook: add class names here if you ever want to hide certain
# labels from the UI. Leave empty — all classes that pass the threshold stay visible.
IGNORED_CLASSES: list[str] = []

# COCO dataset label for smartphones (used by default YOLO weights)
PHONE_CLASS_NAME = "cell phone"
# Only count toward the streak if at least one "cell phone" box is this
# confident or higher (0.0–1.0 inclusive).
PHONE_CONFIDENCE_THRESHOLD = 0.50
# Banner appears when this streak reaches the required count.
PHONE_STREAK_REQUIRED = 5
# On a frame without a qualifying phone:
# - False: streak goes back to 0 (strict "5 consecutive frames").
# - True:  streak drops by PHONE_STREAK_DECAY (more forgiving if YOLO flickers).
PHONE_STREAK_USE_DECAY = False
PHONE_STREAK_DECAY = 1

WINDOW_NAME = "YOLO Webcam"

# FPS overlay: exponential smoothing (higher = steadier FPS number on screen).
FPS_SMOOTHING = 0.9

# HUD (heads-up dashboard) typography
DASHBOARD_FONT = cv2.FONT_HERSHEY_SIMPLEX
DASHBOARD_SCALE = 0.55
DASHBOARD_THICKNESS = 1
DASHBOARD_MARGIN = 12
DASHBOARD_LINE_GAP = 22


def tally_detections(result, class_names: dict[int, str]) -> tuple[int, dict[str, int]]:
    """
    Total box count plus per-class totals for this frame.

    Each bounding box contributes one tally to its class label. Sorting alphabetically
    by class name keeps the list from jumping around visually every frame.
    """
    if result.boxes is None or len(result.boxes) == 0:
        return 0, {}

    labels = [class_names[int(cid)] for cid in result.boxes.cls]
    counts = Counter(labels)
    total = sum(counts.values())
    sorted_counts = dict(sorted(counts.items()))
    return total, sorted_counts


def draw_unified_dashboard(
    frame,
    *,
    timer: PomodoroTimer,
    phone_detected: bool,
    fps: float,
    object_count: int,
) -> None:
    """
    Draw a single unified dashboard panel (top-right).
    
    Combines focus timer, phone status, FPS, and object count into one clean panel.
    Uses status indicator dots instead of aggressive banners.
    """
    font = DASHBOARD_FONT
    scale = 0.55
    thickness = 1
    line_height = 24
    pad = 12
    dot_radius = 6
    
    # Colors
    white = (255, 255, 255)
    gray = (160, 160, 160)
    green = (80, 200, 80)      # Focus mode / OK status
    amber = (80, 180, 255)     # Break mode / Phone detected (BGR: orange-ish)
    dark_bg = (40, 40, 40)
    
    # Determine mode color
    mode_color = green if timer.mode_str == "FOCUS" else amber
    phone_color = amber if phone_detected else gray
    
    # Build rows: (label, value, dot_color or None)
    rows = [
        (timer.mode_str, timer.time_remaining_str, mode_color),
        ("Phone", f"{timer.distraction_count} hits", phone_color if phone_detected else None),
        ("FPS", f"{fps:.1f}", None),
        ("Objects", str(object_count), None),
    ]
    
    # Measure text to determine panel width
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
    
    # Position (top-right)
    _h_frame, w_frame = frame.shape[:2]
    x_right = w_frame - DASHBOARD_MARGIN
    x_left = x_right - panel_w
    y_top = DASHBOARD_MARGIN
    
    # Draw background
    cv2.rectangle(frame, (x_left, y_top), (x_right, y_top + panel_h), dark_bg, -1)
    cv2.rectangle(frame, (x_left, y_top), (x_right, y_top + panel_h), (100, 100, 100), 1)
    
    # Draw rows
    cy = y_top + pad + line_height // 2 + 4
    for label, value, dot_color in rows:
        # Status dot (if any)
        dot_x = x_left + pad + dot_radius
        if dot_color is not None:
            cv2.circle(frame, (dot_x, cy - 4), dot_radius, dot_color, -1)
        
        # Label (left-aligned after dot space)
        label_x = x_left + pad + dot_space
        cv2.putText(frame, label, (label_x, cy), font, scale, white, thickness, cv2.LINE_AA)
        
        # Value (right-aligned)
        (vw, _), _ = cv2.getTextSize(value, font, scale, thickness)
        value_x = x_right - pad - vw
        cv2.putText(frame, value, (value_x, cy), font, scale, gray, thickness, cv2.LINE_AA)
        
        cy += line_height


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


def main() -> None:
    # --- 1. Load the YOLO model ---
    # On first run, Ultralytics downloads yolov8s.pt automatically.
    print(f"Loading YOLO model: {MODEL_PATH} ...")
    model = YOLO(MODEL_PATH)
    print("Model ready. Starting webcam.")

    # --- 2. Open the webcam (same as before) ---
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        raise RuntimeError(
            "Could not open webcam. Check that a camera is connected and "
            "no other app is using it exclusively."
        )

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)

    # Built from qualifying frames; decays when a frame has no strong phone hit.
    phone_streak = 0

    # Running smoothed FPS (updated once per loop — measures webcam read + YOLO + drawing).
    fps_smooth: float | None = None

    # Pomodoro timer for focus sessions
    pomodoro = PomodoroTimer(auto_start=True)
    # Track if we already counted this phone detection event
    phone_distraction_counted = False

    try:
        while True:
            loop_start = time.monotonic()

            ok, frame = cap.read()
            if not ok:
                print("Failed to read frame from webcam.")
                break

            # --- 3. Run YOLO on this frame ---
            # conf= filters low-confidence boxes globally (default in Ultralytics is lower).
            # model(...) returns a list; we only have one image, so use [0].
            # verbose=False keeps the terminal quiet on every frame.
            results = model(
                frame,
                conf=DETECTION_CONFIDENCE_THRESHOLD,
                verbose=False,
            )
            result = results[0]

            # --- 4. Summarize detections for the HUD (counts per class name) ---
            object_count, class_counts = tally_detections(result, model.names)

            # --- 5. Draw boxes, class names, and confidence scores ---
            # plot() returns a new image with annotations drawn on it.
            annotated_frame = result.plot()

            # --- 6. Phone alert logic (threshold + streak + decay) ---
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
                # Count as distraction once per phone detection event
                if not phone_distraction_counted:
                    pomodoro.add_distraction()
                    phone_distraction_counted = True
            else:
                # Reset flag when phone is no longer detected
                phone_distraction_counted = False

            # --- 7. Pomodoro timer update ---
            pomodoro.update()

            # --- 8. Timing + FPS calculation ---
            elapsed = max(time.monotonic() - loop_start, 1e-9)
            instant_fps = 1.0 / elapsed
            if fps_smooth is None:
                fps_smooth = instant_fps
            else:
                fps_smooth = (
                    FPS_SMOOTHING * fps_smooth + (1 - FPS_SMOOTHING) * instant_fps
                )

            # --- 9. Unified dashboard (top-right) ---
            draw_unified_dashboard(
                annotated_frame,
                timer=pomodoro,
                phone_detected=phone_detected,
                fps=fps_smooth,
                object_count=object_count,
            )

            cv2.imshow(WINDOW_NAME, annotated_frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
