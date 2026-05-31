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


class RiskEstimator:
    """
    Estimates distraction risk based on multiple factors.
    
    This is a heuristic-based implementation. The interface is designed
    so it can be swapped with an ML model later by keeping the same
    calculate() signature.
    """
    
    # Weights for each factor (should sum to 1.0)
    WEIGHT_TIME = 0.25
    WEIGHT_RECENT_PHONE = 0.30
    WEIGHT_CURRENT_DISTRACTIONS = 0.25
    WEIGHT_HISTORICAL = 0.20
    
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
    ):
        """
        Initialize with historical baselines.
        
        Args:
            historical_avg_distractions: Average distractions per session historically
            historical_avg_phone_time: Average phone visible seconds historically
        """
        self.historical_avg_distractions = max(0.1, historical_avg_distractions)
        self.historical_avg_phone_time = max(0.1, historical_avg_phone_time)
    
    def calculate(
        self,
        elapsed_seconds: float,
        seconds_since_phone: float | None,
        current_distractions: int,
        current_phone_time: float,
    ) -> RiskEstimate:
        """
        Calculate current distraction risk.
        
        Args:
            elapsed_seconds: Time elapsed in current session
            seconds_since_phone: Seconds since phone was last detected (None if never)
            current_distractions: Number of distractions in current session
            current_phone_time: Total phone visible time in current session
            
        Returns:
            RiskEstimate with score (0-100) and level
        """
        # Factor 1: Time-based fatigue (risk increases over session)
        time_factor = self._calculate_time_factor(elapsed_seconds)
        
        # Factor 2: Recent phone activity (higher if phone seen recently)
        recent_phone_factor = self._calculate_recent_phone_factor(seconds_since_phone)
        
        # Factor 3: Current session distractions (momentum)
        distraction_factor = self._calculate_distraction_factor(current_distractions)
        
        # Factor 4: Historical pattern (baseline tendency)
        historical_factor = self._calculate_historical_factor(
            current_distractions, current_phone_time, elapsed_seconds
        )
        
        # Weighted combination
        raw_score = (
            time_factor * self.WEIGHT_TIME +
            recent_phone_factor * self.WEIGHT_RECENT_PHONE +
            distraction_factor * self.WEIGHT_CURRENT_DISTRACTIONS +
            historical_factor * self.WEIGHT_HISTORICAL
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
    ) -> float:
        """
        Compare current session to historical averages.
        Returns 0.0 to 1.0.
        """
        if elapsed_seconds <= 60:
            return 0.3  # Not enough data yet, neutral-ish
        
        # Project current rate to full session
        time_ratio = self.SESSION_DURATION / elapsed_seconds
        projected_distractions = current_distractions * time_ratio
        projected_phone_time = current_phone_time * time_ratio
        
        # Compare to historical
        distraction_ratio = projected_distractions / self.historical_avg_distractions
        phone_ratio = projected_phone_time / self.historical_avg_phone_time
        
        # Average of both ratios, capped at 1.0
        combined = (distraction_ratio + phone_ratio) / 2
        return min(1.0, combined / 2)  # Soften the impact
