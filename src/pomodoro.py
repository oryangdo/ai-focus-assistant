"""
Pomodoro timer module for focus sessions.

Provides a simple state machine for 25-minute focus sessions
followed by 5-minute breaks, with session tracking.
"""

import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class PomodoroMode(Enum):
    FOCUS = "FOCUS"
    BREAK = "BREAK"


@dataclass
class SessionData:
    """Data for a completed focus session."""
    timestamp: str
    duration_seconds: float
    distractions: int
    phone_visible_seconds: float
    focus_score: int
    peak_risk_score: int = 0
    avg_risk_score: int = 0
    gaze_distractions: int = 0
    gaze_away_seconds: float = 0.0


class PomodoroTimer:
    """
    A Pomodoro timer that tracks focus/break sessions.
    
    Call update() each frame to advance the timer.
    Call add_distraction() when a distraction is detected.
    Call add_phone_time(delta) to accumulate phone visibility.
    """
    
    FOCUS_DURATION = 25 * 60  # 25 minutes in seconds
    BREAK_DURATION = 5 * 60   # 5 minutes in seconds

    # Focus score weights (100 minus penalties, clamped to [0, 100])
    FOCUS_SCORE_PHONE_RATIO_WEIGHT = 50       # major: phone time share of session
    FOCUS_SCORE_PHONE_DISTRACTION_WEIGHT = 5  # major: per phone distraction event
    FOCUS_SCORE_GAZE_DISTRACTION_WEIGHT = 2   # minor: per 5+ sec gaze-away event
    FOCUS_SCORE_GAZE_AWAY_RATIO_WEIGHT = 25   # minor: gaze-away time share of session
    
    def __init__(self, auto_start: bool = True):
        self.mode = PomodoroMode.FOCUS
        self.time_remaining = self.FOCUS_DURATION
        self.distraction_count = 0
        self.phone_visible_seconds = 0.0
        self.running = auto_start
        self._last_update = time.monotonic() if auto_start else None
        self._session_start = datetime.now()
        self._last_session_data: SessionData | None = None
        # Risk tracking
        self._last_phone_time: float | None = None  # monotonic time of last phone detection
        self._risk_scores: list[int] = []  # samples for averaging
        self.gaze_distraction_count = 0
        self.gaze_away_seconds = 0.0
    
    def update(self) -> SessionData | None:
        """
        Advance the timer based on elapsed real time.
        Returns SessionData if a focus session just completed, else None.
        """
        if not self.running:
            return None
        
        now = time.monotonic()
        if self._last_update is not None:
            elapsed = now - self._last_update
            self.time_remaining -= elapsed
        self._last_update = now
        
        if self.time_remaining <= 0:
            return self._switch_mode()
        return None
    
    def _switch_mode(self) -> SessionData | None:
        """Toggle between FOCUS and BREAK modes. Returns session data if focus ended."""
        session_data = None
        
        if self.mode == PomodoroMode.FOCUS:
            session_data = self._create_session_data()
            self._last_session_data = session_data
            self.mode = PomodoroMode.BREAK
            self.time_remaining = self.BREAK_DURATION
        else:
            self.mode = PomodoroMode.FOCUS
            self.time_remaining = self.FOCUS_DURATION
            self._reset_session_tracking()
        
        return session_data
    
    def _create_session_data(self) -> SessionData:
        """Create session data from current tracking."""
        duration = self._get_elapsed_seconds()
        score = self._calculate_focus_score(duration)
        peak_risk = max(self._risk_scores) if self._risk_scores else 0
        avg_risk = int(sum(self._risk_scores) / len(self._risk_scores)) if self._risk_scores else 0
        return SessionData(
            timestamp=self._session_start.isoformat(timespec="seconds"),
            duration_seconds=round(duration, 1),
            distractions=self.distraction_count,
            phone_visible_seconds=round(self.phone_visible_seconds, 1),
            focus_score=score,
            peak_risk_score=peak_risk,
            avg_risk_score=avg_risk,
            gaze_distractions=self.gaze_distraction_count,
            gaze_away_seconds=round(self.gaze_away_seconds, 1),
        )
    
    def _get_elapsed_seconds(self) -> float:
        """Get seconds elapsed since session started."""
        return (datetime.now() - self._session_start).total_seconds()
    
    def _calculate_focus_score(self, duration: float) -> int:
        """
        Calculate focus score 0-100 from phone and gaze behavior.

        Formula (penalties subtracted from 100, result clamped to [0, 100]):

            phone_ratio_penalty       = (phone_visible_seconds / duration) * 50
            phone_distraction_penalty = distractions * 5
            gaze_event_penalty        = gaze_distraction_count * 2
            gaze_away_ratio_penalty   = (gaze_away_seconds / duration) * 25

        Phone penalties are the largest contributors; gaze penalties are smaller.
        """
        if duration <= 0:
            return 100

        phone_ratio_penalty = (
            self.phone_visible_seconds / duration
        ) * self.FOCUS_SCORE_PHONE_RATIO_WEIGHT
        phone_distraction_penalty = (
            self.distraction_count * self.FOCUS_SCORE_PHONE_DISTRACTION_WEIGHT
        )
        gaze_event_penalty = (
            self.gaze_distraction_count * self.FOCUS_SCORE_GAZE_DISTRACTION_WEIGHT
        )
        gaze_away_ratio_penalty = (
            self.gaze_away_seconds / duration
        ) * self.FOCUS_SCORE_GAZE_AWAY_RATIO_WEIGHT

        score = (
            100
            - phone_ratio_penalty
            - phone_distraction_penalty
            - gaze_event_penalty
            - gaze_away_ratio_penalty
        )
        return max(0, min(100, int(score)))
    
    def _reset_session_tracking(self) -> None:
        """Reset tracking for a new focus session."""
        self.distraction_count = 0
        self.phone_visible_seconds = 0.0
        self._session_start = datetime.now()
        self._last_session_data = None
        self._last_phone_time = None
        self._risk_scores = []
        self.gaze_distraction_count = 0
        self.gaze_away_seconds = 0.0
    
    def add_distraction(self) -> None:
        """Increment the distraction counter (only during focus mode)."""
        if self.mode == PomodoroMode.FOCUS:
            self.distraction_count += 1
    
    def add_phone_time(self, seconds: float) -> None:
        """Add to phone visible time (only during focus mode)."""
        if self.mode == PomodoroMode.FOCUS:
            self.phone_visible_seconds += seconds
    
    def mark_phone_detected(self) -> None:
        """Mark that phone was just detected (for risk calculation)."""
        self._last_phone_time = time.monotonic()
    
    def record_risk_score(self, score: int) -> None:
        """Record a risk score sample (only during focus mode)."""
        if self.mode == PomodoroMode.FOCUS:
            self._risk_scores.append(score)

    def sync_gaze_metrics(self, gaze_away_seconds: float, gaze_distraction_count: int) -> None:
        """Copy gaze totals from GazeTracker (only during focus mode)."""
        if self.mode == PomodoroMode.FOCUS:
            self.gaze_away_seconds = gaze_away_seconds
            self.gaze_distraction_count = gaze_distraction_count
    
    @property
    def elapsed_seconds(self) -> float:
        """Get seconds elapsed since session started."""
        return self._get_elapsed_seconds()
    
    @property
    def seconds_since_phone(self) -> float | None:
        """Get seconds since phone was last detected (None if never)."""
        if self._last_phone_time is None:
            return None
        return time.monotonic() - self._last_phone_time
    
    def end_session_early(self) -> SessionData | None:
        """Force end the current focus session early. Returns session data if in focus mode."""
        if self.mode != PomodoroMode.FOCUS:
            return None
        self.time_remaining = 0
        return self._switch_mode()
    
    def get_current_session_data(self) -> SessionData | None:
        """Get session data for current focus session (for saving on quit)."""
        if self.mode != PomodoroMode.FOCUS:
            return None
        return self._create_session_data()
    
    def start(self) -> None:
        """Start or resume the timer."""
        if not self.running:
            self.running = True
            self._last_update = time.monotonic()
    
    def pause(self) -> None:
        """Pause the timer."""
        self.running = False
        self._last_update = None
    
    def reset(self) -> None:
        """Reset to a fresh focus session."""
        self.mode = PomodoroMode.FOCUS
        self.time_remaining = self.FOCUS_DURATION
        self._reset_session_tracking()
        if self.running:
            self._last_update = time.monotonic()
    
    @property
    def time_remaining_str(self) -> str:
        """Return remaining time as MM:SS string."""
        seconds = max(0, int(self.time_remaining))
        minutes, secs = divmod(seconds, 60)
        return f"{minutes:02d}:{secs:02d}"
    
    @property
    def mode_str(self) -> str:
        """Return the current mode as a string."""
        return self.mode.value
    
    @property
    def last_session(self) -> SessionData | None:
        """Return the most recently completed session data."""
        return self._last_session_data
