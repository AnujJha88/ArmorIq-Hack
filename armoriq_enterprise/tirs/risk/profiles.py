"""
Behavioral Profiles
===================
Per-agent behavioral profiling for baseline comparison.
"""

import numpy as np
import logging
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger("TIRS.Profiles")


class ProfileState(Enum):
    """State of a behavioral profile."""
    LEARNING = "learning"       # Still building baseline
    ESTABLISHED = "established"  # Has sufficient data
    STALE = "stale"             # Needs refresh
    ANOMALOUS = "anomalous"     # Detected anomaly in profile


@dataclass
class CapabilityBaseline:
    """Baseline for a single capability."""
    capability: str
    frequency: float  # Calls per hour
    avg_risk_delta: float
    last_seen: datetime
    times_used: int = 0
    times_blocked: int = 0


@dataclass
class BehavioralProfile:
    """
    Behavioral profile for an agent.

    Captures:
    - Normal capability usage patterns
    - Typical risk scores
    - Time-of-day patterns
    - Interaction patterns
    """
    agent_id: str
    agent_type: str
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    state: ProfileState = ProfileState.LEARNING

    # Capability baselines
    capability_baselines: Dict[str, CapabilityBaseline] = field(default_factory=dict)

    # Risk score statistics
    avg_risk_score: float = 0.0
    risk_score_std: float = 0.0
    max_observed_risk: float = 0.0

    # Activity patterns (by hour of day)
    hourly_activity: List[float] = field(default_factory=lambda: [0.0] * 24)

    # Learning parameters
    learning_samples: int = 0
    min_samples_for_established: int = 100

    # Anomaly tracking
    anomaly_count: int = 0
    last_anomaly: Optional[datetime] = None

    def update(
        self,
        capabilities: Set[str],
        risk_score: float,
        was_blocked: bool,
        timestamp: Optional[datetime] = None,
    ):
        """Update profile with new observation."""
        timestamp = timestamp or datetime.now()
        self.last_updated = timestamp
        self.learning_samples += 1

        # Update capability baselines
        for cap in capabilities:
            if cap not in self.capability_baselines:
                self.capability_baselines[cap] = CapabilityBaseline(
                    capability=cap,
                    frequency=0.0,
                    avg_risk_delta=0.0,
                    last_seen=timestamp,
                )

            baseline = self.capability_baselines[cap]
            baseline.times_used += 1
            if was_blocked:
                baseline.times_blocked += 1
            baseline.last_seen = timestamp

            # Update frequency (exponential moving average)
            alpha = 0.1
            hours_since_creation = max((timestamp - self.created_at).total_seconds() / 3600, 1)
            current_freq = baseline.times_used / hours_since_creation
            baseline.frequency = alpha * current_freq + (1 - alpha) * baseline.frequency

            # Update risk delta
            baseline.avg_risk_delta = (
                alpha * risk_score + (1 - alpha) * baseline.avg_risk_delta
            )

        # Update risk statistics (exponential moving average)
        alpha = 0.1
        self.avg_risk_score = alpha * risk_score + (1 - alpha) * self.avg_risk_score

        # Update std (simplified online variance)
        diff = risk_score - self.avg_risk_score
        self.risk_score_std = alpha * abs(diff) + (1 - alpha) * self.risk_score_std

        self.max_observed_risk = max(self.max_observed_risk, risk_score)

        # Update hourly activity
        hour = timestamp.hour
        self.hourly_activity[hour] += 1

        # Update state
        if self.learning_samples >= self.min_samples_for_established:
            if self.state == ProfileState.LEARNING:
                self.state = ProfileState.ESTABLISHED
                logger.info(f"Profile {self.agent_id} now ESTABLISHED")

    def is_anomalous(self, capabilities: Set[str], risk_score: float) -> Tuple[bool, List[str]]:
        """
        Check if current behavior is anomalous compared to profile.

        Returns:
            (is_anomalous, list of anomaly reasons)
        """
        if self.state == ProfileState.LEARNING:
            return False, []

        anomalies = []

        # Check for new capabilities
        for cap in capabilities:
            if cap not in self.capability_baselines:
                anomalies.append(f"New capability: {cap}")

        # Check risk score deviation
        if self.risk_score_std > 0:
            z_score = (risk_score - self.avg_risk_score) / max(self.risk_score_std, 0.01)
            if z_score > 2.5:
                anomalies.append(f"Risk score {z_score:.1f} std above mean")

        # Check for unusual time
        hour = datetime.now().hour
        if self.hourly_activity[hour] < np.mean(self.hourly_activity) * 0.1:
            if sum(self.hourly_activity) > 100:  # Only if we have enough data
                anomalies.append(f"Unusual activity time: hour {hour}")

        is_anomalous = len(anomalies) > 0

        if is_anomalous:
            self.anomaly_count += 1
            self.last_anomaly = datetime.now()

        return is_anomalous, anomalies

    def get_expected_capabilities(self) -> Set[str]:
        """Get capabilities expected for this agent."""
        return set(self.capability_baselines.keys())

    def get_capability_frequency(self, capability: str) -> float:
        """Get expected frequency for a capability."""
        baseline = self.capability_baselines.get(capability)
        return baseline.frequency if baseline else 0.0

    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "state": self.state.value,
            "learning_samples": self.learning_samples,
            "avg_risk_score": self.avg_risk_score,
            "risk_score_std": self.risk_score_std,
            "max_observed_risk": self.max_observed_risk,
            "capability_count": len(self.capability_baselines),
            "anomaly_count": self.anomaly_count,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
        }


