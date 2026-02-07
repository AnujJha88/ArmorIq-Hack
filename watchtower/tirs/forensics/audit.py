"""
Cryptographic Audit Chain
==========================
Tamper-evident audit logging with hash chain.
"""

import json
import hashlib
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
import threading

logger = logging.getLogger("TIRS.Audit")


class AuditEventType(Enum):
    """Types of audit events."""
    # Agent lifecycle
    AGENT_CREATED = "agent_created"
    AGENT_STARTED = "agent_started"
    AGENT_PAUSED = "agent_paused"
    AGENT_RESUMED = "agent_resumed"
    AGENT_KILLED = "agent_killed"
    AGENT_RESURRECTED = "agent_resurrected"

    # Intent processing
    INTENT_RECEIVED = "intent_received"
    INTENT_ALLOWED = "intent_allowed"
    INTENT_DENIED = "intent_denied"
    INTENT_MODIFIED = "intent_modified"

    # Drift detection
    DRIFT_WARNING = "drift_warning"
    DRIFT_CRITICAL = "drift_critical"
    DRIFT_TERMINAL = "drift_terminal"

    # Enforcement
    ENFORCEMENT_THROTTLE = "enforcement_throttle"
    ENFORCEMENT_PAUSE = "enforcement_pause"
    ENFORCEMENT_KILL = "enforcement_kill"
    ENFORCEMENT_QUARANTINE = "enforcement_quarantine"

    # Approvals
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_DENIED = "approval_denied"

    # Appeals
    APPEAL_SUBMITTED = "appeal_submitted"
    APPEAL_APPROVED = "appeal_approved"
    APPEAL_DENIED = "appeal_denied"

    # Forensics
    SNAPSHOT_CREATED = "snapshot_created"
    CHAIN_VERIFIED = "chain_verified"
    CHAIN_TAMPERED = "chain_tampered"

    # System
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    CONFIG_CHANGE = "config_change"


