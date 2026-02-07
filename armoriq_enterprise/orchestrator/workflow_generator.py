"""
Dynamic Workflow Generator
==========================
Generates workflows dynamically from natural language goals.
Uses LLM to design optimal workflow patterns.
"""

import logging
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..llm import get_enterprise_llm, get_planner
from ..llm.planner import ActionPlan, PlanStep
from .workflows import (
    SequentialWorkflow,
    ParallelWorkflow,
    LoopWorkflow,
    ConditionalWorkflow,
    WorkflowStep,
    WorkflowStatus,
)

logger = logging.getLogger("Enterprise.WorkflowGenerator")


class WorkflowPattern(Enum):
    """Detected workflow patterns."""
    SEQUENTIAL = "sequential"      # Step-by-step execution
    PARALLEL = "parallel"          # Concurrent execution
    FORK_JOIN = "fork_join"        # Parallel then merge
    LOOP = "loop"                  # Iterative execution
    CONDITIONAL = "conditional"    # Branch based on condition
    SAGA = "saga"                  # Compensating transactions
    PIPELINE = "pipeline"          # Data transformation chain


@dataclass
class WorkflowDesign:
    """Generated workflow design."""
    workflow_id: str
    name: str
    description: str

    # Pattern
    pattern: WorkflowPattern

    # Steps
    steps: List[Dict[str, Any]]

    # Dependencies
    dependency_graph: Dict[str, List[str]]

    # Parallelization
    parallel_groups: List[List[str]]

    # Estimated metrics
    estimated_duration_ms: float = 0.0
    estimated_risk: float = 0.0

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    llm_reasoning: str = ""

    def to_dict(self) -> Dict:
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "pattern": self.pattern.value,
            "steps": self.steps,
            "dependency_graph": self.dependency_graph,
            "parallel_groups": self.parallel_groups,
            "estimated_duration_ms": self.estimated_duration_ms,
            "estimated_risk": self.estimated_risk,
            "llm_reasoning": self.llm_reasoning,
        }


