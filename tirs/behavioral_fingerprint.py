"""
Behavioral Fingerprinting for Star Drift Detection
===================================================
Learns what "normal" looks like for each agent.

A behavioral fingerprint captures:
- Typical capabilities used
- Time-of-day patterns
- Action sequences
- Baseline embedding centroid
- Rate patterns
"""

import numpy as np
import logging
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, Counter

logger = logging.getLogger("TIRS.Fingerprint")


@dataclass
class TimePattern:
    """Captures when an agent typically operates."""
    hourly_distribution: Dict[int, float] = field(default_factory=dict)  # Hour -> probability
    daily_distribution: Dict[int, float] = field(default_factory=dict)   # Day of week -> prob
    avg_actions_per_hour: float = 0.0
    peak_hours: List[int] = field(default_factory=list)
    quiet_hours: List[int] = field(default_factory=list)
    
    def update(self, timestamps: List[datetime]):
        """Update time patterns from a list of timestamps."""
        if not timestamps:
            return
            
        hour_counts = Counter(ts.hour for ts in timestamps)
        day_counts = Counter(ts.weekday() for ts in timestamps)
        total = len(timestamps)
        
        self.hourly_distribution = {h: c / total for h, c in hour_counts.items()}
        self.daily_distribution = {d: c / total for d, c in day_counts.items()}
        
        # Identify peak and quiet hours
        avg_prob = 1 / 24
        self.peak_hours = [h for h, p in self.hourly_distribution.items() if p > avg_prob * 2]
        self.quiet_hours = [h for h in range(24) if h not in self.hourly_distribution or 
                          self.hourly_distribution.get(h, 0) < avg_prob * 0.25]
        
        # Calculate average actions per hour
        if timestamps:
            time_span = (max(timestamps) - min(timestamps)).total_seconds() / 3600
            self.avg_actions_per_hour = len(timestamps) / max(time_span, 1)
    
    def is_unusual_time(self, timestamp: datetime) -> Tuple[bool, float]:
        """Check if a timestamp is unusual. Returns (is_unusual, confidence)."""
        hour = timestamp.hour
        hour_prob = self.hourly_distribution.get(hour, 0.0)
        
        if hour in self.quiet_hours:
            return True, 0.8
        if hour_prob < 0.01:  # Very rare
            return True, 0.9
        if hour_prob < (1/24) * 0.25:  # Less than quarter of average
            return True, 0.6
            
        return False, 0.0
    
    def to_dict(self) -> Dict:
        return {
            "hourly_distribution": self.hourly_distribution,
            "daily_distribution": self.daily_distribution,
            "avg_actions_per_hour": self.avg_actions_per_hour,
            "peak_hours": self.peak_hours,
            "quiet_hours": self.quiet_hours
        }


@dataclass
class SequencePattern:
    """Captures common action sequences."""
    bigrams: Dict[Tuple[str, str], int] = field(default_factory=dict)  # (cap1, cap2) -> count
    trigrams: Dict[Tuple[str, str, str], int] = field(default_factory=dict)
    common_sequences: List[Tuple[str, ...]] = field(default_factory=list)
    total_sequences: int = 0
    
    def update(self, capability_sequence: List[str]):
        """Update sequence patterns from a list of capabilities in order."""
        if len(capability_sequence) < 2:
            return
            
        # Count bigrams
        for i in range(len(capability_sequence) - 1):
            bigram = (capability_sequence[i], capability_sequence[i + 1])
            self.bigrams[bigram] = self.bigrams.get(bigram, 0) + 1
            self.total_sequences += 1
        
        # Count trigrams
        for i in range(len(capability_sequence) - 2):
            trigram = (capability_sequence[i], capability_sequence[i + 1], capability_sequence[i + 2])
            self.trigrams[trigram] = self.trigrams.get(trigram, 0) + 1
        
        # Identify most common sequences
        sorted_bigrams = sorted(self.bigrams.items(), key=lambda x: x[1], reverse=True)
        self.common_sequences = [seq for seq, _ in sorted_bigrams[:10]]
    
    def sequence_probability(self, prev_cap: str, current_cap: str) -> float:
        """Get probability of this sequence transition."""
        if self.total_sequences == 0:
            return 0.5  # Unknown baseline
        
        bigram = (prev_cap, current_cap)
        count = self.bigrams.get(bigram, 0)
        
        # Get total transitions from prev_cap
        from_prev = sum(c for (p, _), c in self.bigrams.items() if p == prev_cap)
        
        if from_prev == 0:
            return 0.1  # Never seen this capability before
        
        return count / from_prev
    
    def is_unusual_sequence(self, prev_cap: str, current_cap: str) -> Tuple[bool, float]:
        """Check if a sequence is unusual."""
        prob = self.sequence_probability(prev_cap, current_cap)
        
        if prob == 0:
            return True, 0.9  # Never seen this sequence
        if prob < 0.05:
            return True, 0.7  # Very rare sequence
        if prob < 0.1:
            return True, 0.5  # Uncommon
            
        return False, 0.0


