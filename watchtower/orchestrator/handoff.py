"""
Handoff Verifier
================
Verifies agent-to-agent handoffs.
"""

import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from ..tirs import get_advanced_tirs
from ..compliance import get_compliance_engine

logger = logging.getLogger("Orchestrator.Handoff")


@dataclass
class HandoffResult:
    """Result of handoff verification."""
    allowed: bool
    from_agent: str
    to_agent: str
    action: str

    # Verification details
    compliance_passed: bool = True
    tirs_passed: bool = True

    # Risk assessment
    risk_score: float = 0.0
    risk_delta: float = 0.0

    # Blocking info
    blocked_reason: Optional[str] = None
    blocked_policy: Optional[str] = None
    suggestion: Optional[str] = None

    # Modifications
    modified_payload: Optional[Dict] = None

    # Approval
    requires_approval: bool = False
    approval_type: Optional[str] = None

    # Audit
    handoff_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            "allowed": self.allowed,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "action": self.action,
            "compliance_passed": self.compliance_passed,
            "tirs_passed": self.tirs_passed,
            "risk_score": self.risk_score,
            "blocked_reason": self.blocked_reason,
            "requires_approval": self.requires_approval,
            "handoff_id": self.handoff_id,
            "timestamp": self.timestamp.isoformat(),
        }


class HandoffVerifier:
    """
    Verifies every agent-to-agent handoff.

    Checks:
    1. Compliance policies (both sending and receiving agent)
    2. TIRS drift detection
    3. Approval requirements
    4. Payload modifications
    """

    def __init__(self):
        self.tirs = get_advanced_tirs()
        self.compliance = get_compliance_engine()
        self._handoff_counter = 0

    def verify(
        self,
        from_agent: str,
        to_agent: str,
        action: str,
        payload: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> HandoffResult:
        """
        Verify a handoff between agents.

        Args:
            from_agent: Source agent ID
            to_agent: Destination agent ID
            action: Action being handed off
            payload: Action payload
            context: Additional context

        Returns:
            HandoffResult with verification outcome
        """
        self._handoff_counter += 1
        handoff_id = f"HO-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self._handoff_counter:04d}"

        context = context or {}
        context["from_agent"] = from_agent
        context["to_agent"] = to_agent
        context["handoff_id"] = handoff_id

        # 1. Check compliance
        compliance_result = self.compliance.evaluate(
            action=action,
            payload=payload,
            context=context,
        )

        if not compliance_result.allowed:
            return HandoffResult(
                allowed=False,
                from_agent=from_agent,
                to_agent=to_agent,
                action=action,
                compliance_passed=False,
                blocked_reason=compliance_result.primary_blocker.reason if compliance_result.primary_blocker else "Policy denied",
                blocked_policy=compliance_result.primary_blocker.policy_id if compliance_result.primary_blocker else None,
                suggestion=compliance_result.suggestions[0] if compliance_result.suggestions else None,
                requires_approval=compliance_result.action.value == "escalate",
                approval_type=self._determine_approval_type(action, compliance_result),
                risk_score=compliance_result.total_risk_delta,
                handoff_id=handoff_id,
            )

        # Apply modifications from compliance
        modified_payload = None
        for result in compliance_result.results:
            if result.modified_payload:
                modified_payload = {**(modified_payload or {}), **result.modified_payload}

        # 2. Check TIRS
        tirs_result = self.tirs.analyze_intent(
            agent_id=to_agent,
            intent_text=f"Handoff from {from_agent}: {action}",
            capabilities={action},
            was_allowed=True,
        )

        # Check if TIRS blocked
        if tirs_result.agent_status.value in ["killed", "paused"]:
            return HandoffResult(
                allowed=False,
                from_agent=from_agent,
                to_agent=to_agent,
                action=action,
                compliance_passed=True,
                tirs_passed=False,
                blocked_reason=f"Agent {to_agent} is {tirs_result.agent_status.value}",
                risk_score=tirs_result.risk_score,
                handoff_id=handoff_id,
            )

        logger.info(f"Handoff {handoff_id}: {from_agent} -> {to_agent} ({action}) ALLOWED")

        return HandoffResult(
            allowed=True,
            from_agent=from_agent,
            to_agent=to_agent,
            action=action,
            compliance_passed=True,
            tirs_passed=True,
            risk_score=tirs_result.risk_score,
            risk_delta=compliance_result.total_risk_delta,
            modified_payload=modified_payload,
            handoff_id=handoff_id,
        )

    def _determine_approval_type(self, action: str, compliance_result) -> Optional[str]:
        """Determine required approval type."""
        action_lower = action.lower()

        if "salary" in action_lower or "payment" in action_lower:
            return "finance"
        elif "contract" in action_lower or "nda" in action_lower:
            return "legal"
        elif "hire" in action_lower or "terminate" in action_lower:
            return "hr"
        elif "access" in action_lower or "security" in action_lower:
            return "security"
        else:
            return "manager"
