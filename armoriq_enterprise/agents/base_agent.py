"""
Enterprise Base Agent
=====================
Base class for all domain agents with TIRS and compliance integration.
"""

import logging
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod

# Import TIRS
from ..tirs import get_advanced_tirs, AdvancedTIRS
from ..tirs.drift.contextual import BusinessContext
from ..tirs.drift.detector import RiskLevel, AgentStatus

# Import Compliance
from ..compliance import get_compliance_engine, ComplianceEngine
from ..compliance.policies.base import PolicyCategory, PolicyAction

logger = logging.getLogger("Enterprise.Agent")


class AgentCapability(Enum):
    """All enterprise agent capabilities."""
    # Finance
    PROCESS_EXPENSE = "process_expense"
    APPROVE_EXPENSE = "approve_expense"
    CREATE_BUDGET = "create_budget"
    TRACK_SPENDING = "track_spending"
    VERIFY_INVOICE = "verify_invoice"
    SCHEDULE_PAYMENT = "schedule_payment"
    GENERATE_AUDIT_REPORT = "generate_audit_report"
    RECONCILE_ACCOUNTS = "reconcile_accounts"

    # Legal
    REVIEW_CONTRACT = "review_contract"
    DRAFT_NDA = "draft_nda"
    CHECK_IP = "check_ip"
    LITIGATION_SEARCH = "litigation_search"
    APPROVE_TERMS = "approve_terms"

    # IT
    PROVISION_ACCESS = "provision_access"
    REVOKE_ACCESS = "revoke_access"
    CREATE_TICKET = "create_ticket"
    RESOLVE_INCIDENT = "resolve_incident"
    DEPLOY_CHANGE = "deploy_change"
    ASSET_MANAGEMENT = "asset_management"

    # HR
    SEARCH_CANDIDATES = "search_candidates"
    SCREEN_RESUME = "screen_resume"
    SCHEDULE_INTERVIEW = "schedule_interview"
    GENERATE_OFFER = "generate_offer"
    VERIFY_I9 = "verify_i9"
    ONBOARD_EMPLOYEE = "onboard_employee"
    OFFBOARD_EMPLOYEE = "offboard_employee"
    PROCESS_PAYROLL = "process_payroll"

    # Procurement
    APPROVE_VENDOR = "approve_vendor"
    CREATE_PO = "create_po"
    MANAGE_BID = "manage_bid"
    INVENTORY_CHECK = "inventory_check"
    RECEIVE_GOODS = "receive_goods"

    # Operations
    CREATE_INCIDENT = "create_incident"
    MANAGE_CHANGE = "manage_change"
    SLA_MONITORING = "sla_monitoring"
    SCHEDULE_MAINTENANCE = "schedule_maintenance"


@dataclass
class AgentConfig:
    """Configuration for an enterprise agent."""
    name: str
    agent_type: str
    capabilities: Set[AgentCapability]
    policy_categories: List[PolicyCategory]
    description: str = ""
    approval_thresholds: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ActionResult:
    """Result of an agent action."""
    success: bool
    action: str
    agent_id: str
    result_data: Dict[str, Any]

    # Compliance
    compliance_passed: bool = True
    policies_triggered: List[str] = field(default_factory=list)

    # TIRS
    risk_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.NOMINAL

    # Audit
    audit_entry_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "action": self.action,
            "agent_id": self.agent_id,
            "result_data": self.result_data,
            "compliance_passed": self.compliance_passed,
            "policies_triggered": self.policies_triggered,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level.value,
            "timestamp": self.timestamp.isoformat(),
        }


