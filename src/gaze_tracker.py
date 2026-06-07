"""
Lightweight gaze / head-pose tracking using MediaPipe Face Landmarker.

Calibrates your neutral "looking at screen" pose at the start of each focus
session, then flags look-away only when head pose deviates from that baseline.
Counts a gaze distraction only after 5+ continuous seconds looking away.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from statistics import median
from urllib.request import urlretrieve

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_tasks
from mediapipe.tasks.python import vision


MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "face_landmarker/face_landmarker/float16/1/face_landmarker.task"
)
MODEL_PATH = Path(__file__).parent.parent / "models" / "face_landmarker.task"


class GazeStatus(Enum):
    CALIBRATING = "CALIBRATING"
    LOOKING_FORWARD = "LOOKING_FORWARD"
    LOOKING_AWAY = "LOOKING_AWAY"
    NO_FACE = "NO_FACE"


@dataclass
class GazeState:
    """Current gaze metrics for HUD and session logging."""
    status: GazeStatus
    gaze_away_seconds: float
    gaze_distraction_count: int
    continuous_away_seconds: float

    @property
    def status_str(self) -> str:
        return self.status.value


def _ensure_model() -> Path:
    """Download the face landmarker model on first run if needed."""
    if MODEL_PATH.exists():
        return MODEL_PATH

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading face landmarker model to {MODEL_PATH} ...")
    urlretrieve(MODEL_URL, MODEL_PATH)
    print("Face landmarker model ready.")
    return MODEL_PATH


class GazeTracker:
    """
    Tracks head pose and accumulates gaze-away time during focus sessions.

    Call update() each frame with the raw BGR webcam frame.
    """

    DISTRACTION_THRESHOLD_SECONDS = 5.0
    CALIBRATION_SECONDS = 3.0
    MIN_CALIBRATION_SAMPLES = 12

    # Deviation from personal baseline required to count as away
    YAW_DEVIATION_THRESHOLD = 0.22
    PITCH_DEVIATION_THRESHOLD = 0.19
    CHIN_DEVIATION_THRESHOLD = 0.26

    # Sustained deviation before switching state (reduces flicker)
    AWAY_CONFIRM_SECONDS = 0.9
    FORWARD_CONFIRM_SECONDS = 0.35

    def __init__(self) -> None:
        model_path = _ensure_model()
        base_options = mp_tasks.BaseOptions(model_asset_path=str(model_path))
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_faces=1,
        )
        self._landmarker = vision.FaceLandmarker.create_from_options(options)
        self._frame_timestamp_ms = 0
        self.reset_session()

    def reset_session(self) -> None:
        """Reset per-session gaze counters (call when a new focus session starts)."""
        self.gaze_away_seconds = 0.0
        self.gaze_distraction_count = 0
        self._continuous_away_seconds = 0.0
        self._event_counted = False
        self._status = GazeStatus.CALIBRATING
        self._seconds_since_looking_forward: float | None = None
        self._frame_timestamp_ms = 0

        self._calibration_samples: list[tuple[float, float, float]] = []
        self._calibration_seconds = 0.0
        self._baseline_yaw: float | None = None
        self._baseline_pitch: float | None = None
        self._baseline_chin_pitch: float | None = None
        self._calibrated = False

        self._away_streak_seconds = 0.0
        self._forward_streak_seconds = 0.0

    def close(self) -> None:
        """Release MediaPipe resources."""
        self._landmarker.close()

    @property
    def seconds_since_looking_forward(self) -> float | None:
        return self._seconds_since_looking_forward

    def update(
        self,
        frame,
        delta_seconds: float,
        *,
        active: bool,
    ) -> GazeState:
        """Process one frame and update gaze metrics."""
        if not active:
            self._continuous_away_seconds = 0.0
            self._event_counted = False
            self._away_streak_seconds = 0.0
            self._forward_streak_seconds = 0.0
            return self._build_state()

        self._frame_timestamp_ms += max(1, int(delta_seconds * 1000))
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self._landmarker.detect_for_video(mp_image, self._frame_timestamp_ms)

        if not result.face_landmarks:
            self._status = GazeStatus.NO_FACE
            self._away_streak_seconds = 0.0
            self._forward_streak_seconds = 0.0
            return self._build_state()

        ratios = self._pose_ratios(result.face_landmarks[0])
        if ratios is None:
            self._status = GazeStatus.NO_FACE
            return self._build_state()

        if not self._calibrated:
            return self._calibrate(ratios, delta_seconds)

        looking_away = self._classify_looking_away(ratios, delta_seconds)
        self._apply_gaze_state(looking_away, delta_seconds)
        return self._build_state()

    def _calibrate(self, ratios: tuple[float, float, float], delta_seconds: float) -> GazeState:
        """Collect neutral pose samples for the first few seconds of a session."""
        self._calibration_samples.append(ratios)
        self._calibration_seconds += delta_seconds
        self._status = GazeStatus.CALIBRATING

        if (
            self._calibration_seconds >= self.CALIBRATION_SECONDS
            and len(self._calibration_samples) >= self.MIN_CALIBRATION_SAMPLES
        ):
            yaw_vals = [s[0] for s in self._calibration_samples]
            pitch_vals = [s[1] for s in self._calibration_samples]
            chin_vals = [s[2] for s in self._calibration_samples]
            self._baseline_yaw = median(yaw_vals)
            self._baseline_pitch = median(pitch_vals)
            self._baseline_chin_pitch = median(chin_vals)
            self._calibrated = True
            self._status = GazeStatus.LOOKING_FORWARD
            self._seconds_since_looking_forward = 0.0
            print("Gaze calibration complete — neutral pose saved.")

        return self._build_state()

    def _classify_looking_away(
        self,
        ratios: tuple[float, float, float],
        delta_seconds: float,
    ) -> bool:
        """Classify away using deviation from baseline with temporal smoothing."""
        yaw, pitch, chin_pitch = ratios
        assert self._baseline_yaw is not None
        assert self._baseline_pitch is not None
        assert self._baseline_chin_pitch is not None

        yaw_delta = abs(yaw - self._baseline_yaw)
        pitch_delta = abs(pitch - self._baseline_pitch)
        chin_delta = abs(chin_pitch - self._baseline_chin_pitch)

        raw_away = (
            yaw_delta > self.YAW_DEVIATION_THRESHOLD
            or pitch_delta > self.PITCH_DEVIATION_THRESHOLD
            or chin_delta > self.CHIN_DEVIATION_THRESHOLD
        )

        if raw_away:
            self._away_streak_seconds += delta_seconds
            self._forward_streak_seconds = 0.0
        else:
            self._forward_streak_seconds += delta_seconds
            self._away_streak_seconds = 0.0

        if self._status == GazeStatus.LOOKING_AWAY:
            return self._forward_streak_seconds < self.FORWARD_CONFIRM_SECONDS
        return self._away_streak_seconds >= self.AWAY_CONFIRM_SECONDS

    def _apply_gaze_state(self, looking_away: bool, delta_seconds: float) -> None:
        if looking_away:
            self._status = GazeStatus.LOOKING_AWAY
            self.gaze_away_seconds += delta_seconds
            self._continuous_away_seconds += delta_seconds
            self._seconds_since_looking_forward = None

            if (
                self._continuous_away_seconds >= self.DISTRACTION_THRESHOLD_SECONDS
                and not self._event_counted
            ):
                self.gaze_distraction_count += 1
                self._event_counted = True
        else:
            self._status = GazeStatus.LOOKING_FORWARD
            self._continuous_away_seconds = 0.0
            self._event_counted = False
            if self._seconds_since_looking_forward is None:
                self._seconds_since_looking_forward = 0.0
            else:
                self._seconds_since_looking_forward += delta_seconds

    def _build_state(self) -> GazeState:
        return GazeState(
            status=self._status,
            gaze_away_seconds=self.gaze_away_seconds,
            gaze_distraction_count=self.gaze_distraction_count,
            continuous_away_seconds=self._continuous_away_seconds,
        )

    def _pose_ratios(self, landmarks) -> tuple[float, float, float] | None:
        """Return (yaw, pitch, chin_pitch) ratios for head pose."""
        nose = landmarks[1]
        left_cheek = landmarks[234]
        right_cheek = landmarks[454]
        left_eye = landmarks[33]
        right_eye = landmarks[263]
        chin = landmarks[152]

        face_width = abs(right_cheek.x - left_cheek.x)
        if face_width < 1e-6:
            return None

        face_center_x = (left_cheek.x + right_cheek.x) / 2
        yaw_ratio = (nose.x - face_center_x) / face_width

        eye_center_y = (left_eye.y + right_eye.y) / 2
        pitch_ratio = (nose.y - eye_center_y) / face_width
        chin_pitch = (chin.y - eye_center_y) / face_width

        return yaw_ratio, pitch_ratio, chin_pitch
