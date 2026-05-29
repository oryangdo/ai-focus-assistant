"""
Pomodoro timer module for focus sessions.

Provides a simple state machine for 25-minute focus sessions
followed by 5-minute breaks.
"""

import time
from enum import Enum


class PomodoroMode(Enum):
    FOCUS = "FOCUS"
    BREAK = "BREAK"


class PomodoroTimer:
    """
    A Pomodoro timer that tracks focus/break sessions.
    
    Call update() each frame to advance the timer.
    Call add_distraction() when a distraction is detected.
    """
    
    FOCUS_DURATION = 25 * 60  # 25 minutes in seconds
    BREAK_DURATION = 5 * 60   # 5 minutes in seconds
    
    def __init__(self, auto_start: bool = True):
        self.mode = PomodoroMode.FOCUS
        self.time_remaining = self.FOCUS_DURATION
        self.distraction_count = 0
        self.running = auto_start
        self._last_update = time.monotonic() if auto_start else None
    
    def update(self) -> None:
        """Advance the timer based on elapsed real time."""
        if not self.running:
            return
        
        now = time.monotonic()
        if self._last_update is not None:
            elapsed = now - self._last_update
            self.time_remaining -= elapsed
        self._last_update = now
        
        if self.time_remaining <= 0:
            self._switch_mode()
    
    def _switch_mode(self) -> None:
        """Toggle between FOCUS and BREAK modes."""
        if self.mode == PomodoroMode.FOCUS:
            self.mode = PomodoroMode.BREAK
            self.time_remaining = self.BREAK_DURATION
        else:
            self.mode = PomodoroMode.FOCUS
            self.time_remaining = self.FOCUS_DURATION
            self.distraction_count = 0  # Reset for new focus session
    
    def add_distraction(self) -> None:
        """Increment the distraction counter (only during focus mode)."""
        if self.mode == PomodoroMode.FOCUS:
            self.distraction_count += 1
    
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
        self.distraction_count = 0
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
