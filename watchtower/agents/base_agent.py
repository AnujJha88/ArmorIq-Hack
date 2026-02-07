"""
Enterprise Base Agent
=====================
Base class for all domain agents with:
- Watchtower SDK integration (Intent Authentication Protocol)
- TIRS drift detection
- Compliance engine
- LLM-powered autonomous reasoning

The Triple-Layer Security Stack:
1. Watchtower IAP - Cryptographic intent verification
2. TIRS - Behavioral drift detection
3. LLM Reasoning - Intelligent edge case handling
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

# Import LLM for autonomous reasoning
from ..llm import get_enterprise_llm, get_reasoning_engine
from ..llm.service import DecisionContext, DecisionType
from ..llm.reasoning import ReasoningMode

# Import Watchtower Integration
from ..integrations import get_watchtower, WatchtowerOne

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

    # Watchtower layer
    watchtower_passed: bool = True
    watchtower_intent_id: Optional[str] = None
    watchtower_verdict: Optional[str] = None

    # Compliance layer
    compliance_passed: bool = True
    policies_triggered: List[str] = field(default_factory=list)

    # TIRS layer
    risk_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.NOMINAL
    tirs_passed: bool = True

    # LLM Reasoning layer
    reasoning: Optional[str] = None
    confidence: float = 1.0
    decision_type: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Escalation
    escalation_required: bool = False
    blocking_layer: Optional[str] = None

    # Audit
    audit_entry_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "action": self.action,
            "agent_id": self.agent_id,
            "result_data": self.result_data,
            "watchtower_passed": self.watchtower_passed,
            "watchtower_intent_id": self.watchtower_intent_id,
            "watchtower_verdict": self.watchtower_verdict,
            "compliance_passed": self.compliance_passed,
            "policies_triggered": self.policies_triggered,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level.value,
            "tirs_passed": self.tirs_passed,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "decision_type": self.decision_type,
            "recommendations": self.recommendations,
            "warnings": self.warnings,
            "escalation_required": self.escalation_required,
            "blocking_layer": self.blocking_layer,
            "timestamp": self.timestamp.isoformat(),
        }


class EnterpriseAgent(ABC):
    """
    Base class for enterprise domain agents.

    All agents have:
    - Watchtower SDK integration (Intent Authentication Protocol)
    - TIRS drift detection integration
    - Compliance engine integration
    - Capability-based authorization
    - Audit logging
    - LLM-powered autonomous reasoning

    The Triple-Layer Security Stack ensures all actions go through:
    1. Watchtower IAP - Cryptographic intent verification
    2. TIRS - Behavioral drift detection
    3. LLM - Intelligent reasoning for edge cases
    """

    # Autonomous mode settings
    AUTONOMOUS_MODE = True  # Enable/disable autonomous reasoning
    AUTO_APPROVE_THRESHOLD = 0.85  # Confidence threshold for auto-approve
    ESCALATION_THRESHOLD = 0.5  # Below this, escalate to human

    def __init__(self, config: AgentConfig):
        self.config = config
        self.agent_id = f"{config.agent_type}_{config.name}"
        self.capabilities = config.capabilities
        self.policy_categories = config.policy_categories

        # Watchtower Integration (Layer 1)
        self.watchtower = get_watchtower()

        # TIRS Engine (Layer 2)
        self.tirs = get_advanced_tirs()

        # Compliance Engine
        self.compliance = get_compliance_engine()

        # LLM for autonomous reasoning (Layer 3)
        self.llm = get_enterprise_llm()
        self.reasoning_engine = get_reasoning_engine()

        # State
        self._action_count = 0
        self._blocked_count = 0
        self._autonomous_decisions = 0
        self._escalated_count = 0
        self._watchtower_blocked = 0
        self._tirs_blocked = 0
        self._is_active = True

        self.logger = logging.getLogger(f"Agent.{config.name}")
        self.logger.info(
            f"Initialized {config.name} with {len(config.capabilities)} capabilities "
            f"(Watchtower={self.watchtower.mode}, autonomous={self.AUTONOMOUS_MODE})"
        )

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

    async def autonomous_execute(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        reasoning_mode: ReasoningMode = ReasoningMode.STANDARD,
    ) -> ActionResult:
        """
        Execute an action with AUTONOMOUS LLM-powered decision-making.

        This method:
        1. Uses LLM to understand the intent
        2. Reasons about whether to proceed
        3. Makes intelligent decisions with explanations
        4. Handles edge cases and uncertainties
        5. Provides recommendations and warnings

        Args:
            action: Action to perform
            payload: Action parameters
            context: Request context
            reasoning_mode: How deep to reason (QUICK, STANDARD, DEEP, CRITICAL)

        Returns:
            ActionResult with reasoning and confidence
        """
        context = context or {}
        context["agent_id"] = self.agent_id
        context["department"] = self.config.agent_type

        self._action_count += 1
        self._autonomous_decisions += 1

        # Determine capability
        capability = self._action_to_capability(action)

        # Check basic capability
        can_exec, reason = self.can_execute(capability) if capability else (True, "OK")
        if not can_exec:
            self._blocked_count += 1
            return ActionResult(
                success=False,
                action=action,
                agent_id=self.agent_id,
                result_data={"error": reason},
                compliance_passed=False,
                reasoning="Capability check failed",
                confidence=1.0,
                decision_type="deny",
            )

        # Get compliance result
        compliance_result = self.compliance.evaluate(
            action=action,
            payload=payload,
            context=context,
            categories=self.policy_categories,
        )

        # Get TIRS analysis
        tirs_result = self.tirs.analyze_intent(
            agent_id=self.agent_id,
            intent_text=f"{action}: {str(payload)[:100]}",
            capabilities={capability.value} if capability else {action},
            was_allowed=compliance_result.allowed,
        )

        # Use LLM reasoning engine for intelligent decision
        reasoning_result = self.reasoning_engine.reason_about_action(
            agent_id=self.agent_id,
            action=action,
            payload=payload,
            context=context,
            compliance_result={
                "allowed": compliance_result.allowed,
                "policies_triggered": [r.policy_id for r in compliance_result.results if r.action != PolicyAction.ALLOW],
                "suggestions": compliance_result.suggestions,
            },
            tirs_result={
                "risk_score": tirs_result.risk_score,
                "risk_level": tirs_result.risk_level.value,
                "agent_status": tirs_result.agent_status.value,
            },
            mode=reasoning_mode,
        )

        # Log the reasoning
        self.logger.info(
            f"[AUTONOMOUS] {action}: proceed={reasoning_result.should_proceed}, "
            f"confidence={reasoning_result.overall_confidence:.2f}, "
            f"decision={reasoning_result.decision.decision_type.value}"
        )

        # Handle escalation
        if reasoning_result.decision.decision_type == DecisionType.ESCALATE:
            self._escalated_count += 1
            return ActionResult(
                success=False,
                action=action,
                agent_id=self.agent_id,
                result_data={
                    "status": "escalated",
                    "escalate_to": reasoning_result.decision.escalate_to,
                    "reason": reasoning_result.decision.escalation_reason,
                },
                compliance_passed=compliance_result.allowed,
                risk_score=tirs_result.risk_score,
                risk_level=tirs_result.risk_level,
                reasoning=reasoning_result.decision.reasoning,
                confidence=reasoning_result.overall_confidence,
                decision_type="escalate",
                recommendations=reasoning_result.recommendations,
                warnings=reasoning_result.warnings,
            )

        # If reasoning says don't proceed
        if not reasoning_result.should_proceed:
            self._blocked_count += 1
            return ActionResult(
                success=False,
                action=action,
                agent_id=self.agent_id,
                result_data={
                    "status": "blocked_by_reasoning",
                    "reason": reasoning_result.decision.reasoning,
                },
                compliance_passed=compliance_result.allowed,
                policies_triggered=[r.policy_id for r in compliance_result.results if r.action != PolicyAction.ALLOW],
                risk_score=tirs_result.risk_score,
                risk_level=tirs_result.risk_level,
                reasoning=reasoning_result.decision.reasoning,
                confidence=reasoning_result.overall_confidence,
                decision_type=reasoning_result.decision.decision_type.value,
                recommendations=reasoning_result.recommendations,
                warnings=reasoning_result.warnings,
            )

        # Apply modifications if decision suggests them
        if reasoning_result.decision.modified_payload:
            payload = {**payload, **reasoning_result.decision.modified_payload}
            self.logger.info(f"[AUTONOMOUS] Payload modified by reasoning")

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
                reasoning=reasoning_result.decision.reasoning,
                confidence=reasoning_result.overall_confidence,
                decision_type=reasoning_result.decision.decision_type.value,
                recommendations=reasoning_result.recommendations,
                warnings=reasoning_result.warnings,
                audit_entry_id=tirs_result.audit_entry_id,
            )

        except Exception as e:
            self.logger.error(f"[AUTONOMOUS] Action execution error: {e}")

            # Use LLM to suggest recovery
            recovery = self.llm.suggest_recovery(
                failed_action=action,
                error=str(e),
                available_alternatives=[c.value for c in self.capabilities],
                context=context,
            )

            return ActionResult(
                success=False,
                action=action,
                agent_id=self.agent_id,
                result_data={
                    "error": str(e),
                    "recovery_suggestions": recovery.get("suggestions", []),
                    "escalation_needed": recovery.get("escalation_needed", True),
                },
                risk_score=tirs_result.risk_score,
                risk_level=tirs_result.risk_level,
                reasoning=f"Execution failed: {e}",
                confidence=0.0,
                decision_type="failed",
                recommendations=[s.get("option", "") for s in recovery.get("suggestions", [])],
                warnings=["Action failed during execution"],
            )

    async def execute_unified(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> ActionResult:
        """
        Execute an action through the UNIFIED Triple-Layer Security Stack.

        This is the recommended execution method that uses:
        1. Watchtower IAP - Intent verification
        2. TIRS - Drift detection
        3. LLM - Reasoning for edge cases

        Args:
            action: Action to perform
            payload: Action parameters
            context: Request context

        Returns:
            ActionResult with comprehensive verification info
        """
        context = context or {}
        context["agent_id"] = self.agent_id
        context["department"] = self.config.agent_type

        self._action_count += 1

        # Determine capability
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
                blocking_layer="capability",
            )

        # ─────────────────────────────────────────────────────────────────────
        # UNIFIED VERIFICATION: Watchtower + TIRS + LLM
        # ─────────────────────────────────────────────────────────────────────
        verification = self.watchtower.verify_intent(
            agent_id=self.agent_id,
            action=action,
            payload=payload,
            context=context,
        )

        # Log the verification
        self.logger.info(
            f"[UNIFIED] {action}: allowed={verification.allowed}, "
            f"confidence={verification.confidence:.2f}, risk={verification.risk_level}"
        )

        # Handle blocking
        if not verification.allowed:
            self._blocked_count += 1

            if verification.blocking_layer == "Watchtower":
                self._watchtower_blocked += 1
            elif verification.blocking_layer == "TIRS":
                self._tirs_blocked += 1

            return ActionResult(
                success=False,
                action=action,
                agent_id=self.agent_id,
                result_data={
                    "error": f"Blocked by {verification.blocking_layer}",
                    "reason": verification.watchtower_result.reason if verification.watchtower_result else "Unknown",
                },
                watchtower_passed=verification.watchtower_passed,
                watchtower_intent_id=verification.intent_id,
                watchtower_verdict=verification.watchtower_result.verdict.value if verification.watchtower_result else None,
                risk_score=verification.tirs_score,
                risk_level=RiskLevel(verification.tirs_level) if verification.tirs_level != "nominal" else RiskLevel.NOMINAL,
                tirs_passed=verification.tirs_passed,
                confidence=verification.confidence,
                reasoning=verification.llm_reasoning,
                escalation_required=verification.escalation_required,
                blocking_layer=verification.blocking_layer,
            )

        # Handle escalation
        if verification.escalation_required:
            self._escalated_count += 1
            return ActionResult(
                success=False,
                action=action,
                agent_id=self.agent_id,
                result_data={
                    "status": "escalated",
                    "reason": "Requires human approval",
                },
                watchtower_passed=verification.watchtower_passed,
                watchtower_intent_id=verification.intent_id,
                risk_score=verification.tirs_score,
                tirs_passed=verification.tirs_passed,
                confidence=verification.confidence,
                reasoning=verification.llm_reasoning,
                escalation_required=True,
                decision_type="escalate",
            )

        # Handle payload modifications
        if verification.modified_payload:
            payload = verification.modified_payload

        # ─────────────────────────────────────────────────────────────────────
        # EXECUTE ACTION
        # ─────────────────────────────────────────────────────────────────────
        try:
            result_data = await self._execute_action(action, payload, context)

            return ActionResult(
                success=True,
                action=action,
                agent_id=self.agent_id,
                result_data=result_data,
                watchtower_passed=True,
                watchtower_intent_id=verification.intent_id,
                watchtower_verdict="ALLOW",
                risk_score=verification.tirs_score,
                risk_level=RiskLevel(verification.tirs_level) if verification.tirs_level != "nominal" else RiskLevel.NOMINAL,
                tirs_passed=True,
                confidence=verification.confidence,
                reasoning=verification.llm_reasoning,
                decision_type="approve",
            )

        except Exception as e:
            self.logger.error(f"[UNIFIED] Execution error: {e}")
            return ActionResult(
                success=False,
                action=action,
                agent_id=self.agent_id,
                result_data={"error": str(e)},
                watchtower_passed=True,
                risk_score=verification.tirs_score,
                reasoning=f"Execution failed: {e}",
                confidence=0.0,
                decision_type="failed",
            )

    async def understand_request(self, natural_language_request: str) -> Dict[str, Any]:
        """
        Use LLM to understand a natural language request.

        Args:
            natural_language_request: Human language request

        Returns:
            Dict with intent, action, parameters
        """
        available_actions = [c.value for c in self.capabilities]
        return self.llm.understand_intent(natural_language_request, available_actions)

    async def explain_last_decision(self) -> str:
        """Get a human-readable explanation of the last decision."""
        # This would be implemented with decision history
        return "No recent decision to explain"

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
        watchtower_status = self.watchtower.get_status()

        return {
            "agent_id": self.agent_id,
            "name": self.config.name,
            "type": self.config.agent_type,
            "status": self.status.value,
            "capabilities": [c.value for c in self.capabilities],
            "action_count": self._action_count,
            "blocked_count": self._blocked_count,
            "block_rate": self._blocked_count / max(self._action_count, 1),
            # Watchtower layer
            "watchtower_mode": watchtower_status.get("mode", "DEMO"),
            "watchtower_blocked": self._watchtower_blocked,
            # TIRS layer
            "risk_score": tirs_status.get("risk_score", 0.0),
            "is_throttled": tirs_status.get("is_throttled", False),
            "is_paused": tirs_status.get("is_paused", False),
            "tirs_blocked": self._tirs_blocked,
            # LLM layer
            "autonomous_mode": self.AUTONOMOUS_MODE,
            "autonomous_decisions": self._autonomous_decisions,
            "escalated_count": self._escalated_count,
            "llm_mode": self.llm.mode.value if self.llm else "unavailable",
            # Triple-layer summary
            "security_stack": {
                "watchtower": watchtower_status.get("mode", "DEMO"),
                "tirs": "active",
                "llm": "active" if self.llm else "unavailable",
            },
        }

    def __repr__(self) -> str:
        return f"<{self.config.name}Agent status={self.status.value} risk={self.risk_score:.2f}>"
