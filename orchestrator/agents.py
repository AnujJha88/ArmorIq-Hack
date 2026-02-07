"""
Base Agent & Agent Implementations
===================================
Agents that can be orchestrated with ArmorIQ verification.
"""

import os
import sys
from abc import ABC, abstractmethod
from typing import Dict, Any, Set, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import logging
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.registry import AgentCapability, AgentInfo, AgentStatus
from orchestrator.context import Task, TaskResult, TaskStatus, PipelineContext

logger = logging.getLogger("Orchestrator.Agents")


class BaseAgent(ABC):
    """
    Base class for all orchestrated agents.

    Every agent must:
    1. Declare its capabilities
    2. Execute tasks with ArmorIQ verification
    3. Report results back to the orchestrator
    """

    def __init__(self, agent_id: str, name: str, description: str):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.capabilities: Set[AgentCapability] = set()
        self.logger = logging.getLogger(f"Agent.{name}")

    @abstractmethod
    def get_capabilities(self) -> Set[AgentCapability]:
        """Return the capabilities this agent provides."""
        pass

    @abstractmethod
    def execute(self, task: Task, context: PipelineContext) -> TaskResult:
        """Execute a task and return the result."""
        pass

    def to_agent_info(self) -> AgentInfo:
        """Convert to AgentInfo for registry."""
        return AgentInfo(
            agent_id=self.agent_id,
            name=self.name,
            capabilities=self.get_capabilities(),
            description=self.description,
            executor=self.execute
        )


# ═══════════════════════════════════════════════════════════════════════════════
# CONCRETE AGENTS
# ═══════════════════════════════════════════════════════════════════════════════

class SourcerAgent(BaseAgent):
    """Finds and reaches out to candidates."""

    def __init__(self):
        super().__init__(
            agent_id="sourcer-001",
            name="Sourcer",
            description="Searches for candidates and sends outreach"
        )

    def get_capabilities(self) -> Set[AgentCapability]:
        return {
            AgentCapability.SEARCH_CANDIDATES,
            AgentCapability.SEND_EMAIL
        }

    def execute(self, task: Task, context: PipelineContext) -> TaskResult:
        started = datetime.now()
        capability = task.capability

        if capability == AgentCapability.SEARCH_CANDIDATES.value:
            # Simulate candidate search
            role = task.payload.get("role", "Engineer")
            skills = task.payload.get("skills", [])

            candidates = [
                {"name": "Alice Chen", "email": "alice@example.com", "experience": 5, "match": 95},
                {"name": "Bob Smith", "email": "bob@example.com", "experience": 3, "match": 87},
                {"name": "Carol Davis", "email": "carol@example.com", "experience": 7, "match": 82},
            ]

            # Store in context for next agents
            context.store_data("candidates", candidates)
            context.store_data("top_candidate", candidates[0])

            return TaskResult(
                task_id=task.task_id,
                status=TaskStatus.COMPLETED,
                agent_id=self.agent_id,
                output={"candidates": candidates, "count": len(candidates)},
                started_at=started,
                completed_at=datetime.now()
            )

        elif capability == AgentCapability.SEND_EMAIL.value:
            recipient = task.payload.get("to", task.payload.get("recipient", ""))
            body = task.payload.get("body", "")

            return TaskResult(
                task_id=task.task_id,
                status=TaskStatus.COMPLETED,
                agent_id=self.agent_id,
                output={"sent": True, "recipient": recipient},
                started_at=started,
                completed_at=datetime.now()
            )

        return TaskResult(
            task_id=task.task_id,
            status=TaskStatus.FAILED,
            agent_id=self.agent_id,
            error=f"Unknown capability: {capability}",
            started_at=started,
            completed_at=datetime.now()
        )


