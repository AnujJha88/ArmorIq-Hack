"""
Multi-Signal Drift Detector
============================
Core drift detection combining multiple signals with temporal awareness.
"""

import numpy as np
import logging
import math
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .embeddings import EmbeddingEngine, get_embedding_engine, cosine_similarity
from .temporal import TemporalDecay, VelocityTracker, DecayConfig
from .contextual import ContextualThresholds, BusinessContext, ThresholdConfig

logger = logging.getLogger("TIRS.DriftDetector")


class RiskLevel(Enum):
    """Risk levels for agent behavior."""
    NOMINAL = "nominal"       # 0.0 - 0.3: Normal operation
    ELEVATED = "elevated"     # 0.3 - 0.5: Heightened monitoring
    WARNING = "warning"       # 0.5 - 0.7: Alert + throttling
    CRITICAL = "critical"     # 0.7 - 0.85: Auto-pause
    TERMINAL = "terminal"     # 0.85+: Auto-kill


class AgentStatus(Enum):
    """Agent runtime status."""
    ACTIVE = "active"
    THROTTLED = "throttled"
    PAUSED = "paused"
    QUARANTINED = "quarantined"
    KILLED = "killed"
    RESURRECTED = "resurrected"


@dataclass
class SignalWeight:
    """Weights for drift signals."""
    embedding_drift: float = 0.30
    capability_surprisal: float = 0.25
    violation_rate: float = 0.20
    velocity_anomaly: float = 0.15
    context_deviation: float = 0.10


@dataclass
class DriftSignal:
    """Individual drift signal measurement."""
    name: str
    raw_value: float
    weight: float
    contribution: float  # weighted value
    explanation: str


@dataclass
class IntentRecord:
    """Record of a single intent for drift analysis."""
    intent_id: str
    timestamp: datetime
    intent_text: str
    embedding: np.ndarray
    capabilities: Set[str]
    was_allowed: bool
    policy_triggered: Optional[str] = None
    context: Optional[BusinessContext] = None
    risk_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.NOMINAL

    def to_dict(self) -> Dict:
        return {
            "intent_id": self.intent_id,
            "timestamp": self.timestamp.isoformat(),
            "intent_text": self.intent_text,
            "capabilities": list(self.capabilities),
            "was_allowed": self.was_allowed,
            "policy_triggered": self.policy_triggered,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level.value,
        }


@dataclass
class DriftProfile:
    """
    Drift profile for a single agent.

    Tracks behavioral history and computes risk metrics.
    """
    agent_id: str
    window_size: int = 50
    intent_history: List[IntentRecord] = field(default_factory=list)
    centroid: Optional[np.ndarray] = None
    risk_history: List[Tuple[datetime, float]] = field(default_factory=list)
    status: AgentStatus = AgentStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    # Capability tracking
    capability_counts: Dict[str, int] = field(default_factory=dict)
    total_intents: int = 0
    violation_count: int = 0

    # Resurrection tracking
    resurrection_count: int = 0
    last_resurrection: Optional[datetime] = None

    def add_intent(self, record: IntentRecord):
        """Add a new intent record and update metrics."""
        self.intent_history.append(record)
        self.total_intents += 1
        self.last_updated = datetime.now()

        # Track capabilities
        for cap in record.capabilities:
            self.capability_counts[cap] = self.capability_counts.get(cap, 0) + 1

        # Track violations
        if not record.was_allowed:
            self.violation_count += 1

        # Trim to window size
        if len(self.intent_history) > self.window_size:
            self.intent_history = self.intent_history[-self.window_size:]

        # Record risk score with timestamp
        self.risk_history.append((record.timestamp, record.risk_score))
        if len(self.risk_history) > 100:
            self.risk_history = self.risk_history[-100:]

        # Update centroid
        self._update_centroid()

    def _update_centroid(self):
        """Update the running centroid of intent embeddings."""
        if not self.intent_history:
            return

        embeddings = np.array([r.embedding for r in self.intent_history])
        self.centroid = np.mean(embeddings, axis=0)

        # Normalize
        norm = np.linalg.norm(self.centroid)
        if norm > 0:
            self.centroid = self.centroid / norm

    def get_capability_distribution(self) -> Dict[str, float]:
        """Get probability distribution of capabilities."""
        if self.total_intents == 0:
            return {}
        return {
            cap: count / self.total_intents
            for cap, count in self.capability_counts.items()
        }

    def get_recent_violation_rate(self, window: int = 10) -> float:
        """Get violation rate in recent intents."""
        recent = self.intent_history[-window:] if len(self.intent_history) >= window else self.intent_history
        if not recent:
            return 0.0
        violations = sum(1 for r in recent if not r.was_allowed)
        return violations / len(recent)

    @property
    def current_risk_score(self) -> float:
        """Get the most recent risk score."""
        if self.risk_history:
            return self.risk_history[-1][1]
        return 0.0

    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "status": self.status.value,
            "total_intents": self.total_intents,
            "violation_count": self.violation_count,
            "current_risk_score": self.current_risk_score,
            "risk_history": [(ts.isoformat(), score) for ts, score in self.risk_history[-20:]],
            "capability_distribution": self.get_capability_distribution(),
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "resurrection_count": self.resurrection_count,
        }


