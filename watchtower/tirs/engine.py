"""
Advanced TIRS Engine
====================
Main integration point for the Temporal Intent Risk & Simulation system.

The "star" of the Watchtower Enterprise system.
"""

import logging
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# Import all TIRS components
from .drift.detector import DriftDetector, DriftResult, RiskLevel, AgentStatus, DriftProfile
from .drift.embeddings import get_embedding_engine
from .drift.temporal import TemporalDecay, VelocityTracker
from .drift.contextual import ContextualThresholds, BusinessContext
from .drift.explainer import DriftExplainer, DriftExplanation, get_explainer

from .risk.scorer import RiskScorer, CompositeRiskScore, create_drift_scorer
from .risk.thresholds import DynamicThresholds, ThresholdAdjuster
from .risk.profiles import BehavioralProfile, ProfileMatcher, ProfileState

from .enforcement.actions import (
    EnforcementExecutor, EnforcementAction, ActionType,
    create_action, get_executor
)
from .enforcement.remediation import RemediationEngine, RemediationPlan, get_remediation_engine
from .enforcement.appeals import AppealManager, AppealRequest, AppealType, get_appeal_manager

from .forensics.snapshot import ForensicSnapshot, SnapshotManager, get_snapshot_manager
from .forensics.timeline import EventTimeline, EventCategory, EventSeverity, get_timeline
from .forensics.audit import AuditChain, AuditEventType, get_audit_chain

logger = logging.getLogger("TIRS.Engine")


@dataclass
class TIRSConfig:
    """Configuration for Advanced TIRS."""
    # Thresholds
    warning_threshold: float = 0.5
    critical_threshold: float = 0.7
    terminal_threshold: float = 0.85

    # Temporal settings
    decay_half_life_minutes: float = 30.0
    velocity_window_seconds: int = 300

    # Enforcement
    auto_pause_enabled: bool = True
    auto_kill_enabled: bool = True
    throttle_rate_limit: float = 1.0  # actions per minute

    # Resurrection
    allow_resurrection: bool = True
    max_resurrections: int = 3

    # Persistence
    enable_persistence: bool = True
    enable_audit_chain: bool = True


@dataclass
class TIRSResult:
    """Comprehensive result from TIRS analysis."""
    agent_id: str
    timestamp: datetime

    # Risk assessment
    risk_score: float
    risk_level: RiskLevel
    confidence: float

    # Drift details
    drift_result: DriftResult
    explanation: DriftExplanation

    # Agent status
    agent_status: AgentStatus
    status_changed: bool = False

    # Enforcement
    action_taken: Optional[EnforcementAction] = None
    remediation_plan: Optional[RemediationPlan] = None

    # Audit
    audit_entry_id: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "timestamp": self.timestamp.isoformat(),
            "risk_score": self.risk_score,
            "risk_level": self.risk_level.value,
            "confidence": self.confidence,
            "agent_status": self.agent_status.value,
            "status_changed": self.status_changed,
            "action_taken": self.action_taken.to_dict() if self.action_taken else None,
            "remediation_available": self.remediation_plan is not None,
            "audit_entry_id": self.audit_entry_id,
        }


