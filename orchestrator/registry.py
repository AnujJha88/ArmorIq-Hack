"""
Agent Registry
==============
Tracks available agents, their capabilities, and current status.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Callable
from enum import Enum
import logging

logger = logging.getLogger("Orchestrator.Registry")


class AgentCapability(Enum):
    """What agents can do."""
    # Hiring
    SEARCH_CANDIDATES = "search_candidates"
    SCREEN_RESUME = "screen_resume"
    SCHEDULE_INTERVIEW = "schedule_interview"
    CONDUCT_INTERVIEW = "conduct_interview"
    GENERATE_OFFER = "generate_offer"
    NEGOTIATE_OFFER = "negotiate_offer"

    # Onboarding
    ONBOARD_EMPLOYEE = "onboard_employee"
    SETUP_EQUIPMENT = "setup_equipment"
    CREATE_ACCOUNTS = "create_accounts"
    ASSIGN_MENTOR = "assign_mentor"

    # Communication
    SEND_EMAIL = "send_email"
    SEND_SLACK = "send_slack"
    SCHEDULE_MEETING = "schedule_meeting"

    # Data Access
    READ_EMPLOYEE_DATA = "read_employee_data"
    READ_SALARY_DATA = "read_salary_data"
    EXPORT_DATA = "export_data"

    # Compliance
    VERIFY_I9 = "verify_i9"
    CHECK_BACKGROUND = "check_background"
    VERIFY_DOCUMENTS = "verify_documents"

    # Performance
    WRITE_REVIEW = "write_review"
    READ_REVIEWS = "read_reviews"
    PROCESS_FEEDBACK = "process_feedback"

    # Finance
    PROCESS_EXPENSE = "process_expense"
    APPROVE_EXPENSE = "approve_expense"
    PROCESS_PAYROLL = "process_payroll"


class AgentStatus(Enum):
    """Agent operational status."""
    AVAILABLE = "available"
    BUSY = "busy"
    PAUSED = "paused"      # By TIRS drift detection
    KILLED = "killed"       # Terminated due to risk
    OFFLINE = "offline"


@dataclass
class AgentInfo:
    """Information about a registered agent."""
    agent_id: str
    name: str
    capabilities: Set[AgentCapability]
    description: str
    status: AgentStatus = AgentStatus.AVAILABLE
    risk_score: float = 0.0
    tasks_completed: int = 0
    tasks_failed: int = 0
    current_task: Optional[str] = None
    executor: Optional[Callable] = None  # Function to execute tasks

    def can_handle(self, capability: AgentCapability) -> bool:
        """Check if agent can handle a capability."""
        return capability in self.capabilities and self.status == AgentStatus.AVAILABLE

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "capabilities": [c.value for c in self.capabilities],
            "description": self.description,
            "status": self.status.value,
            "risk_score": self.risk_score,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "current_task": self.current_task
        }


class AgentRegistry:
    """
    Central registry of all agents in the system.

    Handles:
    - Agent registration and discovery
    - Capability-based routing
    - Status tracking
    - Load balancing
    """

    def __init__(self):
        self.agents: Dict[str, AgentInfo] = {}
        self._capability_index: Dict[AgentCapability, List[str]] = {}
        logger.info("Agent Registry initialized")

    def register(self, agent: AgentInfo) -> bool:
        """Register an agent with the registry."""
        if agent.agent_id in self.agents:
            logger.warning(f"Agent {agent.agent_id} already registered, updating")

        self.agents[agent.agent_id] = agent

        # Index by capability
        for cap in agent.capabilities:
            if cap not in self._capability_index:
                self._capability_index[cap] = []
            if agent.agent_id not in self._capability_index[cap]:
                self._capability_index[cap].append(agent.agent_id)

        logger.info(f"Registered agent: {agent.name} ({agent.agent_id}) with {len(agent.capabilities)} capabilities")
        return True

    def unregister(self, agent_id: str) -> bool:
        """Remove an agent from the registry."""
        if agent_id not in self.agents:
            return False

        agent = self.agents[agent_id]

        # Remove from capability index
        for cap in agent.capabilities:
            if cap in self._capability_index:
                self._capability_index[cap] = [
                    a for a in self._capability_index[cap] if a != agent_id
                ]

        del self.agents[agent_id]
        logger.info(f"Unregistered agent: {agent_id}")
        return True

    def find_agent_for_capability(self, capability: AgentCapability) -> Optional[AgentInfo]:
        """Find the best available agent for a capability."""
        if capability not in self._capability_index:
            return None

        candidates = []
        for agent_id in self._capability_index[capability]:
            agent = self.agents.get(agent_id)
            if agent and agent.can_handle(capability):
                candidates.append(agent)

        if not candidates:
            return None

        # Sort by: lowest risk score, then most tasks completed (experience)
        candidates.sort(key=lambda a: (a.risk_score, -a.tasks_completed))
        return candidates[0]

    def find_agents_for_capability(self, capability: AgentCapability) -> List[AgentInfo]:
        """Find all available agents for a capability."""
        if capability not in self._capability_index:
            return []

        return [
            self.agents[agent_id]
            for agent_id in self._capability_index[capability]
            if self.agents[agent_id].can_handle(capability)
        ]

    def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """Get agent by ID."""
        return self.agents.get(agent_id)

    def update_status(self, agent_id: str, status: AgentStatus):
        """Update agent status."""
        if agent_id in self.agents:
            self.agents[agent_id].status = status
            logger.info(f"Agent {agent_id} status: {status.value}")

    def update_risk(self, agent_id: str, risk_score: float):
        """Update agent risk score from TIRS."""
        if agent_id in self.agents:
            self.agents[agent_id].risk_score = risk_score

            # Auto-pause if risk too high
            if risk_score >= 0.7:
                self.agents[agent_id].status = AgentStatus.KILLED
                logger.critical(f"Agent {agent_id} KILLED - risk {risk_score:.2f}")
            elif risk_score >= 0.5:
                self.agents[agent_id].status = AgentStatus.PAUSED
                logger.warning(f"Agent {agent_id} PAUSED - risk {risk_score:.2f}")

    def record_task_result(self, agent_id: str, success: bool):
        """Record task completion."""
        if agent_id in self.agents:
            if success:
                self.agents[agent_id].tasks_completed += 1
            else:
                self.agents[agent_id].tasks_failed += 1

    def list_agents(self) -> List[AgentInfo]:
        """List all registered agents."""
        return list(self.agents.values())

    def list_available(self) -> List[AgentInfo]:
        """List all available agents."""
        return [a for a in self.agents.values() if a.status == AgentStatus.AVAILABLE]

    def get_capabilities_summary(self) -> Dict[str, List[str]]:
        """Get summary of capabilities and which agents handle them."""
        return {
            cap.value: [
                self.agents[agent_id].name
                for agent_id in agent_ids
                if agent_id in self.agents and self.agents[agent_id].status == AgentStatus.AVAILABLE
            ]
            for cap, agent_ids in self._capability_index.items()
        }


# Singleton
_registry = None

def get_registry() -> AgentRegistry:
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry
