"""
State Persistence & Audit Logging
=================================
Persistent storage for pipelines, audit trails, and system state.
"""

import os
import json
import sqlite3
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List, Type, TypeVar
from datetime import datetime
from enum import Enum
from contextlib import contextmanager
import logging

logger = logging.getLogger("Orchestrator.Persistence")

T = TypeVar('T')


class AuditEventType(Enum):
    """Types of audit events."""
    # Pipeline events
    PIPELINE_CREATED = "pipeline_created"
    PIPELINE_STARTED = "pipeline_started"
    PIPELINE_COMPLETED = "pipeline_completed"
    PIPELINE_FAILED = "pipeline_failed"
    PIPELINE_PAUSED = "pipeline_paused"
    PIPELINE_KILLED = "pipeline_killed"

    # Task events
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_BLOCKED = "task_blocked"
    TASK_ESCALATED = "task_escalated"

    # Agent events
    AGENT_REGISTERED = "agent_registered"
    AGENT_PAUSED = "agent_paused"
    AGENT_KILLED = "agent_killed"
    AGENT_RESUMED = "agent_resumed"

    # Watchtower events
    WATCHTOWER_TOKEN_ISSUED = "watchtower_token_issued"
    WATCHTOWER_TOKEN_VERIFIED = "watchtower_token_verified"
    WATCHTOWER_POLICY_TRIGGERED = "watchtower_policy_triggered"

    # Approval events
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_DENIED = "approval_denied"
    APPROVAL_EXPIRED = "approval_expired"

    # Drift events
    DRIFT_ALERT = "drift_alert"
    DRIFT_THRESHOLD_EXCEEDED = "drift_threshold_exceeded"

    # System events
    SYSTEM_ERROR = "system_error"
    CONFIGURATION_CHANGE = "configuration_change"


@dataclass
class AuditEvent:
    """An audit log entry."""
    event_id: str
    event_type: AuditEventType
    timestamp: datetime
    pipeline_id: Optional[str] = None
    task_id: Optional[str] = None
    agent_id: Optional[str] = None
    user_id: Optional[str] = None
    action: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    risk_score: float = 0.0
    watchtower_token: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "pipeline_id": self.pipeline_id,
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "user_id": self.user_id,
            "action": self.action,
            "details": self.details,
            "risk_score": self.risk_score,
            "watchtower_token": self.watchtower_token
        }


