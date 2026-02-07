"""
Temporal Intent Drift Detection Engine
=======================================
Detects slow, multi-step deviation in agent behavior over time.

Key Features:
- Tracks intent history per agent (embeddings + capabilities)
- Computes rolling risk score from multiple signals
- Triggers WARN/PAUSE/KILL based on thresholds
"""

import numpy as np
import logging
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import math

from .embeddings import get_embedding_engine, cosine_similarity
from .behavioral_fingerprint import get_fingerprint, BehavioralFingerprint

logger = logging.getLogger("TIRS.Drift")


class RiskLevel(Enum):
    """Risk levels for agent behavior."""
    OK = "OK"
    WARNING = "WARNING"
    PAUSE = "PAUSE"
    KILL = "KILL"


class DriftCategory(Enum):
    """
    Categories of drift for precise alerting.
    
    Each category indicates a different type of behavioral deviation:
    - SEMANTIC: Actions changing in meaning/purpose
    - CAPABILITY: Using new/unusual capabilities
    - TEMPORAL: Unusual timing patterns
    - VELOCITY: Speed/rate changes
    - ESCALATION: Privilege creep
    """
    NONE = "NONE"
    SEMANTIC = "SEMANTIC"         # Intent meaning changed
    CAPABILITY = "CAPABILITY"     # New/unusual capabilities
    TEMPORAL = "TEMPORAL"         # Unusual timing
    VELOCITY = "VELOCITY"         # Speed changes
    ESCALATION = "ESCALATION"     # Privilege creep


class AlertSeverity(Enum):
    """Severity levels for drift alerts."""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AgentStatus(Enum):
    """Agent runtime status."""
    ACTIVE = "active"
    PAUSED = "paused"
    KILLED = "killed"


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
    drift_category: Optional[DriftCategory] = None
    risk_contribution: Optional[Dict[str, float]] = None

    def to_dict(self) -> Dict:
        return {
            "intent_id": self.intent_id,
            "timestamp": self.timestamp.isoformat(),
            "intent_text": self.intent_text,
            "capabilities": list(self.capabilities),
            "was_allowed": self.was_allowed,
            "policy_triggered": self.policy_triggered,
            "drift_category": self.drift_category.value if self.drift_category else None
        }


@dataclass
class DriftAlert:
    """
    Smart drift alert with explainability.
    
    Provides actionable information about detected drift.
    """
    alert_id: str
    timestamp: datetime
    agent_id: str
    severity: AlertSeverity
    drift_categories: List[DriftCategory]
    risk_score: float
    confidence: float
    explanation: str  # Human-readable
    evidence: List[Dict]  # Supporting data
    suggested_action: str
    acknowledged: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "alert_id": self.alert_id,
            "timestamp": self.timestamp.isoformat(),
            "agent_id": self.agent_id,
            "severity": self.severity.value,
            "drift_categories": [c.value for c in self.drift_categories],
            "risk_score": self.risk_score,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "evidence": self.evidence,
            "suggested_action": self.suggested_action,
            "acknowledged": self.acknowledged
        }


@dataclass
class DriftProfile:
    """
    Drift profile for a single agent.

    Tracks behavioral history and computes risk metrics.
    """
    agent_id: str
    window_size: int = 20
    intent_history: List[IntentRecord] = field(default_factory=list)
    centroid: Optional[np.ndarray] = None
    risk_history: List[float] = field(default_factory=list)
    status: AgentStatus = AgentStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    # Capability tracking
    capability_counts: Dict[str, int] = field(default_factory=dict)
    total_intents: int = 0
    violation_count: int = 0

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
        return self.risk_history[-1] if self.risk_history else 0.0

    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "status": self.status.value,
            "total_intents": self.total_intents,
            "violation_count": self.violation_count,
            "current_risk_score": self.current_risk_score,
            "risk_history": self.risk_history[-20:],  # Last 20
            "capability_distribution": self.get_capability_distribution(),
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat()
        }


