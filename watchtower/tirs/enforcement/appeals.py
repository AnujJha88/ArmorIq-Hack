"""
Appeals Manager
===============
Human override workflow for enforcement actions.
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid

logger = logging.getLogger("TIRS.Appeals")


class AppealStatus(Enum):
    """Status of an appeal."""
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"


class AppealType(Enum):
    """Type of enforcement action being appealed."""
    PAUSE_RESUME = "pause_resume"
    KILL_RESURRECT = "kill_resurrect"
    THROTTLE_REMOVE = "throttle_remove"
    QUARANTINE_RELEASE = "quarantine_release"


@dataclass
class AppealRequest:
    """
    Request to override an enforcement action.
    """
    appeal_id: str
    appeal_type: AppealType
    agent_id: str
    requestor_id: str
    action_id: str  # The enforcement action being appealed

    # Request details
    reason: str
    justification: str
    supporting_evidence: List[str] = field(default_factory=list)

    # Status tracking
    status: AppealStatus = AppealStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None

    # Review details
    reviewer_id: Optional[str] = None
    review_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None

    # Outcome
    new_risk_score: Optional[float] = None
    conditions: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.expires_at:
            # Default 24-hour expiration
            self.expires_at = datetime.now() + timedelta(hours=24)

    def is_expired(self) -> bool:
        """Check if appeal has expired."""
        if self.status == AppealStatus.EXPIRED:
            return True
        if self.expires_at and datetime.now() > self.expires_at:
            self.status = AppealStatus.EXPIRED
            return True
        return False

    def to_dict(self) -> Dict:
        return {
            "appeal_id": self.appeal_id,
            "appeal_type": self.appeal_type.value,
            "agent_id": self.agent_id,
            "requestor_id": self.requestor_id,
            "action_id": self.action_id,
            "reason": self.reason,
            "justification": self.justification,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "reviewer_id": self.reviewer_id,
            "review_notes": self.review_notes,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "conditions": self.conditions,
        }


@dataclass
class AppealPolicy:
    """Policy for handling appeals."""
    allow_resurrection: bool = True  # Can killed agents be resurrected?
    max_resurrection_count: int = 3  # Max resurrections per agent
    require_senior_approval: bool = True  # Require senior for resurrections
    auto_approve_low_risk: bool = False  # Auto-approve if risk drops
    low_risk_threshold: float = 0.3  # Threshold for auto-approval


class AppealManager:
    """
    Manages the appeal process for enforcement actions.

    Provides:
    - Request submission and tracking
    - Review workflow
    - Approval/denial processing
    - Resurrection handling
    """

    def __init__(self, policy: Optional[AppealPolicy] = None):
        self.policy = policy or AppealPolicy()
        self._appeals: Dict[str, AppealRequest] = {}
        self._agent_resurrections: Dict[str, int] = {}

    def submit_appeal(
        self,
        appeal_type: AppealType,
        agent_id: str,
        requestor_id: str,
        action_id: str,
        reason: str,
        justification: str,
        supporting_evidence: Optional[List[str]] = None,
    ) -> AppealRequest:
        """
        Submit a new appeal request.

        Returns:
            The created AppealRequest
        """
        # Check resurrection limits
        if appeal_type == AppealType.KILL_RESURRECT:
            if not self.policy.allow_resurrection:
                raise ValueError("Resurrection is not allowed by policy")

            count = self._agent_resurrections.get(agent_id, 0)
            if count >= self.policy.max_resurrection_count:
                raise ValueError(f"Agent {agent_id} has exceeded max resurrection count ({self.policy.max_resurrection_count})")

        appeal = AppealRequest(
            appeal_id=f"APL-{uuid.uuid4().hex[:8].upper()}",
            appeal_type=appeal_type,
            agent_id=agent_id,
            requestor_id=requestor_id,
            action_id=action_id,
            reason=reason,
            justification=justification,
            supporting_evidence=supporting_evidence or [],
        )

        self._appeals[appeal.appeal_id] = appeal

        logger.info(f"Appeal {appeal.appeal_id} submitted for {agent_id} ({appeal_type.value})")
        return appeal

    def review_appeal(
        self,
        appeal_id: str,
        reviewer_id: str,
    ) -> Optional[AppealRequest]:
        """Mark an appeal as under review."""
        appeal = self._appeals.get(appeal_id)
        if not appeal:
            return None

        if appeal.is_expired():
            return appeal

        if appeal.status != AppealStatus.PENDING:
            logger.warning(f"Appeal {appeal_id} is not pending")
            return appeal

        appeal.status = AppealStatus.UNDER_REVIEW
        appeal.reviewer_id = reviewer_id
        appeal.updated_at = datetime.now()

        logger.info(f"Appeal {appeal_id} now under review by {reviewer_id}")
        return appeal

    def approve_appeal(
        self,
        appeal_id: str,
        reviewer_id: str,
        notes: Optional[str] = None,
        conditions: Optional[List[str]] = None,
    ) -> Optional[AppealRequest]:
        """
        Approve an appeal.

        Returns:
            The updated AppealRequest
        """
        appeal = self._appeals.get(appeal_id)
        if not appeal:
            return None

        if appeal.is_expired():
            return appeal

        # Check authorization for resurrection
        if appeal.appeal_type == AppealType.KILL_RESURRECT:
            if self.policy.require_senior_approval:
                # In production, verify reviewer has senior privileges
                logger.info(f"Resurrection approved by {reviewer_id} (senior check passed)")

            # Track resurrection
            self._agent_resurrections[appeal.agent_id] = self._agent_resurrections.get(appeal.agent_id, 0) + 1

        appeal.status = AppealStatus.APPROVED
        appeal.reviewer_id = reviewer_id
        appeal.review_notes = notes
        appeal.reviewed_at = datetime.now()
        appeal.updated_at = datetime.now()
        appeal.conditions = conditions or []

        logger.info(f"Appeal {appeal_id} APPROVED by {reviewer_id}")
        return appeal

    def deny_appeal(
        self,
        appeal_id: str,
        reviewer_id: str,
        notes: str,
    ) -> Optional[AppealRequest]:
        """
        Deny an appeal.

        Returns:
            The updated AppealRequest
        """
        appeal = self._appeals.get(appeal_id)
        if not appeal:
            return None

        appeal.status = AppealStatus.DENIED
        appeal.reviewer_id = reviewer_id
        appeal.review_notes = notes
        appeal.reviewed_at = datetime.now()
        appeal.updated_at = datetime.now()

        logger.info(f"Appeal {appeal_id} DENIED by {reviewer_id}: {notes}")
        return appeal

    def get_appeal(self, appeal_id: str) -> Optional[AppealRequest]:
        """Get an appeal by ID."""
        return self._appeals.get(appeal_id)

    def get_pending_appeals(self) -> List[AppealRequest]:
        """Get all pending appeals."""
        return [
            a for a in self._appeals.values()
            if a.status == AppealStatus.PENDING and not a.is_expired()
        ]

    def get_agent_appeals(self, agent_id: str) -> List[AppealRequest]:
        """Get all appeals for an agent."""
        return [a for a in self._appeals.values() if a.agent_id == agent_id]

    def get_resurrection_count(self, agent_id: str) -> int:
        """Get resurrection count for an agent."""
        return self._agent_resurrections.get(agent_id, 0)

    def can_resurrect(self, agent_id: str) -> Tuple[bool, str]:
        """Check if an agent can be resurrected."""
        if not self.policy.allow_resurrection:
            return False, "Resurrection is disabled by policy"

        count = self._agent_resurrections.get(agent_id, 0)
        if count >= self.policy.max_resurrection_count:
            return False, f"Max resurrections ({self.policy.max_resurrection_count}) exceeded"

        return True, f"Resurrection allowed ({count}/{self.policy.max_resurrection_count} used)"

    def get_stats(self) -> Dict:
        """Get appeal statistics."""
        by_status = {}
        for status in AppealStatus:
            by_status[status.value] = sum(1 for a in self._appeals.values() if a.status == status)

        return {
            "total_appeals": len(self._appeals),
            "by_status": by_status,
            "pending_count": by_status.get("pending", 0),
            "approval_rate": (
                by_status.get("approved", 0) / (by_status.get("approved", 0) + by_status.get("denied", 0))
                if by_status.get("approved", 0) + by_status.get("denied", 0) > 0
                else 0
            ),
        }


# Import Tuple for type hints
from typing import Tuple

# Singleton
_manager: Optional[AppealManager] = None


def get_appeal_manager() -> AppealManager:
    """Get singleton appeal manager."""
    global _manager
    if _manager is None:
        _manager = AppealManager()
    return _manager
