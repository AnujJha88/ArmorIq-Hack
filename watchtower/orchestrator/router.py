"""
Capability-Based Router
=======================
Routes requests to appropriate agents based on capabilities.
"""

import logging
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

from ..agents.base_agent import EnterpriseAgent, AgentCapability

logger = logging.getLogger("Orchestrator.Router")


@dataclass
class RouteResult:
    """Result of routing decision."""
    agent: Optional[EnterpriseAgent]
    capability: Optional[AgentCapability]
    confidence: float
    alternatives: List[str]


class CapabilityRouter:
    """
    Routes requests to agents based on capability matching.

    Features:
    - Capability-based routing
    - Load balancing (when multiple agents available)
    - Fallback handling
    """

    def __init__(self):
        self._agents: Dict[str, EnterpriseAgent] = {}
        self._capability_map: Dict[AgentCapability, List[str]] = {}

    def register_agent(self, agent: EnterpriseAgent):
        """Register an agent."""
        self._agents[agent.agent_id] = agent

        # Map capabilities to agent
        for cap in agent.capabilities:
            if cap not in self._capability_map:
                self._capability_map[cap] = []
            self._capability_map[cap].append(agent.agent_id)

        logger.info(f"Registered agent {agent.agent_id} with {len(agent.capabilities)} capabilities")

    def unregister_agent(self, agent_id: str):
        """Unregister an agent."""
        if agent_id not in self._agents:
            return

        agent = self._agents[agent_id]

        # Remove from capability map
        for cap in agent.capabilities:
            if cap in self._capability_map:
                self._capability_map[cap] = [a for a in self._capability_map[cap] if a != agent_id]

        del self._agents[agent_id]

    def route(self, action: str, context: Optional[Dict] = None) -> RouteResult:
        """
        Route an action to the appropriate agent.

        Args:
            action: The action to perform
            context: Optional context for routing decisions

        Returns:
            RouteResult with selected agent and alternatives
        """
        context = context or {}

        # Find matching capability
        capability = self._match_capability(action)

        if not capability:
            return RouteResult(
                agent=None,
                capability=None,
                confidence=0.0,
                alternatives=[],
            )

        # Get agents with this capability
        agent_ids = self._capability_map.get(capability, [])

        if not agent_ids:
            return RouteResult(
                agent=None,
                capability=capability,
                confidence=0.0,
                alternatives=[],
            )

        # Select best agent
        selected = self._select_agent(agent_ids, context)

        return RouteResult(
            agent=self._agents.get(selected),
            capability=capability,
            confidence=1.0,
            alternatives=[a for a in agent_ids if a != selected],
        )

    def _match_capability(self, action: str) -> Optional[AgentCapability]:
        """Match action string to capability."""
        action_lower = action.lower().replace(" ", "_").replace("-", "_")

        # Try exact match
        for cap in AgentCapability:
            if cap.value == action_lower:
                return cap

        # Try partial match
        for cap in AgentCapability:
            if cap.value in action_lower or action_lower in cap.value:
                return cap

        # Try keyword match
        keywords = action_lower.split("_")
        for cap in AgentCapability:
            cap_keywords = cap.value.split("_")
            if any(k in cap_keywords for k in keywords):
                return cap

        return None

    def _select_agent(self, agent_ids: List[str], context: Dict) -> str:
        """Select the best agent from available options."""
        if len(agent_ids) == 1:
            return agent_ids[0]

        # Score agents based on:
        # - Current status (active > throttled > paused)
        # - Current risk score (lower is better)
        # - Block rate (lower is better)

        best_agent = agent_ids[0]
        best_score = -float("inf")

        for agent_id in agent_ids:
            agent = self._agents.get(agent_id)
            if not agent:
                continue

            status = agent.status
            if status.value == "killed":
                continue
            elif status.value == "paused":
                status_score = 0
            elif status.value == "throttled":
                status_score = 5
            else:
                status_score = 10

            risk_score = 10 - (agent.risk_score * 10)
            block_rate = agent._blocked_count / max(agent._action_count, 1)
            block_score = 10 - (block_rate * 10)

            total_score = status_score + risk_score + block_score

            if total_score > best_score:
                best_score = total_score
                best_agent = agent_id

        return best_agent

    def get_agent(self, agent_id: str) -> Optional[EnterpriseAgent]:
        """Get an agent by ID."""
        return self._agents.get(agent_id)

    def list_agents(self) -> List[Dict]:
        """List all registered agents."""
        return [agent.get_status() for agent in self._agents.values()]

    def get_capabilities(self) -> Dict[str, List[str]]:
        """Get capability to agent mapping."""
        return {
            cap.value: agent_ids
            for cap, agent_ids in self._capability_map.items()
        }