@dataclass
class AuditEntry:
    """Single entry in the audit chain."""
    entry_id: str
    timestamp: datetime
    event_type: AuditEventType
    agent_id: Optional[str]
    user_id: Optional[str]
    data: Dict[str, Any]

    # Chain integrity
    sequence: int
    previous_hash: str
    content_hash: str

    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute hash of entry content."""
        content = {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "agent_id": self.agent_id,
            "user_id": self.user_id,
            "data": self.data,
            "sequence": self.sequence,
            "previous_hash": self.previous_hash,
        }
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()

    def verify(self) -> bool:
        """Verify entry integrity."""
        return self.content_hash == self._compute_hash()

    def to_dict(self) -> Dict:
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "agent_id": self.agent_id,
            "user_id": self.user_id,
            "data": self.data,
            "sequence": self.sequence,
            "previous_hash": self.previous_hash[:16] + "...",
            "content_hash": self.content_hash[:16] + "...",
        }


class AuditChain:
    """
    Cryptographic audit chain with tamper detection.

    Features:
    - Hash chain for integrity verification
    - Thread-safe operations
    - Persistent storage
    - Chain verification
    """

    GENESIS_HASH = "0" * 64  # Genesis block hash

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("/tmp/watchtower_audit.jsonl")
        self._entries: List[AuditEntry] = []
        self._lock = threading.Lock()
        self._sequence = 0

        # Load existing entries
        self._load_entries()

    def _load_entries(self):
        """Load entries from storage."""
        if not self.storage_path.exists():
            return

        try:
            with open(self.storage_path, "r") as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        entry = AuditEntry(
                            entry_id=data["entry_id"],
                            timestamp=datetime.fromisoformat(data["timestamp"]),
                            event_type=AuditEventType(data["event_type"]),
                            agent_id=data.get("agent_id"),
                            user_id=data.get("user_id"),
                            data=data.get("data", {}),
                            sequence=data["sequence"],
                            previous_hash=data["previous_hash"],
                            content_hash=data["content_hash"],
                        )
                        self._entries.append(entry)
                        self._sequence = max(self._sequence, entry.sequence)
                    except Exception as e:
                        logger.warning(f"Failed to load entry: {e}")

            logger.info(f"Loaded {len(self._entries)} audit entries")

        except Exception as e:
            logger.error(f"Failed to load audit chain: {e}")

    def _persist_entry(self, entry: AuditEntry):
        """Persist entry to storage."""
        try:
            with open(self.storage_path, "a") as f:
                entry_dict = {
                    "entry_id": entry.entry_id,
                    "timestamp": entry.timestamp.isoformat(),
                    "event_type": entry.event_type.value,
                    "agent_id": entry.agent_id,
                    "user_id": entry.user_id,
                    "data": entry.data,
                    "sequence": entry.sequence,
                    "previous_hash": entry.previous_hash,
                    "content_hash": entry.content_hash,
                }
                f.write(json.dumps(entry_dict) + "\n")
        except Exception as e:
            logger.error(f"Failed to persist audit entry: {e}")

    def log(
        self,
        event_type: AuditEventType,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        data: Optional[Dict] = None,
    ) -> AuditEntry:
        """
        Add an entry to the audit chain.

        Thread-safe operation that maintains chain integrity.
        """
        with self._lock:
            self._sequence += 1

            # Get previous hash
            if self._entries:
                previous_hash = self._entries[-1].content_hash
            else:
                previous_hash = self.GENESIS_HASH

            entry = AuditEntry(
                entry_id=f"AUD-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self._sequence:06d}",
                timestamp=datetime.now(),
                event_type=event_type,
                agent_id=agent_id,
                user_id=user_id,
                data=data or {},
                sequence=self._sequence,
                previous_hash=previous_hash,
                content_hash="",  # Will be computed in __post_init__
            )

            self._entries.append(entry)
            self._persist_entry(entry)

            return entry

    def verify_chain(self) -> Tuple[bool, List[str]]:
        """
        Verify the integrity of the entire chain.

        Returns:
            (is_valid, list of issues)
        """
        issues = []

        if not self._entries:
            return True, []

        # Check genesis
        if self._entries[0].previous_hash != self.GENESIS_HASH:
            issues.append("Genesis block has invalid previous hash")

        for i, entry in enumerate(self._entries):
            # Verify individual entry
            if not entry.verify():
                issues.append(f"Entry {entry.entry_id} failed integrity check")

            # Verify chain linkage
            if i > 0:
                expected_hash = self._entries[i - 1].content_hash
                if entry.previous_hash != expected_hash:
                    issues.append(
                        f"Chain broken at {entry.entry_id} (seq {entry.sequence})"
                    )

            # Verify sequence
            if entry.sequence != i + 1:
                issues.append(
                    f"Sequence gap at {entry.entry_id}: expected {i + 1}, got {entry.sequence}"
                )

        is_valid = len(issues) == 0

        # Log verification result
        self.log(
            AuditEventType.CHAIN_VERIFIED if is_valid else AuditEventType.CHAIN_TAMPERED,
            data={"is_valid": is_valid, "issues_count": len(issues)},
        )

        return is_valid, issues

    def get_entries(
        self,
        event_type: Optional[AuditEventType] = None,
        agent_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AuditEntry]:
        """Get filtered audit entries."""
        entries = self._entries

        if event_type:
            entries = [e for e in entries if e.event_type == event_type]

        if agent_id:
            entries = [e for e in entries if e.agent_id == agent_id]

        if start_time:
            entries = [e for e in entries if e.timestamp >= start_time]

        if end_time:
            entries = [e for e in entries if e.timestamp <= end_time]

        return entries[-limit:]

    def get_summary(self) -> Dict:
        """Get audit chain summary."""
        by_type = {}
        by_agent = {}

        for entry in self._entries:
            by_type[entry.event_type.value] = by_type.get(entry.event_type.value, 0) + 1
            if entry.agent_id:
                by_agent[entry.agent_id] = by_agent.get(entry.agent_id, 0) + 1

        return {
            "total_entries": len(self._entries),
            "current_sequence": self._sequence,
            "by_event_type": by_type,
            "by_agent": by_agent,
            "last_entry": self._entries[-1].to_dict() if self._entries else None,
        }

    def export_json(self, filepath: Path):
        """Export chain to JSON file."""
        with open(filepath, "w") as f:
            json.dump(
                {
                    "exported_at": datetime.now().isoformat(),
                    "total_entries": len(self._entries),
                    "entries": [e.to_dict() for e in self._entries],
                },
                f,
                indent=2,
            )


# Convenience logging functions
def log_intent(
    chain: AuditChain,
    agent_id: str,
    intent_id: str,
    intent_text: str,
    verdict: str,
    policy_triggered: Optional[str] = None,
) -> AuditEntry:
    """Log an intent event."""
    event_type = {
        "ALLOW": AuditEventType.INTENT_ALLOWED,
        "DENY": AuditEventType.INTENT_DENIED,
        "MODIFY": AuditEventType.INTENT_MODIFIED,
    }.get(verdict.upper(), AuditEventType.INTENT_RECEIVED)

    return chain.log(
        event_type=event_type,
        agent_id=agent_id,
        data={
            "intent_id": intent_id,
            "intent_text": intent_text[:200],
            "verdict": verdict,
            "policy_triggered": policy_triggered,
        },
    )


def log_drift_event(
    chain: AuditChain,
    agent_id: str,
    risk_score: float,
    risk_level: str,
) -> AuditEntry:
    """Log a drift event."""
    event_type = {
        "warning": AuditEventType.DRIFT_WARNING,
        "critical": AuditEventType.DRIFT_CRITICAL,
        "terminal": AuditEventType.DRIFT_TERMINAL,
    }.get(risk_level.lower(), AuditEventType.DRIFT_WARNING)

    return chain.log(
        event_type=event_type,
        agent_id=agent_id,
        data={
            "risk_score": risk_score,
            "risk_level": risk_level,
        },
    )


# Singleton
_chain: Optional[AuditChain] = None


def get_audit_chain() -> AuditChain:
    """Get singleton audit chain."""
    global _chain
    if _chain is None:
        _chain = AuditChain()
    return _chain
