"""
Agent Collaboration Framework
=============================
Enables multi-agent collaboration, negotiation, and coordination.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

from ..llm import get_enterprise_llm
from ..agents.base_agent import EnterpriseAgent

logger = logging.getLogger("Enterprise.Collaboration")


class MessageType(Enum):
    """Types of inter-agent messages."""
    REQUEST = "request"           # Request help or resource
    RESPONSE = "response"         # Response to a request
    INFORM = "inform"             # Share information
    PROPOSE = "propose"           # Propose an action or agreement
    ACCEPT = "accept"             # Accept a proposal
    REJECT = "reject"             # Reject a proposal
    COUNTER = "counter"           # Counter-proposal
    DELEGATE = "delegate"         # Delegate a task
    COMPLETE = "complete"         # Task completion notification
    ERROR = "error"               # Error notification


class NegotiationStatus(Enum):
    """Status of a negotiation."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    AGREED = "agreed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class AgentMessage:
    """Message between agents."""
    message_id: str
    from_agent: str
    to_agent: str
    message_type: MessageType
    content: Dict[str, Any]
    correlation_id: Optional[str] = None  # Links related messages
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            "message_id": self.message_id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "message_type": self.message_type.value,
            "content": self.content,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class Negotiation:
    """Represents a negotiation between agents."""
    negotiation_id: str
    participants: List[str]
    goal: str
    status: NegotiationStatus = NegotiationStatus.OPEN

    # Positions
    positions: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Messages
    messages: List[AgentMessage] = field(default_factory=list)

    # Result
    agreement: Optional[Dict[str, Any]] = None
    concessions: Dict[str, List[str]] = field(default_factory=dict)

    # Timing
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    max_rounds: int = 5

    def to_dict(self) -> Dict:
        return {
            "negotiation_id": self.negotiation_id,
            "participants": self.participants,
            "goal": self.goal,
            "status": self.status.value,
            "positions": self.positions,
            "agreement": self.agreement,
            "message_count": len(self.messages),
        }


