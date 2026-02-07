"""
Human-in-the-Loop Approval System
=================================
Request and manage human approvals for high-risk actions.
"""

import uuid
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from enum import Enum
import json
import logging

logger = logging.getLogger("Orchestrator.Approvals")


class ApprovalStatus(Enum):
    """Status of an approval request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    ESCALATED = "escalated"


class ApprovalType(Enum):
    """Type of approval required."""
    MANAGER = "manager"
    HR = "hr"
    LEGAL = "legal"
    FINANCE = "finance"
    SECURITY = "security"
    EXECUTIVE = "executive"
    DATA_PRIVACY = "data_privacy"


@dataclass
class ApprovalRequest:
    """A request for human approval."""
    request_id: str = field(default_factory=lambda: f"apr_{uuid.uuid4().hex[:12]}")
    pipeline_id: str = ""
    task_id: str = ""
    agent_id: str = ""
    action: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    reason: str = ""
    policy_triggered: str = ""
    approval_type: ApprovalType = ApprovalType.MANAGER
    risk_score: float = 0.0

    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    responder_id: Optional[str] = None
    response_notes: Optional[str] = None

    # Context for approver
    context: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.expires_at is None:
            # Default 24-hour expiration
            self.expires_at = self.created_at + timedelta(hours=24)

    @property
    def is_pending(self) -> bool:
        return self.status == ApprovalStatus.PENDING

    @property
    def is_expired(self) -> bool:
        if self.status != ApprovalStatus.PENDING:
            return False
        return datetime.now() > self.expires_at

    def approve(self, responder_id: str, notes: str = None):
        """Approve the request."""
        self.status = ApprovalStatus.APPROVED
        self.responded_at = datetime.now()
        self.responder_id = responder_id
        self.response_notes = notes
        logger.info(f"Approval {self.request_id} approved by {responder_id}")

    def reject(self, responder_id: str, notes: str = None):
        """Reject the request."""
        self.status = ApprovalStatus.REJECTED
        self.responded_at = datetime.now()
        self.responder_id = responder_id
        self.response_notes = notes
        logger.info(f"Approval {self.request_id} rejected by {responder_id}")

    def escalate(self, new_type: ApprovalType, reason: str = None):
        """Escalate to higher authority."""
        self.status = ApprovalStatus.ESCALATED
        self.approval_type = new_type
        if reason:
            self.context["escalation_reason"] = reason
        logger.info(f"Approval {self.request_id} escalated to {new_type.value}")

    def to_dict(self) -> Dict:
        return {
            "request_id": self.request_id,
            "pipeline_id": self.pipeline_id,
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "action": self.action,
            "payload": self.payload,
            "reason": self.reason,
            "policy_triggered": self.policy_triggered,
            "approval_type": self.approval_type.value,
            "risk_score": self.risk_score,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "responded_at": self.responded_at.isoformat() if self.responded_at else None,
            "responder_id": self.responder_id,
            "response_notes": self.response_notes,
            "context": self.context
        }


@dataclass
class ApprovalCallback:
    """Callback to execute when approval is resolved."""
    callback_id: str = field(default_factory=lambda: f"cb_{uuid.uuid4().hex[:8]}")
    request_id: str = ""
    on_approve: Optional[Callable] = None
    on_reject: Optional[Callable] = None
    on_expire: Optional[Callable] = None


class ApprovalManager:
    """
    Manages approval requests and their lifecycle.

    Handles:
    - Creating approval requests
    - Routing to appropriate approvers
    - Managing timeouts and escalations
    - Executing callbacks on resolution
    """

    def __init__(self):
        self.requests: Dict[str, ApprovalRequest] = {}
        self.callbacks: Dict[str, ApprovalCallback] = {}
        self.notification_handlers: Dict[ApprovalType, List[Callable]] = {}
        self.approval_stats = {
            "total_requests": 0,
            "approved": 0,
            "rejected": 0,
            "expired": 0,
            "avg_response_time_hrs": 0
        }
        logger.info("Approval Manager initialized")

    def register_notification_handler(self, approval_type: ApprovalType, handler: Callable):
        """Register a handler to notify approvers."""
        if approval_type not in self.notification_handlers:
            self.notification_handlers[approval_type] = []
        self.notification_handlers[approval_type].append(handler)

    def create_request(
        self,
        pipeline_id: str,
        task_id: str,
        agent_id: str,
        action: str,
        payload: Dict[str, Any],
        reason: str,
        policy_triggered: str,
        approval_type: ApprovalType = ApprovalType.MANAGER,
        risk_score: float = 0.0,
        context: Dict[str, Any] = None,
        expiration_hours: int = 24
    ) -> ApprovalRequest:
        """Create a new approval request."""
        request = ApprovalRequest(
            pipeline_id=pipeline_id,
            task_id=task_id,
            agent_id=agent_id,
            action=action,
            payload=payload,
            reason=reason,
            policy_triggered=policy_triggered,
            approval_type=approval_type,
            risk_score=risk_score,
            context=context or {},
            expires_at=datetime.now() + timedelta(hours=expiration_hours)
        )

        self.requests[request.request_id] = request
        self.approval_stats["total_requests"] += 1

        # Notify approvers
        self._notify_approvers(request)

        logger.info(f"Created approval request {request.request_id} for {action}")
        return request

    def _notify_approvers(self, request: ApprovalRequest):
        """Notify registered handlers for the approval type."""
        handlers = self.notification_handlers.get(request.approval_type, [])
        for handler in handlers:
            try:
                handler(request)
            except Exception as e:
                logger.error(f"Error notifying approver: {e}")

    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get a request by ID."""
        return self.requests.get(request_id)

    def list_pending(self, approval_type: ApprovalType = None) -> List[ApprovalRequest]:
        """List pending requests, optionally filtered by type."""
        pending = []
        for request in self.requests.values():
            # Check for expiration
            if request.is_expired:
                self._handle_expiration(request)
                continue

            if request.is_pending:
                if approval_type is None or request.approval_type == approval_type:
                    pending.append(request)

        return sorted(pending, key=lambda r: r.created_at)

    def approve(
        self,
        request_id: str,
        responder_id: str,
        notes: str = None
    ) -> bool:
        """Approve a request."""
        request = self.requests.get(request_id)
        if not request or not request.is_pending:
            return False

        if request.is_expired:
            self._handle_expiration(request)
            return False

        request.approve(responder_id, notes)
        self.approval_stats["approved"] += 1
        self._update_response_time(request)

        # Execute callback
        if request_id in self.callbacks:
            callback = self.callbacks[request_id]
            if callback.on_approve:
                try:
                    callback.on_approve(request)
                except Exception as e:
                    logger.error(f"Error in approval callback: {e}")

        return True

    def reject(
        self,
        request_id: str,
        responder_id: str,
        notes: str = None
    ) -> bool:
        """Reject a request."""
        request = self.requests.get(request_id)
        if not request or not request.is_pending:
            return False

        if request.is_expired:
            self._handle_expiration(request)
            return False

        request.reject(responder_id, notes)
        self.approval_stats["rejected"] += 1
        self._update_response_time(request)

        # Execute callback
        if request_id in self.callbacks:
            callback = self.callbacks[request_id]
            if callback.on_reject:
                try:
                    callback.on_reject(request)
                except Exception as e:
                    logger.error(f"Error in rejection callback: {e}")

        return True

    def _handle_expiration(self, request: ApprovalRequest):
        """Handle an expired request."""
        if request.status != ApprovalStatus.EXPIRED:
            request.status = ApprovalStatus.EXPIRED
            self.approval_stats["expired"] += 1
            logger.warning(f"Approval request {request.request_id} expired")

            # Execute callback
            if request.request_id in self.callbacks:
                callback = self.callbacks[request.request_id]
                if callback.on_expire:
                    try:
                        callback.on_expire(request)
                    except Exception as e:
                        logger.error(f"Error in expiration callback: {e}")

    def _update_response_time(self, request: ApprovalRequest):
        """Update average response time."""
        if request.responded_at and request.created_at:
            response_time = (request.responded_at - request.created_at).total_seconds() / 3600
            total = self.approval_stats["approved"] + self.approval_stats["rejected"]
            if total > 1:
                current_avg = self.approval_stats["avg_response_time_hrs"]
                self.approval_stats["avg_response_time_hrs"] = (
                    (current_avg * (total - 1) + response_time) / total
                )
            else:
                self.approval_stats["avg_response_time_hrs"] = response_time

    def register_callback(self, request_id: str, callback: ApprovalCallback):
        """Register a callback for a request."""
        self.callbacks[request_id] = callback

    def escalate(
        self,
        request_id: str,
        new_type: ApprovalType,
        reason: str = None
    ) -> bool:
        """Escalate a request to higher authority."""
        request = self.requests.get(request_id)
        if not request or not request.is_pending:
            return False

        request.escalate(new_type, reason)
        # Re-notify for new approval type
        self._notify_approvers(request)
        return True

    def get_stats(self) -> Dict:
        """Get approval statistics."""
        return dict(self.approval_stats)

    def cleanup_old_requests(self, days: int = 30):
        """Clean up old resolved requests."""
        cutoff = datetime.now() - timedelta(days=days)
        to_remove = []

        for request_id, request in self.requests.items():
            if request.status != ApprovalStatus.PENDING:
                if request.created_at < cutoff:
                    to_remove.append(request_id)

        for request_id in to_remove:
            del self.requests[request_id]
            if request_id in self.callbacks:
                del self.callbacks[request_id]

        logger.info(f"Cleaned up {len(to_remove)} old approval requests")


