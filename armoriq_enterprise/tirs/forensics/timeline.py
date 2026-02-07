"""
Event Timeline
==============
Reconstructs temporal sequence of events.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict

logger = logging.getLogger("TIRS.Timeline")


class EventCategory(Enum):
    """Categories of timeline events."""
    INTENT = "intent"
    POLICY = "policy"
    DRIFT = "drift"
    ENFORCEMENT = "enforcement"
    APPROVAL = "approval"
    SYSTEM = "system"


class EventSeverity(Enum):
    """Severity levels for events."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class TimelineEvent:
    """Single event in the timeline."""
    event_id: str
    timestamp: datetime
    category: EventCategory
    severity: EventSeverity
    agent_id: str
    action: str
    description: str

    # Optional details
    details: Dict[str, Any] = field(default_factory=dict)
    related_events: List[str] = field(default_factory=list)

    # Causation tracking
    caused_by: Optional[str] = None
    causes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "category": self.category.value,
            "severity": self.severity.value,
            "agent_id": self.agent_id,
            "action": self.action,
            "description": self.description,
            "details": self.details,
            "related_events": self.related_events,
            "caused_by": self.caused_by,
            "causes": self.causes,
        }


class EventTimeline:
    """
    Reconstructs and analyzes event timelines.

    Features:
    - Event recording with causation
    - Timeline reconstruction
    - Pattern detection
    - Root cause analysis
    """

    def __init__(self, max_events: int = 10000):
        self.max_events = max_events
        self._events: List[TimelineEvent] = []
        self._event_index: Dict[str, TimelineEvent] = {}
        self._agent_events: Dict[str, List[str]] = defaultdict(list)
        self._event_counter = 0

    def record_event(
        self,
        category: EventCategory,
        severity: EventSeverity,
        agent_id: str,
        action: str,
        description: str,
        details: Optional[Dict] = None,
        caused_by: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> TimelineEvent:
        """Record a new event."""
        self._event_counter += 1
        event_id = f"EVT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self._event_counter:06d}"

        event = TimelineEvent(
            event_id=event_id,
            timestamp=timestamp or datetime.now(),
            category=category,
            severity=severity,
            agent_id=agent_id,
            action=action,
            description=description,
            details=details or {},
            caused_by=caused_by,
        )

        # Link causation
        if caused_by and caused_by in self._event_index:
            self._event_index[caused_by].causes.append(event_id)

        # Store
        self._events.append(event)
        self._event_index[event_id] = event
        self._agent_events[agent_id].append(event_id)

        # Trim if needed
        if len(self._events) > self.max_events:
            old_event = self._events.pop(0)
            del self._event_index[old_event.event_id]

        return event

    def get_timeline(
        self,
        agent_id: Optional[str] = None,
        category: Optional[EventCategory] = None,
        severity: Optional[EventSeverity] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[TimelineEvent]:
        """
        Get filtered timeline of events.

        Args:
            agent_id: Filter by agent
            category: Filter by category
            severity: Filter by minimum severity
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum events to return

        Returns:
            List of matching events, sorted by timestamp
        """
        events = self._events

        if agent_id:
            event_ids = self._agent_events.get(agent_id, [])
            events = [self._event_index[eid] for eid in event_ids if eid in self._event_index]

        if category:
            events = [e for e in events if e.category == category]

        if severity:
            severity_order = [EventSeverity.INFO, EventSeverity.WARNING, EventSeverity.ERROR, EventSeverity.CRITICAL]
            min_index = severity_order.index(severity)
            events = [e for e in events if severity_order.index(e.severity) >= min_index]

        if start_time:
            events = [e for e in events if e.timestamp >= start_time]

        if end_time:
            events = [e for e in events if e.timestamp <= end_time]

        # Sort by timestamp and limit
        events = sorted(events, key=lambda e: e.timestamp, reverse=True)
        return events[:limit]

    def get_causal_chain(self, event_id: str) -> List[TimelineEvent]:
        """
        Get the causal chain leading to an event.

        Traces back through caused_by relationships.
        """
        chain = []
        current_id = event_id

        while current_id and current_id in self._event_index:
            event = self._event_index[current_id]
            chain.append(event)
            current_id = event.caused_by

        return list(reversed(chain))

    def get_consequence_tree(self, event_id: str) -> Dict:
        """
        Get the tree of consequences from an event.

        Follows causes relationships forward.
        """
        if event_id not in self._event_index:
            return {}

        event = self._event_index[event_id]

        return {
            "event": event.to_dict(),
            "consequences": [
                self.get_consequence_tree(cause_id)
                for cause_id in event.causes
            ],
        }

    def find_root_cause(self, event_id: str) -> Optional[TimelineEvent]:
        """Find the root cause of an event."""
        chain = self.get_causal_chain(event_id)
        return chain[0] if chain else None

    def detect_patterns(self, agent_id: str, window_minutes: int = 60) -> List[Dict]:
        """
        Detect patterns in agent behavior.

        Returns:
            List of detected patterns
        """
        patterns = []
        cutoff = datetime.now() - timedelta(minutes=window_minutes)

        events = [
            e for e in self._events
            if e.agent_id == agent_id and e.timestamp >= cutoff
        ]

        if not events:
            return patterns

        # Count by category
        category_counts = defaultdict(int)
        for e in events:
            category_counts[e.category.value] += 1

        # Detect high violation rate
        policy_events = category_counts.get("policy", 0)
        if policy_events > 5:
            patterns.append({
                "pattern": "high_violation_rate",
                "description": f"High policy violation rate: {policy_events} in {window_minutes} minutes",
                "severity": "warning" if policy_events < 10 else "critical",
                "count": policy_events,
            })

        # Detect enforcement escalation
        enforcement_events = [e for e in events if e.category == EventCategory.ENFORCEMENT]
        if len(enforcement_events) > 2:
            patterns.append({
                "pattern": "enforcement_escalation",
                "description": f"Multiple enforcement actions: {len(enforcement_events)} in {window_minutes} minutes",
                "severity": "warning",
                "count": len(enforcement_events),
            })

        # Detect rapid-fire actions
        if len(events) > 20:
            patterns.append({
                "pattern": "rapid_fire_activity",
                "description": f"High activity rate: {len(events)} events in {window_minutes} minutes",
                "severity": "warning",
                "count": len(events),
            })

        return patterns

    def generate_summary(self, agent_id: str, hours: int = 24) -> Dict:
        """Generate a summary of agent activity."""
        cutoff = datetime.now() - timedelta(hours=hours)

        events = [
            e for e in self._events
            if e.agent_id == agent_id and e.timestamp >= cutoff
        ]

        by_category = defaultdict(int)
        by_severity = defaultdict(int)
        by_hour = defaultdict(int)

        for e in events:
            by_category[e.category.value] += 1
            by_severity[e.severity.value] += 1
            by_hour[e.timestamp.hour] += 1

        return {
            "agent_id": agent_id,
            "period_hours": hours,
            "total_events": len(events),
            "by_category": dict(by_category),
            "by_severity": dict(by_severity),
            "peak_hour": max(by_hour.items(), key=lambda x: x[1])[0] if by_hour else None,
            "patterns": self.detect_patterns(agent_id),
        }


# Singleton
_timeline: Optional[EventTimeline] = None


def get_timeline() -> EventTimeline:
    """Get singleton timeline."""
    global _timeline
    if _timeline is None:
        _timeline = EventTimeline()
    return _timeline
