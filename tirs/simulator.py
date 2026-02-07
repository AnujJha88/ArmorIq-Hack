"""
Plan Dry-Run Simulator
======================
Simulates entire agent plans before any real execution.

Key Features:
- Parse multi-step plans from agents
- Execute against MCP stubs (no real actions)
- Run each step through policy engine
- Return detailed simulation results
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger("TIRS.Simulator")


class StepVerdict(Enum):
    """Verdict for a single plan step."""
    ALLOW = "ALLOW"
    DENY = "DENY"
    MODIFY = "MODIFY"


@dataclass
class PlanStep:
    """A single step in an agent's plan."""
    step_number: int
    mcp: str  # MCP endpoint name
    action: str  # Action within MCP
    args: Dict[str, Any]
    description: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "step": self.step_number,
            "mcp": self.mcp,
            "action": self.action,
            "args": self.args,
            "description": self.description
        }


@dataclass
class StepResult:
    """Result of simulating a single step."""
    step_number: int
    mcp: str
    action: str
    args: Dict[str, Any]
    verdict: StepVerdict
    reason: str
    policy_triggered: Optional[str] = None
    modified_args: Optional[Dict] = None
    remediation: Optional[Dict] = None
    stub_output: Optional[Dict] = None

    def to_dict(self) -> Dict:
        result = {
            "step": self.step_number,
            "mcp": self.mcp,
            "action": self.action,
            "args": self.args,
            "verdict": self.verdict.value,
            "reason": self.reason
        }
        if self.policy_triggered:
            result["policy_triggered"] = self.policy_triggered
        if self.modified_args:
            result["modified_args"] = self.modified_args
        if self.remediation:
            result["remediation"] = self.remediation
        return result


@dataclass
class SimulationResult:
    """Complete result of simulating a plan."""
    plan_id: str
    agent_id: str
    simulation_time: datetime
    steps: List[StepResult]
    overall_verdict: str  # "ALLOWED" or "BLOCKED"
    blocked_count: int
    allowed_count: int
    modified_count: int
    total_steps: int
    capabilities_requested: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "plan_id": self.plan_id,
            "agent_id": self.agent_id,
            "simulation_time": self.simulation_time.isoformat(),
            "overall_verdict": self.overall_verdict,
            "summary": {
                "total_steps": self.total_steps,
                "allowed": self.allowed_count,
                "blocked": self.blocked_count,
                "modified": self.modified_count
            },
            "capabilities_requested": self.capabilities_requested,
            "steps": [s.to_dict() for s in self.steps]
        }

    @property
    def is_allowed(self) -> bool:
        return self.overall_verdict == "ALLOWED"


class MCPStub:
    """Base class for MCP stubs."""

    def __init__(self, name: str):
        self.name = name
        self.call_log: List[Dict] = []

    def simulate(self, action: str, args: Dict) -> Dict:
        """
        Simulate an MCP call without real execution.

        Returns:
            Dict with simulated result
        """
        self.call_log.append({
            "action": action,
            "args": args,
            "timestamp": datetime.now().isoformat()
        })
        return {"status": "simulated", "mcp": self.name, "action": action}

    def get_capabilities(self, action: str) -> List[str]:
        """Get capabilities required for an action."""
        return [f"{self.name}.{action}"]


class HRISStub(MCPStub):
    """HRIS (Human Resource Information System) stub."""

    def __init__(self):
        super().__init__("HRIS")
        self.mock_employees = {
            "E001": {"name": "John Doe", "role": "L4", "department": "Engineering"},
            "E002": {"name": "Jane Smith", "role": "L5", "department": "Product"},
            "E003": {"name": "Bob Wilson", "role": "L3", "department": "Sales"}
        }

    def simulate(self, action: str, args: Dict) -> Dict:
        super().simulate(action, args)

        if action == "get_employee":
            emp_id = args.get("employee_id")
            if emp_id in self.mock_employees:
                return {"status": "success", "data": self.mock_employees[emp_id]}
            return {"status": "not_found"}

        elif action == "get_salary_band":
            role = args.get("role", "L3")
            bands = {"L3": (100000, 140000), "L4": (130000, 180000), "L5": (170000, 240000)}
            return {"status": "success", "data": {"role": role, "range": bands.get(role, (80000, 100000))}}

        elif action == "query":
            return {"status": "success", "data": list(self.mock_employees.values())}

        elif action == "export":
            return {"status": "success", "data": {"exported": len(self.mock_employees)}}

        return {"status": "simulated", "action": action}

    def get_capabilities(self, action: str) -> List[str]:
        caps = [f"hris.{action}"]
        if action == "export":
            caps.append("hris.bulk_read")
        if action in ["update", "delete", "create"]:
            caps.append("hris.write")
        return caps