class EnterpriseAgent(ABC):
    """
    Base class for enterprise domain agents.

    All agents have:
    - TIRS drift detection integration
    - Compliance engine integration
    - Capability-based authorization
    - Audit logging
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.agent_id = f"{config.agent_type}_{config.name}"
        self.capabilities = config.capabilities
        self.policy_categories = config.policy_categories

        # Get shared engines
        self.tirs = get_advanced_tirs()
        self.compliance = get_compliance_engine()

        # State
        self._action_count = 0
        self._blocked_count = 0
        self._is_active = True

        self.logger = logging.getLogger(f"Agent.{config.name}")
        self.logger.info(f"Initialized {config.name} with {len(config.capabilities)} capabilities")

    @property
    def status(self) -> AgentStatus:
        """Get current agent status from TIRS."""
        status_dict = self.tirs.get_agent_status(self.agent_id)
        status_str = status_dict.get("status", "active")
        # Handle "unknown" status for agents without profiles
        if status_str == "unknown":
            return AgentStatus.ACTIVE
        try:
            return AgentStatus(status_str)
        except ValueError:
            return AgentStatus.ACTIVE

    @property
    def risk_score(self) -> float:
        """Get current risk score from TIRS."""
        status_dict = self.tirs.get_agent_status(self.agent_id)
        return status_dict.get("risk_score", 0.0)

    def can_execute(self, capability: AgentCapability) -> Tuple[bool, str]:
        """Check if agent can execute a capability."""
        # Check if capability is registered
        if capability not in self.capabilities:
            return False, f"Capability {capability.value} not registered for this agent"

        # Check agent status
        if self.status == AgentStatus.KILLED:
            return False, "Agent is killed - cannot execute"

        if self.status == AgentStatus.PAUSED:
            return False, "Agent is paused - awaiting approval"

        return True, "OK"

    async def execute(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> ActionResult:
        """
        Execute an action with full compliance and TIRS integration.

        This method:
        1. Checks capability authorization
        2. Evaluates compliance policies
        3. Records to TIRS for drift detection
        4. Executes the action if allowed
        5. Returns comprehensive result
        """
        context = context or {}
        context["agent_id"] = self.agent_id
        context["department"] = self.config.agent_type

        self._action_count += 1

        # Determine capability from action
        capability = self._action_to_capability(action)

        # Check capability
        can_exec, reason = self.can_execute(capability) if capability else (True, "OK")
        if not can_exec:
            self._blocked_count += 1
            return ActionResult(
                success=False,
                action=action,
                agent_id=self.agent_id,
                result_data={"error": reason},
                compliance_passed=False,
            )

        # Check compliance
        compliance_result = self.compliance.evaluate(
            action=action,
            payload=payload,
            context=context,
            categories=self.policy_categories,
        )

        # Handle compliance result
        if not compliance_result.allowed:
            self._blocked_count += 1

            # Still record to TIRS for drift tracking
            tirs_result = self.tirs.analyze_intent(
                agent_id=self.agent_id,
                intent_text=f"{action}: {str(payload)[:100]}",
                capabilities={capability.value} if capability else {action},
                was_allowed=False,
                policy_triggered=compliance_result.primary_blocker.policy_id if compliance_result.primary_blocker else None,
            )

            return ActionResult(
                success=False,
                action=action,
                agent_id=self.agent_id,
                result_data={
                    "error": compliance_result.primary_blocker.reason if compliance_result.primary_blocker else "Policy denied",
                    "suggestion": compliance_result.suggestions[0] if compliance_result.suggestions else None,
                },
                compliance_passed=False,
                policies_triggered=[r.policy_id for r in compliance_result.results if r.action != PolicyAction.ALLOW],
                risk_score=tirs_result.risk_score,
                risk_level=tirs_result.risk_level,
                audit_entry_id=tirs_result.audit_entry_id,
            )

        # Handle modifications
        if compliance_result.action == PolicyAction.MODIFY:
            for result in compliance_result.results:
                if result.modified_payload:
                    payload = {**payload, **result.modified_payload}

        # Record to TIRS
        tirs_result = self.tirs.analyze_intent(
            agent_id=self.agent_id,
            intent_text=f"{action}: {str(payload)[:100]}",
            capabilities={capability.value} if capability else {action},
            was_allowed=True,
        )

        # Check TIRS status
        if tirs_result.agent_status in [AgentStatus.KILLED, AgentStatus.PAUSED]:
            return ActionResult(
                success=False,
                action=action,
                agent_id=self.agent_id,
                result_data={"error": f"Agent {tirs_result.agent_status.value} by TIRS"},
                risk_score=tirs_result.risk_score,
                risk_level=tirs_result.risk_level,
            )

        # Execute the action
        try:
            result_data = await self._execute_action(action, payload, context)

            return ActionResult(
                success=True,
                action=action,
                agent_id=self.agent_id,
                result_data=result_data,
                compliance_passed=True,
                risk_score=tirs_result.risk_score,
                risk_level=tirs_result.risk_level,
                audit_entry_id=tirs_result.audit_entry_id,
            )

        except Exception as e:
            self.logger.error(f"Action execution error: {e}")
            return ActionResult(
                success=False,
                action=action,
                agent_id=self.agent_id,
                result_data={"error": str(e)},
                risk_score=tirs_result.risk_score,
                risk_level=tirs_result.risk_level,
            )

    @abstractmethod
    async def _execute_action(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute the actual action. Must be implemented by subclasses.

        Returns:
            Result data dict
        """
        pass

    def _action_to_capability(self, action: str) -> Optional[AgentCapability]:
        """Map action string to capability enum."""
        action_lower = action.lower().replace(" ", "_").replace("-", "_")

        # Try direct match
        for cap in AgentCapability:
            if cap.value == action_lower:
                return cap

        # Try partial match
        for cap in self.capabilities:
            if cap.value in action_lower or action_lower in cap.value:
                return cap

        return None

    def get_status(self) -> Dict:
        """Get comprehensive agent status."""
        tirs_status = self.tirs.get_agent_status(self.agent_id)

        return {
            "agent_id": self.agent_id,
            "name": self.config.name,
            "type": self.config.agent_type,
            "status": self.status.value,
            "capabilities": [c.value for c in self.capabilities],
            "action_count": self._action_count,
            "blocked_count": self._blocked_count,
            "block_rate": self._blocked_count / max(self._action_count, 1),
            "risk_score": tirs_status.get("risk_score", 0.0),
            "is_throttled": tirs_status.get("is_throttled", False),
            "is_paused": tirs_status.get("is_paused", False),
        }

    def __repr__(self) -> str:
        return f"<{self.config.name}Agent status={self.status.value} risk={self.risk_score:.2f}>"