@dataclass
class DriftResult:
    """Result of drift detection."""
    agent_id: str
    risk_score: float
    risk_level: RiskLevel
    signals: List[DriftSignal]
    status: AgentStatus
    thresholds_applied: ThresholdConfig
    context: BusinessContext
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level.value,
            "signals": [
                {
                    "name": s.name,
                    "raw_value": s.raw_value,
                    "weight": s.weight,
                    "contribution": s.contribution,
                    "explanation": s.explanation,
                }
                for s in self.signals
            ],
            "status": self.status.value,
            "thresholds": {
                "warning": self.thresholds_applied.warning,
                "critical": self.thresholds_applied.critical,
                "terminal": self.thresholds_applied.terminal,
            },
            "timestamp": self.timestamp.isoformat(),
        }


class DriftDetector:
    """
    Multi-signal drift detector with temporal awareness.

    Combines multiple signals:
    1. Embedding drift - semantic divergence from centroid
    2. Capability surprisal - information-theoretic surprisal
    3. Violation rate - recent policy violations
    4. Velocity anomaly - action rate vs baseline
    5. Context deviation - time/role context mismatches
    """

    def __init__(
        self,
        signal_weights: Optional[SignalWeight] = None,
        base_thresholds: Optional[ThresholdConfig] = None,
        decay_config: Optional[DecayConfig] = None,
    ):
        self.weights = signal_weights or SignalWeight()
        self.contextual_thresholds = ContextualThresholds(base_thresholds)
        self.temporal_decay = TemporalDecay(decay_config)
        self.velocity_tracker = VelocityTracker()
        self.embedding_engine = get_embedding_engine()

        self.profiles: Dict[str, DriftProfile] = {}
        self._intent_counter = 0

        # Capability baselines per agent type
        self.capability_baselines: Dict[str, Set[str]] = {}

        logger.info("DriftDetector initialized with multi-signal detection")

    def register_capability_baseline(self, agent_type: str, capabilities: Set[str]):
        """Register expected capabilities for an agent type."""
        self.capability_baselines[agent_type] = capabilities
        logger.info(f"Registered baseline for {agent_type}: {len(capabilities)} capabilities")

    def get_or_create_profile(self, agent_id: str) -> DriftProfile:
        """Get existing profile or create new one for agent."""
        if agent_id not in self.profiles:
            self.profiles[agent_id] = DriftProfile(agent_id=agent_id)
            logger.info(f"Created drift profile for agent: {agent_id}")
        return self.profiles[agent_id]

    def detect_drift(
        self,
        agent_id: str,
        intent_text: str,
        capabilities: Set[str],
        was_allowed: bool,
        policy_triggered: Optional[str] = None,
        context: Optional[BusinessContext] = None,
    ) -> DriftResult:
        """
        Detect drift for an intent and record it.

        Args:
            agent_id: Agent identifier
            intent_text: The intent description
            capabilities: Set of capabilities requested
            was_allowed: Whether the intent was allowed
            policy_triggered: Policy that blocked/modified (if any)
            context: Business context for threshold adjustment

        Returns:
            DriftResult with signals and risk level
        """
        profile = self.get_or_create_profile(agent_id)
        context = context or BusinessContext.from_current()

        # Check if agent is already dead
        if profile.status == AgentStatus.KILLED:
            logger.warning(f"Agent {agent_id} is KILLED, rejecting intent")
            return DriftResult(
                agent_id=agent_id,
                risk_score=1.0,
                risk_level=RiskLevel.TERMINAL,
                signals=[],
                status=AgentStatus.KILLED,
                thresholds_applied=self.contextual_thresholds.get_adjusted_thresholds(context),
                context=context,
            )

        # Generate embedding
        self._intent_counter += 1
        intent_id = f"INT-{datetime.now().strftime('%Y%m%d')}-{self._intent_counter:06d}"
        embedding = self.embedding_engine.embed(intent_text)

        # Calculate signals
        signals = self._calculate_signals(profile, embedding, capabilities, was_allowed, context)

        # Compute weighted risk score
        risk_score = sum(s.contribution for s in signals)
        risk_score = min(max(risk_score, 0.0), 1.0)

        # Get context-adjusted thresholds
        thresholds = self.contextual_thresholds.get_adjusted_thresholds(context)

        # Determine risk level
        risk_level = self._evaluate_risk_level(risk_score, thresholds)

        # Create intent record
        record = IntentRecord(
            intent_id=intent_id,
            timestamp=datetime.now(),
            intent_text=intent_text,
            embedding=embedding,
            capabilities=capabilities,
            was_allowed=was_allowed,
            policy_triggered=policy_triggered,
            context=context,
            risk_score=risk_score,
            risk_level=risk_level,
        )

        # Add to profile
        profile.add_intent(record)

        # Record velocity
        self.velocity_tracker.record_action(agent_id)

        # Enforce thresholds
        new_status = self._enforce_thresholds(profile, risk_score, risk_level)

        logger.info(f"[{agent_id}] Intent {intent_id}: risk={risk_score:.3f} ({risk_level.value})")

        return DriftResult(
            agent_id=agent_id,
            risk_score=risk_score,
            risk_level=risk_level,
            signals=signals,
            status=new_status,
            thresholds_applied=thresholds,
            context=context,
        )

    def _calculate_signals(
        self,
        profile: DriftProfile,
        embedding: np.ndarray,
        capabilities: Set[str],
        was_allowed: bool,
        context: BusinessContext,
    ) -> List[DriftSignal]:
        """Calculate all drift signals."""
        signals = []

        # 1. Embedding Drift
        if profile.centroid is not None:
            drift_value = 1 - cosine_similarity(embedding, profile.centroid)
        else:
            drift_value = 0.1  # Small baseline for first intent

        signals.append(DriftSignal(
            name="embedding_drift",
            raw_value=drift_value,
            weight=self.weights.embedding_drift,
            contribution=drift_value * self.weights.embedding_drift,
            explanation=f"Semantic distance from behavioral centroid: {drift_value:.3f}",
        ))

        # 2. Capability Surprisal
        surprisal = self._calculate_surprisal(profile, capabilities)
        signals.append(DriftSignal(
            name="capability_surprisal",
            raw_value=surprisal,
            weight=self.weights.capability_surprisal,
            contribution=surprisal * self.weights.capability_surprisal,
            explanation=f"Unusual capability request: {surprisal:.3f}",
        ))

        # 3. Violation Rate (with temporal decay)
        violation_rate = self._calculate_decayed_violation_rate(profile)
        signals.append(DriftSignal(
            name="violation_rate",
            raw_value=violation_rate,
            weight=self.weights.violation_rate,
            contribution=violation_rate * self.weights.violation_rate,
            explanation=f"Recent violation rate (decayed): {violation_rate:.3f}",
        ))

        # 4. Velocity Anomaly
        velocity_score = self.velocity_tracker.get_anomaly_score(profile.agent_id)
        signals.append(DriftSignal(
            name="velocity_anomaly",
            raw_value=velocity_score,
            weight=self.weights.velocity_anomaly,
            contribution=velocity_score * self.weights.velocity_anomaly,
            explanation=f"Action rate anomaly: {velocity_score:.3f}",
        ))

        # 5. Context Deviation
        context_score = self._calculate_context_deviation(context)
        signals.append(DriftSignal(
            name="context_deviation",
            raw_value=context_score,
            weight=self.weights.context_deviation,
            contribution=context_score * self.weights.context_deviation,
            explanation=f"Context risk factors: {context_score:.3f}",
        ))

        return signals

    def _calculate_surprisal(self, profile: DriftProfile, capabilities: Set[str]) -> float:
        """Calculate capability surprisal using information theory."""
        if not capabilities:
            return 0.0

        cap_dist = profile.get_capability_distribution()

        total_surprisal = 0.0
        for cap in capabilities:
            # Use low probability for unseen capabilities
            prob = cap_dist.get(cap, 0.01)
            prob = max(prob, 0.001)
            total_surprisal += -math.log(prob)

        # Normalize
        avg_surprisal = total_surprisal / len(capabilities)
        # Map to [0, 1] (assuming max surprisal ~7 for p=0.001)
        normalized = min(avg_surprisal / 7.0, 1.0)

        return normalized

    def _calculate_decayed_violation_rate(self, profile: DriftProfile) -> float:
        """Calculate violation rate with temporal decay."""
        if not profile.intent_history:
            return 0.0

        violations = [
            (r.timestamp, 1.0 if not r.was_allowed else 0.0)
            for r in profile.intent_history[-20:]
        ]

        return self.temporal_decay.apply_decay(violations)

    def _calculate_context_deviation(self, context: BusinessContext) -> float:
        """Calculate risk from context factors."""
        score = 0.0

        # After hours is riskier
        from .contextual import BusinessHours
        if context.time_of_day == BusinessHours.AFTER_HOURS:
            score += 0.3
        elif context.time_of_day == BusinessHours.WEEKEND:
            score += 0.4
        elif context.time_of_day == BusinessHours.HOLIDAY:
            score += 0.5

        # External roles are riskier
        if context.user_role == "external":
            score += 0.3
        elif context.user_role == "contractor":
            score += 0.2

        # Sensitive operations
        if context.is_sensitive_operation:
            score += 0.2

        return min(score, 1.0)

    def _evaluate_risk_level(self, risk_score: float, thresholds: ThresholdConfig) -> RiskLevel:
        """Determine risk level from score."""
        if risk_score >= thresholds.terminal:
            return RiskLevel.TERMINAL
        elif risk_score >= thresholds.critical:
            return RiskLevel.CRITICAL
        elif risk_score >= thresholds.warning:
            return RiskLevel.WARNING
        elif risk_score >= 0.3:
            return RiskLevel.ELEVATED
        else:
            return RiskLevel.NOMINAL

    def _enforce_thresholds(
        self,
        profile: DriftProfile,
        risk_score: float,
        risk_level: RiskLevel,
    ) -> AgentStatus:
        """Enforce actions based on risk level."""
        if risk_level == RiskLevel.TERMINAL and profile.status != AgentStatus.KILLED:
            profile.status = AgentStatus.KILLED
            logger.critical(f"AGENT KILLED: {profile.agent_id} (risk={risk_score:.3f})")

        elif risk_level == RiskLevel.CRITICAL and profile.status in [AgentStatus.ACTIVE, AgentStatus.THROTTLED]:
            profile.status = AgentStatus.PAUSED
            logger.warning(f"AGENT PAUSED: {profile.agent_id} (risk={risk_score:.3f})")

        elif risk_level == RiskLevel.WARNING and profile.status == AgentStatus.ACTIVE:
            profile.status = AgentStatus.THROTTLED
            logger.warning(f"AGENT THROTTLED: {profile.agent_id} (risk={risk_score:.3f})")

        return profile.status

    def resurrect_agent(self, agent_id: str, admin_id: str, reason: str) -> bool:
        """
        Resurrect a killed agent (requires admin approval).

        This provides a path to recover from KILL state.
        """
        profile = self.profiles.get(agent_id)
        if not profile:
            return False

        if profile.status != AgentStatus.KILLED:
            logger.warning(f"Agent {agent_id} is not killed, cannot resurrect")
            return False

        # Record resurrection
        profile.status = AgentStatus.RESURRECTED
        profile.resurrection_count += 1
        profile.last_resurrection = datetime.now()

        # Reset risk history partially
        profile.risk_history = profile.risk_history[-5:]

        logger.info(f"Agent {agent_id} RESURRECTED by {admin_id}: {reason}")
        return True

    def get_agent_status(self, agent_id: str) -> Optional[AgentStatus]:
        """Get current status of an agent."""
        profile = self.profiles.get(agent_id)
        return profile.status if profile else None

    def get_all_profiles(self) -> Dict[str, Dict]:
        """Get all agent profiles as dicts."""
        return {aid: p.to_dict() for aid, p in self.profiles.items()}

    def get_risk_summary(self) -> Dict:
        """Get summary of all agent risks."""
        summary = {
            "total_agents": len(self.profiles),
            "by_status": {},
            "high_risk": [],
            "agents": {},
        }

        for status in AgentStatus:
            summary["by_status"][status.value] = 0

        for agent_id, profile in self.profiles.items():
            summary["by_status"][profile.status.value] += 1

            if profile.current_risk_score >= 0.5:
                summary["high_risk"].append({
                    "agent_id": agent_id,
                    "risk_score": profile.current_risk_score,
                    "status": profile.status.value,
                })

            summary["agents"][agent_id] = {
                "risk_score": profile.current_risk_score,
                "status": profile.status.value,
            }

        return summary