class StateStore:
    """
    SQLite-based state persistence.

    Stores:
    - Pipeline configurations and states
    - Task results
    - Audit logs
    - Drift metrics
    - Approval requests
    """

    def __init__(self, db_path: str = None):
        if db_path is None:
            # Default to project root
            project_root = Path(__file__).parent.parent
            db_dir = project_root / "data"
            db_dir.mkdir(exist_ok=True)
            db_path = str(db_dir / "orchestrator.db")

        self.db_path = db_path
        self._init_db()
        logger.info(f"State store initialized at {db_path}")

    @contextmanager
    def _get_connection(self):
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _init_db(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Pipelines table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pipelines (
                    pipeline_id TEXT PRIMARY KEY,
                    goal TEXT,
                    status TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    completed_at TEXT,
                    config JSON,
                    summary JSON,
                    cumulative_risk REAL DEFAULT 0.0,
                    max_risk REAL DEFAULT 0.0
                )
            """)

            # Tasks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    pipeline_id TEXT,
                    name TEXT,
                    capability TEXT,
                    agent_id TEXT,
                    status TEXT,
                    payload JSON,
                    result JSON,
                    started_at TEXT,
                    completed_at TEXT,
                    risk_score REAL DEFAULT 0.0,
                    watchtower_token TEXT,
                    FOREIGN KEY (pipeline_id) REFERENCES pipelines(pipeline_id)
                )
            """)

            # Audit log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT,
                    timestamp TEXT,
                    pipeline_id TEXT,
                    task_id TEXT,
                    agent_id TEXT,
                    user_id TEXT,
                    action TEXT,
                    details JSON,
                    risk_score REAL DEFAULT 0.0,
                    watchtower_token TEXT
                )
            """)

            # Approvals table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS approvals (
                    request_id TEXT PRIMARY KEY,
                    pipeline_id TEXT,
                    task_id TEXT,
                    agent_id TEXT,
                    action TEXT,
                    payload JSON,
                    reason TEXT,
                    policy_triggered TEXT,
                    approval_type TEXT,
                    status TEXT,
                    created_at TEXT,
                    expires_at TEXT,
                    responded_at TEXT,
                    responder_id TEXT,
                    response_notes TEXT
                )
            """)

            # Drift metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS drift_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pipeline_id TEXT,
                    agent_id TEXT,
                    timestamp TEXT,
                    risk_delta REAL,
                    cumulative_risk REAL,
                    drift_level TEXT,
                    alert_type TEXT,
                    details JSON
                )
            """)

            # Watchtower tokens table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS watchtower_tokens (
                    token_id TEXT PRIMARY KEY,
                    pipeline_id TEXT,
                    task_id TEXT,
                    agent_id TEXT,
                    plan_hash TEXT,
                    action TEXT,
                    issued_at TEXT,
                    verified_at TEXT,
                    status TEXT,
                    details JSON
                )
            """)

            # Create indices
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_pipeline ON tasks(pipeline_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_pipeline ON audit_log(pipeline_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_drift_pipeline ON drift_metrics(pipeline_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals(status)")

    # ═══════════════════════════════════════════════════════════════════════════
    # PIPELINE OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════

    def save_pipeline(self, pipeline_id: str, data: Dict):
        """Save pipeline state."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO pipelines
                (pipeline_id, goal, status, created_at, updated_at, completed_at, config, summary, cumulative_risk, max_risk)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pipeline_id,
                data.get("goal", ""),
                data.get("status", "created"),
                data.get("created_at", datetime.now().isoformat()),
                datetime.now().isoformat(),
                data.get("completed_at"),
                json.dumps(data.get("config", {})),
                json.dumps(data.get("summary", {})),
                data.get("cumulative_risk", 0.0),
                data.get("max_risk", 0.0)
            ))

    def get_pipeline(self, pipeline_id: str) -> Optional[Dict]:
        """Get pipeline by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pipelines WHERE pipeline_id = ?", (pipeline_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "pipeline_id": row["pipeline_id"],
                    "goal": row["goal"],
                    "status": row["status"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "completed_at": row["completed_at"],
                    "config": json.loads(row["config"]) if row["config"] else {},
                    "summary": json.loads(row["summary"]) if row["summary"] else {},
                    "cumulative_risk": row["cumulative_risk"],
                    "max_risk": row["max_risk"]
                }
            return None

    def list_pipelines(self, status: str = None, limit: int = 100) -> List[Dict]:
        """List pipelines, optionally filtered by status."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute(
                    "SELECT * FROM pipelines WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                    (status, limit)
                )
            else:
                cursor.execute(
                    "SELECT * FROM pipelines ORDER BY created_at DESC LIMIT ?",
                    (limit,)
                )
            return [dict(row) for row in cursor.fetchall()]

    def update_pipeline_status(self, pipeline_id: str, status: str, summary: Dict = None):
        """Update pipeline status."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if summary:
                cursor.execute("""
                    UPDATE pipelines
                    SET status = ?, updated_at = ?, summary = ?,
                        cumulative_risk = ?, max_risk = ?
                    WHERE pipeline_id = ?
                """, (
                    status,
                    datetime.now().isoformat(),
                    json.dumps(summary),
                    summary.get("cumulative_risk", 0.0),
                    summary.get("max_risk", 0.0),
                    pipeline_id
                ))
            else:
                cursor.execute("""
                    UPDATE pipelines SET status = ?, updated_at = ? WHERE pipeline_id = ?
                """, (status, datetime.now().isoformat(), pipeline_id))

    # ═══════════════════════════════════════════════════════════════════════════
    # TASK OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════

    def save_task(self, task_id: str, pipeline_id: str, data: Dict):
        """Save task state."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO tasks
                (task_id, pipeline_id, name, capability, agent_id, status, payload, result,
                 started_at, completed_at, risk_score, watchtower_token)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_id,
                pipeline_id,
                data.get("name", ""),
                data.get("capability", ""),
                data.get("agent_id"),
                data.get("status", "pending"),
                json.dumps(data.get("payload", {})),
                json.dumps(data.get("result", {})) if data.get("result") else None,
                data.get("started_at"),
                data.get("completed_at"),
                data.get("risk_score", 0.0),
                data.get("watchtower_token")
            ))

    def get_tasks_for_pipeline(self, pipeline_id: str) -> List[Dict]:
        """Get all tasks for a pipeline."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM tasks WHERE pipeline_id = ? ORDER BY started_at",
                (pipeline_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    # ═══════════════════════════════════════════════════════════════════════════
    # AUDIT LOG OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════

    def log_event(self, event: AuditEvent):
        """Log an audit event."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO audit_log
                (event_id, event_type, timestamp, pipeline_id, task_id, agent_id,
                 user_id, action, details, risk_score, watchtower_token)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.event_id,
                event.event_type.value,
                event.timestamp.isoformat(),
                event.pipeline_id,
                event.task_id,
                event.agent_id,
                event.user_id,
                event.action,
                json.dumps(event.details),
                event.risk_score,
                event.watchtower_token
            ))

    def get_audit_log(
        self,
        pipeline_id: str = None,
        agent_id: str = None,
        event_type: AuditEventType = None,
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 1000
    ) -> List[Dict]:
        """Query audit log with filters."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM audit_log WHERE 1=1"
            params = []

            if pipeline_id:
                query += " AND pipeline_id = ?"
                params.append(pipeline_id)

            if agent_id:
                query += " AND agent_id = ?"
                params.append(agent_id)

            if event_type:
                query += " AND event_type = ?"
                params.append(event_type.value)

            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time.isoformat())

            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time.isoformat())

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    # ═══════════════════════════════════════════════════════════════════════════
    # APPROVAL OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════

    def save_approval(self, request_id: str, data: Dict):
        """Save approval request."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO approvals
                (request_id, pipeline_id, task_id, agent_id, action, payload, reason,
                 policy_triggered, approval_type, status, created_at, expires_at,
                 responded_at, responder_id, response_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request_id,
                data.get("pipeline_id"),
                data.get("task_id"),
                data.get("agent_id"),
                data.get("action"),
                json.dumps(data.get("payload", {})),
                data.get("reason"),
                data.get("policy_triggered"),
                data.get("approval_type"),
                data.get("status", "pending"),
                data.get("created_at"),
                data.get("expires_at"),
                data.get("responded_at"),
                data.get("responder_id"),
                data.get("response_notes")
            ))

    def get_pending_approvals(self, approval_type: str = None) -> List[Dict]:
        """Get pending approval requests."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if approval_type:
                cursor.execute(
                    "SELECT * FROM approvals WHERE status = 'pending' AND approval_type = ?",
                    (approval_type,)
                )
            else:
                cursor.execute("SELECT * FROM approvals WHERE status = 'pending'")
            return [dict(row) for row in cursor.fetchall()]

    # ═══════════════════════════════════════════════════════════════════════════
    # DRIFT METRICS OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════

    def record_drift_metric(self, data: Dict):
        """Record a drift metric."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO drift_metrics
                (pipeline_id, agent_id, timestamp, risk_delta, cumulative_risk,
                 drift_level, alert_type, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get("pipeline_id"),
                data.get("agent_id"),
                datetime.now().isoformat(),
                data.get("risk_delta", 0.0),
                data.get("cumulative_risk", 0.0),
                data.get("drift_level"),
                data.get("alert_type"),
                json.dumps(data.get("details", {}))
            ))

    def get_drift_history(self, pipeline_id: str = None, limit: int = 100) -> List[Dict]:
        """Get drift history."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if pipeline_id:
                cursor.execute(
                    "SELECT * FROM drift_metrics WHERE pipeline_id = ? ORDER BY timestamp DESC LIMIT ?",
                    (pipeline_id, limit)
                )
            else:
                cursor.execute(
                    "SELECT * FROM drift_metrics ORDER BY timestamp DESC LIMIT ?",
                    (limit,)
                )
            return [dict(row) for row in cursor.fetchall()]

    # ═══════════════════════════════════════════════════════════════════════════
    # WATCHTOWER TOKEN OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════

    def save_watchtower_token(self, token_id: str, data: Dict):
        """Save Watchtower token."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO watchtower_tokens
                (token_id, pipeline_id, task_id, agent_id, plan_hash, action,
                 issued_at, verified_at, status, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                token_id,
                data.get("pipeline_id"),
                data.get("task_id"),
                data.get("agent_id"),
                data.get("plan_hash"),
                data.get("action"),
                data.get("issued_at", datetime.now().isoformat()),
                data.get("verified_at"),
                data.get("status", "issued"),
                json.dumps(data.get("details", {}))
            ))

    def get_pipeline_tokens(self, pipeline_id: str) -> List[Dict]:
        """Get all tokens for a pipeline."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM watchtower_tokens WHERE pipeline_id = ? ORDER BY issued_at",
                (pipeline_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    # ═══════════════════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_stats(self) -> Dict:
        """Get overall statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            stats = {}

            # Pipeline counts
            cursor.execute("SELECT status, COUNT(*) as count FROM pipelines GROUP BY status")
            stats["pipelines_by_status"] = {row["status"]: row["count"] for row in cursor.fetchall()}

            # Task counts
            cursor.execute("SELECT status, COUNT(*) as count FROM tasks GROUP BY status")
            stats["tasks_by_status"] = {row["status"]: row["count"] for row in cursor.fetchall()}

            # Recent audit events
            cursor.execute("""
                SELECT event_type, COUNT(*) as count
                FROM audit_log
                WHERE timestamp > datetime('now', '-24 hours')
                GROUP BY event_type
            """)
            stats["events_last_24h"] = {row["event_type"]: row["count"] for row in cursor.fetchall()}

            # Approval stats
            cursor.execute("SELECT status, COUNT(*) as count FROM approvals GROUP BY status")
            stats["approvals_by_status"] = {row["status"]: row["count"] for row in cursor.fetchall()}

            # Risk metrics
            cursor.execute("""
                SELECT AVG(cumulative_risk) as avg_risk, MAX(max_risk) as max_risk
                FROM pipelines
            """)
            row = cursor.fetchone()
            stats["risk"] = {
                "avg_cumulative": row["avg_risk"] or 0,
                "max_observed": row["max_risk"] or 0
            }

            return stats


class AuditLogger:
    """
    High-level audit logging interface.

    Provides convenient methods for logging common events.
    """

    def __init__(self, store: StateStore):
        self.store = store
        self.event_counter = 0

    def _next_event_id(self) -> str:
        """Generate next event ID."""
        self.event_counter += 1
        return f"evt_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self.event_counter:04d}"

    def log(
        self,
        event_type: AuditEventType,
        pipeline_id: str = None,
        task_id: str = None,
        agent_id: str = None,
        user_id: str = None,
        action: str = None,
        details: Dict = None,
        risk_score: float = 0.0,
        watchtower_token: str = None
    ):
        """Log an audit event."""
        event = AuditEvent(
            event_id=self._next_event_id(),
            event_type=event_type,
            timestamp=datetime.now(),
            pipeline_id=pipeline_id,
            task_id=task_id,
            agent_id=agent_id,
            user_id=user_id,
            action=action,
            details=details or {},
            risk_score=risk_score,
            watchtower_token=watchtower_token
        )
        self.store.log_event(event)
        return event

    def log_pipeline_created(self, pipeline_id: str, goal: str, config: Dict = None):
        """Log pipeline creation."""
        return self.log(
            AuditEventType.PIPELINE_CREATED,
            pipeline_id=pipeline_id,
            details={"goal": goal, "config": config or {}}
        )

    def log_pipeline_completed(self, pipeline_id: str, summary: Dict):
        """Log pipeline completion."""
        return self.log(
            AuditEventType.PIPELINE_COMPLETED,
            pipeline_id=pipeline_id,
            details=summary,
            risk_score=summary.get("max_risk", 0.0)
        )

    def log_task_started(self, pipeline_id: str, task_id: str, agent_id: str, action: str):
        """Log task start."""
        return self.log(
            AuditEventType.TASK_STARTED,
            pipeline_id=pipeline_id,
            task_id=task_id,
            agent_id=agent_id,
            action=action
        )

    def log_task_completed(self, pipeline_id: str, task_id: str, agent_id: str, result: Dict):
        """Log task completion."""
        return self.log(
            AuditEventType.TASK_COMPLETED,
            pipeline_id=pipeline_id,
            task_id=task_id,
            agent_id=agent_id,
            details=result,
            risk_score=result.get("risk_score", 0.0),
            watchtower_token=result.get("watchtower_token")
        )

    def log_task_blocked(self, pipeline_id: str, task_id: str, agent_id: str, reason: str, policy: str):
        """Log blocked task."""
        return self.log(
            AuditEventType.TASK_BLOCKED,
            pipeline_id=pipeline_id,
            task_id=task_id,
            agent_id=agent_id,
            details={"reason": reason, "policy": policy}
        )

    def log_watchtower_token(self, pipeline_id: str, task_id: str, agent_id: str, token_id: str, plan_hash: str):
        """Log Watchtower token issuance."""
        return self.log(
            AuditEventType.WATCHTOWER_TOKEN_ISSUED,
            pipeline_id=pipeline_id,
            task_id=task_id,
            agent_id=agent_id,
            watchtower_token=token_id,
            details={"plan_hash": plan_hash}
        )

    def log_drift_alert(self, pipeline_id: str, agent_id: str, alert_type: str, severity: str, message: str):
        """Log drift alert."""
        return self.log(
            AuditEventType.DRIFT_ALERT,
            pipeline_id=pipeline_id,
            agent_id=agent_id,
            details={"alert_type": alert_type, "severity": severity, "message": message}
        )


# Singleton
_state_store = None
_audit_logger = None

def get_state_store() -> StateStore:
    global _state_store
    if _state_store is None:
        _state_store = StateStore()
    return _state_store

def get_audit_logger() -> AuditLogger:
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger(get_state_store())
    return _audit_logger