class ProfileMatcher:
    """
    Matches agent behavior against established profiles.

    Used for:
    - Cold-start mitigation (new agents match against type profiles)
    - Anomaly detection (compare to similar agents)
    - Behavioral clustering
    """

    def __init__(self):
        self.profiles: Dict[str, BehavioralProfile] = {}
        self.type_profiles: Dict[str, BehavioralProfile] = {}

    def register_profile(self, profile: BehavioralProfile):
        """Register an agent profile."""
        self.profiles[profile.agent_id] = profile

        # Also contribute to type profile
        if profile.state == ProfileState.ESTABLISHED:
            self._update_type_profile(profile)

    def _update_type_profile(self, profile: BehavioralProfile):
        """Update aggregate type profile."""
        if profile.agent_type not in self.type_profiles:
            self.type_profiles[profile.agent_type] = BehavioralProfile(
                agent_id=f"type:{profile.agent_type}",
                agent_type=profile.agent_type,
            )

        type_profile = self.type_profiles[profile.agent_type]

        # Merge capability baselines
        for cap, baseline in profile.capability_baselines.items():
            if cap not in type_profile.capability_baselines:
                type_profile.capability_baselines[cap] = CapabilityBaseline(
                    capability=cap,
                    frequency=baseline.frequency,
                    avg_risk_delta=baseline.avg_risk_delta,
                    last_seen=baseline.last_seen,
                )
            else:
                existing = type_profile.capability_baselines[cap]
                # Average frequencies
                existing.frequency = (existing.frequency + baseline.frequency) / 2
                existing.avg_risk_delta = (existing.avg_risk_delta + baseline.avg_risk_delta) / 2

    def get_baseline_for_new_agent(self, agent_type: str) -> Optional[BehavioralProfile]:
        """Get baseline profile for a new agent based on type."""
        return self.type_profiles.get(agent_type)

    def find_similar_profiles(self, profile: BehavioralProfile, top_k: int = 3) -> List[Tuple[str, float]]:
        """
        Find most similar profiles.

        Returns:
            List of (agent_id, similarity_score) tuples
        """
        similarities = []

        profile_caps = set(profile.capability_baselines.keys())

        for other_id, other in self.profiles.items():
            if other_id == profile.agent_id:
                continue

            if other.state != ProfileState.ESTABLISHED:
                continue

            # Jaccard similarity of capabilities
            other_caps = set(other.capability_baselines.keys())
            intersection = len(profile_caps & other_caps)
            union = len(profile_caps | other_caps)
            cap_sim = intersection / union if union > 0 else 0

            # Risk score similarity
            risk_diff = abs(profile.avg_risk_score - other.avg_risk_score)
            risk_sim = 1 - min(risk_diff, 1)

            # Combined similarity
            similarity = 0.6 * cap_sim + 0.4 * risk_sim
            similarities.append((other_id, similarity))

        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]


# Import Tuple for type hints
from typing import Tuple
