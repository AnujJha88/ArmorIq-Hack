"""
Temporal Decay and Velocity Tracking
=====================================
Time-based decay for risk scores and action velocity monitoring.
"""

import math
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque

logger = logging.getLogger("TIRS.Temporal")


class DecayFunction(Enum):
    """Types of decay functions."""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    STEP = "step"
    SIGMOID = "sigmoid"


@dataclass
class DecayConfig:
    """Configuration for temporal decay."""
    function: DecayFunction = DecayFunction.EXPONENTIAL
    half_life_minutes: float = 30.0
    min_weight: float = 0.1
    max_weight: float = 1.0


class TemporalDecay:
    """
    Applies time-based decay to risk scores.

    Older events contribute less to the current risk assessment.
    """

    def __init__(self, config: Optional[DecayConfig] = None):
        self.config = config or DecayConfig()
        self._decay_constant = math.log(2) / (self.config.half_life_minutes * 60)

    def compute_weight(self, event_time: datetime, current_time: Optional[datetime] = None) -> float:
        """
        Compute the temporal weight for an event.

        Args:
            event_time: When the event occurred
            current_time: Current time (defaults to now)

        Returns:
            Weight in [min_weight, max_weight]
        """
        current = current_time or datetime.now()
        age_seconds = (current - event_time).total_seconds()

        if age_seconds <= 0:
            return self.config.max_weight

        if self.config.function == DecayFunction.EXPONENTIAL:
            weight = math.exp(-self._decay_constant * age_seconds)
        elif self.config.function == DecayFunction.LINEAR:
            half_life_seconds = self.config.half_life_minutes * 60
            weight = max(0, 1 - (age_seconds / (2 * half_life_seconds)))
        elif self.config.function == DecayFunction.STEP:
            half_life_seconds = self.config.half_life_minutes * 60
            if age_seconds < half_life_seconds:
                weight = 1.0
            elif age_seconds < 2 * half_life_seconds:
                weight = 0.5
            else:
                weight = 0.1
        elif self.config.function == DecayFunction.SIGMOID:
            half_life_seconds = self.config.half_life_minutes * 60
            x = (age_seconds - half_life_seconds) / (half_life_seconds / 4)
            weight = 1 / (1 + math.exp(x))
        else:
            weight = 1.0

        # Clamp to range
        return max(self.config.min_weight, min(self.config.max_weight, weight))

    def apply_decay(
        self,
        values: List[Tuple[datetime, float]],
        current_time: Optional[datetime] = None
    ) -> float:
        """
        Apply decay to a list of timestamped values.

        Args:
            values: List of (timestamp, value) pairs
            current_time: Current time

        Returns:
            Weighted average with temporal decay
        """
        if not values:
            return 0.0

        current = current_time or datetime.now()
        total_weight = 0.0
        weighted_sum = 0.0

        for timestamp, value in values:
            weight = self.compute_weight(timestamp, current)
            weighted_sum += weight * value
            total_weight += weight

        if total_weight == 0:
            return 0.0

        return weighted_sum / total_weight


@dataclass
class VelocityConfig:
    """Configuration for velocity tracking."""
    window_size_seconds: int = 300  # 5 minutes
    baseline_actions_per_minute: float = 2.0
    spike_threshold: float = 3.0  # 3x baseline = spike
    sustained_threshold: float = 2.0  # 2x baseline for sustained period


class VelocityTracker:
    """
    Tracks action velocity (rate of actions over time).

    Detects:
    - Sudden spikes in activity
    - Sustained high activity
    - Unusual patterns (e.g., activity at odd hours)
    """

    def __init__(self, config: Optional[VelocityConfig] = None):
        self.config = config or VelocityConfig()
        self._agent_actions: Dict[str, deque] = {}
        self._agent_baselines: Dict[str, float] = {}

    def record_action(self, agent_id: str, timestamp: Optional[datetime] = None) -> Dict:
        """
        Record an action and compute velocity metrics.

        Returns:
            Dict with velocity metrics
        """
        timestamp = timestamp or datetime.now()

        if agent_id not in self._agent_actions:
            self._agent_actions[agent_id] = deque()
            self._agent_baselines[agent_id] = self.config.baseline_actions_per_minute

        actions = self._agent_actions[agent_id]
        actions.append(timestamp)

        # Prune old actions
        cutoff = timestamp - timedelta(seconds=self.config.window_size_seconds)
        while actions and actions[0] < cutoff:
            actions.popleft()

        # Compute current velocity
        window_minutes = self.config.window_size_seconds / 60
        current_rate = len(actions) / window_minutes if window_minutes > 0 else 0

        baseline = self._agent_baselines[agent_id]
        velocity_ratio = current_rate / baseline if baseline > 0 else 1.0

        # Detect anomalies
        is_spike = velocity_ratio >= self.config.spike_threshold
        is_sustained = velocity_ratio >= self.config.sustained_threshold

        # Update baseline with exponential moving average
        alpha = 0.1
        self._agent_baselines[agent_id] = alpha * current_rate + (1 - alpha) * baseline

        return {
            "agent_id": agent_id,
            "current_rate": current_rate,
            "baseline_rate": baseline,
            "velocity_ratio": velocity_ratio,
            "is_spike": is_spike,
            "is_sustained": is_sustained,
            "actions_in_window": len(actions),
            "window_seconds": self.config.window_size_seconds,
        }

    def get_anomaly_score(self, agent_id: str) -> float:
        """
        Get velocity anomaly score for an agent.

        Returns:
            Score in [0, 1] where 1 is highly anomalous
        """
        if agent_id not in self._agent_actions:
            return 0.0

        actions = self._agent_actions[agent_id]
        if not actions:
            return 0.0

        window_minutes = self.config.window_size_seconds / 60
        current_rate = len(actions) / window_minutes
        baseline = self._agent_baselines.get(agent_id, self.config.baseline_actions_per_minute)

        if baseline <= 0:
            return 0.0

        ratio = current_rate / baseline

        # Map ratio to [0, 1] score using sigmoid
        if ratio <= 1:
            return 0.0
        elif ratio >= self.config.spike_threshold:
            return 1.0
        else:
            # Linear interpolation between thresholds
            normalized = (ratio - 1) / (self.config.spike_threshold - 1)
            return min(1.0, normalized)

    def get_agent_stats(self, agent_id: str) -> Dict:
        """Get velocity statistics for an agent."""
        if agent_id not in self._agent_actions:
            return {
                "agent_id": agent_id,
                "total_actions": 0,
                "current_rate": 0.0,
                "baseline_rate": self.config.baseline_actions_per_minute,
            }

        actions = self._agent_actions[agent_id]
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.config.window_size_seconds)

        # Count recent actions
        recent = sum(1 for a in actions if a >= cutoff)
        window_minutes = self.config.window_size_seconds / 60

        return {
            "agent_id": agent_id,
            "total_actions": len(actions),
            "actions_in_window": recent,
            "current_rate": recent / window_minutes if window_minutes > 0 else 0,
            "baseline_rate": self._agent_baselines.get(agent_id, self.config.baseline_actions_per_minute),
            "anomaly_score": self.get_anomaly_score(agent_id),
        }
