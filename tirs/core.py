"""
TIRS Core Integration
=====================
Main entry point that integrates all TIRS components.

Provides a unified interface for:
- Intent verification with drift detection
- Plan simulation with policy checks
- Signed audit logging
- Remediation suggestions
"""

import logging
from typing import Dict, List, Optional, Set, Any, Tuple
from datetime import datetime

from .drift_engine import DriftEngine, RiskLevel, AgentStatus, get_drift_engine
from .simulator import PlanSimulator, SimulationResult, get_simulator
from .audit import AuditLedger, AuditEventType, get_audit_ledger
from .remediation import RemediationEngine, RemediationResult, get_remediation_engine

logger = logging.getLogger("TIRS")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(name)s] %(levelname)s: %(message)s'
)


class TIRSResult:
    """Result from TIRS verification."""

    def __init__(
        self,
        allowed: bool,
        risk_score: float,
        risk_level: RiskLevel,
        agent_status: AgentStatus,
        simulation: Optional[SimulationResult] = None,
        remediation: Optional[RemediationResult] = None,
        audit_entry_id: Optional[str] = None
    ):
        self.allowed = allowed
        self.risk_score = risk_score
        self.risk_level = risk_level
        self.agent_status = agent_status
        self.simulation = simulation
        self.remediation = remediation
        self.audit_entry_id = audit_entry_id

    def to_dict(self) -> Dict:
        return {
            "allowed": self.allowed,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level.value,
            "agent_status": self.agent_status.value,
            "simulation": self.simulation.to_dict() if self.simulation else None,
            "remediation": self.remediation.to_dict() if self.remediation else None,
            "audit_entry_id": self.audit_entry_id
        }