class DynamicWorkflowGenerator:
    """
    Generates workflows dynamically from natural language descriptions.

    Features:
    - Pattern detection (sequential, parallel, fork-join, saga)
    - Automatic parallelization where possible
    - Dependency analysis
    - Risk-aware step ordering
    - Compensation planning for sagas
    """

    def __init__(self):
        self.llm = get_enterprise_llm()
        self.planner = get_planner()
        self._workflow_counter = 0
        logger.info("Dynamic Workflow Generator initialized")

    def generate(
        self,
        goal: str,
        available_agents: Dict[str, Set[str]],
        constraints: Optional[List[str]] = None,
        preferred_pattern: Optional[WorkflowPattern] = None,
    ) -> WorkflowDesign:
        """
        Generate a workflow from a natural language goal.

        Args:
            goal: Natural language goal description
            available_agents: Dict mapping agent_id to capabilities
            constraints: Constraints to apply
            preferred_pattern: Optional pattern preference

        Returns:
            WorkflowDesign with steps and structure
        """
        self._workflow_counter += 1
        workflow_id = f"GEN-WF-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self._workflow_counter:04d}"

        logger.info(f"Generating workflow {workflow_id} for: {goal[:50]}...")

        # Step 1: Decompose goal into steps
        plan = self.planner.create_plan(
            goal=goal,
            available_agents=available_agents,
            constraints=constraints,
        )

        # Step 2: Analyze pattern
        pattern = self._detect_pattern(goal, plan, preferred_pattern)

        # Step 3: Build dependency graph
        dep_graph = self._build_dependency_graph(plan)

        # Step 4: Identify parallel groups
        parallel_groups = self._identify_parallel_groups(plan, dep_graph)

        # Step 5: Estimate metrics
        estimated_duration = self._estimate_duration(plan)
        estimated_risk = self._estimate_risk(plan)

        # Step 6: Create workflow design
        design = WorkflowDesign(
            workflow_id=workflow_id,
            name=self._generate_name(goal),
            description=goal,
            pattern=pattern,
            steps=[s.to_dict() for s in plan.steps],
            dependency_graph=dep_graph,
            parallel_groups=parallel_groups,
            estimated_duration_ms=estimated_duration,
            estimated_risk=estimated_risk,
            llm_reasoning=self._generate_reasoning(goal, plan, pattern),
        )

        logger.info(
            f"Generated workflow {workflow_id}: "
            f"{len(plan.steps)} steps, pattern={pattern.value}"
        )

        return design

    def generate_with_compensation(
        self,
        goal: str,
        available_agents: Dict[str, Set[str]],
        constraints: Optional[List[str]] = None,
    ) -> WorkflowDesign:
        """
        Generate a SAGA-style workflow with compensation actions.

        For each step, also generates a rollback/compensation action
        in case of failure.
        """
        # Get base design
        design = self.generate(
            goal=goal,
            available_agents=available_agents,
            constraints=constraints,
            preferred_pattern=WorkflowPattern.SAGA,
        )

        # Add compensation actions
        compensated_steps = []
        for step in design.steps:
            # Original step
            compensated_steps.append(step)

            # Compensation step
            compensation = self._generate_compensation(step, available_agents)
            if compensation:
                compensated_steps.append(compensation)

        design.steps = compensated_steps
        design.pattern = WorkflowPattern.SAGA

        return design

    def create_executable_workflow(
        self,
        design: WorkflowDesign,
    ):
        """
        Convert a WorkflowDesign into an executable workflow object.

        Returns the appropriate workflow type based on pattern.
        """
        if design.pattern == WorkflowPattern.SEQUENTIAL:
            workflow = SequentialWorkflow(design.workflow_id, design.name)
        elif design.pattern == WorkflowPattern.PARALLEL:
            workflow = ParallelWorkflow(design.workflow_id, design.name)
        elif design.pattern == WorkflowPattern.LOOP:
            workflow = LoopWorkflow(design.workflow_id, design.name)
        elif design.pattern == WorkflowPattern.CONDITIONAL:
            workflow = ConditionalWorkflow(design.workflow_id, design.name)
        else:
            # Default to sequential with parallel groups
            workflow = SequentialWorkflow(design.workflow_id, design.name)

        # Add steps
        for step_data in design.steps:
            workflow.add_step(
                action=step_data.get("action", "unknown"),
                payload=step_data.get("parameters", {}),
                agent_type=step_data.get("agent_id", "").replace("_agent", ""),
                depends_on=step_data.get("depends_on", []),
            )

        return workflow

    def _detect_pattern(
        self,
        goal: str,
        plan: ActionPlan,
        preferred: Optional[WorkflowPattern],
    ) -> WorkflowPattern:
        """Detect the best workflow pattern for this goal."""
        if preferred:
            return preferred

        # Analyze the plan structure
        parallelizable = [s for s in plan.steps if s.can_parallelize]
        has_loops = any("repeat" in goal.lower() or "each" in goal.lower() for _ in [1])
        has_conditions = any("if" in goal.lower() or "when" in goal.lower() for _ in [1])

        # Calculate parallelization ratio
        if plan.steps:
            parallel_ratio = len(parallelizable) / len(plan.steps)
        else:
            parallel_ratio = 0

        # Detect pattern
        if has_loops:
            return WorkflowPattern.LOOP
        elif has_conditions:
            return WorkflowPattern.CONDITIONAL
        elif parallel_ratio > 0.7:
            return WorkflowPattern.PARALLEL
        elif parallel_ratio > 0.3:
            return WorkflowPattern.FORK_JOIN
        else:
            return WorkflowPattern.SEQUENTIAL

    def _build_dependency_graph(
        self,
        plan: ActionPlan,
    ) -> Dict[str, List[str]]:
        """Build a dependency graph from plan steps."""
        graph = {}
        for step in plan.steps:
            graph[step.step_id] = step.depends_on
        return graph

    def _identify_parallel_groups(
        self,
        plan: ActionPlan,
        dep_graph: Dict[str, List[str]],
    ) -> List[List[str]]:
        """Identify groups of steps that can run in parallel."""
        groups = []
        completed = set()
        remaining = {s.step_id: s for s in plan.steps}

        while remaining:
            # Find steps with all dependencies met
            ready = []
            for step_id, step in remaining.items():
                deps_met = all(d in completed for d in step.depends_on)
                if deps_met:
                    ready.append(step_id)

            if not ready:
                # No progress possible - circular dependency or error
                break

            # Group parallelizable steps
            group = [s for s in ready if remaining[s].can_parallelize]
            sequential = [s for s in ready if not remaining[s].can_parallelize]

            if group:
                groups.append(group)
                for s in group:
                    completed.add(s)
                    del remaining[s]

            for s in sequential:
                groups.append([s])
                completed.add(s)
                del remaining[s]

        return groups

    def _estimate_duration(self, plan: ActionPlan) -> float:
        """Estimate workflow duration in milliseconds."""
        # Base estimate: 500ms per step
        base_per_step = 500

        # Get parallel groups
        groups = plan.get_parallelizable_groups()

        # Duration is sum of max duration in each group
        total = 0
        for group in groups:
            # Parallel group takes as long as the slowest step
            group_duration = base_per_step  # All steps assumed equal for now
            total += group_duration

        return total

    def _estimate_risk(self, plan: ActionPlan) -> float:
        """Estimate workflow risk score (0-1)."""
        if not plan.steps:
            return 0.0

        # Factors that increase risk
        num_steps = len(plan.steps)
        num_agents = len(plan.estimated_agents)
        has_high_risk_actions = len(plan.risks_identified) > 0

        # Calculate risk
        step_risk = min(num_steps / 20, 0.5)  # More steps = more risk
        agent_risk = min(num_agents / 6, 0.3)  # More agents = coordination risk
        action_risk = 0.2 if has_high_risk_actions else 0.0

        return min(step_risk + agent_risk + action_risk, 1.0)

    def _generate_name(self, goal: str) -> str:
        """Generate a short workflow name from goal."""
        # Take first few meaningful words
        words = goal.split()[:5]
        return "_".join(w.lower() for w in words if len(w) > 2)

    def _generate_reasoning(
        self,
        goal: str,
        plan: ActionPlan,
        pattern: WorkflowPattern,
    ) -> str:
        """Generate LLM reasoning about the workflow design."""
        return (
            f"Generated {pattern.value} workflow with {len(plan.steps)} steps "
            f"involving {len(plan.estimated_agents)} agents. "
            f"Risks identified: {', '.join(plan.risks_identified) if plan.risks_identified else 'none'}. "
            f"Constraints applied: {', '.join(plan.constraints_applied) if plan.constraints_applied else 'none'}."
        )

    def _generate_compensation(
        self,
        step: Dict[str, Any],
        available_agents: Dict[str, Set[str]],
    ) -> Optional[Dict[str, Any]]:
        """Generate a compensation action for a step."""
        action = step.get("action", "")

        # Map actions to their compensating actions
        compensation_map = {
            "provision_access": "revoke_access",
            "create_budget": "cancel_budget",
            "approve_expense": "reverse_expense",
            "onboard_employee": "offboard_employee",
            "sign_contract": "terminate_contract",
            "create_purchase_order": "cancel_purchase_order",
            "approve_vendor": "suspend_vendor",
            "open_incident": "close_incident",
        }

        compensation_action = compensation_map.get(action)
        if not compensation_action:
            return None

        # Find agent that can perform compensation
        for agent_id, caps in available_agents.items():
            if compensation_action in caps:
                return {
                    "step_id": f"{step.get('step_id', 'unknown')}_COMP",
                    "step_number": -1,  # Compensation step
                    "agent_id": agent_id,
                    "action": compensation_action,
                    "parameters": step.get("parameters", {}),
                    "is_compensation": True,
                    "compensates_for": step.get("step_id"),
                }

        return None