class AdvancedTIRS:
    """
    Advanced Temporal Intent Risk & Simulation Engine.

    The comprehensive TIRS implementation with:
    - Multi-signal drift detection
    - Temporal decay with configurable half-life
    - Context-aware thresholds
    - Explainable risk scores
    - Automated enforcement
    - Resurrection workflow
    - Forensic snapshots
    - Cryptographic audit chain
    """

    def __init__(self, config: Optional[TIRSConfig] = None):
        self.config = config or TIRSConfig()

        # Initialize components
        self.drift_detector = DriftDetector()
        self.explainer = get_explainer()
        self.risk_scorer = create_drift_scorer()
        self.dynamic_thresholds = DynamicThresholds()
        self.threshold_adjuster = ThresholdAdjuster()

        self.enforcement = get_executor()
        self.remediation = get_remediation_engine()
        self.appeals = get_appeal_manager()

        self.snapshots = get_snapshot_manager()
        self.timeline = get_timeline()
        self.audit = get_audit_chain() if self.config.enable_audit_chain else None

        self.profile_matcher = ProfileMatcher()

        # Log initialization
        self._log_system_start()

        logger.info("=" * 60)
        logger.info("  ADVANCED TIRS ENGINE INITIALIZED")
        logger.info("=" * 60)
        logger.info(f"  Config:")
        logger.info(f"    - Warning threshold: {self.config.warning_threshold}")
        logger.info(f"    - Critical threshold: {self.config.critical_threshold}")
        logger.info(f"    - Terminal threshold: {self.config.terminal_threshold}")
        logger.info(f"    - Auto-pause: {self.config.auto_pause_enabled}")
        logger.info(f"    - Auto-kill: {self.config.auto_kill_enabled}")
        logger.info(f"    - Resurrection allowed: {self.config.allow_resurrection}")
        logger.info("=" * 60)

    def _log_system_start(self):
        """Log system start to audit chain."""
        if self.audit:
            self.audit.log(
                AuditEventType.SYSTEM_START,
                data={"config": {
                    "warning_threshold": self.config.warning_threshold,
                    "critical_threshold": self.config.critical_threshold,
                    "terminal_threshold": self.config.terminal_threshold,
                }},
            )

        self.timeline.record_event(
            EventCategory.SYSTEM,
            EventSeverity.INFO,
            agent_id="system",
            action="start",
            description="Advanced TIRS engine started",
        )

    def analyze_intent(
        self,
        agent_id: str,
        intent_text: str,
        capabilities: Set[str],
        was_allowed: bool = True,
        policy_triggered: Optional[str] = None,
        context: Optional[BusinessContext] = None,
    ) -> TIRSResult:
        """
        Main entry point: Analyze an intent for drift.

        This method:
        1. Detects drift using multi-signal analysis
        2. Generates human-readable explanation
        3. Applies enforcement if needed
        4. Creates audit trail
        5. Suggests remediation if blocked

        Args:
            agent_id: Agent identifier
            intent_text: Description of the intent
            capabilities: Set of capabilities being used
            was_allowed: Whether the intent passed policy checks
            policy_triggered: Which policy was triggered (if any)
            context: Business context for threshold adjustment

        Returns:
            TIRSResult with full analysis
        """
        timestamp = datetime.now()
        context = context or BusinessContext.from_current()

        # Get current agent status
        profile = self.drift_detector.get_or_create_profile(agent_id)
        previous_status = profile.status

        # Check if agent is already dead
        if profile.status == AgentStatus.KILLED:
            return self._handle_killed_agent(agent_id, timestamp, context)

        # Detect drift
        drift_result = self.drift_detector.detect_drift(
            agent_id=agent_id,
            intent_text=intent_text,
            capabilities=capabilities,
            was_allowed=was_allowed,
            policy_triggered=policy_triggered,
            context=context,
        )

        # Record to dynamic thresholds
        self.dynamic_thresholds.record_score(agent_id, drift_result.risk_score)

        # Generate explanation
        explanation = self.explainer.explain(drift_result, profile)

        # Record timeline event
        self._record_intent_event(agent_id, drift_result, was_allowed, policy_triggered)

        # Determine enforcement action
        action_taken = None
        status_changed = profile.status != previous_status

        if status_changed:
            action_taken = self._handle_status_change(
                agent_id, previous_status, profile.status, drift_result
            )

        # Generate remediation if needed
        remediation_plan = None
        if drift_result.risk_level in [RiskLevel.WARNING, RiskLevel.CRITICAL]:
            remediation_plan = self.remediation.generate_plan(
                agent_id=agent_id,
                risk_score=drift_result.risk_score,
                signals=[
                    {"name": s.name, "raw_value": s.raw_value, "contribution": s.contribution}
                    for s in drift_result.signals
                ],
            )

        # Audit logging
        audit_entry_id = None
        if self.audit:
            event_type = AuditEventType.INTENT_ALLOWED if was_allowed else AuditEventType.INTENT_DENIED
            entry = self.audit.log(
                event_type=event_type,
                agent_id=agent_id,
                data={
                    "intent_text": intent_text[:200],
                    "risk_score": drift_result.risk_score,
                    "risk_level": drift_result.risk_level.value,
                    "capabilities": list(capabilities),
                    "policy_triggered": policy_triggered,
                },
            )
            audit_entry_id = entry.entry_id

        # Update behavioral profile
        self._update_profile(agent_id, capabilities, drift_result.risk_score, not was_allowed)

        # Calculate confidence from signal variance
        # High variance = low confidence (signals disagree)
        # Low variance = high confidence (signals agree)
        signal_contributions = [s.contribution for s in drift_result.signals] if drift_result.signals else []
        if signal_contributions:
            mean_contrib = sum(signal_contributions) / len(signal_contributions)
            variance = sum((x - mean_contrib) ** 2 for x in signal_contributions) / len(signal_contributions)
            std_dev = variance ** 0.5
            # Map std_dev to confidence: 0 std_dev = 1.0 confidence, 0.5+ std_dev = 0.5 confidence
            confidence = max(0.5, 1.0 - min(0.5, std_dev))
        else:
            confidence = 0.5  # No signals = low confidence

        return TIRSResult(
            agent_id=agent_id,
            timestamp=timestamp,
            risk_score=drift_result.risk_score,
            risk_level=drift_result.risk_level,
            confidence=confidence,
            drift_result=drift_result,
            explanation=explanation,
            agent_status=profile.status,
            status_changed=status_changed,
            action_taken=action_taken,
            remediation_plan=remediation_plan,
            audit_entry_id=audit_entry_id,
        )

    def _handle_killed_agent(
        self,
        agent_id: str,
        timestamp: datetime,
        context: BusinessContext,
    ) -> TIRSResult:
        """Handle intent from a killed agent."""
        logger.warning(f"Intent rejected: Agent {agent_id} is KILLED")

        # Create minimal result
        return TIRSResult(
            agent_id=agent_id,
            timestamp=timestamp,
            risk_score=1.0,
            risk_level=RiskLevel.TERMINAL,
            confidence=1.0,
            drift_result=DriftResult(
                agent_id=agent_id,
                risk_score=1.0,
                risk_level=RiskLevel.TERMINAL,
                signals=[],
                status=AgentStatus.KILLED,
                thresholds_applied=self.drift_detector.contextual_thresholds.get_adjusted_thresholds(context),
                context=context,
            ),
            explanation=DriftExplanation(
                agent_id=agent_id,
                overall_score=1.0,
                risk_level=RiskLevel.TERMINAL,
                timestamp=timestamp,
                primary_factor="agent_killed",
                primary_factor_contribution=1.0,
                secondary_factors=[],
                signal_explanations={"agent_killed": "Agent has been terminated"},
                counterfactuals=[],
                remediation_suggestions=[],
                similar_patterns=[],
                summary=f"Agent {agent_id} is KILLED. Submit resurrection appeal to restore.",
            ),
            agent_status=AgentStatus.KILLED,
            status_changed=False,
        )

    def _handle_status_change(
        self,
        agent_id: str,
        old_status: AgentStatus,
        new_status: AgentStatus,
        drift_result: DriftResult,
    ) -> Optional[EnforcementAction]:
        """Handle agent status change with enforcement."""
        action = None

        if new_status == AgentStatus.KILLED:
            # Create forensic snapshot
            profile = self.drift_detector.profiles[agent_id]
            self.snapshots.create_snapshot(
                agent_id=agent_id,
                trigger="kill",
                profile_data=profile.to_dict(),
                environment={"drift_result": drift_result.to_dict()},
            )

            # Execute kill action
            action = create_action(
                ActionType.KILL,
                agent_id,
                f"Risk score {drift_result.risk_score:.2f} exceeded terminal threshold",
                risk_score=drift_result.risk_score,
            )
            self.enforcement.execute(action)

            # Audit
            if self.audit:
                self.audit.log(
                    AuditEventType.AGENT_KILLED,
                    agent_id=agent_id,
                    data={"risk_score": drift_result.risk_score},
                )

        elif new_status == AgentStatus.PAUSED:
            action = create_action(
                ActionType.PAUSE,
                agent_id,
                f"Risk score {drift_result.risk_score:.2f} exceeded critical threshold",
                risk_score=drift_result.risk_score,
            )
            self.enforcement.execute(action)

            if self.audit:
                self.audit.log(
                    AuditEventType.AGENT_PAUSED,
                    agent_id=agent_id,
                    data={"risk_score": drift_result.risk_score},
                )

        elif new_status == AgentStatus.THROTTLED:
            action = create_action(
                ActionType.THROTTLE,
                agent_id,
                f"Risk score {drift_result.risk_score:.2f} in warning range",
                risk_score=drift_result.risk_score,
                rate_limit=self.config.throttle_rate_limit,
                duration_seconds=300,
            )
            self.enforcement.execute(action)

        return action

    def _record_intent_event(
        self,
        agent_id: str,
        drift_result: DriftResult,
        was_allowed: bool,
        policy_triggered: Optional[str],
    ):
        """Record intent to timeline."""
        severity = EventSeverity.INFO
        if drift_result.risk_level == RiskLevel.WARNING:
            severity = EventSeverity.WARNING
        elif drift_result.risk_level in [RiskLevel.CRITICAL, RiskLevel.TERMINAL]:
            severity = EventSeverity.CRITICAL

        self.timeline.record_event(
            EventCategory.INTENT,
            severity,
            agent_id,
            action="intent_processed",
            description=f"Intent processed: risk={drift_result.risk_score:.2f}",
            details={
                "was_allowed": was_allowed,
                "risk_score": drift_result.risk_score,
                "risk_level": drift_result.risk_level.value,
                "policy_triggered": policy_triggered,
            },
        )

    def _update_profile(
        self,
        agent_id: str,
        capabilities: Set[str],
        risk_score: float,
        was_blocked: bool,
    ):
        """Update behavioral profile."""
        # Get or create profile in profile matcher
        if agent_id not in self.profile_matcher.profiles:
            # Determine agent type from ID
            agent_type = agent_id.split("_")[0] if "_" in agent_id else "general"
            profile = BehavioralProfile(agent_id=agent_id, agent_type=agent_type)
            self.profile_matcher.register_profile(profile)
        else:
            profile = self.profile_matcher.profiles[agent_id]

        profile.update(capabilities, risk_score, was_blocked)

    def resurrect_agent(
        self,
        agent_id: str,
        admin_id: str,
        reason: str,
        appeal_id: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Resurrect a killed agent.

        Requires admin approval (or approved appeal).

        Returns:
            (success, message)
        """
        # Check if resurrection is allowed
        can_resurrect, msg = self.appeals.can_resurrect(agent_id)
        if not can_resurrect:
            return False, msg

        # Resurrect in drift detector
        success = self.drift_detector.resurrect_agent(agent_id, admin_id, reason)
        if not success:
            return False, "Agent not found or not in killed state"

        # Record
        if self.audit:
            self.audit.log(
                AuditEventType.AGENT_RESURRECTED,
                agent_id=agent_id,
                user_id=admin_id,
                data={"reason": reason, "appeal_id": appeal_id},
            )

        self.timeline.record_event(
            EventCategory.ENFORCEMENT,
            EventSeverity.WARNING,
            agent_id,
            action="resurrection",
            description=f"Agent resurrected by {admin_id}",
            details={"reason": reason},
        )

        logger.info(f"Agent {agent_id} RESURRECTED by {admin_id}")
        return True, f"Agent {agent_id} resurrected successfully"

    def submit_resurrection_appeal(
        self,
        agent_id: str,
        requestor_id: str,
        reason: str,
        justification: str,
    ) -> AppealRequest:
        """Submit an appeal to resurrect a killed agent."""
        profile = self.drift_detector.profiles.get(agent_id)
        if not profile:
            raise ValueError(f"Agent {agent_id} not found")

        if profile.status != AgentStatus.KILLED:
            raise ValueError(f"Agent {agent_id} is not killed")

        # Find the kill action
        action_history = self.enforcement.get_action_history(agent_id)
        kill_action = next(
            (a for a in reversed(action_history) if a.get("action_type") == "kill"),
            None,
        )
        action_id = kill_action.get("action_id", "unknown") if kill_action else "unknown"

        return self.appeals.submit_appeal(
            appeal_type=AppealType.KILL_RESURRECT,
            agent_id=agent_id,
            requestor_id=requestor_id,
            action_id=action_id,
            reason=reason,
            justification=justification,
        )

    def get_agent_status(self, agent_id: str) -> Dict:
        """Get comprehensive agent status."""
        profile = self.drift_detector.profiles.get(agent_id)
        if not profile:
            return {"agent_id": agent_id, "status": "unknown", "message": "No profile found"}

        behavioral = self.profile_matcher.profiles.get(agent_id)

        return {
            "agent_id": agent_id,
            "status": profile.status.value,
            "risk_score": profile.current_risk_score,
            "total_intents": profile.total_intents,
            "violation_count": profile.violation_count,
            "resurrection_count": profile.resurrection_count,
            "is_throttled": self.enforcement.is_throttled(agent_id),
            "is_paused": self.enforcement.is_paused(agent_id),
            "behavioral_state": behavioral.state.value if behavioral else "unknown",
            "created_at": profile.created_at.isoformat(),
            "last_updated": profile.last_updated.isoformat(),
        }

    def get_risk_dashboard(self) -> Dict:
        """Get system-wide risk dashboard."""
        drift_summary = self.drift_detector.get_risk_summary()
        appeal_stats = self.appeals.get_stats()

        return {
            "timestamp": datetime.now().isoformat(),
            "agents": drift_summary,
            "appeals": appeal_stats,
            "timeline_patterns": self.timeline.detect_patterns("system"),
            "audit_summary": self.audit.get_summary() if self.audit else None,
        }

    def verify_audit_chain(self) -> Tuple[bool, List[str]]:
        """Verify the audit chain integrity."""
        if not self.audit:
            return True, ["Audit chain not enabled"]

        return self.audit.verify_chain()

    def export_agent_forensics(self, agent_id: str, output_dir: str) -> bool:
        """Export complete forensic data for an agent."""
        from pathlib import Path
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Export snapshots
        self.snapshots.export_chain(agent_id, output_path / f"{agent_id}_snapshots.json.gz")

        # Export timeline
        timeline_data = self.timeline.generate_summary(agent_id, hours=168)  # 1 week
        with open(output_path / f"{agent_id}_timeline.json", "w") as f:
            import json
            json.dump(timeline_data, f, indent=2)

        # Export profile
        profile = self.drift_detector.profiles.get(agent_id)
        if profile:
            with open(output_path / f"{agent_id}_profile.json", "w") as f:
                import json
                json.dump(profile.to_dict(), f, indent=2)

        logger.info(f"Forensic data exported to {output_path}")
        return True


# Singleton
_tirs: Optional[AdvancedTIRS] = None


def get_advanced_tirs(config: Optional[TIRSConfig] = None) -> AdvancedTIRS:
    """Get the singleton Advanced TIRS instance."""
    global _tirs
    if _tirs is None:
        _tirs = AdvancedTIRS(config)
    return _tirs


def reset_tirs():
    """Reset the singleton (for testing)."""
    global _tirs
    _tirs = None
