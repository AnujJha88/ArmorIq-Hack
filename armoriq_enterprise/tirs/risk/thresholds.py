"""
Dynamic Threshold Management
============================
Adaptive thresholds based on historical data.
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import statistics

logger = logging.getLogger("TIRS.Thresholds")


@dataclass
class ThresholdBand:
    """Risk threshold band."""
    name: str
    lower: float
    upper: float
    action: str
    color: str = "gray"


@dataclass
class ThresholdHistory:
    """Historical threshold data."""
    timestamp: datetime
    value: float
    reason: str


class DynamicThresholds:
    """
    Thresholds that adapt based on historical behavior.

    Features:
    - Learns normal risk distribution
    - Adjusts thresholds based on percentiles
    - Supports temporary overrides
    - Tracks threshold changes for audit
    """

    DEFAULT_BANDS = [
        ThresholdBand("nominal", 0.0, 0.3, "monitor", "green"),
        ThresholdBand("elevated", 0.3, 0.5, "alert", "yellow"),
        ThresholdBand("warning", 0.5, 0.7, "throttle", "orange"),
        ThresholdBand("critical", 0.7, 0.85, "pause", "red"),
        ThresholdBand("terminal", 0.85, 1.0, "kill", "black"),
    ]

    def __init__(
        self,
        learning_window_hours: int = 24,
        min_samples: int = 50,
        adaptation_rate: float = 0.1,
    ):
        self.learning_window = timedelta(hours=learning_window_hours)
        self.min_samples = min_samples
        self.adaptation_rate = adaptation_rate

        self.bands = list(self.DEFAULT_BANDS)
        self._score_history: Dict[str, deque] = {}
        self._threshold_history: List[ThresholdHistory] = []
        self._overrides: Dict[str, float] = {}

    def record_score(self, agent_id: str, score: float):
        """Record a risk score for learning."""
        if agent_id not in self._score_history:
            self._score_history[agent_id] = deque(maxlen=1000)

        self._score_history[agent_id].append((datetime.now(), score))

    def get_band(self, score: float, agent_id: Optional[str] = None) -> ThresholdBand:
        """Get the threshold band for a score."""
        # Check for agent-specific override
        if agent_id and agent_id in self._overrides:
            adjusted_score = score * self._overrides[agent_id]
        else:
            adjusted_score = score

        for band in self.bands:
            if band.lower <= adjusted_score < band.upper:
                return band

        # Default to last band if score is 1.0
        return self.bands[-1]

    def should_adapt(self, agent_id: str) -> bool:
        """Check if we have enough data to adapt thresholds."""
        if agent_id not in self._score_history:
            return False

        history = self._score_history[agent_id]
        if len(history) < self.min_samples:
            return False

        # Check if data is recent enough
        cutoff = datetime.now() - self.learning_window
        recent = [score for ts, score in history if ts > cutoff]

        return len(recent) >= self.min_samples // 2

    def adapt_thresholds(self, agent_id: str) -> Optional[List[ThresholdBand]]:
        """
        Adapt thresholds based on historical data.

        Uses percentile-based adjustment to find natural breaks.
        """
        if not self.should_adapt(agent_id):
            return None

        history = self._score_history[agent_id]
        cutoff = datetime.now() - self.learning_window
        recent_scores = [score for ts, score in history if ts > cutoff]

        if not recent_scores:
            return None

        # Calculate percentiles
        try:
            p50 = statistics.median(recent_scores)
            p75 = statistics.quantiles(recent_scores, n=4)[2] if len(recent_scores) > 3 else p50
            p90 = statistics.quantiles(recent_scores, n=10)[8] if len(recent_scores) > 9 else p75
            p95 = statistics.quantiles(recent_scores, n=20)[18] if len(recent_scores) > 19 else p90
        except Exception as e:
            logger.warning(f"Failed to calculate percentiles: {e}")
            return None

        # Adjust bands based on percentiles
        # But don't let thresholds go too low or too high
        new_bands = [
            ThresholdBand("nominal", 0.0, max(0.2, min(p50 * 1.2, 0.4)), "monitor", "green"),
            ThresholdBand("elevated", max(0.2, min(p50 * 1.2, 0.4)), max(0.35, min(p75, 0.55)), "alert", "yellow"),
            ThresholdBand("warning", max(0.35, min(p75, 0.55)), max(0.5, min(p90, 0.75)), "throttle", "orange"),
            ThresholdBand("critical", max(0.5, min(p90, 0.75)), max(0.7, min(p95, 0.9)), "pause", "red"),
            ThresholdBand("terminal", max(0.7, min(p95, 0.9)), 1.0, "kill", "black"),
        ]

        # Apply adaptation rate (blend with current)
        for i, (old, new) in enumerate(zip(self.bands, new_bands)):
            new.lower = old.lower * (1 - self.adaptation_rate) + new.lower * self.adaptation_rate
            new.upper = old.upper * (1 - self.adaptation_rate) + new.upper * self.adaptation_rate

        # Record change
        self._threshold_history.append(ThresholdHistory(
            timestamp=datetime.now(),
            value=new_bands[2].lower,  # Track warning threshold
            reason=f"Adapted for {agent_id} based on {len(recent_scores)} samples",
        ))

        return new_bands

    def set_override(self, agent_id: str, multiplier: float, reason: str):
        """Set a temporary threshold override for an agent."""
        self._overrides[agent_id] = multiplier
        self._threshold_history.append(ThresholdHistory(
            timestamp=datetime.now(),
            value=multiplier,
            reason=f"Override for {agent_id}: {reason}",
        ))
        logger.info(f"Threshold override for {agent_id}: {multiplier}x ({reason})")

    def clear_override(self, agent_id: str):
        """Clear threshold override for an agent."""
        if agent_id in self._overrides:
            del self._overrides[agent_id]

    def get_threshold_history(self, limit: int = 50) -> List[Dict]:
        """Get recent threshold changes."""
        return [
            {
                "timestamp": h.timestamp.isoformat(),
                "value": h.value,
                "reason": h.reason,
            }
            for h in self._threshold_history[-limit:]
        ]


class ThresholdAdjuster:
    """
    Adjusts thresholds based on various factors.

    Applies multipliers for:
    - Agent type (some agents have stricter thresholds)
    - Time of day
    - Current risk level
    - System-wide risk state
    """

    def __init__(self):
        self.agent_type_multipliers: Dict[str, float] = {
            "finance": 0.85,
            "legal": 0.85,
            "hr": 0.9,
            "it": 0.95,
            "procurement": 0.9,
            "operations": 0.95,
        }

        self.risk_state_multipliers: Dict[str, float] = {
            "normal": 1.0,
            "elevated": 0.9,
            "high_alert": 0.8,
            "incident": 0.7,
        }

    def get_multiplier(
        self,
        agent_type: Optional[str] = None,
        system_state: str = "normal",
        custom_factors: Optional[Dict[str, float]] = None,
    ) -> float:
        """Calculate combined threshold multiplier."""
        multiplier = 1.0

        # Agent type
        if agent_type and agent_type in self.agent_type_multipliers:
            multiplier *= self.agent_type_multipliers[agent_type]

        # System state
        if system_state in self.risk_state_multipliers:
            multiplier *= self.risk_state_multipliers[system_state]

        # Custom factors
        if custom_factors:
            for factor, value in custom_factors.items():
                multiplier *= value

        return multiplier

    def apply_to_band(self, band: ThresholdBand, multiplier: float) -> ThresholdBand:
        """Apply multiplier to a threshold band."""
        return ThresholdBand(
            name=band.name,
            lower=band.lower * multiplier,
            upper=band.upper * multiplier,
            action=band.action,
            color=band.color,
        )
