"""
Enterprise Gateway
==================
Root ADK-style orchestrator for the enterprise agentic system.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from ..tirs import get_advanced_tirs, AdvancedTIRS
from ..compliance import get_compliance_engine, ComplianceEngine
from ..agents import (
    EnterpriseAgent,
    FinanceAgent,
    LegalAgent,
    ITAgent,
    HRAgent,
    ProcurementAgent,
    OperationsAgent,
)
from .router import CapabilityRouter
from .handoff import HandoffVerifier
from .workflows import (
    WorkflowEngine,
    SequentialWorkflow,
    ParallelWorkflow,
    WorkflowResult,
)

logger = logging.getLogger("Enterprise.Gateway")


@dataclass
class GatewayConfig:
    """Configuration for the enterprise gateway."""
    enable_tirs: bool = True
    enable_compliance: bool = True
    enable_audit: bool = True
    max_concurrent_workflows: int = 5
    default_timeout_seconds: int = 300


@dataclass
class RequestResult:
    """Result of a gateway request."""
    success: bool
    request_id: str
    action: str

    # Routing
    routed_to: Optional[str] = None

    # Execution
    result_data: Optional[Dict] = None
    error: Optional[str] = None

    # Compliance
    compliance_passed: bool = True
    policies_triggered: List[str] = field(default_factory=list)

    # TIRS
    risk_score: float = 0.0
    risk_level: str = "nominal"

    # Timing
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "request_id": self.request_id,
            "action": self.action,
            "routed_to": self.routed_to,
            "result_data": self.result_data,
            "error": self.error,
            "compliance_passed": self.compliance_passed,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
        }


class EnterpriseGateway:
    """
    Root orchestrator for the ArmorIQ Enterprise Agentic System.

    This is the main entry point that:
    1. Receives user/system requests
    2. Routes to appropriate domain agents
    3. Coordinates multi-agent workflows
    4. Enforces compliance at every handoff
    5. Tracks drift across all agents
    """

    def __init__(self, config: Optional[GatewayConfig] = None):
        self.config = config or GatewayConfig()

        # Core engines
        self.tirs = get_advanced_tirs() if self.config.enable_tirs else None
        self.compliance = get_compliance_engine() if self.config.enable_compliance else None

        # Orchestration components
        self.router = CapabilityRouter()
        self.handoff_verifier = HandoffVerifier()
        self.workflow_engine = WorkflowEngine()

        # Agents
        self.agents: Dict[str, EnterpriseAgent] = {}

        # State
        self._request_counter = 0
        self._initialized = False

        logger.info("=" * 70)
        logger.info("  ARMORIQ ENTERPRISE GATEWAY")
        logger.info("=" * 70)

    async def initialize(self):
        """Initialize the gateway with all domain agents."""
        if self._initialized:
            return

        logger.info("Initializing domain agents...")

        # Create all domain agents
        agent_classes = [
            FinanceAgent,
            LegalAgent,
            ITAgent,
            HRAgent,
            ProcurementAgent,
            OperationsAgent,
        ]

        for agent_class in agent_classes:
            agent = agent_class()
            self.agents[agent.agent_id] = agent
            self.router.register_agent(agent)
            logger.info(f"  Registered: {agent.config.name} ({len(agent.capabilities)} capabilities)")

        # Register workflow templates
        self._register_workflow_templates()

        self._initialized = True
        logger.info(f"Gateway initialized with {len(self.agents)} agents")
        logger.info("=" * 70)

    def _register_workflow_templates(self):
        """Register common workflow templates."""
        # New Hire Workflow
        new_hire = SequentialWorkflow("wf_new_hire", "New Hire Onboarding")
        new_hire.add_step("search_candidates", {"count": 10}, agent_type="hr")
        new_hire.add_step("screen_resume", {}, agent_type="hr")
        new_hire.add_step("schedule_interview", {}, agent_type="hr")
        new_hire.add_step("generate_offer", {}, agent_type="hr")
        new_hire.add_step("verify_i9", {}, agent_type="hr")
        new_hire.add_step("provision_access", {}, agent_type="it")
        new_hire.add_step("onboard_employee", {}, agent_type="hr")
        self.workflow_engine.register_workflow(new_hire)

        # Vendor Onboarding Workflow
        vendor_onboard = SequentialWorkflow("wf_vendor_onboard", "Vendor Onboarding")
        vendor_onboard.add_step("approve_vendor", {"operation": "check"}, agent_type="procurement")
        vendor_onboard.add_step("review_contract", {}, agent_type="legal")
        vendor_onboard.add_step("verify_invoice", {}, agent_type="finance")
        vendor_onboard.add_step("provision_access", {}, agent_type="it")
        self.workflow_engine.register_workflow(vendor_onboard)

        # Expense Processing Workflow
        expense = SequentialWorkflow("wf_expense", "Expense Processing")
        expense.add_step("process_expense", {}, agent_type="finance")
        expense.add_step("approve_expense", {}, agent_type="finance")
        self.workflow_engine.register_workflow(expense)

        logger.info(f"Registered {len(self.workflow_engine._workflows)} workflow templates")

    async def process_request(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> RequestResult:
        """
        Process a single request by routing to appropriate agent.

        Args:
            action: The action to perform
            payload: Action payload
            context: Additional context

        Returns:
            RequestResult with outcome
        """
        import time
        start_time = time.time()

        if not self._initialized:
            await self.initialize()

        self._request_counter += 1
        request_id = f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self._request_counter:06d}"

        context = context or {}
        context["request_id"] = request_id

        logger.info(f"Processing request {request_id}: {action}")

        # Route to agent
        route_result = self.router.route(action, context)

        if not route_result.agent:
            return RequestResult(
                success=False,
                request_id=request_id,
                action=action,
                error=f"No agent found for action: {action}",
                duration_ms=(time.time() - start_time) * 1000,
            )

        agent = route_result.agent
        logger.info(f"  Routed to: {agent.agent_id}")

        # Execute via agent
        try:
            result = await agent.execute(action, payload, context)

            return RequestResult(
                success=result.success,
                request_id=request_id,
                action=action,
                routed_to=agent.agent_id,
                result_data=result.result_data,
                error=result.result_data.get("error") if not result.success else None,
                compliance_passed=result.compliance_passed,
                policies_triggered=result.policies_triggered,
                risk_score=result.risk_score,
                risk_level=result.risk_level.value,
                duration_ms=(time.time() - start_time) * 1000,
            )

        except Exception as e:
            logger.error(f"Request {request_id} failed: {e}")
            return RequestResult(
                success=False,
                request_id=request_id,
                action=action,
                routed_to=agent.agent_id,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000,
            )

    async def execute_workflow(
        self,
        workflow_id: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> WorkflowResult:
        """
        Execute a registered workflow.

        Args:
            workflow_id: ID of the workflow to execute
            parameters: Parameters to pass to the workflow

        Returns:
            WorkflowResult with execution outcome
        """
        if not self._initialized:
            await self.initialize()

        logger.info(f"Executing workflow: {workflow_id}")

        return await self.workflow_engine.execute(
            workflow_id=workflow_id,
            agents=self.agents,
            context=parameters or {},
        )

    async def create_custom_workflow(
        self,
        name: str,
        steps: List[Dict[str, Any]],
        parallel: bool = False,
    ) -> str:
        """
        Create and register a custom workflow.

        Args:
            name: Workflow name
            steps: List of step definitions
            parallel: Whether to execute in parallel

        Returns:
            Workflow ID
        """
        workflow_id = f"wf_custom_{self._request_counter}"

        if parallel:
            workflow = ParallelWorkflow(workflow_id, name)
        else:
            workflow = SequentialWorkflow(workflow_id, name)

        for step_def in steps:
            workflow.add_step(
                action=step_def.get("action", ""),
                payload=step_def.get("payload", {}),
                agent_type=step_def.get("agent_type"),
                depends_on=step_def.get("depends_on", []),
            )

        self.workflow_engine.register_workflow(workflow)

        return workflow_id

    def get_system_status(self) -> Dict:
        """Get comprehensive system status."""
        return {
            "gateway": {
                "initialized": self._initialized,
                "request_count": self._request_counter,
            },
            "agents": {
                agent_id: agent.get_status()
                for agent_id, agent in self.agents.items()
            },
            "tirs": self.tirs.get_risk_dashboard() if self.tirs else None,
            "compliance": self.compliance.get_stats() if self.compliance else None,
            "workflows": self.workflow_engine.list_workflows(),
            "routing": {
                "capabilities": self.router.get_capabilities(),
            },
        }

    def get_agent(self, agent_id: str) -> Optional[EnterpriseAgent]:
        """Get an agent by ID."""
        return self.agents.get(agent_id)

    def list_agents(self) -> List[Dict]:
        """List all registered agents."""
        return [agent.get_status() for agent in self.agents.values()]


# Singleton
_gateway: Optional[EnterpriseGateway] = None


def get_gateway() -> EnterpriseGateway:
    """Get the singleton gateway."""
    global _gateway
    if _gateway is None:
        _gateway = EnterpriseGateway()
    return _gateway


async def initialize_gateway() -> EnterpriseGateway:
    """Initialize and return the gateway."""
    gateway = get_gateway()
    await gateway.initialize()
    return gateway
