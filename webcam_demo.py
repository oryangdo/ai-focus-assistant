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
PHONE_CONFIDENCE_THRESHOLD = 0.75
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


def draw_dashboard_overlay(
    frame,
    *,
    fps: float,
    object_count: int,
    class_counts: dict[str, int],
) -> None:
    """
    Draw a lightweight stats panel over the webcam image.

    A dark rectangle plus light border improve contrast; text lists FPS, raw object
    count, then one line per class (name: instances). Anchored TOP-RIGHT so it
    does not cover the PHONE DETECTED banner on the left.
    """
    lines: list[str] = [f"FPS: {fps:.1f}", f"Objects: {object_count}"]
    if class_counts:
        lines.append("-" * 14)
        for name, cnt in class_counts.items():
            lines.append(f"{name}: {cnt}")

    text_metrics = []
    max_w = 0
    for line in lines:
        (tw, th), baseline = cv2.getTextSize(
            line, DASHBOARD_FONT, DASHBOARD_SCALE, DASHBOARD_THICKNESS
        )
        text_metrics.append((line, tw, th, baseline))
        max_w = max(max_w, tw)

    gap = DASHBOARD_LINE_GAP
    if text_metrics:
        content_h = sum(t[2] + t[3] for t in text_metrics)
        content_h += gap * (len(text_metrics) - 1)
    else:
        content_h = 0

    pad = 10
    bg_w = max_w + 2 * pad
    bg_h = content_h + 2 * pad

    _h_frame, w_frame = frame.shape[:2]
    x_right = w_frame - DASHBOARD_MARGIN
    x_left = x_right - bg_w
    y_top = DASHBOARD_MARGIN

    cv2.rectangle(frame, (x_left, y_top), (x_right, y_top + bg_h), (32, 32, 32), thickness=-1)
    cv2.rectangle(frame, (x_left, y_top), (x_right, y_top + bg_h), (200, 200, 200), thickness=1)

    cx = x_left + pad
    cy = y_top + pad
    white = (255, 255, 255)

    for idx, (_line, _tw, th, baseline) in enumerate(text_metrics):
        cy += th
        cv2.putText(
            frame,
            text_metrics[idx][0],
            (cx, cy),
            DASHBOARD_FONT,
            DASHBOARD_SCALE,
            white,
            DASHBOARD_THICKNESS,
            cv2.LINE_AA,
        )
        cy += baseline
        if idx < len(text_metrics) - 1:
            cy += gap


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


def draw_phone_warning(frame) -> None:
    """Draw a bold red banner on the frame (modifies frame in place)."""
    text = "PHONE DETECTED"
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 1.2
    thickness = 3

    (text_width, text_height), baseline = cv2.getTextSize(
        text, font, scale, thickness
    )
    padding = 12
    x, y = 20, 30 + text_height

    # Filled red rectangle behind the text
    cv2.rectangle(
        frame,
        (x - padding, y - text_height - padding),
        (x + text_width + padding, y + baseline + padding),
        (0, 0, 255),
        -1,
    )
    cv2.putText(
        frame,
        text,
        (x, y),
        font,
        scale,
        (255, 255, 255),
        thickness,
        cv2.LINE_AA,
    )


def main() -> None:
    # --- 1. Load the YOLO model ---
    # On first run, Ultralytics downloads yolov8s.pt automatically.
    print(f"Loading YOLO model: {MODEL_PATH} ...")
    model = YOLO(MODEL_PATH)
    print("Model ready. Starting webcam.")

    # --- 2. Open the webcam (same as before) ---
    cap = cv2.VideoCapture(1)

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

            if phone_streak >= PHONE_STREAK_REQUIRED:
                draw_phone_warning(annotated_frame)

            # --- 7. Timing + FPS overlay ---
            # Seconds spent on everything above (capture through overlays).
            elapsed = max(time.monotonic() - loop_start, 1e-9)
            instant_fps = 1.0 / elapsed
            if fps_smooth is None:
                fps_smooth = instant_fps
            else:
                fps_smooth = (
                    FPS_SMOOTHING * fps_smooth + (1 - FPS_SMOOTHING) * instant_fps
                )

            # --- 8. Dashboard panel (FPS + counts / last so text stays readable) ---
            draw_dashboard_overlay(
                annotated_frame,
                fps=fps_smooth,
                object_count=object_count,
                class_counts=class_counts,
            )

            cv2.imshow(WINDOW_NAME, annotated_frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