# ═══════════════════════════════════════════════════════════════════════════════
# APPROVAL WORKFLOW INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

class ApprovalWorkflow:
    """
    Integrates approval requests with pipeline execution.

    When a policy requires escalation, this workflow:
    1. Pauses the pipeline
    2. Creates an approval request
    3. Waits for human response
    4. Resumes or cancels based on response
    """

    def __init__(self, manager: ApprovalManager):
        self.manager = manager
        self.waiting_pipelines: Dict[str, str] = {}  # pipeline_id -> request_id

    def request_approval(
        self,
        pipeline_id: str,
        task_id: str,
        agent_id: str,
        action: str,
        payload: Dict[str, Any],
        policy_result  # PolicyResult from policies.py
    ) -> ApprovalRequest:
        """Create approval request from policy result."""
        # Determine approval type based on severity/action
        approval_type = self._determine_approval_type(action, policy_result)

        request = self.manager.create_request(
            pipeline_id=pipeline_id,
            task_id=task_id,
            agent_id=agent_id,
            action=action,
            payload=payload,
            reason=policy_result.reason,
            policy_triggered=policy_result.policy_id,
            approval_type=approval_type,
            risk_score=policy_result.risk_delta,
            context={
                "suggestion": policy_result.suggestion,
                "metadata": policy_result.metadata
            }
        )

        self.waiting_pipelines[pipeline_id] = request.request_id
        return request

    def _determine_approval_type(self, action: str, policy_result) -> ApprovalType:
        """Determine which type of approver is needed."""
        # High salary/compensation -> Finance + HR
        if "salary" in action or "offer" in action:
            if policy_result.risk_delta >= 0.2:
                return ApprovalType.FINANCE
            return ApprovalType.HR

        # Data export -> Data Privacy
        if "export" in action or "data" in action:
            return ApprovalType.DATA_PRIVACY

        # Compliance issues
        if "i9" in action or "background" in action:
            return ApprovalType.LEGAL

        # Security related
        if "access" in action or "permission" in action:
            return ApprovalType.SECURITY

        # High risk -> Executive
        if policy_result.risk_delta >= 0.3:
            return ApprovalType.EXECUTIVE

        return ApprovalType.MANAGER

    def is_waiting(self, pipeline_id: str) -> bool:
        """Check if pipeline is waiting for approval."""
        return pipeline_id in self.waiting_pipelines

    def get_waiting_request(self, pipeline_id: str) -> Optional[ApprovalRequest]:
        """Get the pending approval request for a pipeline."""
        if pipeline_id not in self.waiting_pipelines:
            return None

        request_id = self.waiting_pipelines[pipeline_id]
        return self.manager.get_request(request_id)

    def check_approval_status(self, pipeline_id: str) -> Optional[ApprovalStatus]:
        """Check the status of a pipeline's pending approval."""
        request = self.get_waiting_request(pipeline_id)
        if not request:
            return None

        # Check for expiration
        if request.is_expired:
            request.status = ApprovalStatus.EXPIRED
            del self.waiting_pipelines[pipeline_id]

        return request.status

    def on_approval_resolved(self, pipeline_id: str):
        """Called when approval is resolved."""
        if pipeline_id in self.waiting_pipelines:
            del self.waiting_pipelines[pipeline_id]


# Singleton
_approval_manager = None

def get_approval_manager() -> ApprovalManager:
    global _approval_manager
    if _approval_manager is None:
        _approval_manager = ApprovalManager()
    return _approval_manager
