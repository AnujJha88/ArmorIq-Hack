"""
Goal Planner
============
LLM-powered goal decomposition and action planning.
"""

import logging
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .service import EnterpriseLLM, get_enterprise_llm

logger = logging.getLogger("Enterprise.Planner")


class PlanStatus(Enum):
    """Status of a plan."""
    DRAFT = "draft"
    READY = "ready"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class PlanStep:
    """Single step in an action plan."""
    step_id: str
    step_number: int

    # Assignment
    agent_id: str
    action: str
    parameters: Dict[str, Any]

    # Dependencies
    depends_on: List[str] = field(default_factory=list)
    can_parallelize: bool = False

    # Reasoning
    reason: str = ""
    expected_outcome: str = ""

    # Execution
    status: str = "pending"
    result: Optional[Dict] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "step_id": self.step_id,
            "step_number": self.step_number,
            "agent_id": self.agent_id,
            "action": self.action,
            "parameters": self.parameters,
            "depends_on": self.depends_on,
            "can_parallelize": self.can_parallelize,
            "reason": self.reason,
            "expected_outcome": self.expected_outcome,
            "status": self.status,
        }


@dataclass
class ActionPlan:
    """Complete action plan for achieving a goal."""
    plan_id: str
    goal: str
    created_at: datetime = field(default_factory=datetime.now)

    # Steps
    steps: List[PlanStep] = field(default_factory=list)

    # Metadata
    estimated_agents: List[str] = field(default_factory=list)
    constraints_applied: List[str] = field(default_factory=list)
    risks_identified: List[str] = field(default_factory=list)

    # Status
    status: PlanStatus = PlanStatus.DRAFT
    current_step: int = 0

    # Fallbacks
    fallback_plans: List["ActionPlan"] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "plan_id": self.plan_id,
            "goal": self.goal,
            "status": self.status.value,
            "steps": [s.to_dict() for s in self.steps],
            "estimated_agents": self.estimated_agents,
            "constraints_applied": self.constraints_applied,
            "risks_identified": self.risks_identified,
            "current_step": self.current_step,
            "total_steps": len(self.steps),
        }

    def get_next_steps(self) -> List[PlanStep]:
        """Get steps that are ready to execute (dependencies met)."""
        completed_ids = {s.step_id for s in self.steps if s.status == "completed"}
        ready = []

        for step in self.steps:
            if step.status != "pending":
                continue

            # Check if all dependencies are met
            deps_met = all(dep in completed_ids for dep in step.depends_on)
            if deps_met:
                ready.append(step)

        return ready

    def get_parallelizable_groups(self) -> List[List[PlanStep]]:
        """Get groups of steps that can run in parallel."""
        groups = []
        completed_ids = {s.step_id for s in self.steps if s.status == "completed"}
        pending = [s for s in self.steps if s.status == "pending"]

        while pending:
            # Find all steps whose dependencies are met
            ready = []
            for step in pending:
                deps_met = all(dep in completed_ids for dep in step.depends_on)
                if deps_met:
                    ready.append(step)

            if not ready:
                break

            # Separate parallelizable from sequential
            parallel_group = [s for s in ready if s.can_parallelize]
            sequential = [s for s in ready if not s.can_parallelize]

            if parallel_group:
                groups.append(parallel_group)
                for s in parallel_group:
                    completed_ids.add(s.step_id)
                    pending.remove(s)

            if sequential:
                for s in sequential:
                    groups.append([s])
                    completed_ids.add(s.step_id)
                    pending.remove(s)

        return groups


