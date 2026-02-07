"""
Enforcement Actions
===================
Actions taken in response to risk thresholds.
"""

import logging
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger("TIRS.Enforcement")


class ActionType(Enum):
    """Types of enforcement actions."""
    MONITOR = "monitor"       # Passive observation
    ALERT = "alert"           # Send notification
    THROTTLE = "throttle"     # Rate limit actions
    PAUSE = "pause"           # Suspend execution
    QUARANTINE = "quarantine" # Isolate + investigate
    KILL = "kill"             # Terminate agent
    ESCALATE = "escalate"     # Require human approval


class ActionSeverity(Enum):
    """Severity levels for actions."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class EnforcementAction:
    """
    An enforcement action to take on an agent.
    """
    action_type: ActionType
    severity: ActionSeverity
    agent_id: str
    reason: str
    timestamp: datetime = field(default_factory=datetime.now)

    # Action parameters
    duration_seconds: Optional[int] = None  # For throttle/pause
    rate_limit: Optional[float] = None      # For throttle (actions per minute)
    escalation_level: Optional[str] = None  # For escalate
    metadata: Dict = field(default_factory=dict)

    # Tracking
    action_id: str = ""
    executed: bool = False
    executed_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.action_id:
            self.action_id = f"ACT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{id(self) % 10000:04d}"

    def to_dict(self) -> Dict:
        return {
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "severity": self.severity.name,
            "agent_id": self.agent_id,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
            "duration_seconds": self.duration_seconds,
            "rate_limit": self.rate_limit,
            "escalation_level": self.escalation_level,
            "executed": self.executed,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
        }


@dataclass
class EnforcementResult:
    """Result of executing an enforcement action."""
    action: EnforcementAction
    success: bool
    message: str
    side_effects: List[str] = field(default_factory=list)
    rollback_available: bool = False


class EnforcementExecutor:
    """
    Executes enforcement actions.

    Provides hooks for integration with external systems.
    """

    def __init__(self):
        self._action_handlers: Dict[ActionType, Callable] = {}
        self._action_history: List[EnforcementAction] = []
        self._active_throttles: Dict[str, EnforcementAction] = {}
        self._active_pauses: Dict[str, EnforcementAction] = {}

        # Register default handlers
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Register default action handlers."""
        self._action_handlers[ActionType.MONITOR] = self._handle_monitor
        self._action_handlers[ActionType.ALERT] = self._handle_alert
        self._action_handlers[ActionType.THROTTLE] = self._handle_throttle
        self._action_handlers[ActionType.PAUSE] = self._handle_pause
        self._action_handlers[ActionType.QUARANTINE] = self._handle_quarantine
        self._action_handlers[ActionType.KILL] = self._handle_kill
        self._action_handlers[ActionType.ESCALATE] = self._handle_escalate

    def register_handler(self, action_type: ActionType, handler: Callable):
        """Register a custom handler for an action type."""
        self._action_handlers[action_type] = handler

    def execute(self, action: EnforcementAction) -> EnforcementResult:
        """Execute an enforcement action."""
        handler = self._action_handlers.get(action.action_type)

        if not handler:
            logger.error(f"No handler for action type: {action.action_type}")
            return EnforcementResult(
                action=action,
                success=False,
                message=f"No handler for {action.action_type}",
            )

        try:
            result = handler(action)
            action.executed = True
            action.executed_at = datetime.now()
            self._action_history.append(action)
            return result

        except Exception as e:
            logger.error(f"Error executing action {action.action_id}: {e}")
            return EnforcementResult(
                action=action,
                success=False,
                message=str(e),
            )

    def _handle_monitor(self, action: EnforcementAction) -> EnforcementResult:
        """Handle monitor action (logging only)."""
        logger.info(f"[MONITOR] {action.agent_id}: {action.reason}")
        return EnforcementResult(
            action=action,
            success=True,
            message="Monitoring enabled",
        )

    def _handle_alert(self, action: EnforcementAction) -> EnforcementResult:
        """Handle alert action."""
        logger.warning(f"[ALERT] {action.agent_id}: {action.reason}")
        # In production, this would send to notification system
        return EnforcementResult(
            action=action,
            success=True,
            message="Alert sent",
            side_effects=["notification_sent"],
        )

    def _handle_throttle(self, action: EnforcementAction) -> EnforcementResult:
        """Handle throttle action."""
        rate = action.rate_limit or 1.0
        duration = action.duration_seconds or 300

        logger.warning(f"[THROTTLE] {action.agent_id}: {rate} actions/min for {duration}s")
        self._active_throttles[action.agent_id] = action

        return EnforcementResult(
            action=action,
            success=True,
            message=f"Throttled to {rate} actions/min",
            side_effects=["rate_limited"],
            rollback_available=True,
        )

    def _handle_pause(self, action: EnforcementAction) -> EnforcementResult:
        """Handle pause action."""
        logger.warning(f"[PAUSE] {action.agent_id}: {action.reason}")
        self._active_pauses[action.agent_id] = action

        return EnforcementResult(
            action=action,
            success=True,
            message="Agent paused",
            side_effects=["execution_suspended"],
            rollback_available=True,
        )

    def _handle_quarantine(self, action: EnforcementAction) -> EnforcementResult:
        """Handle quarantine action."""
        logger.critical(f"[QUARANTINE] {action.agent_id}: {action.reason}")

        return EnforcementResult(
            action=action,
            success=True,
            message="Agent quarantined for investigation",
            side_effects=["execution_suspended", "network_isolated", "investigation_opened"],
            rollback_available=True,
        )

    def _handle_kill(self, action: EnforcementAction) -> EnforcementResult:
        """Handle kill action."""
        logger.critical(f"[KILL] {action.agent_id}: {action.reason}")

        # Remove from active lists
        self._active_throttles.pop(action.agent_id, None)
        self._active_pauses.pop(action.agent_id, None)

        return EnforcementResult(
            action=action,
            success=True,
            message="Agent terminated",
            side_effects=["execution_terminated", "forensic_snapshot_created"],
            rollback_available=False,  # Kill is permanent without resurrection
        )

    def _handle_escalate(self, action: EnforcementAction) -> EnforcementResult:
        """Handle escalate action."""
        level = action.escalation_level or "manager"
        logger.warning(f"[ESCALATE] {action.agent_id}: Escalated to {level}")

        return EnforcementResult(
            action=action,
            success=True,
            message=f"Escalated to {level} for approval",
            side_effects=["approval_requested"],
        )

    def is_throttled(self, agent_id: str) -> bool:
        """Check if agent is currently throttled."""
        if agent_id not in self._active_throttles:
            return False

        action = self._active_throttles[agent_id]
        if action.duration_seconds:
            elapsed = (datetime.now() - action.timestamp).total_seconds()
            if elapsed >= action.duration_seconds:
                del self._active_throttles[agent_id]
                return False

        return True

    def is_paused(self, agent_id: str) -> bool:
        """Check if agent is currently paused."""
        return agent_id in self._active_pauses

    def resume(self, agent_id: str, admin_id: str) -> bool:
        """Resume a paused agent."""
        if agent_id in self._active_pauses:
            del self._active_pauses[agent_id]
            logger.info(f"Agent {agent_id} resumed by {admin_id}")
            return True
        return False

    def get_action_history(self, agent_id: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Get action history."""
        history = self._action_history
        if agent_id:
            history = [a for a in history if a.agent_id == agent_id]

        return [a.to_dict() for a in history[-limit:]]


# Factory for creating actions
def create_action(
    action_type: ActionType,
    agent_id: str,
    reason: str,
    risk_score: Optional[float] = None,
    **kwargs,
) -> EnforcementAction:
    """Create an enforcement action with appropriate severity."""
    severity_map = {
        ActionType.MONITOR: ActionSeverity.LOW,
        ActionType.ALERT: ActionSeverity.MEDIUM,
        ActionType.THROTTLE: ActionSeverity.MEDIUM,
        ActionType.PAUSE: ActionSeverity.HIGH,
        ActionType.QUARANTINE: ActionSeverity.CRITICAL,
        ActionType.KILL: ActionSeverity.CRITICAL,
        ActionType.ESCALATE: ActionSeverity.HIGH,
    }

    return EnforcementAction(
        action_type=action_type,
        severity=severity_map.get(action_type, ActionSeverity.MEDIUM),
        agent_id=agent_id,
        reason=reason,
        metadata={"risk_score": risk_score} if risk_score else {},
        **kwargs,
    )


# Singleton executor
_executor: Optional[EnforcementExecutor] = None


def get_executor() -> EnforcementExecutor:
    """Get singleton executor."""
    global _executor
    if _executor is None:
        _executor = EnforcementExecutor()
    return _executor
