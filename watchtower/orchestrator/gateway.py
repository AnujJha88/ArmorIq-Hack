"""
Enterprise Gateway
==================
Root ADK-style orchestrator for the enterprise agentic system.

Now with AUTONOMOUS goal decomposition and LLM-powered request understanding.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Set
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

# LLM for autonomous orchestration
from ..llm import get_enterprise_llm, get_planner
from ..llm.planner import ActionPlan, PlanStatus

# Collaboration
from .collaboration import get_collaboration_hub, CollaborationHub
from .workflow_generator import get_workflow_generator, DynamicWorkflowGenerator

logger = logging.getLogger("Enterprise.Gateway")


@dataclass
class GatewayConfig:
    """Configuration for the enterprise gateway."""
    enable_tirs: bool = True
    enable_compliance: bool = True
    enable_audit: bool = True
    max_concurrent_workflows: int = 5
    default_timeout_seconds: int = 300
    # Autonomous mode settings
    autonomous_mode: bool = True
    use_llm_routing: bool = True
    use_goal_decomposition: bool = True


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

    # LLM Reasoning (NEW)
    reasoning: Optional[str] = None
    confidence: float = 1.0
    autonomous_mode: bool = False

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
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "autonomous_mode": self.autonomous_mode,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
        }


class EnterpriseGateway:
    """
    Root orchestrator for the Watchtower Enterprise Agentic System.

    This is the main entry point that:
    1. Receives user/system requests (or natural language goals)
    2. Routes to appropriate domain agents (with LLM understanding)
    3. Coordinates multi-agent workflows (with dynamic generation)
    4. Enforces compliance at every handoff
    5. Tracks drift across all agents
    6. Makes autonomous decisions with LLM reasoning (NEW)
    """

    def __init__(self, config: Optional[GatewayConfig] = None):
        self.config = config or GatewayConfig()

        # Core engines
        self.tirs = get_advanced_tirs() if self.config.enable_tirs else None
        self.compliance = get_compliance_engine() if self.config.enable_compliance else None

        # LLM for autonomous orchestration
        self.llm = get_enterprise_llm()
        self.planner = get_planner()
        self.workflow_generator = get_workflow_generator()

        # Collaboration hub
        self.collaboration_hub = get_collaboration_hub()

        # Orchestration components
        self.router = CapabilityRouter()
        self.handoff_verifier = HandoffVerifier()
        self.workflow_engine = WorkflowEngine()

        # Agents
        self.agents: Dict[str, EnterpriseAgent] = {}

        # State
        self._request_counter = 0
        self._autonomous_requests = 0
        self._goals_processed = 0
        self._initialized = False

        logger.info("=" * 70)
        logger.info("  WATCHTOWER ENTERPRISE GATEWAY")
        logger.info(f"  Autonomous Mode: {self.config.autonomous_mode}")
        logger.info(f"  LLM Mode: {self.llm.mode.value}")
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
            self.collaboration_hub.register_agent(agent)
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

    async def process_goal(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None,
        constraints: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Process a high-level GOAL using LLM-powered decomposition.

        This is the AUTONOMOUS entry point - give it a goal in natural language
        and it will figure out what agents and actions are needed.

        Args:
            goal: Natural language goal description
            context: Additional context
            constraints: Constraints to apply

        Returns:
            Dict with plan and execution results
        """
        import time
        start_time = time.time()

        if not self._initialized:
            await self.initialize()

        self._goals_processed += 1
        goal_id = f"GOAL-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self._goals_processed:04d}"

        logger.info(f"[AUTONOMOUS] Processing goal {goal_id}: {goal[:50]}...")

        # Get available agents and their capabilities
        available_agents = self._get_agent_capabilities()

        # Use LLM planner to decompose goal
        plan = self.planner.create_plan(
            goal=goal,
            available_agents=available_agents,
            constraints=constraints,
            context=context,
        )

        logger.info(f"[AUTONOMOUS] Plan created with {len(plan.steps)} steps")

        # Validate plan
        validation_errors = self.planner.validate_plan(plan, available_agents)
        if validation_errors:
            logger.warning(f"[AUTONOMOUS] Plan validation errors: {validation_errors}")

        # Execute the plan
        results = await self._execute_plan(plan, context or {})

        duration_ms = (time.time() - start_time) * 1000

        return {
            "goal_id": goal_id,
            "goal": goal,
            "plan": plan.to_dict(),
            "results": results,
            "success": all(r.get("success", False) for r in results),
            "duration_ms": duration_ms,
            "validation_errors": validation_errors,
        }

    async def process_natural_language(
        self,
        request: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RequestResult:
        """
        Process a natural language request using LLM understanding.

        Args:
            request: Natural language request
            context: Additional context

        Returns:
            RequestResult with execution outcome
        """
        import time
        start_time = time.time()

        if not self._initialized:
            await self.initialize()

        self._request_counter += 1
        self._autonomous_requests += 1
        request_id = f"NL-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self._request_counter:06d}"

        logger.info(f"[AUTONOMOUS] Processing NL request {request_id}: {request[:50]}...")

        # Get all available actions
        all_actions = []
        for agent in self.agents.values():
            all_actions.extend([c.value for c in agent.capabilities])

        # Use LLM to understand intent
        intent = self.llm.understand_intent(request, all_actions)

        logger.info(f"[AUTONOMOUS] Understood intent: {intent.get('intent', 'unknown')}")
        logger.info(f"[AUTONOMOUS] Primary action: {intent.get('primary_action', 'unknown')}")
        logger.info(f"[AUTONOMOUS] Confidence: {intent.get('confidence', 0):.2f}")

        # Check if we need clarification
        if intent.get("clarifications_needed"):
            return RequestResult(
                success=False,
                request_id=request_id,
                action="clarification_needed",
                result_data={
                    "clarifications": intent.get("clarifications_needed"),
                    "partial_understanding": intent,
                },
                reasoning="Need clarification before proceeding",
                confidence=intent.get("confidence", 0),
                autonomous_mode=True,
                duration_ms=(time.time() - start_time) * 1000,
            )

        # Check if this is a multi-action goal
        if intent.get("secondary_actions"):
            # Treat as a goal and decompose
            goal_result = await self.process_goal(
                goal=request,
                context=context,
                constraints=None,
            )

            return RequestResult(
                success=goal_result.get("success", False),
                request_id=request_id,
                action=intent.get("primary_action", "unknown"),
                result_data=goal_result,
                reasoning=f"Decomposed into {len(goal_result.get('results', []))} steps",
                confidence=intent.get("confidence", 0),
                autonomous_mode=True,
                duration_ms=(time.time() - start_time) * 1000,
            )

        # Single action - route and execute with autonomous reasoning
        action = intent.get("primary_action", "unknown")
        payload = intent.get("extracted_parameters", {})

        # Route to agent
        route_result = self.router.route(action, context or {})

        if not route_result.agent:
            return RequestResult(
                success=False,
                request_id=request_id,
                action=action,
                error=f"No agent found for action: {action}",
                reasoning=intent.get("reasoning", ""),
                confidence=intent.get("confidence", 0),
                autonomous_mode=True,
                duration_ms=(time.time() - start_time) * 1000,
            )

        agent = route_result.agent
        logger.info(f"[AUTONOMOUS] Routed to: {agent.agent_id}")

        # Execute with autonomous reasoning
        try:
            result = await agent.autonomous_execute(action, payload, context)

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
                reasoning=result.reasoning,
                confidence=result.confidence,
                autonomous_mode=True,
                duration_ms=(time.time() - start_time) * 1000,
            )

        except Exception as e:
            logger.error(f"[AUTONOMOUS] Request {request_id} failed: {e}")
            return RequestResult(
                success=False,
                request_id=request_id,
                action=action,
                routed_to=agent.agent_id,
                error=str(e),
                reasoning="Execution failed",
                confidence=0,
                autonomous_mode=True,
                duration_ms=(time.time() - start_time) * 1000,
            )

    async def _execute_plan(
        self,
        plan: ActionPlan,
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Execute an action plan step by step."""
        results = []
        plan.status = PlanStatus.EXECUTING

        # Get parallelizable groups
        groups = plan.get_parallelizable_groups()

        for group in groups:
            if len(group) == 1:
                # Single step - execute directly
                step = group[0]
                result = await self._execute_plan_step(step, context)
                results.append(result)

                if not result.get("success", False):
                    logger.warning(f"[AUTONOMOUS] Step {step.step_id} failed")
                    # Try to adapt the plan
                    plan = self.planner.adapt_plan(
                        plan,
                        {"step_id": step.step_id, "error": result.get("error", "Unknown")},
                        self._get_agent_capabilities(),
                    )
                    if plan.status == PlanStatus.FAILED:
                        break
            else:
                # Parallel steps - execute concurrently
                tasks = [self._execute_plan_step(step, context) for step in group]
                group_results = await asyncio.gather(*tasks, return_exceptions=True)

                for step, result in zip(group, group_results):
                    if isinstance(result, Exception):
                        results.append({
                            "step_id": step.step_id,
                            "success": False,
                            "error": str(result),
                        })
                    else:
                        results.append(result)

        # Update plan status
        if all(r.get("success", False) for r in results):
            plan.status = PlanStatus.COMPLETED
        else:
            plan.status = PlanStatus.FAILED

        return results

    async def _execute_plan_step(
        self,
        step,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a single plan step."""
        logger.info(f"[AUTONOMOUS] Executing step {step.step_id}: {step.action}")

        # Find agent
        agent = self.agents.get(step.agent_id)
        if not agent:
            # Try to find by type
            for a in self.agents.values():
                if a.config.agent_type.lower() in step.agent_id.lower():
                    agent = a
                    break

        if not agent:
            return {
                "step_id": step.step_id,
                "success": False,
                "error": f"Agent not found: {step.agent_id}",
            }

        # Merge context with step parameters
        step_context = {**context, **step.parameters}

        # Execute with autonomous reasoning
        try:
            result = await agent.autonomous_execute(
                action=step.action,
                payload=step.parameters,
                context=step_context,
            )

            step.status = "completed" if result.success else "failed"
            step.result = result.to_dict()

            return {
                "step_id": step.step_id,
                "agent_id": agent.agent_id,
                "action": step.action,
                "success": result.success,
                "result": result.result_data,
                "reasoning": result.reasoning,
                "confidence": result.confidence,
            }

        except Exception as e:
            step.status = "failed"
            step.error = str(e)

            return {
                "step_id": step.step_id,
                "agent_id": agent.agent_id if agent else "unknown",
                "action": step.action,
                "success": False,
                "error": str(e),
            }

    def _get_agent_capabilities(self) -> Dict[str, Set[str]]:
        """Get all agent capabilities as a dict."""
        return {
            agent_id: {c.value for c in agent.capabilities}
            for agent_id, agent in self.agents.items()
        }

    def get_system_status(self) -> Dict:
        """Get comprehensive system status."""
        return {
            "gateway": {
                "initialized": self._initialized,
                "request_count": self._request_counter,
                # Autonomous mode stats
                "autonomous_mode": self.config.autonomous_mode,
                "autonomous_requests": self._autonomous_requests,
                "goals_processed": self._goals_processed,
                "llm_mode": self.llm.mode.value,
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
            "collaboration": self.collaboration_hub.get_collaboration_stats(),
        }

    def get_agent(self, agent_id: str) -> Optional[EnterpriseAgent]:
        """Get an agent by ID."""
        return self.agents.get(agent_id)

    def list_agents(self) -> List[Dict]:
        """List all registered agents."""
        return [agent.get_status() for agent in self.agents.values()]

    async def delegate_task(
        self,
        from_agent: str,
        to_agent: str,
        action: str,
        payload: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Delegate a task from one agent to another.

        Args:
            from_agent: Delegating agent ID
            to_agent: Target agent ID
            action: Action to perform
            payload: Action payload
            context: Additional context

        Returns:
            Delegation result
        """
        return await self.collaboration_hub.delegate_task(
            from_agent=from_agent,
            to_agent=to_agent,
            action=action,
            payload=payload,
            context=context,
        )

    async def negotiate_between_agents(
        self,
        participants: List[str],
        goal: str,
        initial_positions: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Start a negotiation between agents.

        Args:
            participants: Agent IDs participating
            goal: Shared goal
            initial_positions: Each agent's initial position

        Returns:
            Negotiation result
        """
        negotiation = await self.collaboration_hub.negotiate(
            participants=participants,
            goal=goal,
            initial_positions=initial_positions,
        )
        return negotiation.to_dict()

    async def generate_workflow(
        self,
        goal: str,
        constraints: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a dynamic workflow from a goal.

        Args:
            goal: Natural language goal
            constraints: Constraints to apply

        Returns:
            Generated workflow design
        """
        if not self._initialized:
            await self.initialize()

        design = self.workflow_generator.generate(
            goal=goal,
            available_agents=self._get_agent_capabilities(),
            constraints=constraints,
        )

        # Create executable workflow
        workflow = self.workflow_generator.create_executable_workflow(design)
        self.workflow_engine.register_workflow(workflow)

        return design.to_dict()


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