@dataclass
class SharedContext:
    """Shared context between collaborating agents."""
    context_id: str
    participants: List[str]
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class CollaborationHub:
    """
    Central hub for agent collaboration.

    Provides:
    - Message passing between agents
    - Negotiation orchestration
    - Shared context management
    - Consensus mechanisms
    - Task delegation
    """

    def __init__(self):
        self.llm = get_enterprise_llm()
        self.agents: Dict[str, EnterpriseAgent] = {}

        # Message infrastructure
        self._message_queues: Dict[str, asyncio.Queue] = {}
        self._message_history: List[AgentMessage] = []

        # Negotiations
        self._negotiations: Dict[str, Negotiation] = {}

        # Shared contexts
        self._shared_contexts: Dict[str, SharedContext] = {}

        # Subscriptions
        self._subscriptions: Dict[str, List[Callable]] = {}

        logger.info("Collaboration Hub initialized")

    def register_agent(self, agent: EnterpriseAgent):
        """Register an agent with the collaboration hub."""
        agent_id = agent.agent_id
        self.agents[agent_id] = agent
        self._message_queues[agent_id] = asyncio.Queue()
        logger.info(f"Agent registered for collaboration: {agent_id}")

    async def send_message(
        self,
        from_agent: str,
        to_agent: str,
        message_type: MessageType,
        content: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> AgentMessage:
        """
        Send a message from one agent to another.

        Args:
            from_agent: Sender agent ID
            to_agent: Recipient agent ID
            message_type: Type of message
            content: Message content
            correlation_id: ID to link related messages

        Returns:
            The sent message
        """
        message = AgentMessage(
            message_id=str(uuid.uuid4()),
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=message_type,
            content=content,
            correlation_id=correlation_id,
        )

        # Store in history
        self._message_history.append(message)

        # Deliver to recipient's queue
        if to_agent in self._message_queues:
            await self._message_queues[to_agent].put(message)

        # Notify subscribers
        if to_agent in self._subscriptions:
            for callback in self._subscriptions[to_agent]:
                try:
                    await callback(message)
                except Exception as e:
                    logger.error(f"Subscriber callback failed: {e}")

        logger.debug(f"Message sent: {from_agent} -> {to_agent} ({message_type.value})")

        return message

    async def receive_message(
        self,
        agent_id: str,
        timeout: float = 30.0,
    ) -> Optional[AgentMessage]:
        """
        Receive a message for an agent.

        Args:
            agent_id: Agent to receive message for
            timeout: Timeout in seconds

        Returns:
            Message or None if timeout
        """
        if agent_id not in self._message_queues:
            return None

        try:
            message = await asyncio.wait_for(
                self._message_queues[agent_id].get(),
                timeout=timeout,
            )
            return message
        except asyncio.TimeoutError:
            return None

    async def broadcast(
        self,
        from_agent: str,
        message_type: MessageType,
        content: Dict[str, Any],
        to_agents: Optional[List[str]] = None,
    ) -> List[AgentMessage]:
        """
        Broadcast a message to multiple agents.

        Args:
            from_agent: Sender agent ID
            message_type: Type of message
            content: Message content
            to_agents: List of recipients (all if None)

        Returns:
            List of sent messages
        """
        recipients = to_agents or [a for a in self.agents.keys() if a != from_agent]

        messages = []
        for to_agent in recipients:
            msg = await self.send_message(
                from_agent=from_agent,
                to_agent=to_agent,
                message_type=message_type,
                content=content,
            )
            messages.append(msg)

        return messages

    async def request_collaboration(
        self,
        requester: str,
        helper: str,
        task: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Request collaboration from another agent.

        Args:
            requester: Requesting agent ID
            helper: Helper agent ID
            task: Task description
            payload: Task payload

        Returns:
            Collaboration result
        """
        correlation_id = str(uuid.uuid4())

        # Send request
        await self.send_message(
            from_agent=requester,
            to_agent=helper,
            message_type=MessageType.REQUEST,
            content={"task": task, "payload": payload},
            correlation_id=correlation_id,
        )

        # Wait for response
        response = await self._wait_for_response(helper, requester, correlation_id)

        if response:
            return {
                "success": True,
                "response": response.content,
                "helper": helper,
            }
        else:
            return {
                "success": False,
                "error": "Timeout waiting for response",
                "helper": helper,
            }

    async def delegate_task(
        self,
        from_agent: str,
        to_agent: str,
        action: str,
        payload: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Delegate a task to another agent.

        Args:
            from_agent: Delegating agent ID
            to_agent: Target agent ID
            action: Action to perform
            payload: Action payload
            context: Additional context

        Returns:
            Delegation result
        """
        if to_agent not in self.agents:
            return {
                "success": False,
                "error": f"Agent {to_agent} not found",
            }

        target_agent = self.agents[to_agent]

        # Send delegation message
        correlation_id = str(uuid.uuid4())
        await self.send_message(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=MessageType.DELEGATE,
            content={"action": action, "payload": payload},
            correlation_id=correlation_id,
        )

        # Execute on target agent
        try:
            result = await target_agent.execute(action, payload, context or {})

            # Send completion notification
            await self.send_message(
                from_agent=to_agent,
                to_agent=from_agent,
                message_type=MessageType.COMPLETE,
                content={"result": result.to_dict()},
                correlation_id=correlation_id,
            )

            return {
                "success": result.success,
                "result": result.to_dict(),
                "delegated_to": to_agent,
            }

        except Exception as e:
            await self.send_message(
                from_agent=to_agent,
                to_agent=from_agent,
                message_type=MessageType.ERROR,
                content={"error": str(e)},
                correlation_id=correlation_id,
            )

            return {
                "success": False,
                "error": str(e),
                "delegated_to": to_agent,
            }

    async def negotiate(
        self,
        participants: List[str],
        goal: str,
        initial_positions: Dict[str, Dict[str, Any]],
        max_rounds: int = 5,
    ) -> Negotiation:
        """
        Start a negotiation between agents.

        Uses LLM to find compromises between conflicting positions.

        Args:
            participants: Agent IDs participating
            goal: Shared goal of the negotiation
            initial_positions: Each agent's initial position
            max_rounds: Maximum negotiation rounds

        Returns:
            Negotiation result
        """
        negotiation_id = str(uuid.uuid4())

        negotiation = Negotiation(
            negotiation_id=negotiation_id,
            participants=participants,
            goal=goal,
            status=NegotiationStatus.IN_PROGRESS,
            positions=initial_positions,
            max_rounds=max_rounds,
        )

        self._negotiations[negotiation_id] = negotiation
        logger.info(f"Starting negotiation {negotiation_id}: {goal}")

        # Negotiate using LLM
        for round_num in range(max_rounds):
            logger.debug(f"Negotiation round {round_num + 1}/{max_rounds}")

            # Use LLM to find compromise
            if len(participants) >= 2:
                agent1_id = participants[0]
                agent2_id = participants[1]

                result = self.llm.negotiate_constraints(
                    agent1_position=initial_positions.get(agent1_id, {}),
                    agent2_position=initial_positions.get(agent2_id, {}),
                    shared_goal=goal,
                )

                if result.get("resolution_possible", False):
                    # Agreement reached
                    negotiation.status = NegotiationStatus.AGREED
                    negotiation.agreement = result.get("compromise", {})
                    negotiation.concessions = {
                        agent1_id: result.get("compromise", {}).get("agent1_concessions", []),
                        agent2_id: result.get("compromise", {}).get("agent2_concessions", []),
                    }
                    break

                # Update positions for next round
                modified = result.get("compromise", {}).get("modified_parameters", {})
                if modified:
                    for agent_id in participants:
                        if agent_id in initial_positions:
                            initial_positions[agent_id].update(modified)

        if negotiation.status != NegotiationStatus.AGREED:
            negotiation.status = NegotiationStatus.FAILED

        negotiation.completed_at = datetime.now()
        logger.info(f"Negotiation {negotiation_id} completed: {negotiation.status.value}")

        return negotiation

    def create_shared_context(
        self,
        participants: List[str],
        initial_data: Optional[Dict[str, Any]] = None,
    ) -> SharedContext:
        """
        Create a shared context for collaborating agents.

        Args:
            participants: Agents that will share this context
            initial_data: Initial context data

        Returns:
            SharedContext instance
        """
        context_id = str(uuid.uuid4())

        context = SharedContext(
            context_id=context_id,
            participants=participants,
            data=initial_data or {},
        )

        self._shared_contexts[context_id] = context
        logger.info(f"Shared context created: {context_id} for {participants}")

        return context

    def update_shared_context(
        self,
        context_id: str,
        agent_id: str,
        updates: Dict[str, Any],
    ) -> bool:
        """
        Update a shared context.

        Args:
            context_id: Context to update
            agent_id: Agent making the update
            updates: Data to add/update

        Returns:
            Success status
        """
        if context_id not in self._shared_contexts:
            return False

        context = self._shared_contexts[context_id]

        if agent_id not in context.participants:
            logger.warning(f"Agent {agent_id} not a participant in context {context_id}")
            return False

        context.data.update(updates)
        context.updated_at = datetime.now()
        context.metadata[f"last_updated_by"] = agent_id

        return True

    def get_shared_context(
        self,
        context_id: str,
        agent_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get a shared context.

        Args:
            context_id: Context ID
            agent_id: Agent requesting access

        Returns:
            Context data or None
        """
        if context_id not in self._shared_contexts:
            return None

        context = self._shared_contexts[context_id]

        if agent_id not in context.participants:
            return None

        return context.data

    async def reach_consensus(
        self,
        participants: List[str],
        proposal: Dict[str, Any],
        threshold: float = 0.66,
    ) -> Dict[str, Any]:
        """
        Reach consensus among agents on a proposal.

        Args:
            participants: Agents that need to agree
            proposal: The proposal to vote on
            threshold: Required approval ratio (default 2/3)

        Returns:
            Consensus result
        """
        votes: Dict[str, bool] = {}
        reasons: Dict[str, str] = {}

        # Request votes from each participant
        for agent_id in participants:
            if agent_id not in self.agents:
                continue

            agent = self.agents[agent_id]

            # Use agent's reasoning to evaluate proposal
            try:
                result = await agent.execute(
                    "evaluate_proposal",
                    {"proposal": proposal},
                    {"consensus_check": True},
                )

                # Interpret result as vote
                if result.success:
                    vote = result.result_data.get("approved", False)
                    reason = result.result_data.get("reason", "")
                else:
                    vote = False
                    reason = "Agent declined to vote"

            except Exception as e:
                vote = False
                reason = f"Error: {e}"

            votes[agent_id] = vote
            reasons[agent_id] = reason

        # Calculate consensus
        if participants:
            approval_ratio = sum(1 for v in votes.values() if v) / len(participants)
        else:
            approval_ratio = 0

        consensus_reached = approval_ratio >= threshold

        return {
            "consensus_reached": consensus_reached,
            "approval_ratio": approval_ratio,
            "threshold": threshold,
            "votes": votes,
            "reasons": reasons,
            "proposal": proposal,
        }

    async def _wait_for_response(
        self,
        from_agent: str,
        to_agent: str,
        correlation_id: str,
        timeout: float = 30.0,
    ) -> Optional[AgentMessage]:
        """Wait for a response message with matching correlation ID."""
        deadline = datetime.now().timestamp() + timeout

        while datetime.now().timestamp() < deadline:
            message = await self.receive_message(to_agent, timeout=1.0)

            if message and message.correlation_id == correlation_id:
                if message.message_type == MessageType.RESPONSE:
                    return message

        return None

    def get_agent_connections(self, agent_id: str) -> List[str]:
        """Get agents that have communicated with the given agent."""
        connected = set()

        for msg in self._message_history:
            if msg.from_agent == agent_id:
                connected.add(msg.to_agent)
            elif msg.to_agent == agent_id:
                connected.add(msg.from_agent)

        return list(connected)

    def get_collaboration_stats(self) -> Dict[str, Any]:
        """Get collaboration statistics."""
        return {
            "registered_agents": len(self.agents),
            "total_messages": len(self._message_history),
            "active_negotiations": len([n for n in self._negotiations.values()
                                        if n.status == NegotiationStatus.IN_PROGRESS]),
            "completed_negotiations": len([n for n in self._negotiations.values()
                                           if n.status in [NegotiationStatus.AGREED,
                                                           NegotiationStatus.FAILED]]),
            "shared_contexts": len(self._shared_contexts),
        }


# Singleton
_hub: Optional[CollaborationHub] = None


def get_collaboration_hub() -> CollaborationHub:
    """Get the singleton collaboration hub."""
    global _hub
    if _hub is None:
        _hub = CollaborationHub()
    return _hub


def reset_collaboration_hub():
    """Reset the singleton (for testing)."""
    global _hub
    _hub = None
