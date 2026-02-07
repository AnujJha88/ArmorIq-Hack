"""
Forensic Snapshot
=================
Captures agent state for post-incident analysis.
"""

import json
import hashlib
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
import gzip

logger = logging.getLogger("TIRS.Forensics")


@dataclass
class ForensicSnapshot:
    """
    Complete forensic snapshot of agent state.

    Captures everything needed for post-incident analysis:
    - Current risk state
    - Recent intent history
    - Capability usage patterns
    - Policy violations
    - Environmental context
    """
    snapshot_id: str
    agent_id: str
    trigger: str  # What triggered the snapshot (kill, quarantine, manual)
    timestamp: datetime = field(default_factory=datetime.now)

    # Risk state
    risk_score: float = 0.0
    risk_level: str = "unknown"
    risk_history: List[float] = field(default_factory=list)

    # Intent history
    recent_intents: List[Dict] = field(default_factory=list)
    total_intents: int = 0
    violation_count: int = 0

    # Capability analysis
    capability_distribution: Dict[str, float] = field(default_factory=dict)
    unusual_capabilities: List[str] = field(default_factory=list)

    # Policy context
    policies_triggered: List[str] = field(default_factory=list)
    approval_requests: List[Dict] = field(default_factory=list)

    # Environmental context
    environment: Dict[str, Any] = field(default_factory=dict)

    # Cryptographic integrity
    content_hash: str = ""
    previous_snapshot_hash: Optional[str] = None

    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute hash of snapshot content."""
        content = {
            "snapshot_id": self.snapshot_id,
            "agent_id": self.agent_id,
            "trigger": self.trigger,
            "timestamp": self.timestamp.isoformat(),
            "risk_score": self.risk_score,
            "total_intents": self.total_intents,
            "violation_count": self.violation_count,
            "previous_hash": self.previous_snapshot_hash,
        }
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()

    def verify_integrity(self) -> bool:
        """Verify snapshot hasn't been tampered with."""
        return self.content_hash == self._compute_hash()

    def to_dict(self) -> Dict:
        return {
            "snapshot_id": self.snapshot_id,
            "agent_id": self.agent_id,
            "trigger": self.trigger,
            "timestamp": self.timestamp.isoformat(),
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "risk_history": self.risk_history,
            "recent_intents": self.recent_intents,
            "total_intents": self.total_intents,
            "violation_count": self.violation_count,
            "capability_distribution": self.capability_distribution,
            "unusual_capabilities": self.unusual_capabilities,
            "policies_triggered": self.policies_triggered,
            "environment": self.environment,
            "content_hash": self.content_hash,
            "previous_snapshot_hash": self.previous_snapshot_hash,
            "integrity_valid": self.verify_integrity(),
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)