@dataclass
class DriftThresholds:
    """Configurable thresholds for drift detection."""
    warning: float = 0.5
    pause: float = 0.7
    kill: float = 0.9

    # Weights for risk score components
    embedding_weight: float = 0.4
    surprisal_weight: float = 0.35
    violation_weight: float = 0.25


class DriftEngine:
    """
    Main drift detection engine.

    Monitors agent behavior over time and detects when agents
    drift from their normal operating patterns.
    """

    def __init__(self, thresholds: Optional[DriftThresholds] = None):
        self.thresholds = thresholds or DriftThresholds()
        self.profiles: Dict[str, DriftProfile] = {}
        self.embedding_engine = get_embedding_engine()
        self._intent_counter = 0

        logger.info(f"DriftEngine initialized")
        logger.info(f"  Thresholds: warn={self.thresholds.warning}, "
                   f"pause={self.thresholds.pause}, kill={self.thresholds.kill}")

    def get_or_create_profile(self, agent_id: str) -> DriftProfile:
        """Get existing profile or create new one for agent."""
        if agent_id not in self.profiles:
            self.profiles[agent_id] = DriftProfile(agent_id=agent_id)
            logger.info(f"Created drift profile for agent: {agent_id}")
        return self.profiles[agent_id]

    def record_intent(
        self,
        agent_id: str,
        intent_text: str,
        capabilities: Set[str],
        was_allowed: bool,
        policy_triggered: Optional[str] = None
    ) -> Tuple[float, RiskLevel]:
        """
        Record a new intent and compute risk score.

        Args:
            agent_id: Agent identifier
            intent_text: The intent description
            capabilities: Set of capabilities requested
            was_allowed: Whether the intent was allowed
            policy_triggered: Policy that blocked/modified (if any)

        Returns:
            Tuple of (risk_score, risk_level)
        """
        profile = self.get_or_create_profile(agent_id)

        # Check if agent is already killed
        if profile.status == AgentStatus.KILLED:
            logger.warning(f"Agent {agent_id} is KILLED, rejecting intent")
            return 1.0, RiskLevel.KILL

        # Generate embedding
        self._intent_counter += 1
        intent_id = f"INT-{datetime.now().strftime('%Y%m%d')}-{self._intent_counter:06d}"
        embedding = self.embedding_engine.embed(intent_text)

        # Create intent record
        record = IntentRecord(
            intent_id=intent_id,
            timestamp=datetime.now(),
            intent_text=intent_text,
            embedding=embedding,
            capabilities=capabilities,
            was_allowed=was_allowed,
            policy_triggered=policy_triggered
        )

        # Calculate risk BEFORE adding (compare to existing behavior)
        risk_score = self._calculate_risk_score(profile, record)

        # Add to profile
        profile.add_intent(record)
        profile.risk_history.append(risk_score)

        # Determine risk level
        risk_level = self._evaluate_risk_level(risk_score)

        # Enforce thresholds
        self._enforce_thresholds(profile, risk_score, risk_level)

        logger.info(f"[{agent_id}] Intent recorded: {intent_id}")
        logger.info(f"  Risk: {risk_score:.3f} ({risk_level.value})")

        return risk_score, risk_level

    def _calculate_risk_score(self, profile: DriftProfile, new_intent: IntentRecord) -> float:
        """
        Calculate risk score from multiple signals with drift categorization.

        Components:
        1. Embedding drift - distance from behavioral centroid (SEMANTIC)
        2. Capability surprisal - how unusual are the requested capabilities (CAPABILITY)
        3. Violation rate - recent policy violation frequency
        4. Fingerprint-based drift (TEMPORAL, VELOCITY, ESCALATION)
        
        Returns:
            Risk score and updates intent record with detected categories
        """
        # If this is the first intent, no drift possible
        if not profile.intent_history:
            return 0.1  # Small baseline risk

        detected_categories: List[DriftCategory] = []
        category_contributions: Dict[str, float] = {}
        explanations: List[str] = []

        # Get behavioral fingerprint
        fingerprint = get_fingerprint(profile.agent_id)

        # 1. Embedding Drift (SEMANTIC)
        if profile.centroid is not None:
            embedding_drift = 1 - cosine_similarity(new_intent.embedding, profile.centroid)
            category_contributions["semantic"] = embedding_drift
            if embedding_drift > 0.3:
                detected_categories.append(DriftCategory.SEMANTIC)
                explanations.append(f"Semantic drift: {embedding_drift:.2f} from baseline")
        else:
            embedding_drift = 0.0

        # 2. Capability Surprisal (CAPABILITY)
        surprisal = self._calculate_surprisal(profile, new_intent.capabilities)
        category_contributions["capability"] = surprisal
        if surprisal > 0.4:
            detected_categories.append(DriftCategory.CAPABILITY)
            explanations.append(f"Unusual capabilities detected (surprisal: {surprisal:.2f})")

        # 3. Violation Rate
        violation_rate = profile.get_recent_violation_rate(window=10)
        category_contributions["violation"] = violation_rate

        # 4. Fingerprint-based drift checks
        if fingerprint.learning_complete:
            # Temporal drift
            is_temporal, temporal_conf, temporal_exp = fingerprint.check_temporal_drift(new_intent.timestamp)
            if is_temporal:
                detected_categories.append(DriftCategory.TEMPORAL)
                explanations.append(temporal_exp)
                category_contributions["temporal"] = temporal_conf

            # Capability drift from fingerprint
            is_cap_drift, cap_conf, cap_exp = fingerprint.check_capability_drift(new_intent.capabilities)
            if is_cap_drift and DriftCategory.CAPABILITY not in detected_categories:
                detected_categories.append(DriftCategory.CAPABILITY)
                explanations.append(cap_exp)

            # Velocity drift
            recent_timestamps = [r.timestamp for r in profile.intent_history[-10:]]
            recent_timestamps.append(new_intent.timestamp)
            is_velocity, vel_conf, vel_exp = fingerprint.check_velocity_drift(recent_timestamps)
            if is_velocity:
                detected_categories.append(DriftCategory.VELOCITY)
                explanations.append(vel_exp)
                category_contributions["velocity"] = vel_conf

            # Escalation drift
            is_escalation, esc_conf, esc_exp = fingerprint.check_escalation_drift(new_intent.capabilities)
            if is_escalation:
                detected_categories.append(DriftCategory.ESCALATION)
                explanations.append(esc_exp)
                category_contributions["escalation"] = esc_conf

            # Sequence drift
            if profile.intent_history:
                prev_caps = list(profile.intent_history[-1].capabilities)
                if prev_caps and new_intent.capabilities:
                    prev_cap = prev_caps[0]
                    curr_cap = list(new_intent.capabilities)[0]
                    is_seq, seq_conf, seq_exp = fingerprint.check_sequence_drift(prev_cap, curr_cap)
                    if is_seq:
                        explanations.append(seq_exp)
                        category_contributions["sequence"] = seq_conf
        else:
            # Still learning - record for fingerprint
            fingerprint.record_action(
                timestamp=new_intent.timestamp,
                capabilities=new_intent.capabilities,
                embedding=new_intent.embedding,
                risk_score=0.1
            )

        # Store drift info in intent record
        new_intent.drift_category = detected_categories[0] if detected_categories else DriftCategory.NONE
        new_intent.risk_contribution = category_contributions

        # Weighted combination
        risk_score = (
            self.thresholds.embedding_weight * embedding_drift +
            self.thresholds.surprisal_weight * surprisal +
            self.thresholds.violation_weight * violation_rate
        )

        # Add fingerprint-based contributions
        for cat_name in ["temporal", "velocity", "escalation"]:
            if cat_name in category_contributions:
                risk_score += 0.1 * category_contributions[cat_name]

        # Generate alert if significant drift detected
        if detected_categories and risk_score > self.thresholds.warning:
            self._generate_alert(profile, new_intent, detected_categories, 
                               risk_score, explanations, category_contributions)

        # Clamp to [0, 1]
        return min(max(risk_score, 0.0), 1.0)

    def _calculate_surprisal(self, profile: DriftProfile, capabilities: Set[str]) -> float:
        """
        Calculate how surprising the requested capabilities are.

        Uses information-theoretic surprisal: -log(P(capability))
        """
        if not capabilities:
            return 0.0

        cap_dist = profile.get_capability_distribution()

        total_surprisal = 0.0
        for cap in capabilities:
            # Use low probability for unseen capabilities
            prob = cap_dist.get(cap, 0.01)
            # Avoid log(0)
            prob = max(prob, 0.001)
            total_surprisal += -math.log(prob)

        # Normalize by number of capabilities and log scale
        avg_surprisal = total_surprisal / len(capabilities)
        # Map to [0, 1] range (assuming max surprisal ~7 for p=0.001)
        normalized = min(avg_surprisal / 7.0, 1.0)

        return normalized

    def _generate_alert(self, 
                       profile: DriftProfile,
                       intent: IntentRecord,
                       categories: List[DriftCategory],
                       risk_score: float,
                       explanations: List[str],
                       contributions: Dict[str, float]) -> DriftAlert:
        """
        Generate a smart drift alert with explanation and suggested action.
        """
        self._alert_counter = getattr(self, '_alert_counter', 0) + 1
        
        # Determine severity
        if risk_score >= self.thresholds.kill:
            severity = AlertSeverity.CRITICAL
        elif risk_score >= self.thresholds.pause:
            severity = AlertSeverity.WARNING
        else:
            severity = AlertSeverity.INFO
        
        # Build human-readable explanation
        primary_category = categories[0] if categories else DriftCategory.NONE
        if explanations:
            explanation = f"{primary_category.value} drift detected. " + " | ".join(explanations[:3])
        else:
            explanation = f"Risk score elevated to {risk_score:.2f}"
        
        # Build evidence
        evidence = [
            {"intent_id": intent.intent_id, "timestamp": intent.timestamp.isoformat()},
            {"risk_contributions": contributions},
            {"capabilities": list(intent.capabilities)},
            {"recent_risk_history": profile.risk_history[-5:]}
        ]
        
        # Suggest action based on severity and category
        if severity == AlertSeverity.CRITICAL:
            if DriftCategory.ESCALATION in categories:
                suggested_action = "IMMEDIATE: Agent killed due to privilege escalation. Review audit trail."
            else:
                suggested_action = "IMMEDIATE: Agent killed. Review forensic snapshot and recent actions."
        elif severity == AlertSeverity.WARNING:
            if DriftCategory.VELOCITY in categories:
                suggested_action = "Review action rate - consider rate limiting this agent."
            elif DriftCategory.TEMPORAL in categories:
                suggested_action = "Unusual timing detected - verify authorized operation."
            else:
                suggested_action = "Agent paused. Review recent behavior before resuming."
        else:
            suggested_action = "Monitor this agent - drift patterns emerging."
        
        # Calculate confidence (average of contributing factors)
        confidence = sum(contributions.values()) / max(len(contributions), 1)
        
        alert = DriftAlert(
            alert_id=f"ALERT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self._alert_counter:04d}",
            timestamp=datetime.now(),
            agent_id=profile.agent_id,
            severity=severity,
            drift_categories=categories,
            risk_score=risk_score,
            confidence=min(confidence, 1.0),
            explanation=explanation,
            evidence=evidence,
            suggested_action=suggested_action
        )
        
        # Store alert
        if not hasattr(self, 'alerts'):
            self.alerts: List[DriftAlert] = []
        self.alerts.append(alert)
        
        # Log alert
        log_method = logger.critical if severity == AlertSeverity.CRITICAL else logger.warning
        log_method(f"🚨 DRIFT ALERT: {alert.alert_id}")
        log_method(f"   Agent: {profile.agent_id} | Severity: {severity.value}")
        log_method(f"   Categories: {[c.value for c in categories]}")
        log_method(f"   {explanation}")
        log_method(f"   Suggested: {suggested_action}")
        
        return alert

    def get_alerts(self, agent_id: str = None, acknowledged: bool = None) -> List[Dict]:
        """Get drift alerts, optionally filtered."""
        alerts = getattr(self, 'alerts', [])
        
        if agent_id:
            alerts = [a for a in alerts if a.agent_id == agent_id]
        if acknowledged is not None:
            alerts = [a for a in alerts if a.acknowledged == acknowledged]
        
        return [a.to_dict() for a in alerts]
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Mark an alert as acknowledged."""
        for alert in getattr(self, 'alerts', []):
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                logger.info(f"Alert {alert_id} acknowledged")
                return True
        return False

    def _evaluate_risk_level(self, risk_score: float) -> RiskLevel:
        """Determine risk level from score."""
        if risk_score >= self.thresholds.kill:
            return RiskLevel.KILL
        elif risk_score >= self.thresholds.pause:
            return RiskLevel.PAUSE
        elif risk_score >= self.thresholds.warning:
            return RiskLevel.WARNING
        else:
            return RiskLevel.OK

    def _enforce_thresholds(self, profile: DriftProfile, risk_score: float, risk_level: RiskLevel):
        """Enforce actions based on risk level."""
        if risk_level == RiskLevel.KILL and profile.status != AgentStatus.KILLED:
            profile.status = AgentStatus.KILLED
            logger.critical(f"AGENT KILLED: {profile.agent_id} (risk={risk_score:.3f})")
            self._create_forensic_snapshot(profile)

        elif risk_level == RiskLevel.PAUSE and profile.status == AgentStatus.ACTIVE:
            profile.status = AgentStatus.PAUSED
            logger.warning(f"AGENT PAUSED: {profile.agent_id} (risk={risk_score:.3f})")

        elif risk_level == RiskLevel.WARNING:
            logger.warning(f"AGENT WARNING: {profile.agent_id} (risk={risk_score:.3f})")

    def _create_forensic_snapshot(self, profile: DriftProfile) -> Dict:
        """Create a forensic snapshot when agent is killed."""
        snapshot = {
            "snapshot_type": "FORENSIC_KILL",
            "timestamp": datetime.now().isoformat(),
            "agent_id": profile.agent_id,
            "final_risk_score": profile.current_risk_score,
            "risk_history": profile.risk_history,
            "total_intents": profile.total_intents,
            "violation_count": profile.violation_count,
            "recent_intents": [r.to_dict() for r in profile.intent_history[-10:]],
            "capability_distribution": profile.get_capability_distribution()
        }

        logger.critical(f"Forensic snapshot created for {profile.agent_id}")
        return snapshot

    def resume_agent(self, agent_id: str) -> bool:
        """Resume a paused agent (requires admin approval)."""
        profile = self.profiles.get(agent_id)
        if not profile:
            return False

        if profile.status == AgentStatus.PAUSED:
            profile.status = AgentStatus.ACTIVE
            # Reset risk history to give fresh start
            profile.risk_history = profile.risk_history[-5:]  # Keep some history
            logger.info(f"Agent {agent_id} RESUMED by admin")
            return True

        return False

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
            "active": 0,
            "paused": 0,
            "killed": 0,
            "high_risk": [],
            "agents": {}
        }

        for agent_id, profile in self.profiles.items():
            if profile.status == AgentStatus.ACTIVE:
                summary["active"] += 1
            elif profile.status == AgentStatus.PAUSED:
                summary["paused"] += 1
            elif profile.status == AgentStatus.KILLED:
                summary["killed"] += 1

            if profile.current_risk_score >= self.thresholds.warning:
                summary["high_risk"].append({
                    "agent_id": agent_id,
                    "risk_score": profile.current_risk_score,
                    "status": profile.status.value
                })

            summary["agents"][agent_id] = {
                "risk_score": profile.current_risk_score,
                "status": profile.status.value
            }

        return summary


# Singleton instance
_drift_engine: Optional[DriftEngine] = None


def get_drift_engine() -> DriftEngine:
    """Get the singleton drift engine."""
    global _drift_engine
    if _drift_engine is None:
        _drift_engine = DriftEngine()
    return _drift_engine