class EmailStub(MCPStub):
    """Email service stub."""

    def __init__(self):
        super().__init__("Email")

    def simulate(self, action: str, args: Dict) -> Dict:
        super().simulate(action, args)

        if action == "send":
            return {
                "status": "would_send",
                "to": args.get("to"),
                "subject": args.get("subject", "(no subject)"),
                "body_length": len(args.get("body", ""))
            }

        elif action == "draft":
            return {"status": "drafted", "draft_id": "DRAFT-001"}

        return {"status": "simulated", "action": action}

    def get_capabilities(self, action: str) -> List[str]:
        caps = [f"email.{action}"]
        to = self.call_log[-1]["args"].get("to", "") if self.call_log else ""
        if to and not to.endswith("@company.com"):
            caps.append("email.external")
        return caps


class CalendarStub(MCPStub):
    """Calendar service stub."""

    def __init__(self):
        super().__init__("Calendar")

    def simulate(self, action: str, args: Dict) -> Dict:
        super().simulate(action, args)

        if action == "check_availability":
            return {"status": "success", "available": True}

        elif action == "book":
            return {
                "status": "would_book",
                "date": args.get("date"),
                "time": args.get("time"),
                "attendees": args.get("attendees", [])
            }

        return {"status": "simulated", "action": action}


class PayrollStub(MCPStub):
    """Payroll service stub."""

    def __init__(self):
        super().__init__("Payroll")

    def simulate(self, action: str, args: Dict) -> Dict:
        super().simulate(action, args)

        if action == "get_salary":
            return {"status": "success", "data": {"salary": 150000, "currency": "USD"}}

        elif action == "process_expense":
            return {
                "status": "would_process",
                "amount": args.get("amount"),
                "category": args.get("category")
            }

        return {"status": "simulated", "action": action}

    def get_capabilities(self, action: str) -> List[str]:
        caps = [f"payroll.{action}"]
        if action in ["get_salary", "get_compensation"]:
            caps.append("payroll.read_sensitive")
        return caps


class OfferStub(MCPStub):
    """Offer generation stub."""

    def __init__(self):
        super().__init__("Offer")

    def simulate(self, action: str, args: Dict) -> Dict:
        super().simulate(action, args)

        if action == "generate":
            return {
                "status": "would_generate",
                "role": args.get("role"),
                "salary": args.get("salary"),
                "equity": args.get("equity", 0)
            }

        elif action == "send":
            return {"status": "would_send", "to": args.get("candidate_email")}

        return {"status": "simulated", "action": action}


class PerformanceStub(MCPStub):
    """Performance review stub."""

    def __init__(self):
        super().__init__("Performance")

    def simulate(self, action: str, args: Dict) -> Dict:
        super().simulate(action, args)

        if action == "get_reviews":
            return {"status": "success", "data": [{"rating": 4, "period": "Q4"}]}

        elif action == "submit_feedback":
            return {"status": "would_submit"}

        return {"status": "simulated", "action": action}

    def get_capabilities(self, action: str) -> List[str]:
        caps = [f"perf.{action}"]
        if action in ["get_reviews", "get_ratings"]:
            caps.append("perf.read")
        return caps