class SnapshotManager:
    """
    Manages forensic snapshots.

    Features:
    - Automatic snapshot on kill/quarantine
    - Manual snapshot capability
    - Chain integrity verification
    - Compressed storage
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or Path("/tmp/armoriq_forensics")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self._snapshots: Dict[str, ForensicSnapshot] = {}
        self._agent_chains: Dict[str, List[str]] = {}  # agent_id -> list of snapshot_ids
        self._snapshot_counter = 0

    def create_snapshot(
        self,
        agent_id: str,
        trigger: str,
        profile_data: Dict,
        environment: Optional[Dict] = None,
    ) -> ForensicSnapshot:
        """
        Create a forensic snapshot of agent state.

        Args:
            agent_id: Agent being snapshotted
            trigger: What triggered the snapshot
            profile_data: Agent profile data
            environment: Environmental context

        Returns:
            Created snapshot
        """
        self._snapshot_counter += 1
        snapshot_id = f"SNAP-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self._snapshot_counter:04d}"

        # Get previous snapshot hash for chain
        previous_hash = None
        if agent_id in self._agent_chains and self._agent_chains[agent_id]:
            prev_id = self._agent_chains[agent_id][-1]
            prev_snap = self._snapshots.get(prev_id)
            if prev_snap:
                previous_hash = prev_snap.content_hash

        # Extract risk history
        risk_history = profile_data.get("risk_history", [])
        if isinstance(risk_history, list) and risk_history:
            if isinstance(risk_history[0], tuple):
                risk_history = [score for _, score in risk_history[-20:]]
            elif isinstance(risk_history[0], list):
                risk_history = [item[1] if len(item) > 1 else item[0] for item in risk_history[-20:]]

        snapshot = ForensicSnapshot(
            snapshot_id=snapshot_id,
            agent_id=agent_id,
            trigger=trigger,
            risk_score=profile_data.get("current_risk_score", 0.0),
            risk_level=profile_data.get("risk_level", "unknown"),
            risk_history=risk_history,
            recent_intents=profile_data.get("recent_intents", []),
            total_intents=profile_data.get("total_intents", 0),
            violation_count=profile_data.get("violation_count", 0),
            capability_distribution=profile_data.get("capability_distribution", {}),
            unusual_capabilities=profile_data.get("unusual_capabilities", []),
            policies_triggered=profile_data.get("policies_triggered", []),
            environment=environment or {},
            previous_snapshot_hash=previous_hash,
        )

        # Store in memory
        self._snapshots[snapshot_id] = snapshot

        # Add to agent chain
        if agent_id not in self._agent_chains:
            self._agent_chains[agent_id] = []
        self._agent_chains[agent_id].append(snapshot_id)

        # Persist to disk
        self._persist_snapshot(snapshot)

        logger.critical(f"Forensic snapshot {snapshot_id} created for {agent_id} ({trigger})")
        return snapshot

    def _persist_snapshot(self, snapshot: ForensicSnapshot):
        """Persist snapshot to disk."""
        filepath = self.storage_dir / f"{snapshot.snapshot_id}.json.gz"

        try:
            content = snapshot.to_json().encode("utf-8")
            with gzip.open(filepath, "wb") as f:
                f.write(content)
        except Exception as e:
            logger.error(f"Failed to persist snapshot: {e}")

    def load_snapshot(self, snapshot_id: str) -> Optional[ForensicSnapshot]:
        """Load a snapshot from disk."""
        if snapshot_id in self._snapshots:
            return self._snapshots[snapshot_id]

        filepath = self.storage_dir / f"{snapshot_id}.json.gz"
        if not filepath.exists():
            return None

        try:
            with gzip.open(filepath, "rb") as f:
                data = json.loads(f.read().decode("utf-8"))

            snapshot = ForensicSnapshot(
                snapshot_id=data["snapshot_id"],
                agent_id=data["agent_id"],
                trigger=data["trigger"],
                timestamp=datetime.fromisoformat(data["timestamp"]),
                risk_score=data.get("risk_score", 0.0),
                risk_level=data.get("risk_level", "unknown"),
                risk_history=data.get("risk_history", []),
                recent_intents=data.get("recent_intents", []),
                total_intents=data.get("total_intents", 0),
                violation_count=data.get("violation_count", 0),
                capability_distribution=data.get("capability_distribution", {}),
                unusual_capabilities=data.get("unusual_capabilities", []),
                policies_triggered=data.get("policies_triggered", []),
                environment=data.get("environment", {}),
                previous_snapshot_hash=data.get("previous_snapshot_hash"),
                content_hash=data.get("content_hash", ""),
            )

            self._snapshots[snapshot_id] = snapshot
            return snapshot

        except Exception as e:
            logger.error(f"Failed to load snapshot {snapshot_id}: {e}")
            return None

    def get_agent_snapshots(self, agent_id: str) -> List[ForensicSnapshot]:
        """Get all snapshots for an agent."""
        snapshot_ids = self._agent_chains.get(agent_id, [])
        snapshots = []

        for sid in snapshot_ids:
            snap = self.load_snapshot(sid)
            if snap:
                snapshots.append(snap)

        return snapshots

    def verify_chain(self, agent_id: str) -> Tuple[bool, List[str]]:
        """
        Verify the integrity of an agent's snapshot chain.

        Returns:
            (is_valid, list of issues)
        """
        snapshots = self.get_agent_snapshots(agent_id)
        if not snapshots:
            return True, []

        issues = []

        for i, snapshot in enumerate(snapshots):
            # Verify individual snapshot
            if not snapshot.verify_integrity():
                issues.append(f"Snapshot {snapshot.snapshot_id} failed integrity check")

            # Verify chain linkage
            if i > 0:
                expected_hash = snapshots[i - 1].content_hash
                if snapshot.previous_snapshot_hash != expected_hash:
                    issues.append(
                        f"Chain broken at {snapshot.snapshot_id}: "
                        f"expected prev={expected_hash[:16]}..., got {snapshot.previous_snapshot_hash[:16] if snapshot.previous_snapshot_hash else 'None'}..."
                    )

        return len(issues) == 0, issues

    def get_latest_snapshot(self, agent_id: str) -> Optional[ForensicSnapshot]:
        """Get the most recent snapshot for an agent."""
        chain = self._agent_chains.get(agent_id, [])
        if not chain:
            return None

        return self.load_snapshot(chain[-1])

    def export_chain(self, agent_id: str, output_path: Path) -> bool:
        """Export complete snapshot chain for an agent."""
        snapshots = self.get_agent_snapshots(agent_id)
        if not snapshots:
            return False

        try:
            export_data = {
                "agent_id": agent_id,
                "exported_at": datetime.now().isoformat(),
                "snapshot_count": len(snapshots),
                "chain_valid": self.verify_chain(agent_id)[0],
                "snapshots": [s.to_dict() for s in snapshots],
            }

            with gzip.open(output_path, "wt") as f:
                json.dump(export_data, f, indent=2)

            return True

        except Exception as e:
            logger.error(f"Failed to export chain: {e}")
            return False


# Import for type hints
from typing import Tuple

# Singleton
_manager: Optional[SnapshotManager] = None


def get_snapshot_manager() -> SnapshotManager:
    """Get singleton snapshot manager."""
    global _manager
    if _manager is None:
        _manager = SnapshotManager()
    return _manager
