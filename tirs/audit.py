"""
Signed Forensic Audit Ledger
============================
Cryptographically signed, tamper-evident audit trail.

Key Features:
- Every decision logged with signature
- Hash chaining for tamper evidence
- Forensic snapshots on critical events
"""

import hashlib
import hmac
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import os

logger = logging.getLogger("TIRS.Audit")

# Demo signing key (in production, use proper key management)
SIGNING_KEY = os.getenv("TIRS_SIGNING_KEY", "tirs-demo-key-2026").encode()


class AuditEventType(Enum):
    """Types of audit events."""
    INTENT_CAPTURED = "INTENT_CAPTURED"
    PLAN_SIMULATED = "PLAN_SIMULATED"
    POLICY_ALLOW = "POLICY_ALLOW"
    POLICY_DENY = "POLICY_DENY"
    POLICY_MODIFY = "POLICY_MODIFY"
    DRIFT_WARNING = "DRIFT_WARNING"
    AGENT_PAUSED = "AGENT_PAUSED"
    AGENT_KILLED = "AGENT_KILLED"
    AGENT_RESUMED = "AGENT_RESUMED"
    FORENSIC_SNAPSHOT = "FORENSIC_SNAPSHOT"


@dataclass
class SignedAuditEntry:
    """
    A single signed audit entry.

    Entries are hash-chained for tamper evidence.
    """
    entry_id: str
    timestamp: datetime
    event_type: AuditEventType
    agent_id: str
    data: Dict[str, Any]
    previous_hash: str
    entry_hash: str
    signature: str

    def to_dict(self) -> Dict:
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "agent_id": self.agent_id,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "hash": self.entry_hash,
            "signature": self.signature
        }

    def verify(self, signing_key: bytes = SIGNING_KEY) -> bool:
        """Verify the signature of this entry."""
        # Reconstruct hash
        content = self._get_signable_content()
        expected_hash = hashlib.sha256(content.encode()).hexdigest()

        if expected_hash != self.entry_hash:
            return False

        # Verify signature
        expected_sig = hmac.new(signing_key, expected_hash.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected_sig, self.signature)

    def _get_signable_content(self) -> str:
        """Get the content that was signed."""
        return json.dumps({
            "entry_id": self.entry_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "agent_id": self.agent_id,
            "data": self.data,
            "previous_hash": self.previous_hash
        }, sort_keys=True)