class GoalPlanner:
    """
    LLM-powered goal decomposition and planning.

    Converts high-level goals into executable action plans.
    """

    def __init__(self, llm: EnterpriseLLM = None):
        self.llm = llm or get_enterprise_llm()
        self._plan_counter = 0
        logger.info("Goal Planner initialized")

    def create_plan(
        self,
        goal: str,
        available_agents: Dict[str, Set[str]],
        constraints: List[str] = None,
        context: Dict[str, Any] = None,
    ) -> ActionPlan:
        """
        Create an action plan to achieve a goal.

        Args:
            goal: High-level goal description
            available_agents: Dict mapping agent_id to capabilities
            constraints: List of constraints to apply
            context: Additional context

        Returns:
            ActionPlan with steps to achieve goal
        """
        self._plan_counter += 1
        plan_id = f"PLAN-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self._plan_counter:04d}"

        logger.info(f"Creating plan {plan_id} for goal: {goal}")

        # Use LLM to decompose goal
        steps_data = self.llm.decompose_goal(
            goal=goal,
            available_agents=available_agents,
            constraints=constraints,
        )

        # Convert to PlanStep objects
        steps = []
        for i, step_data in enumerate(steps_data):
            step = PlanStep(
                step_id=f"{plan_id}_S{i+1:03d}",
                step_number=i + 1,
                agent_id=step_data.get("agent_id", "unknown"),
                action=step_data.get("action", "unknown"),
                parameters=step_data.get("parameters", {}),
                depends_on=step_data.get("depends_on", []),
                can_parallelize=step_data.get("can_parallelize", False),
                reason=step_data.get("reason", ""),
                expected_outcome=step_data.get("expected_outcome", ""),
            )
            steps.append(step)

        # Fix dependency references (convert step numbers to step IDs)
        step_num_to_id = {s.step_number: s.step_id for s in steps}
        for step in steps:
            fixed_deps = []
            for dep in step.depends_on:
                if isinstance(dep, int):
                    fixed_deps.append(step_num_to_id.get(dep, str(dep)))
                elif isinstance(dep, str) and dep.isdigit():
                    fixed_deps.append(step_num_to_id.get(int(dep), dep))
                else:
                    fixed_deps.append(dep)
            step.depends_on = fixed_deps

        # Identify risks
        risks = self._identify_risks(goal, steps, available_agents)

        plan = ActionPlan(
            plan_id=plan_id,
            goal=goal,
            steps=steps,
            estimated_agents=list(set(s.agent_id for s in steps)),
            constraints_applied=constraints or [],
            risks_identified=risks,
            status=PlanStatus.READY,
        )

        logger.info(f"Plan {plan_id} created with {len(steps)} steps")
        return plan

    def adapt_plan(
        self,
        plan: ActionPlan,
        failure: Dict[str, Any],
        available_agents: Dict[str, Set[str]],
    ) -> ActionPlan:
        """
        Adapt a plan after a step failure.

        Args:
            plan: Original plan
            failure: Information about what failed
            available_agents: Currently available agents

        Returns:
            Adapted plan or fallback
        """
        logger.info(f"Adapting plan {plan.plan_id} after failure")

        # Get recovery suggestions from LLM
        recovery = self.llm.suggest_recovery(
            failed_action=failure.get("action", "unknown"),
            error=failure.get("error", "Unknown error"),
            available_alternatives=list(
                cap for caps in available_agents.values() for cap in caps
            ),
            context={
                "plan_id": plan.plan_id,
                "goal": plan.goal,
                "completed_steps": [s.step_id for s in plan.steps if s.status == "completed"],
                "remaining_steps": [s.step_id for s in plan.steps if s.status == "pending"],
            }
        )

        # Handle None or invalid recovery response
        if not recovery or not isinstance(recovery, dict):
            logger.warning(f"Plan {plan.plan_id} recovery failed - invalid response")
            plan.status = PlanStatus.FAILED
            return plan

        if not recovery.get("recoverable", False):
            logger.warning(f"Plan {plan.plan_id} is not recoverable")
            plan.status = PlanStatus.FAILED
            return plan

        # Create adapted plan with suggested alternatives
        suggestions = recovery.get("suggestions", [])
        if suggestions:
            best_suggestion = max(suggestions, key=lambda x: x.get("success_probability", 0))

            if best_suggestion.get("action"):
                # Insert recovery step
                recovery_step = PlanStep(
                    step_id=f"{plan.plan_id}_R{len(plan.steps)+1:03d}",
                    step_number=len(plan.steps) + 1,
                    agent_id=self._find_agent_for_action(
                        best_suggestion["action"], available_agents
                    ),
                    action=best_suggestion["action"],
                    parameters=best_suggestion.get("parameters", {}),
                    depends_on=[],  # Recovery step has no dependencies
                    reason=f"Recovery: {best_suggestion.get('option', 'Alternative approach')}",
                )

                # Mark failed step
                for step in plan.steps:
                    if step.step_id == failure.get("step_id"):
                        step.status = "failed"
                        step.error = failure.get("error")

                # Insert recovery step after the failed one
                plan.steps.append(recovery_step)

        return plan

    def optimize_plan(self, plan: ActionPlan) -> ActionPlan:
        """
        Optimize a plan for parallel execution.

        Args:
            plan: Plan to optimize

        Returns:
            Optimized plan
        """
        # Identify steps that can be parallelized
        for i, step in enumerate(plan.steps):
            # Check if step has no dependencies on previous step
            if not step.depends_on:
                step.can_parallelize = True
            elif all(
                dep_id in [s.step_id for s in plan.steps[:i] if s.can_parallelize]
                for dep_id in step.depends_on
            ):
                step.can_parallelize = True

        return plan

    def validate_plan(
        self,
        plan: ActionPlan,
        available_agents: Dict[str, Set[str]],
    ) -> List[str]:
        """
        Validate a plan is executable.

        Returns list of validation errors (empty if valid).
        """
        errors = []

        # Check all agents exist
        for step in plan.steps:
            if step.agent_id not in available_agents:
                errors.append(f"Step {step.step_id}: Agent '{step.agent_id}' not available")

            # Check capability exists
            if step.agent_id in available_agents:
                caps = available_agents[step.agent_id]
                action_cap = step.action.lower().replace(" ", "_").replace("-", "_")
                if action_cap not in caps and step.action not in caps:
                    errors.append(
                        f"Step {step.step_id}: Action '{step.action}' not in agent capabilities"
                    )

        # Check dependencies are valid
        step_ids = {s.step_id for s in plan.steps}
        for step in plan.steps:
            for dep in step.depends_on:
                if dep not in step_ids:
                    errors.append(f"Step {step.step_id}: Dependency '{dep}' not found")

        # Check for circular dependencies
        if self._has_circular_deps(plan):
            errors.append("Plan has circular dependencies")

        return errors

    def _identify_risks(
        self,
        goal: str,
        steps: List[PlanStep],
        available_agents: Dict[str, Set[str]],
    ) -> List[str]:
        """Identify risks in the plan."""
        risks = []

        # Check for missing agents
        needed_agents = set(s.agent_id for s in steps)
        available = set(available_agents.keys())
        missing = needed_agents - available
        if missing:
            risks.append(f"Missing agents: {', '.join(missing)}")

        # Check for long dependency chains
        max_chain = self._longest_dep_chain(steps)
        if max_chain > 5:
            risks.append(f"Long dependency chain ({max_chain} steps) - failure risk")

        # Check for no parallelization
        parallelizable = sum(1 for s in steps if s.can_parallelize)
        if parallelizable == 0 and len(steps) > 3:
            risks.append("No parallel execution possible - slow execution")

        # High-risk actions
        high_risk_actions = ["terminate", "delete", "revoke", "kill", "destroy"]
        for step in steps:
            if any(hr in step.action.lower() for hr in high_risk_actions):
                risks.append(f"High-risk action: {step.action}")

        return risks

    def _find_agent_for_action(
        self,
        action: str,
        available_agents: Dict[str, Set[str]],
    ) -> str:
        """Find an agent that can perform an action."""
        action_lower = action.lower().replace(" ", "_").replace("-", "_")

        for agent_id, caps in available_agents.items():
            caps_lower = {c.lower() for c in caps}
            if action_lower in caps_lower or action in caps:
                return agent_id

        return "unknown"

    def _has_circular_deps(self, plan: ActionPlan) -> bool:
        """Check for circular dependencies."""
        # Build adjacency list
        deps = {s.step_id: set(s.depends_on) for s in plan.steps}

        # DFS to find cycles
        visited = set()
        rec_stack = set()

        def dfs(node):
            visited.add(node)
            rec_stack.add(node)

            for dep in deps.get(node, []):
                if dep not in visited:
                    if dfs(dep):
                        return True
                elif dep in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for step_id in deps:
            if step_id not in visited:
                if dfs(step_id):
                    return True

        return False

    def _longest_dep_chain(self, steps: List[PlanStep]) -> int:
        """Find the longest dependency chain."""
        deps = {s.step_id: s.depends_on for s in steps}
        memo = {}

        def chain_length(step_id):
            if step_id in memo:
                return memo[step_id]

            if not deps.get(step_id):
                memo[step_id] = 1
                return 1

            max_dep = max(chain_length(d) for d in deps[step_id] if d in deps)
            memo[step_id] = max_dep + 1
            return memo[step_id]

        return max(chain_length(s.step_id) for s in steps) if steps else 0


# Singleton
_planner: Optional[GoalPlanner] = None


def get_planner() -> GoalPlanner:
    """Get the singleton planner."""
    global _planner
    if _planner is None:
        _planner = GoalPlanner()
    return _planner


def reset_planner():
    """Reset the singleton (for testing)."""
    global _planner
    _planner = None