class ScreenerAgent(BaseAgent):
    """Screens resumes and evaluates candidates."""

    def __init__(self):
        super().__init__(
            agent_id="screener-001",
            name="Screener",
            description="Screens resumes and evaluates candidate fit"
        )

    def get_capabilities(self) -> Set[AgentCapability]:
        return {
            AgentCapability.SCREEN_RESUME,
            AgentCapability.READ_EMPLOYEE_DATA
        }

    def execute(self, task: Task, context: PipelineContext) -> TaskResult:
        started = datetime.now()

        if task.capability == AgentCapability.SCREEN_RESUME.value:
            # Get candidates from context
            candidates = context.get_data("candidates", [])

            screened = []
            for candidate in candidates:
                screened.append({
                    **candidate,
                    "screen_score": candidate.get("match", 80),
                    "passed": candidate.get("match", 80) >= 75,
                    "notes": "Meets requirements" if candidate.get("match", 80) >= 75 else "Below threshold"
                })

            passed = [c for c in screened if c["passed"]]
            context.store_data("screened_candidates", screened)
            context.store_data("passed_candidates", passed)

            return TaskResult(
                task_id=task.task_id,
                status=TaskStatus.COMPLETED,
                agent_id=self.agent_id,
                output={"screened": len(screened), "passed": len(passed)},
                started_at=started,
                completed_at=datetime.now()
            )

        return TaskResult(
            task_id=task.task_id,
            status=TaskStatus.FAILED,
            agent_id=self.agent_id,
            error=f"Unknown capability: {task.capability}",
            started_at=started,
            completed_at=datetime.now()
        )