# Workflow Templates for common patterns

class WorkflowTemplates:
    """Pre-defined workflow templates that can be customized."""

    @staticmethod
    def new_hire_onboarding(employee_data: Dict) -> List[Dict]:
        """Template for new hire onboarding workflow."""
        return [
            {"action": "create_offer", "agent_type": "hr", "parameters": employee_data},
            {"action": "verify_i9", "agent_type": "hr", "depends_on": [0]},
            {"action": "background_check", "agent_type": "hr", "depends_on": [0]},
            {"action": "provision_access", "agent_type": "it", "depends_on": [1, 2]},
            {"action": "setup_payroll", "agent_type": "finance", "depends_on": [1]},
            {"action": "assign_equipment", "agent_type": "operations", "depends_on": [3]},
            {"action": "schedule_orientation", "agent_type": "hr", "depends_on": [3, 4]},
        ]

    @staticmethod
    def vendor_onboarding(vendor_data: Dict) -> List[Dict]:
        """Template for vendor onboarding workflow."""
        return [
            {"action": "approve_vendor", "agent_type": "procurement", "parameters": vendor_data},
            {"action": "review_contract", "agent_type": "legal", "depends_on": [0]},
            {"action": "sign_contract", "agent_type": "legal", "depends_on": [1]},
            {"action": "setup_payment", "agent_type": "finance", "depends_on": [2]},
            {"action": "provision_access", "agent_type": "it", "depends_on": [2]},
        ]

    @staticmethod
    def expense_approval(expense_data: Dict) -> List[Dict]:
        """Template for expense approval workflow."""
        return [
            {"action": "process_expense", "agent_type": "finance", "parameters": expense_data},
            {"action": "approve_expense", "agent_type": "finance", "depends_on": [0]},
            {"action": "schedule_reimbursement", "agent_type": "finance", "depends_on": [1]},
        ]

    @staticmethod
    def incident_response(incident_data: Dict) -> List[Dict]:
        """Template for incident response workflow."""
        return [
            {"action": "open_incident", "agent_type": "operations", "parameters": incident_data},
            {"action": "assess_impact", "agent_type": "operations", "depends_on": [0]},
            {"action": "notify_stakeholders", "agent_type": "operations", "depends_on": [1]},
            {"action": "investigate_cause", "agent_type": "it", "depends_on": [1]},
            {"action": "implement_fix", "agent_type": "it", "depends_on": [3]},
            {"action": "verify_resolution", "agent_type": "operations", "depends_on": [4]},
            {"action": "close_incident", "agent_type": "operations", "depends_on": [5]},
        ]

    @staticmethod
    def contract_lifecycle(contract_data: Dict) -> List[Dict]:
        """Template for contract lifecycle management."""
        return [
            {"action": "draft_contract", "agent_type": "legal", "parameters": contract_data},
            {"action": "review_contract", "agent_type": "legal", "depends_on": [0]},
            {"action": "check_compliance", "agent_type": "legal", "depends_on": [1]},
            {"action": "negotiate_terms", "agent_type": "legal", "depends_on": [2]},
            {"action": "approve_contract", "agent_type": "legal", "depends_on": [3]},
            {"action": "sign_contract", "agent_type": "legal", "depends_on": [4]},
            {"action": "archive_contract", "agent_type": "legal", "depends_on": [5]},
        ]


# Singleton
_generator: Optional[DynamicWorkflowGenerator] = None


def get_workflow_generator() -> DynamicWorkflowGenerator:
    """Get the singleton workflow generator."""
    global _generator
    if _generator is None:
        _generator = DynamicWorkflowGenerator()
    return _generator