class AuditLedger:
    """
    Tamper-evident audit ledger with cryptographic signatures.

    All TIRS decisions and events are logged here for:
    - Enterprise compliance audits
    - Forensic investigation
    - Proof of policy enforcement
    """

    def __init__(self, signing_key: bytes = SIGNING_KEY):
        self.signing_key = signing_key
        self.entries: List[SignedAuditEntry] = []
        self._entry_counter = 0
        self._genesis_hash = self._create_genesis()

        logger.info("AuditLedger initialized")

    def _create_genesis(self) -> str:
        """Create genesis hash for the chain."""
        genesis = {
            "type": "GENESIS",
            "timestamp": datetime.now().isoformat(),
            "version": "TIRS-1.0"
        }
        return hashlib.sha256(json.dumps(genesis).encode()).hexdigest()

    def _get_previous_hash(self) -> str:
        """Get hash of the previous entry (or genesis)."""
        if self.entries:
            return self.entries[-1].entry_hash
        return self._genesis_hash

    def _sign(self, hash_value: str) -> str:
        """Create HMAC signature of a hash."""
        return hmac.new(self.signing_key, hash_value.encode(), hashlib.sha256).hexdigest()

    def log(
        self,
        event_type: AuditEventType,
        agent_id: str,
        data: Dict[str, Any]
    ) -> SignedAuditEntry:
        """
        Log a new audit entry.

        Args:
            event_type: Type of event
            agent_id: Agent that triggered the event
            data: Event-specific data

        Returns:
            The signed audit entry
        """
        self._entry_counter += 1
        entry_id = f"AUDIT-{datetime.now().strftime('%Y%m%d')}-{self._entry_counter:06d}"
        timestamp = datetime.now()
        previous_hash = self._get_previous_hash()

        # Create signable content
        content = json.dumps({
            "entry_id": entry_id,
            "timestamp": timestamp.isoformat(),
            "event_type": event_type.value,
            "agent_id": agent_id,
            "data": data,
            "previous_hash": previous_hash
        }, sort_keys=True)

        # Hash and sign
        entry_hash = hashlib.sha256(content.encode()).hexdigest()
        signature = self._sign(entry_hash)

        entry = SignedAuditEntry(
            entry_id=entry_id,
            timestamp=timestamp,
            event_type=event_type,
            agent_id=agent_id,
            data=data,
            previous_hash=previous_hash,
            entry_hash=entry_hash,
            signature=signature
        )

        self.entries.append(entry)

        logger.debug(f"Logged: {entry_id} [{event_type.value}] agent={agent_id}")

        return entry

    def log_intent(self, agent_id: str, intent_id: str, intent_text: str,
                   verdict: str, policy: Optional[str] = None) -> SignedAuditEntry:
        """Log an intent capture event."""
        return self.log(
            AuditEventType.INTENT_CAPTURED,
            agent_id,
            {
                "intent_id": intent_id,
                "intent_text": intent_text[:200],  # Truncate for storage
                "verdict": verdict,
                "policy_triggered": policy
            }
        )

    def log_simulation(self, agent_id: str, plan_id: str,
                       result: Dict) -> SignedAuditEntry:
        """Log a plan simulation event."""
        return self.log(
            AuditEventType.PLAN_SIMULATED,
            agent_id,
            {
                "plan_id": plan_id,
                "overall_verdict": result.get("overall_verdict"),
                "total_steps": result.get("total_steps"),
                "blocked_count": result.get("blocked_count"),
                "allowed_count": result.get("allowed_count")
            }
        )

    def log_policy_decision(self, agent_id: str, action: str,
                            verdict: str, reason: str, policy: str) -> SignedAuditEntry:
        """Log a policy decision."""
        event_type = {
            "ALLOW": AuditEventType.POLICY_ALLOW,
            "DENY": AuditEventType.POLICY_DENY,
            "MODIFY": AuditEventType.POLICY_MODIFY
        }.get(verdict, AuditEventType.POLICY_ALLOW)

        return self.log(
            event_type,
            agent_id,
            {
                "action": action,
                "verdict": verdict,
                "reason": reason,
                "policy": policy
            }
        )

    def log_drift_warning(self, agent_id: str, risk_score: float,
                          risk_level: str) -> SignedAuditEntry:
        """Log a drift detection warning."""
        return self.log(
            AuditEventType.DRIFT_WARNING,
            agent_id,
            {
                "risk_score": risk_score,
                "risk_level": risk_level
            }
        )

    def log_agent_paused(self, agent_id: str, risk_score: float,
                         reason: str) -> SignedAuditEntry:
        """Log an agent pause event."""
        return self.log(
            AuditEventType.AGENT_PAUSED,
            agent_id,
            {
                "risk_score": risk_score,
                "reason": reason
            }
        )

    def log_agent_killed(self, agent_id: str, risk_score: float,
                         forensic_snapshot: Dict) -> SignedAuditEntry:
        """Log an agent kill event."""
        return self.log(
            AuditEventType.AGENT_KILLED,
            agent_id,
            {
                "risk_score": risk_score,
                "forensic_snapshot": forensic_snapshot
            }
        )

    def log_forensic_snapshot(self, agent_id: str, snapshot: Dict) -> SignedAuditEntry:
        """Log a forensic snapshot."""
        return self.log(
            AuditEventType.FORENSIC_SNAPSHOT,
            agent_id,
            snapshot
        )

    def verify_chain(self) -> tuple:
        """
        Verify the entire audit chain for tampering.

        Returns:
            (is_valid, list of invalid entry IDs)
        """
        invalid = []

        for i, entry in enumerate(self.entries):
            # Verify signature
            if not entry.verify(self.signing_key):
                invalid.append(entry.entry_id)
                continue

            # Verify chain
            expected_prev = self.entries[i-1].entry_hash if i > 0 else self._genesis_hash
            if entry.previous_hash != expected_prev:
                invalid.append(entry.entry_id)

        is_valid = len(invalid) == 0
        logger.info(f"Chain verification: {'VALID' if is_valid else 'INVALID'} ({len(self.entries)} entries)")

        return is_valid, invalid

    def get_entries_for_agent(self, agent_id: str) -> List[SignedAuditEntry]:
        """Get all entries for a specific agent."""
        return [e for e in self.entries if e.agent_id == agent_id]

    def get_entries_by_type(self, event_type: AuditEventType) -> List[SignedAuditEntry]:
        """Get all entries of a specific type."""
        return [e for e in self.entries if e.event_type == event_type]

    def get_entries_in_range(self, start: datetime, end: datetime) -> List[SignedAuditEntry]:
        """Get entries within a time range."""
        return [e for e in self.entries if start <= e.timestamp <= end]

    def get_summary(self) -> Dict:
        """Get audit summary statistics."""
        by_type = {}
        by_agent = {}

        for entry in self.entries:
            # Count by type
            t = entry.event_type.value
            by_type[t] = by_type.get(t, 0) + 1

            # Count by agent
            a = entry.agent_id
            by_agent[a] = by_agent.get(a, 0) + 1

        is_valid, _ = self.verify_chain()

        return {
            "total_entries": len(self.entries),
            "chain_valid": is_valid,
            "by_event_type": by_type,
            "by_agent": by_agent,
            "first_entry": self.entries[0].timestamp.isoformat() if self.entries else None,
            "last_entry": self.entries[-1].timestamp.isoformat() if self.entries else None
        }

    def export_json(self, filepath: str):
        """Export the entire ledger to JSON."""
        data = {
            "metadata": {
                "version": "TIRS-1.0",
                "exported_at": datetime.now().isoformat(),
                "total_entries": len(self.entries),
                "genesis_hash": self._genesis_hash
            },
            "entries": [e.to_dict() for e in self.entries]
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported {len(self.entries)} entries to {filepath}")

    def to_dict(self) -> Dict:
        """Convert ledger to dict."""
        return {
            "genesis_hash": self._genesis_hash,
            "entries": [e.to_dict() for e in self.entries],
            "summary": self.get_summary()
        }


# Singleton instance
_audit_ledger: Optional[AuditLedger] = None


def get_audit_ledger() -> AuditLedger:
    """Get the singleton audit ledger."""
    global _audit_ledger
    if _audit_ledger is None:
        _audit_ledger = AuditLedger()
    return _audit_ledger
