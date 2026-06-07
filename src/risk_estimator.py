"""
Focus risk estimation module.

Provides a heuristic-based risk score estimating likelihood of distraction.
Designed to be modular so it can be replaced with an ML model later.
"""

from dataclasses import dataclass
from enum import Enum


class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass
class RiskEstimate:
    """Risk estimation result."""
    score: int  # 0-100
    level: RiskLevel
    
    @property
    def level_str(self) -> str:
        return self.level.value


@dataclass
class DistractionWarning:
    """Proactive warning before a distraction is logged."""
    message: str
    severity: str  # "caution" or "alert"


class RiskEstimator:
    """
    Estimates distraction risk based on multiple factors.

    Live gaze (Factor 5) reacts to current head pose. Historical gaze baselines
    (Factor 4) compare the current session pace to past gaze_away_seconds and
    gaze_distractions from CSV, and raise early-session baseline risk when the
    user historically looks away often. Phone metrics remain the stronger signal.
    
    This is a heuristic-based implementation. The interface is designed
    so it can be swapped with an ML model later by keeping the same
    calculate() signature.
    """
    
    # Weights for each factor (should sum to 1.0)
    WEIGHT_TIME = 0.18
    WEIGHT_RECENT_PHONE = 0.22
    WEIGHT_CURRENT_DISTRACTIONS = 0.18
    WEIGHT_HISTORICAL = 0.12
    WEIGHT_GAZE = 0.30
    
    # Within the historical factor, phone vs gaze contribution
    HIST_PHONE_WEIGHT = 0.60  # stronger: distractions + phone visible time
    HIST_GAZE_WEIGHT = 0.40   # weaker: gaze events + gaze away time
    
    # Thresholds for risk levels
    THRESHOLD_LOW = 33
    THRESHOLD_MEDIUM = 66
    
    # Parameters for factor calculations
    SESSION_DURATION = 25 * 60  # Expected session length
    PHONE_RECENCY_WINDOW = 30   # Seconds - phone seen within this is "recent"
    MAX_DISTRACTIONS_SCALE = 5  # Distractions at which factor maxes out
    
    def __init__(
        self,
        historical_avg_distractions: float = 2.0,
        historical_avg_phone_time: float = 30.0,
        historical_avg_gaze_distractions: float = 0.5,
        historical_avg_gaze_away_seconds: float = 20.0,
    ):
        """
        Initialize with historical baselines from sessions.csv.

        Args:
            historical_avg_distractions: Average phone distractions per session
            historical_avg_phone_time: Average phone visible seconds per session
            historical_avg_gaze_distractions: Average gaze distraction events per session
            historical_avg_gaze_away_seconds: Average total gaze-away seconds per session
        """
        self.historical_avg_distractions = max(0.1, historical_avg_distractions)
        self.historical_avg_phone_time = max(0.1, historical_avg_phone_time)
        self.historical_avg_gaze_distractions = max(0.1, historical_avg_gaze_distractions)
        self.historical_avg_gaze_away_seconds = max(0.1, historical_avg_gaze_away_seconds)

        # Static baseline: users with high historical gaze-away start sessions riskier
        away_share = self.historical_avg_gaze_away_seconds / self.SESSION_DURATION
        event_share = min(1.0, self.historical_avg_gaze_distractions / 3.0)
        self._historical_gaze_baseline = min(1.0, (away_share * 1.5 + event_share * 0.5) / 2)
    
    def calculate(
        self,
        elapsed_seconds: float,
        seconds_since_phone: float | None,
        current_distractions: int,
        current_phone_time: float,
        *,
        current_gaze_distractions: int = 0,
        current_gaze_away_seconds: float = 0.0,
        is_looking_away: bool = False,
        continuous_gaze_away_seconds: float = 0.0,
        seconds_since_looking_forward: float | None = None,
    ) -> RiskEstimate:
        """
        Calculate current distraction risk.
        
        Args:
            elapsed_seconds: Time elapsed in current session
            seconds_since_phone: Seconds since phone was last detected (None if never)
            current_distractions: Number of phone distractions in current session
            current_phone_time: Total phone visible time in current session
            current_gaze_distractions: Gaze distraction events (5+ sec look-aways) so far
            current_gaze_away_seconds: Total seconds looking away so far this session
            is_looking_away: Whether the user is currently looking away from screen
            continuous_gaze_away_seconds: Seconds in the current look-away episode
            seconds_since_looking_forward: Seconds since user last looked at screen
            
        Returns:
            RiskEstimate with score (0-100) and level
        """
        # Factor 1: Time-based fatigue (risk increases over session)
        time_factor = self._calculate_time_factor(elapsed_seconds)
        
        # Factor 2: Recent phone activity (higher if phone seen recently)
        recent_phone_factor = self._calculate_recent_phone_factor(seconds_since_phone)
        
        # Factor 3: Current session distractions (momentum)
        distraction_factor = self._calculate_distraction_factor(current_distractions)
        
        # Factor 4: Historical pattern (baseline tendency from CSV history)
        historical_factor = self._calculate_historical_factor(
            current_distractions,
            current_phone_time,
            elapsed_seconds,
            current_gaze_distractions,
            current_gaze_away_seconds,
        )

        # Factor 5: Gaze / head pose (looking away from screen)
        gaze_factor = self._calculate_gaze_factor(
            is_looking_away,
            continuous_gaze_away_seconds,
            seconds_since_looking_forward,
        )
        
        # Weighted combination
        raw_score = (
            time_factor * self.WEIGHT_TIME +
            recent_phone_factor * self.WEIGHT_RECENT_PHONE +
            distraction_factor * self.WEIGHT_CURRENT_DISTRACTIONS +
            historical_factor * self.WEIGHT_HISTORICAL +
            gaze_factor * self.WEIGHT_GAZE
        )
        
        # Normalize to 0-100
        score = int(max(0, min(100, raw_score * 100)))
        
        # Determine level
        if score <= self.THRESHOLD_LOW:
            level = RiskLevel.LOW
        elif score <= self.THRESHOLD_MEDIUM:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.HIGH
        
        return RiskEstimate(score=score, level=level)

    def evaluate_warning(
        self,
        risk: RiskEstimate | None,
        *,
        phone_detected: bool,
        phone_streak: int,
        phone_streak_required: int,
        previous_score: int | None = None,
        continuous_gaze_away_seconds: float = 0.0,
        is_looking_away: bool = False,
    ) -> DistractionWarning | None:
        """
        Return a proactive warning when distraction is likely but not yet logged.

        Warnings are suppressed while the phone is already counted as detected.
        """
        if risk is None or phone_detected:
            return None

        if is_looking_away and 3.0 <= continuous_gaze_away_seconds < 5.0:
            return DistractionWarning(
                message="Looking away — refocus on screen",
                severity="caution",
            )

        # Phone streak building — YOLO may confirm a distraction soon
        streak_warning_threshold = max(1, phone_streak_required - 2)
        if phone_streak >= streak_warning_threshold:
            return DistractionWarning(
                message="Phone may be detected — refocus now",
                severity="caution",
            )

        if risk.level == RiskLevel.HIGH:
            return DistractionWarning(
                message="High distraction risk — stay off your phone",
                severity="alert",
            )

        if risk.level == RiskLevel.MEDIUM:
            if previous_score is not None and risk.score - previous_score >= 15:
                return DistractionWarning(
                    message="Risk rising — take a short break or refocus",
                    severity="caution",
                )
            if risk.score >= 55:
                return DistractionWarning(
                    message="Elevated distraction risk — stay focused",
                    severity="caution",
                )

        return None
    
    def _calculate_time_factor(self, elapsed_seconds: float) -> float:
        """
        Risk increases as session progresses (fatigue).
        Returns 0.0 to 1.0.
        """
        if elapsed_seconds <= 0:
            return 0.0
        
        # Risk ramps up, peaks around 80% of session
        progress = elapsed_seconds / self.SESSION_DURATION
        # Quadratic ramp: slow start, faster increase later
        return min(1.0, progress ** 1.5)
    
    def _calculate_recent_phone_factor(self, seconds_since_phone: float | None) -> float:
        """
        Higher risk if phone was seen recently.
        Returns 0.0 to 1.0.
        """
        if seconds_since_phone is None:
            return 0.0  # Never seen phone
        
        if seconds_since_phone <= 0:
            return 1.0  # Phone visible right now
        
        if seconds_since_phone >= self.PHONE_RECENCY_WINDOW:
            return 0.0  # Phone not seen recently
        
        # Linear decay from 1.0 to 0.0 over the window
        return 1.0 - (seconds_since_phone / self.PHONE_RECENCY_WINDOW)
    
    def _calculate_distraction_factor(self, current_distractions: int) -> float:
        """
        More distractions = higher risk of another.
        Returns 0.0 to 1.0.
        """
        return min(1.0, current_distractions / self.MAX_DISTRACTIONS_SCALE)
    
    def _calculate_historical_factor(
        self,
        current_distractions: int,
        current_phone_time: float,
        elapsed_seconds: float,
        current_gaze_distractions: int,
        current_gaze_away_seconds: float,
    ) -> float:
        """
        Compare current session pace to historical CSV averages.

        Phone distractions and phone visible time contribute 60% of this factor;
        gaze distractions and gaze away time contribute 40%. High historical
        gaze-away behavior also raises the early-session baseline via
        _historical_gaze_baseline.

        Returns 0.0 to 1.0.
        """
        gaze_baseline_boost = self._historical_gaze_baseline * 0.20

        if elapsed_seconds <= 60:
            # Not enough session data yet; phone-neutral floor plus gaze history
            return min(1.0, 0.30 + gaze_baseline_boost)

        # Project current rates to a full 25-minute session
        time_ratio = self.SESSION_DURATION / elapsed_seconds
        projected_distractions = current_distractions * time_ratio
        projected_phone_time = current_phone_time * time_ratio
        projected_gaze_distractions = current_gaze_distractions * time_ratio
        projected_gaze_away = current_gaze_away_seconds * time_ratio

        phone_distraction_ratio = (
            projected_distractions / self.historical_avg_distractions
        )
        phone_time_ratio = projected_phone_time / self.historical_avg_phone_time
        gaze_event_ratio = (
            projected_gaze_distractions / self.historical_avg_gaze_distractions
        )
        gaze_away_ratio = (
            projected_gaze_away / self.historical_avg_gaze_away_seconds
        )

        phone_combined = (phone_distraction_ratio + phone_time_ratio) / 2
        gaze_combined = (gaze_event_ratio + gaze_away_ratio) / 2
        weighted = (
            phone_combined * self.HIST_PHONE_WEIGHT
            + gaze_combined * self.HIST_GAZE_WEIGHT
        )

        session_factor = min(1.0, weighted / 2)
        return min(1.0, session_factor * 0.85 + gaze_baseline_boost)

    def _calculate_gaze_factor(
        self,
        is_looking_away: bool,
        continuous_gaze_away_seconds: float,
        seconds_since_looking_forward: float | None,
    ) -> float:
        """
        Higher risk when looking away or shortly after returning from look-away.
        Returns 0.0 to 1.0.
        """
        if is_looking_away:
            return min(1.0, continuous_gaze_away_seconds / 5.0)

        if seconds_since_looking_forward is not None and seconds_since_looking_forward < 15:
            return max(0.0, 1.0 - seconds_since_looking_forward / 15.0) * 0.4

        return 0.0