@dataclass
class BehavioralFingerprint:
    """
    Complete behavioral fingerprint for an agent.
    
    Captures what "normal" looks like across multiple dimensions.
    """
    agent_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    learning_complete: bool = False
    min_samples_for_learning: int = 20
    
    # Core patterns
    typical_capabilities: Set[str] = field(default_factory=set)
    capability_frequency: Dict[str, float] = field(default_factory=dict)
    time_patterns: TimePattern = field(default_factory=TimePattern)
    sequence_patterns: SequencePattern = field(default_factory=SequencePattern)
    
    # Baseline metrics
    baseline_centroid: Optional[np.ndarray] = None
    baseline_risk_avg: float = 0.0
    baseline_risk_std: float = 0.0
    
    # Rate tracking
    actions_per_minute_avg: float = 0.0
    actions_per_minute_std: float = 0.0
    
    # Privilege level tracking (for escalation detection)
    typical_privilege_level: float = 0.0  # 0=read, 0.5=write, 1=admin
    
    # Historical data for learning
    _timestamps: List[datetime] = field(default_factory=list)
    _capabilities_sequence: List[str] = field(default_factory=list)
    _risk_scores: List[float] = field(default_factory=list)
    _action_rates: List[float] = field(default_factory=list)
    
    def record_action(self, 
                     timestamp: datetime,
                     capabilities: Set[str],
                     embedding: np.ndarray,
                     risk_score: float):
        """Record an action for fingerprint learning."""
        self._timestamps.append(timestamp)
        self._risk_scores.append(risk_score)
        
        # Track capabilities
        for cap in capabilities:
            self.typical_capabilities.add(cap)
            self._capabilities_sequence.append(cap)
        
        # Update centroid
        if self.baseline_centroid is None:
            self.baseline_centroid = embedding
        else:
            # Running average
            n = len(self._timestamps)
            self.baseline_centroid = (self.baseline_centroid * (n - 1) + embedding) / n
        
        # Check if we have enough samples
        if len(self._timestamps) >= self.min_samples_for_learning and not self.learning_complete:
            self._complete_learning()
        
        self.last_updated = datetime.now()
    
    def _complete_learning(self):
        """Finalize the fingerprint after enough samples."""
        # Calculate capability frequency
        cap_counts = Counter(self._capabilities_sequence)
        total = len(self._capabilities_sequence)
        self.capability_frequency = {cap: count / total for cap, count in cap_counts.items()}
        
        # Update time patterns
        self.time_patterns.update(self._timestamps)
        
        # Update sequence patterns
        self.sequence_patterns.update(self._capabilities_sequence)
        
        # Calculate baseline risk statistics
        if self._risk_scores:
            self.baseline_risk_avg = np.mean(self._risk_scores)
            self.baseline_risk_std = np.std(self._risk_scores) if len(self._risk_scores) > 1 else 0.1
        
        # Calculate action rate
        if len(self._timestamps) > 1:
            sorted_ts = sorted(self._timestamps)
            intervals = [(sorted_ts[i+1] - sorted_ts[i]).total_seconds() / 60 
                        for i in range(len(sorted_ts) - 1)]
            rates = [1 / max(interval, 0.01) for interval in intervals]
            self.actions_per_minute_avg = np.mean(rates)
            self.actions_per_minute_std = np.std(rates) if len(rates) > 1 else 0.5
        
        # Estimate privilege level
        self._estimate_privilege_level()
        
        self.learning_complete = True
        logger.info(f"Fingerprint learning complete for {self.agent_id}")
        logger.info(f"  Typical capabilities: {len(self.typical_capabilities)}")
        logger.info(f"  Peak hours: {self.time_patterns.peak_hours}")
        logger.info(f"  Baseline risk: {self.baseline_risk_avg:.3f} ± {self.baseline_risk_std:.3f}")
    
    def _estimate_privilege_level(self):
        """Estimate typical privilege level from capabilities."""
        admin_keywords = {"admin", "delete", "create", "modify", "write", "export", "execute"}
        write_keywords = {"write", "update", "send", "book", "schedule", "edit"}
        
        levels = []
        for cap in self.typical_capabilities:
            cap_lower = cap.lower()
            if any(kw in cap_lower for kw in admin_keywords):
                levels.append(1.0)
            elif any(kw in cap_lower for kw in write_keywords):
                levels.append(0.5)
            else:
                levels.append(0.0)
        
        self.typical_privilege_level = np.mean(levels) if levels else 0.0
    
    def check_temporal_drift(self, timestamp: datetime) -> Tuple[bool, float, str]:
        """Check if timing is unusual."""
        if not self.learning_complete:
            return False, 0.0, ""
        
        is_unusual, confidence = self.time_patterns.is_unusual_time(timestamp)
        
        if is_unusual:
            hour = timestamp.hour
            explanation = f"Action at {hour}:00 is unusual (quiet hours: {self.time_patterns.quiet_hours})"
            return True, confidence, explanation
        
        return False, 0.0, ""
    
    def check_capability_drift(self, capabilities: Set[str]) -> Tuple[bool, float, str]:
        """Check if capabilities are unusual."""
        if not self.learning_complete:
            return False, 0.0, ""
        
        new_caps = capabilities - self.typical_capabilities
        
        if new_caps:
            confidence = min(0.9, 0.5 + 0.2 * len(new_caps))
            explanation = f"New capabilities not in baseline: {list(new_caps)}"
            return True, confidence, explanation
        
        # Check if using rare capabilities
        rare_caps = [cap for cap in capabilities 
                    if self.capability_frequency.get(cap, 0) < 0.05]
        
        if rare_caps:
            confidence = min(0.7, 0.3 + 0.1 * len(rare_caps))
            explanation = f"Using rare capabilities: {rare_caps}"
            return True, confidence, explanation
        
        return False, 0.0, ""
    
    def check_velocity_drift(self, recent_timestamps: List[datetime]) -> Tuple[bool, float, str]:
        """Check if action rate is unusual."""
        if not self.learning_complete or len(recent_timestamps) < 2:
            return False, 0.0, ""
        
        # Calculate recent rate
        sorted_ts = sorted(recent_timestamps)
        interval = (sorted_ts[-1] - sorted_ts[0]).total_seconds() / 60
        current_rate = len(recent_timestamps) / max(interval, 0.01)
        
        # Compare to baseline
        if self.actions_per_minute_std > 0:
            z_score = (current_rate - self.actions_per_minute_avg) / self.actions_per_minute_std
            
            if abs(z_score) > 3:
                direction = "higher" if z_score > 0 else "lower"
                explanation = f"Action rate is {abs(z_score):.1f}σ {direction} than baseline"
                return True, min(0.9, abs(z_score) / 5), explanation
            elif abs(z_score) > 2:
                direction = "higher" if z_score > 0 else "lower"
                explanation = f"Action rate is {abs(z_score):.1f}σ {direction} than baseline"
                return True, min(0.6, abs(z_score) / 5), explanation
        
        return False, 0.0, ""
    
    def check_escalation_drift(self, capabilities: Set[str]) -> Tuple[bool, float, str]:
        """Check for privilege escalation."""
        if not self.learning_complete:
            return False, 0.0, ""
        
        # Calculate current privilege level
        admin_keywords = {"admin", "delete", "create", "modify", "write", "export", "execute"}
        write_keywords = {"write", "update", "send", "book", "schedule", "edit"}
        
        levels = []
        for cap in capabilities:
            cap_lower = cap.lower()
            if any(kw in cap_lower for kw in admin_keywords):
                levels.append(1.0)
            elif any(kw in cap_lower for kw in write_keywords):
                levels.append(0.5)
            else:
                levels.append(0.0)
        
        current_level = np.mean(levels) if levels else 0.0
        
        # Check for escalation
        escalation = current_level - self.typical_privilege_level
        
        if escalation > 0.3:
            confidence = min(0.9, escalation)
            explanation = f"Privilege escalation detected: {self.typical_privilege_level:.2f} → {current_level:.2f}"
            return True, confidence, explanation
        
        return False, 0.0, ""
    
    def check_sequence_drift(self, prev_capability: str, current_capability: str) -> Tuple[bool, float, str]:
        """Check if action sequence is unusual."""
        if not self.learning_complete or not prev_capability:
            return False, 0.0, ""
        
        is_unusual, confidence = self.sequence_patterns.is_unusual_sequence(
            prev_capability, current_capability
        )
        
        if is_unusual:
            explanation = f"Unusual sequence: {prev_capability} → {current_capability}"
            return True, confidence, explanation
        
        return False, 0.0, ""
    
    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "learning_complete": self.learning_complete,
            "typical_capabilities": list(self.typical_capabilities),
            "capability_frequency": self.capability_frequency,
            "time_patterns": self.time_patterns.to_dict(),
            "baseline_risk_avg": self.baseline_risk_avg,
            "baseline_risk_std": self.baseline_risk_std,
            "actions_per_minute_avg": self.actions_per_minute_avg,
            "typical_privilege_level": self.typical_privilege_level,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat()
        }


# Fingerprint registry
_fingerprints: Dict[str, BehavioralFingerprint] = {}


def get_fingerprint(agent_id: str) -> BehavioralFingerprint:
    """Get or create fingerprint for an agent."""
    if agent_id not in _fingerprints:
        _fingerprints[agent_id] = BehavioralFingerprint(agent_id=agent_id)
        logger.info(f"Created behavioral fingerprint for {agent_id}")
    return _fingerprints[agent_id]


def get_all_fingerprints() -> Dict[str, Dict]:
    """Get all fingerprints as dicts."""
    return {aid: fp.to_dict() for aid, fp in _fingerprints.items()}