class PlanSimulator:
    """
    Main plan simulation engine.

    Simulates multi-step agent plans before any real execution,
    checking each step against policies.
    """

    def __init__(self, policy_engine=None):
        """
        Initialize simulator with optional policy engine.

        Args:
            policy_engine: ArmorIQ policy engine instance (or uses local stub)
        """
        self.policy_engine = policy_engine
        self._plan_counter = 0

        # Initialize MCP stubs
        self.stubs: Dict[str, MCPStub] = {
            "HRIS": HRISStub(),
            "Email": EmailStub(),
            "Calendar": CalendarStub(),
            "Payroll": PayrollStub(),
            "Offer": OfferStub(),
            "Performance": PerformanceStub()
        }

        logger.info(f"PlanSimulator initialized with {len(self.stubs)} MCP stubs")

    def simulate_plan(self, agent_id: str, plan: List[Dict]) -> SimulationResult:
        """
        Simulate an entire plan before execution.

        Args:
            agent_id: Agent identifier
            plan: List of plan steps, each with mcp, action, args

        Returns:
            SimulationResult with detailed step-by-step results
        """
        self._plan_counter += 1
        plan_id = f"PLAN-{datetime.now().strftime('%Y%m%d')}-{self._plan_counter:06d}"

        logger.info(f"Simulating plan {plan_id} for agent {agent_id}")
        logger.info(f"  Steps: {len(plan)}")

        step_results: List[StepResult] = []
        all_capabilities: List[str] = []
        blocked = 0
        allowed = 0
        modified = 0

        for i, step_def in enumerate(plan):
            step = PlanStep(
                step_number=i + 1,
                mcp=step_def.get("mcp", "Unknown"),
                action=step_def.get("action", "unknown"),
                args=step_def.get("args", {}),
                description=step_def.get("description")
            )

            result = self._simulate_step(step)
            step_results.append(result)

            # Track capabilities
            stub = self.stubs.get(step.mcp)
            if stub:
                caps = stub.get_capabilities(step.action)
                all_capabilities.extend(caps)

            # Count verdicts
            if result.verdict == StepVerdict.DENY:
                blocked += 1
            elif result.verdict == StepVerdict.MODIFY:
                modified += 1
                allowed += 1  # Modified still executes
            else:
                allowed += 1

        # Overall verdict
        overall = "BLOCKED" if blocked > 0 else "ALLOWED"

        result = SimulationResult(
            plan_id=plan_id,
            agent_id=agent_id,
            simulation_time=datetime.now(),
            steps=step_results,
            overall_verdict=overall,
            blocked_count=blocked,
            allowed_count=allowed,
            modified_count=modified,
            total_steps=len(plan),
            capabilities_requested=list(set(all_capabilities))
        )

        logger.info(f"Simulation complete: {overall}")
        logger.info(f"  Allowed: {allowed}, Blocked: {blocked}, Modified: {modified}")

        return result

    def _simulate_step(self, step: PlanStep) -> StepResult:
        """Simulate a single plan step."""

        # Get the MCP stub
        stub = self.stubs.get(step.mcp)
        stub_output = None

        if stub:
            # Execute against stub (no real action)
            stub_output = stub.simulate(step.action, step.args)
        else:
            logger.warning(f"No stub for MCP: {step.mcp}")

        # Check against policy engine
        verdict, reason, modified_args, policy = self._check_policy(step)

        # Generate remediation if blocked
        remediation = None
        if verdict == StepVerdict.DENY:
            remediation = self._generate_remediation(step, policy, reason)

        return StepResult(
            step_number=step.step_number,
            mcp=step.mcp,
            action=step.action,
            args=step.args,
            verdict=verdict,
            reason=reason,
            policy_triggered=policy,
            modified_args=modified_args,
            remediation=remediation,
            stub_output=stub_output
        )

    def _check_policy(self, step: PlanStep) -> tuple:
        """
        Check a step against the policy engine.

        Returns:
            (verdict, reason, modified_args, policy_name)
        """
        # Map MCP actions to policy intent types
        intent_type = f"{step.mcp.lower()}_{step.action}"

        # Use external policy engine if available
        if self.policy_engine:
            try:
                result = self.policy_engine.capture_intent(
                    action_type=intent_type,
                    payload=step.args,
                    agent_name="simulator"
                )
                if not result.allowed:
                    return StepVerdict.DENY, result.reason, None, result.policy_triggered
                if result.verdict.value == "MODIFY":
                    return StepVerdict.MODIFY, result.reason, result.modified_payload, result.policy_triggered
                return StepVerdict.ALLOW, "Policy approved", None, None
            except Exception as e:
                logger.warning(f"Policy engine error: {e}")

        # Fallback: Local policy checks
        return self._local_policy_check(step)

    def _local_policy_check(self, step: PlanStep) -> tuple:
        """Local policy checks when no external engine."""

        # Scheduling policies
        if step.mcp == "Calendar" and step.action == "book":
            time_str = step.args.get("time", "")
            date_str = step.args.get("date", "")

            # Weekend check (simple)
            if date_str:
                from datetime import datetime as dt
                try:
                    date = dt.strptime(date_str, "%Y-%m-%d")
                    if date.weekday() >= 5:
                        return StepVerdict.DENY, "No scheduling on weekends", None, "Work-Life Balance"
                except ValueError:
                    pass

            # Hours check
            if time_str:
                try:
                    hour = int(time_str.split(":")[0])
                    if hour < 9 or hour >= 17:
                        return StepVerdict.DENY, "Outside work hours (9-5)", None, "Work-Life Balance"
                except (ValueError, IndexError):
                    pass

        # Offer policies
        if step.mcp == "Offer" and step.action == "generate":
            salary = step.args.get("salary", 0)
            role = step.args.get("role", "L3")
            caps = {"L3": 140000, "L4": 180000, "L5": 240000}
            cap = caps.get(role, 100000)

            if salary > cap:
                return StepVerdict.DENY, f"Salary ${salary:,} exceeds ${cap:,} cap for {role}", None, "Salary Caps"

        # Email policies
        if step.mcp == "Email" and step.action == "send":
            body = step.args.get("body", "")
            to = step.args.get("to", "")

            # Bias terms
            bias_terms = ["rockstar", "ninja", "guru", "guys"]
            for term in bias_terms:
                if term in body.lower():
                    return StepVerdict.DENY, f"Non-inclusive language: '{term}'", None, "Inclusive Language"

            # PII for external
            if to and not to.endswith("@company.com"):
                import re
                phone_pattern = r"\d{3}[-.]?\d{3}[-.]?\d{4}"
                if re.search(phone_pattern, body):
                    new_body = re.sub(phone_pattern, "[PHONE_REDACTED]", body)
                    modified = {**step.args, "body": new_body}
                    return StepVerdict.MODIFY, "PII redacted for external email", modified, "PII Protection"

        # Expense policies
        if step.mcp == "Payroll" and step.action == "process_expense":
            amount = step.args.get("amount", 0)
            has_receipt = step.args.get("has_receipt", False)

            if amount > 50 and not has_receipt:
                return StepVerdict.DENY, "Receipt required for expenses > $50", None, "Fraud Prevention"

        # HRIS export policies
        if step.mcp == "HRIS" and step.action == "export":
            return StepVerdict.DENY, "Bulk data export requires admin approval", None, "Data Protection"

        # Performance data policies
        if step.mcp == "Performance" and step.action == "get_reviews":
            employee_id = step.args.get("employee_id")
            requester = step.args.get("requester")
            # Check if accessing own data or is manager (simplified)
            if employee_id and requester and employee_id != requester:
                return StepVerdict.DENY, "Cannot access others' performance reviews", None, "Data Privacy"

        return StepVerdict.ALLOW, "Policy approved", None, None

    def _generate_remediation(self, step: PlanStep, policy: str, reason: str) -> Dict:
        """Generate remediation suggestions for blocked actions."""

        suggestions = []

        if policy == "Salary Caps":
            role = step.args.get("role", "L3")
            caps = {"L3": 140000, "L4": 180000, "L5": 240000}
            cap = caps.get(role, 100000)
            suggestions.append({
                "type": "modify_value",
                "field": "salary",
                "suggested_value": cap,
                "description": f"Reduce salary to ${cap:,} (max for {role})"
            })
            suggestions.append({
                "type": "escalate",
                "description": "Request VP approval for above-band offer"
            })

        elif policy == "Work-Life Balance":
            suggestions.append({
                "type": "modify_value",
                "field": "date",
                "description": "Reschedule to a weekday"
            })
            suggestions.append({
                "type": "modify_value",
                "field": "time",
                "description": "Reschedule to work hours (9 AM - 5 PM)"
            })

        elif policy == "Inclusive Language":
            suggestions.append({
                "type": "modify_content",
                "description": "Remove non-inclusive terms from email body"
            })

        elif policy == "Fraud Prevention":
            suggestions.append({
                "type": "add_requirement",
                "field": "has_receipt",
                "description": "Attach receipt for expenses over $50"
            })

        elif policy == "Data Protection":
            suggestions.append({
                "type": "escalate",
                "description": "Request admin approval for bulk export"
            })
            suggestions.append({
                "type": "alternative",
                "description": "Use filtered query instead of full export"
            })

        return {
            "policy_violated": policy,
            "reason": reason,
            "suggestions": suggestions,
            "reversibility": "high" if suggestions else "low"
        }

    def what_if(self, agent_id: str, plan: List[Dict], policy_changes: Dict = None) -> SimulationResult:
        """
        Run a what-if simulation with hypothetical policy changes.

        Args:
            agent_id: Agent identifier
            plan: Plan to simulate
            policy_changes: Dict of policy modifications to apply

        Returns:
            SimulationResult under modified policies
        """
        # TODO: Implement policy modification for what-if scenarios
        logger.info(f"What-if simulation for {agent_id}")
        if policy_changes:
            logger.info(f"  Policy changes: {policy_changes}")

        return self.simulate_plan(agent_id, plan)


# Singleton instance
_simulator: Optional[PlanSimulator] = None


def get_simulator(policy_engine=None) -> PlanSimulator:
    """Get the singleton simulator."""
    global _simulator
    if _simulator is None:
        _simulator = PlanSimulator(policy_engine)
    return _simulator