class TIRS:
    """
    Temporal Intent Risk & Simulation Engine.

    Main interface for TIRS functionality:
    - Verify single intents with drift detection
    - Simulate full plans before execution
    - Get remediation suggestions
    - Access audit logs
    """

    def __init__(self, policy_engine=None):
        """
        Initialize TIRS.

        Args:
            policy_engine: Optional ArmorIQ policy engine for live verification
        """
        self.drift_engine = get_drift_engine()
        self.simulator = get_simulator(policy_engine)
        self.audit = get_audit_ledger()
        self.remediation = get_remediation_engine()

        logger.info("="*60)
        logger.info("  TIRS: Temporal Intent Risk & Simulation")
        logger.info("="*60)
        logger.info("  Components initialized:")
        logger.info("    - Drift Engine (temporal detection)")
        logger.info("    - Plan Simulator (dry-run)")
        logger.info("    - Audit Ledger (signed logs)")
        logger.info("    - Remediation Engine (auto-fix)")
        logger.info("="*60)

    def verify_intent(
        self,
        agent_id: str,
        intent_text: str,
        capabilities: Set[str],
        was_allowed: bool = True,
        policy_triggered: Optional[str] = None
    ) -> Tuple[float, RiskLevel]:
        """
        Verify a single intent and update drift tracking.

        Args:
            agent_id: Agent identifier
            intent_text: Description of the intent
            capabilities: Capabilities requested
            was_allowed: Whether the intent was allowed by policy
            policy_triggered: Policy that blocked/modified (if any)

        Returns:
            Tuple of (risk_score, risk_level)
        """
        # Record in drift engine
        risk_score, risk_level = self.drift_engine.record_intent(
            agent_id=agent_id,
            intent_text=intent_text,
            capabilities=capabilities,
            was_allowed=was_allowed,
            policy_triggered=policy_triggered
        )

        # Log to audit
        verdict = "ALLOW" if was_allowed else "DENY"
        self.audit.log_intent(agent_id, f"INT-{agent_id}", intent_text, verdict, policy_triggered)

        # Log drift events
        if risk_level == RiskLevel.WARNING:
            self.audit.log_drift_warning(agent_id, risk_score, risk_level.value)
        elif risk_level == RiskLevel.PAUSE:
            self.audit.log_agent_paused(agent_id, risk_score, "Drift threshold exceeded")
        elif risk_level == RiskLevel.KILL:
            snapshot = {"risk_score": risk_score, "timestamp": datetime.now().isoformat()}
            self.audit.log_agent_killed(agent_id, risk_score, snapshot)

        return risk_score, risk_level

    def simulate_plan(self, agent_id: str, plan: List[Dict]) -> TIRSResult:
        """
        Simulate a full plan before execution.

        Args:
            agent_id: Agent identifier
            plan: List of plan steps

        Returns:
            TIRSResult with simulation details and recommendations
        """
        # Check agent status first
        status = self.drift_engine.get_agent_status(agent_id)
        if status == AgentStatus.KILLED:
            logger.warning(f"Agent {agent_id} is KILLED, cannot simulate")
            return TIRSResult(
                allowed=False,
                risk_score=1.0,
                risk_level=RiskLevel.KILL,
                agent_status=AgentStatus.KILLED
            )

        if status == AgentStatus.PAUSED:
            logger.warning(f"Agent {agent_id} is PAUSED, cannot simulate")
            return TIRSResult(
                allowed=False,
                risk_score=0.8,
                risk_level=RiskLevel.PAUSE,
                agent_status=AgentStatus.PAUSED
            )

        # Run simulation
        sim_result = self.simulator.simulate_plan(agent_id, plan)

        # Log simulation
        audit_entry = self.audit.log_simulation(agent_id, sim_result.plan_id, sim_result.to_dict())

        # Track intent for drift detection
        plan_text = f"Plan with {len(plan)} steps: " + ", ".join(
            f"{s.get('mcp', 'Unknown')}.{s.get('action', 'unknown')}" for s in plan[:3]
        )
        risk_score, risk_level = self.verify_intent(
            agent_id=agent_id,
            intent_text=plan_text,
            capabilities=set(sim_result.capabilities_requested),
            was_allowed=sim_result.is_allowed,
            policy_triggered=None
        )

        # Generate remediation if blocked
        remediation = None
        if not sim_result.is_allowed:
            # Find first blocked step
            blocked_step = next((s for s in sim_result.steps if s.verdict.value == "DENY"), None)
            if blocked_step:
                remediation = self.remediation.analyze(
                    action=f"{blocked_step.mcp}.{blocked_step.action}",
                    args=blocked_step.args,
                    policy_violated=blocked_step.policy_triggered or "Unknown",
                    block_reason=blocked_step.reason
                )

        return TIRSResult(
            allowed=sim_result.is_allowed,
            risk_score=risk_score,
            risk_level=risk_level,
            agent_status=status or AgentStatus.ACTIVE,
            simulation=sim_result,
            remediation=remediation,
            audit_entry_id=audit_entry.entry_id
        )

    def what_if(self, agent_id: str, plan: List[Dict]) -> SimulationResult:
        """
        Run a what-if simulation without affecting drift tracking.

        Args:
            agent_id: Agent identifier
            plan: Plan to simulate

        Returns:
            SimulationResult (doesn't affect drift profile)
        """
        return self.simulator.what_if(agent_id, plan)

    def get_agent_status(self, agent_id: str) -> Dict:
        """Get current status and risk info for an agent."""
        profile = self.drift_engine.profiles.get(agent_id)
        if not profile:
            return {"agent_id": agent_id, "status": "unknown", "message": "No profile found"}

        return profile.to_dict()

    def resume_agent(self, agent_id: str) -> bool:
        """Resume a paused agent (requires admin approval context)."""
        result = self.drift_engine.resume_agent(agent_id)
        if result:
            self.audit.log(AuditEventType.AGENT_RESUMED, agent_id, {"resumed_at": datetime.now().isoformat()})
        return result

    def get_risk_summary(self) -> Dict:
        """Get summary of all agent risks."""
        return self.drift_engine.get_risk_summary()

    def get_audit_summary(self) -> Dict:
        """Get audit ledger summary."""
        return self.audit.get_summary()

    def verify_audit_chain(self) -> Tuple[bool, List[str]]:
        """Verify the audit chain integrity."""
        return self.audit.verify_chain()

    def record_intent(
        self,
        agent_id: str,
        action: str,
        capabilities: List[str],
        was_violation: bool = False
    ):
        """Simple interface to record an intent for drift tracking."""
        self.verify_intent(
            agent_id=agent_id,
            intent_text=action,
            capabilities=set(capabilities),
            was_allowed=not was_violation,
            policy_triggered="policy_violation" if was_violation else None
        )

    def get_risk_score(self, agent_id: str) -> float:
        """Get current risk score for an agent."""
        profile = self.drift_engine.profiles.get(agent_id)
        if not profile:
            return 0.0
        return profile.current_risk_score

    def get_risk_level(self, agent_id: str) -> RiskLevel:
        """Get current risk level for an agent based on score."""
        score = self.get_risk_score(agent_id)
        thresholds = self.drift_engine.thresholds
        if score >= thresholds.kill:
            return RiskLevel.KILL
        elif score >= thresholds.pause:
            return RiskLevel.PAUSE
        elif score >= thresholds.warning:
            return RiskLevel.WARNING
        return RiskLevel.OK

    def get_drift_history(self, agent_id: str) -> List[Dict]:
        """Get drift score history for an agent."""
        profile = self.drift_engine.profiles.get(agent_id)
        if not profile:
            return []

        # Return risk history
        history = []
        risk_scores = profile.risk_history[-10:] if profile.risk_history else [0.0]

        for i, score in enumerate(risk_scores):
            history.append({
                "time": f"{9 + i}:00",
                "score": score
            })

        if not history:
            history.append({
                "time": datetime.now().strftime("%H:%M"),
                "score": profile.current_risk_score
            })

        return history

    def get_audit_log(self, limit: int = 50) -> List[Dict]:
        """Get recent audit log entries."""
        entries = self.audit.entries[-limit:] if hasattr(self.audit, 'entries') else []
        return [
            {
                "id": i,
                "time": e.timestamp.strftime("%H:%M:%S") if hasattr(e, 'timestamp') else "00:00:00",
                "agent": e.agent_id if hasattr(e, 'agent_id') else "unknown",
                "event": e.event_type.value if hasattr(e, 'event_type') else "unknown",
                "details": str(e.data)[:100] if hasattr(e, 'data') else ""
            }
            for i, e in enumerate(reversed(entries))
        ]

    def export_audit(self, filepath: str):
        """Export the audit ledger to JSON."""
        self.audit.export_json(filepath)


# Singleton instance
_tirs: Optional[TIRS] = None


def get_tirs(policy_engine=None) -> TIRS:
    """Get the singleton TIRS instance."""
    global _tirs
    if _tirs is None:
        _tirs = TIRS(policy_engine)
    return _tirs


def verify_intent(
    agent_id: str,
    intent_text: str,
    capabilities: Set[str],
    was_allowed: bool = True,
    policy_triggered: Optional[str] = None
) -> Tuple[float, RiskLevel]:
    """Convenience function to verify intent."""
    return get_tirs().verify_intent(agent_id, intent_text, capabilities, was_allowed, policy_triggered)


def simulate_plan(agent_id: str, plan: List[Dict]) -> TIRSResult:
    """Convenience function to simulate plan."""
    return get_tirs().simulate_plan(agent_id, plan)