class SchedulerAgent(BaseAgent):
    """Schedules interviews and meetings."""

    def __init__(self):
        super().__init__(
            agent_id="scheduler-001",
            name="Scheduler",
            description="Schedules interviews and coordinates calendars"
        )

    def get_capabilities(self) -> Set[AgentCapability]:
        return {
            AgentCapability.SCHEDULE_INTERVIEW,
            AgentCapability.SCHEDULE_MEETING
        }

    def execute(self, task: Task, context: PipelineContext) -> TaskResult:
        started = datetime.now()

        if task.capability == AgentCapability.SCHEDULE_INTERVIEW.value:
            candidate = task.payload.get("candidate", context.get_data("top_candidate", {}).get("name", "Unknown"))
            time = task.payload.get("time", "2026-02-10 14:00")
            interviewer = task.payload.get("interviewer", "Hiring Manager")

            interview = {
                "candidate": candidate,
                "time": time,
                "interviewer": interviewer,
                "meeting_id": f"INT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            }

            context.store_data("scheduled_interview", interview)

            return TaskResult(
                task_id=task.task_id,
                status=TaskStatus.COMPLETED,
                agent_id=self.agent_id,
                output=interview,
                started_at=started,
                completed_at=datetime.now()
            )

        return TaskResult(
            task_id=task.task_id,
            status=TaskStatus.FAILED,
            agent_id=self.agent_id,
            error=f"Unknown capability: {task.capability}",
            started_at=started,
            completed_at=datetime.now()
        )


class NegotiatorAgent(BaseAgent):
    """Handles offer generation and negotiation."""

    def __init__(self):
        super().__init__(
            agent_id="negotiator-001",
            name="Negotiator",
            description="Generates and negotiates job offers"
        )

    def get_capabilities(self) -> Set[AgentCapability]:
        return {
            AgentCapability.GENERATE_OFFER,
            AgentCapability.NEGOTIATE_OFFER,
            AgentCapability.READ_SALARY_DATA
        }

    def execute(self, task: Task, context: PipelineContext) -> TaskResult:
        started = datetime.now()

        if task.capability == AgentCapability.GENERATE_OFFER.value:
            candidate = task.payload.get("candidate", context.get_data("top_candidate", {}).get("name", "Unknown"))
            role = task.payload.get("role", "Senior Engineer")
            level = task.payload.get("level", "L4")
            salary = task.payload.get("salary", 175000)

            offer = {
                "candidate": candidate,
                "role": role,
                "level": level,
                "salary": salary,
                "equity": task.payload.get("equity", 5000),
                "start_date": task.payload.get("start_date", "2026-03-01"),
                "offer_id": f"OFR-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            }

            context.store_data("offer", offer)

            return TaskResult(
                task_id=task.task_id,
                status=TaskStatus.COMPLETED,
                agent_id=self.agent_id,
                output=offer,
                started_at=started,
                completed_at=datetime.now()
            )

        return TaskResult(
            task_id=task.task_id,
            status=TaskStatus.FAILED,
            agent_id=self.agent_id,
            error=f"Unknown capability: {task.capability}",
            started_at=started,
            completed_at=datetime.now()
        )


class OnboarderAgent(BaseAgent):
    """Handles employee onboarding."""

    def __init__(self):
        super().__init__(
            agent_id="onboarder-001",
            name="Onboarder",
            description="Manages new employee onboarding process"
        )

    def get_capabilities(self) -> Set[AgentCapability]:
        return {
            AgentCapability.ONBOARD_EMPLOYEE,
            AgentCapability.SETUP_EQUIPMENT,
            AgentCapability.CREATE_ACCOUNTS,
            AgentCapability.VERIFY_I9
        }

    def execute(self, task: Task, context: PipelineContext) -> TaskResult:
        started = datetime.now()

        if task.capability == AgentCapability.ONBOARD_EMPLOYEE.value:
            employee = task.payload.get("employee", context.get_data("top_candidate", {}).get("name", "Unknown"))
            start_date = task.payload.get("start_date", context.get_data("offer", {}).get("start_date", "TBD"))

            onboarding = {
                "employee": employee,
                "start_date": start_date,
                "equipment_ordered": True,
                "accounts_created": ["email", "slack", "github"],
                "mentor_assigned": "Senior Team Member",
                "onboarding_id": f"ONB-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            }

            context.store_data("onboarding", onboarding)

            return TaskResult(
                task_id=task.task_id,
                status=TaskStatus.COMPLETED,
                agent_id=self.agent_id,
                output=onboarding,
                started_at=started,
                completed_at=datetime.now()
            )

        if task.capability == AgentCapability.VERIFY_I9.value:
            # I-9 verification
            i9_status = task.payload.get("i9_status", "pending")

            return TaskResult(
                task_id=task.task_id,
                status=TaskStatus.COMPLETED,
                agent_id=self.agent_id,
                output={"i9_verified": i9_status == "verified"},
                started_at=started,
                completed_at=datetime.now()
            )

        return TaskResult(
            task_id=task.task_id,
            status=TaskStatus.FAILED,
            agent_id=self.agent_id,
            error=f"Unknown capability: {task.capability}",
            started_at=started,
            completed_at=datetime.now()
        )


class ComplianceAgent(BaseAgent):
    """Handles compliance and legal verification."""

    def __init__(self):
        super().__init__(
            agent_id="compliance-001",
            name="Compliance",
            description="Verifies legal and compliance requirements"
        )

    def get_capabilities(self) -> Set[AgentCapability]:
        return {
            AgentCapability.VERIFY_I9,
            AgentCapability.CHECK_BACKGROUND,
            AgentCapability.VERIFY_DOCUMENTS
        }

    def execute(self, task: Task, context: PipelineContext) -> TaskResult:
        started = datetime.now()

        if task.capability == AgentCapability.VERIFY_I9.value:
            status = task.payload.get("i9_status", "verified")

            return TaskResult(
                task_id=task.task_id,
                status=TaskStatus.COMPLETED,
                agent_id=self.agent_id,
                output={"i9_verified": status == "verified", "status": status},
                started_at=started,
                completed_at=datetime.now()
            )

        if task.capability == AgentCapability.CHECK_BACKGROUND.value:
            return TaskResult(
                task_id=task.task_id,
                status=TaskStatus.COMPLETED,
                agent_id=self.agent_id,
                output={"background_clear": True, "check_id": "BGC-001"},
                started_at=started,
                completed_at=datetime.now()
            )

        return TaskResult(
            task_id=task.task_id,
            status=TaskStatus.FAILED,
            agent_id=self.agent_id,
            error=f"Unknown capability: {task.capability}",
            started_at=started,
            completed_at=datetime.now()
        )


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT FACTORY
# ═══════════════════════════════════════════════════════════════════════════════

def create_all_agents() -> list:
    """Create all available agents."""
    return [
        SourcerAgent(),
        ScreenerAgent(),
        SchedulerAgent(),
        NegotiatorAgent(),
        OnboarderAgent(),
        ComplianceAgent(),
    ]
