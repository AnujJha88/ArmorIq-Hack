"""
Agent Tools
============
Tool integrations that agents can use.
Each tool call goes through Watchtower verification.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from enum import Enum
import json
import uuid
import logging

logger = logging.getLogger("Orchestrator.Tools")


class ToolCategory(Enum):
    """Categories of tools."""
    COMMUNICATION = "communication"
    DATA_ACCESS = "data_access"
    CALENDAR = "calendar"
    DOCUMENT = "document"
    FINANCE = "finance"
    COMPLIANCE = "compliance"
    EXTERNAL_API = "external_api"


class RiskLevel(Enum):
    """Risk level of tool operations."""
    LOW = "low"          # Read-only, internal
    MEDIUM = "medium"    # Write, internal
    HIGH = "high"        # External communication
    CRITICAL = "critical" # Financial, PII, compliance


@dataclass
class ToolCall:
    """A tool invocation request."""
    tool_id: str
    tool_name: str
    parameters: Dict[str, Any]
    agent_id: str
    pipeline_id: str
    risk_level: RiskLevel = RiskLevel.MEDIUM
    requires_approval: bool = False
    call_id: str = field(default_factory=lambda: f"call_{uuid.uuid4().hex[:12]}")
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ToolResult:
    """Result of a tool invocation."""
    call_id: str
    success: bool
    output: Any = None
    error: Optional[str] = None
    modified_by_policy: bool = False
    original_params: Optional[Dict] = None
    execution_time_ms: float = 0.0


class BaseTool(ABC):
    """Base class for all tools."""

    def __init__(self, tool_id: str, name: str, category: ToolCategory, risk_level: RiskLevel):
        self.tool_id = tool_id
        self.name = name
        self.category = category
        self.risk_level = risk_level
        self.calls_made = 0
        self.calls_blocked = 0

    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """Execute the tool with given parameters."""
        pass

    @abstractmethod
    def get_schema(self) -> Dict:
        """Return JSON schema for tool parameters."""
        pass

    def to_dict(self) -> Dict:
        return {
            "tool_id": self.tool_id,
            "name": self.name,
            "category": self.category.value,
            "risk_level": self.risk_level.value,
            "schema": self.get_schema()
        }


# ═══════════════════════════════════════════════════════════════════════════════
# COMMUNICATION TOOLS
# ═══════════════════════════════════════════════════════════════════════════════

class EmailTool(BaseTool):
    """Send emails to internal or external recipients."""

    def __init__(self):
        super().__init__(
            tool_id="email",
            name="Send Email",
            category=ToolCategory.COMMUNICATION,
            risk_level=RiskLevel.HIGH
        )
        self.sent_emails = []

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        start = datetime.now()

        to = params.get("to", "")
        subject = params.get("subject", "")
        body = params.get("body", "")
        cc = params.get("cc", [])

        if not to or not subject:
            return ToolResult(
                call_id=params.get("_call_id", ""),
                success=False,
                error="Missing required fields: to, subject"
            )

        # Simulate sending
        email = {
            "id": f"email_{uuid.uuid4().hex[:8]}",
            "to": to,
            "subject": subject,
            "body": body,
            "cc": cc,
            "sent_at": datetime.now().isoformat()
        }
        self.sent_emails.append(email)

        exec_time = (datetime.now() - start).total_seconds() * 1000

        return ToolResult(
            call_id=params.get("_call_id", ""),
            success=True,
            output={"email_id": email["id"], "status": "sent"},
            execution_time_ms=exec_time
        )

    def get_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient email"},
                "subject": {"type": "string", "description": "Email subject"},
                "body": {"type": "string", "description": "Email body"},
                "cc": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["to", "subject", "body"]
        }


class SlackTool(BaseTool):
    """Send Slack messages."""

    def __init__(self):
        super().__init__(
            tool_id="slack",
            name="Send Slack Message",
            category=ToolCategory.COMMUNICATION,
            risk_level=RiskLevel.MEDIUM
        )
        self.sent_messages = []

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        start = datetime.now()

        channel = params.get("channel", "")
        message = params.get("message", "")
        thread_ts = params.get("thread_ts")

        if not channel or not message:
            return ToolResult(
                call_id=params.get("_call_id", ""),
                success=False,
                error="Missing required fields: channel, message"
            )

        msg = {
            "ts": f"{datetime.now().timestamp()}",
            "channel": channel,
            "text": message,
            "thread_ts": thread_ts
        }
        self.sent_messages.append(msg)

        exec_time = (datetime.now() - start).total_seconds() * 1000

        return ToolResult(
            call_id=params.get("_call_id", ""),
            success=True,
            output={"ts": msg["ts"], "channel": channel},
            execution_time_ms=exec_time
        )

    def get_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "channel": {"type": "string"},
                "message": {"type": "string"},
                "thread_ts": {"type": "string"}
            },
            "required": ["channel", "message"]
        }


# ═══════════════════════════════════════════════════════════════════════════════
# CALENDAR TOOLS
# ═══════════════════════════════════════════════════════════════════════════════

class CalendarTool(BaseTool):
    """Manage calendar events."""

    def __init__(self):
        super().__init__(
            tool_id="calendar",
            name="Calendar Management",
            category=ToolCategory.CALENDAR,
            risk_level=RiskLevel.MEDIUM
        )
        self.events = []

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        start = datetime.now()

        action = params.get("action", "create")

        if action == "create":
            event = {
                "id": f"evt_{uuid.uuid4().hex[:8]}",
                "title": params.get("title", "Meeting"),
                "start": params.get("start_time"),
                "end": params.get("end_time"),
                "attendees": params.get("attendees", []),
                "location": params.get("location", "Virtual"),
                "created_at": datetime.now().isoformat()
            }
            self.events.append(event)

            exec_time = (datetime.now() - start).total_seconds() * 1000
            return ToolResult(
                call_id=params.get("_call_id", ""),
                success=True,
                output={"event_id": event["id"], "status": "created"},
                execution_time_ms=exec_time
            )

        elif action == "check_availability":
            attendees = params.get("attendees", [])
            time_range = params.get("time_range", {})

            # Simulate availability check
            available_slots = [
                {"start": "2026-02-10 10:00", "end": "2026-02-10 11:00"},
                {"start": "2026-02-10 14:00", "end": "2026-02-10 15:00"},
                {"start": "2026-02-11 09:00", "end": "2026-02-11 10:00"},
            ]

            exec_time = (datetime.now() - start).total_seconds() * 1000
            return ToolResult(
                call_id=params.get("_call_id", ""),
                success=True,
                output={"available_slots": available_slots},
                execution_time_ms=exec_time
            )

        return ToolResult(
            call_id=params.get("_call_id", ""),
            success=False,
            error=f"Unknown action: {action}"
        )

    def get_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["create", "check_availability", "cancel"]},
                "title": {"type": "string"},
                "start_time": {"type": "string"},
                "end_time": {"type": "string"},
                "attendees": {"type": "array", "items": {"type": "string"}},
                "location": {"type": "string"}
            },
            "required": ["action"]
        }


# ═══════════════════════════════════════════════════════════════════════════════
# DATA ACCESS TOOLS
# ═══════════════════════════════════════════════════════════════════════════════

class HRDatabaseTool(BaseTool):
    """Access HR database for employee information."""

    def __init__(self):
        super().__init__(
            tool_id="hr_database",
            name="HR Database Access",
            category=ToolCategory.DATA_ACCESS,
            risk_level=RiskLevel.HIGH
        )

        # Simulated database
        self.employees = {
            "emp_001": {"name": "John Smith", "department": "Engineering", "salary": 150000, "level": "L4"},
            "emp_002": {"name": "Jane Doe", "department": "HR", "salary": 120000, "level": "L3"},
            "emp_003": {"name": "Bob Wilson", "department": "Engineering", "salary": 180000, "level": "L5"},
        }

        self.salary_bands = {
            "L3": {"min": 100000, "max": 140000, "midpoint": 120000},
            "L4": {"min": 130000, "max": 180000, "midpoint": 155000},
            "L5": {"min": 170000, "max": 240000, "midpoint": 205000},
            "L6": {"min": 220000, "max": 320000, "midpoint": 270000},
        }

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        start = datetime.now()
        query = params.get("query", "")

        if query == "get_employee":
            emp_id = params.get("employee_id")
            if emp_id in self.employees:
                exec_time = (datetime.now() - start).total_seconds() * 1000
                return ToolResult(
                    call_id=params.get("_call_id", ""),
                    success=True,
                    output=self.employees[emp_id],
                    execution_time_ms=exec_time
                )
            return ToolResult(
                call_id=params.get("_call_id", ""),
                success=False,
                error=f"Employee not found: {emp_id}"
            )

        elif query == "get_salary_band":
            level = params.get("level")
            if level in self.salary_bands:
                exec_time = (datetime.now() - start).total_seconds() * 1000
                return ToolResult(
                    call_id=params.get("_call_id", ""),
                    success=True,
                    output=self.salary_bands[level],
                    execution_time_ms=exec_time
                )
            return ToolResult(
                call_id=params.get("_call_id", ""),
                success=False,
                error=f"Unknown level: {level}"
            )

        elif query == "list_employees":
            department = params.get("department")
            employees = [
                {"id": k, **v}
                for k, v in self.employees.items()
                if not department or v["department"] == department
            ]
            exec_time = (datetime.now() - start).total_seconds() * 1000
            return ToolResult(
                call_id=params.get("_call_id", ""),
                success=True,
                output={"employees": employees, "count": len(employees)},
                execution_time_ms=exec_time
            )

        return ToolResult(
            call_id=params.get("_call_id", ""),
            success=False,
            error=f"Unknown query: {query}"
        )

    def get_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "enum": ["get_employee", "get_salary_band", "list_employees"]},
                "employee_id": {"type": "string"},
                "level": {"type": "string"},
                "department": {"type": "string"}
            },
            "required": ["query"]
        }


class CandidateDatabaseTool(BaseTool):
    """Access candidate database for recruiting."""

    def __init__(self):
        super().__init__(
            tool_id="candidate_db",
            name="Candidate Database",
            category=ToolCategory.DATA_ACCESS,
            risk_level=RiskLevel.MEDIUM
        )

        self.candidates = [
            {"id": "cand_001", "name": "Alice Chen", "skills": ["Python", "AWS", "ML"], "experience": 5, "score": 95},
            {"id": "cand_002", "name": "Bob Martinez", "skills": ["JavaScript", "React", "Node"], "experience": 3, "score": 87},
            {"id": "cand_003", "name": "Carol Johnson", "skills": ["Python", "Django", "PostgreSQL"], "experience": 7, "score": 92},
            {"id": "cand_004", "name": "David Lee", "skills": ["Go", "Kubernetes", "AWS"], "experience": 4, "score": 88},
            {"id": "cand_005", "name": "Eva Wilson", "skills": ["Python", "TensorFlow", "PyTorch"], "experience": 6, "score": 94},
        ]

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        start = datetime.now()
        action = params.get("action", "search")

        if action == "search":
            skills = params.get("skills", [])
            min_experience = params.get("min_experience", 0)
            limit = params.get("limit", 10)

            matches = []
            for candidate in self.candidates:
                if candidate["experience"] >= min_experience:
                    skill_match = len(set(skills) & set(candidate["skills"]))
                    if skill_match > 0 or not skills:
                        matches.append({
                            **candidate,
                            "skill_match": skill_match
                        })

            matches.sort(key=lambda x: (-x["skill_match"], -x["score"]))
            matches = matches[:limit]

            exec_time = (datetime.now() - start).total_seconds() * 1000
            return ToolResult(
                call_id=params.get("_call_id", ""),
                success=True,
                output={"candidates": matches, "total": len(matches)},
                execution_time_ms=exec_time
            )

        elif action == "get":
            candidate_id = params.get("candidate_id")
            for candidate in self.candidates:
                if candidate["id"] == candidate_id:
                    exec_time = (datetime.now() - start).total_seconds() * 1000
                    return ToolResult(
                        call_id=params.get("_call_id", ""),
                        success=True,
                        output=candidate,
                        execution_time_ms=exec_time
                    )
            return ToolResult(
                call_id=params.get("_call_id", ""),
                success=False,
                error=f"Candidate not found: {candidate_id}"
            )

        return ToolResult(
            call_id=params.get("_call_id", ""),
            success=False,
            error=f"Unknown action: {action}"
        )

    def get_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["search", "get"]},
                "skills": {"type": "array", "items": {"type": "string"}},
                "min_experience": {"type": "integer"},
                "limit": {"type": "integer"},
                "candidate_id": {"type": "string"}
            },
            "required": ["action"]
        }


# ═══════════════════════════════════════════════════════════════════════════════
# DOCUMENT TOOLS
# ═══════════════════════════════════════════════════════════════════════════════

class DocumentGeneratorTool(BaseTool):
    """Generate documents like offer letters, contracts."""

    def __init__(self):
        super().__init__(
            tool_id="doc_generator",
            name="Document Generator",
            category=ToolCategory.DOCUMENT,
            risk_level=RiskLevel.HIGH
        )
        self.generated_docs = []

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        start = datetime.now()
        doc_type = params.get("type", "")

        if doc_type == "offer_letter":
            doc = {
                "id": f"doc_{uuid.uuid4().hex[:8]}",
                "type": "offer_letter",
                "candidate": params.get("candidate_name"),
                "role": params.get("role"),
                "salary": params.get("salary"),
                "start_date": params.get("start_date"),
                "equity": params.get("equity", 0),
                "signing_bonus": params.get("signing_bonus", 0),
                "created_at": datetime.now().isoformat(),
                "status": "draft"
            }
            self.generated_docs.append(doc)

            exec_time = (datetime.now() - start).total_seconds() * 1000
            return ToolResult(
                call_id=params.get("_call_id", ""),
                success=True,
                output={"document_id": doc["id"], "type": doc_type, "status": "draft"},
                execution_time_ms=exec_time
            )

        elif doc_type == "contract":
            doc = {
                "id": f"doc_{uuid.uuid4().hex[:8]}",
                "type": "contract",
                "employee": params.get("employee_name"),
                "terms": params.get("terms", {}),
                "created_at": datetime.now().isoformat(),
                "status": "pending_review"
            }
            self.generated_docs.append(doc)

            exec_time = (datetime.now() - start).total_seconds() * 1000
            return ToolResult(
                call_id=params.get("_call_id", ""),
                success=True,
                output={"document_id": doc["id"], "type": doc_type, "status": "pending_review"},
                execution_time_ms=exec_time
            )

        return ToolResult(
            call_id=params.get("_call_id", ""),
            success=False,
            error=f"Unknown document type: {doc_type}"
        )

    def get_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["offer_letter", "contract", "nda"]},
                "candidate_name": {"type": "string"},
                "role": {"type": "string"},
                "salary": {"type": "number"},
                "start_date": {"type": "string"},
                "equity": {"type": "number"},
                "signing_bonus": {"type": "number"},
                "terms": {"type": "object"}
            },
            "required": ["type"]
        }


# ═══════════════════════════════════════════════════════════════════════════════
# COMPLIANCE TOOLS
# ═══════════════════════════════════════════════════════════════════════════════

class BackgroundCheckTool(BaseTool):
    """Run background checks on candidates."""

    def __init__(self):
        super().__init__(
            tool_id="background_check",
            name="Background Check Service",
            category=ToolCategory.COMPLIANCE,
            risk_level=RiskLevel.CRITICAL
        )
        self.checks = []

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        start = datetime.now()

        candidate_id = params.get("candidate_id")
        check_type = params.get("check_type", "standard")

        # Simulate background check
        check = {
            "id": f"bgc_{uuid.uuid4().hex[:8]}",
            "candidate_id": candidate_id,
            "type": check_type,
            "status": "completed",
            "result": "clear",
            "details": {
                "criminal": "clear",
                "employment": "verified",
                "education": "verified",
                "credit": "good" if check_type == "comprehensive" else None
            },
            "completed_at": datetime.now().isoformat()
        }
        self.checks.append(check)

        exec_time = (datetime.now() - start).total_seconds() * 1000
        return ToolResult(
            call_id=params.get("_call_id", ""),
            success=True,
            output=check,
            execution_time_ms=exec_time
        )

    def get_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string"},
                "check_type": {"type": "string", "enum": ["standard", "comprehensive"]}
            },
            "required": ["candidate_id"]
        }


class I9VerificationTool(BaseTool):
    """Verify I-9 employment eligibility."""

    def __init__(self):
        super().__init__(
            tool_id="i9_verification",
            name="I-9 Verification",
            category=ToolCategory.COMPLIANCE,
            risk_level=RiskLevel.CRITICAL
        )
        self.verifications = []

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        start = datetime.now()

        employee_id = params.get("employee_id")
        documents = params.get("documents", [])

        # Simulate I-9 verification
        verification = {
            "id": f"i9_{uuid.uuid4().hex[:8]}",
            "employee_id": employee_id,
            "documents_provided": documents,
            "status": "verified" if len(documents) >= 2 else "pending",
            "verified_at": datetime.now().isoformat() if len(documents) >= 2 else None,
            "expires_at": "2029-02-07" if len(documents) >= 2 else None
        }
        self.verifications.append(verification)

        exec_time = (datetime.now() - start).total_seconds() * 1000
        return ToolResult(
            call_id=params.get("_call_id", ""),
            success=True,
            output=verification,
            execution_time_ms=exec_time
        )

    def get_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "employee_id": {"type": "string"},
                "documents": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["employee_id"]
        }


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL REGISTRY
# ═══════════════════════════════════════════════════════════════════════════════

class ToolRegistry:
    """Central registry of all available tools."""

    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        """Register all built-in tools."""
        default_tools = [
            EmailTool(),
            SlackTool(),
            CalendarTool(),
            HRDatabaseTool(),
            CandidateDatabaseTool(),
            DocumentGeneratorTool(),
            BackgroundCheckTool(),
            I9VerificationTool(),
        ]

        for tool in default_tools:
            self.register(tool)

    def register(self, tool: BaseTool):
        """Register a tool."""
        self.tools[tool.tool_id] = tool
        logger.info(f"Registered tool: {tool.name} ({tool.tool_id})")

    def get(self, tool_id: str) -> Optional[BaseTool]:
        """Get a tool by ID."""
        return self.tools.get(tool_id)

    def list_tools(self) -> List[BaseTool]:
        """List all registered tools."""
        return list(self.tools.values())

    def list_by_category(self, category: ToolCategory) -> List[BaseTool]:
        """List tools by category."""
        return [t for t in self.tools.values() if t.category == category]

    def list_by_risk(self, max_risk: RiskLevel) -> List[BaseTool]:
        """List tools up to a certain risk level."""
        risk_order = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        max_idx = risk_order.index(max_risk)
        return [t for t in self.tools.values() if risk_order.index(t.risk_level) <= max_idx]

    def get_tools_summary(self) -> Dict:
        """Get summary of all tools."""
        return {
            "total": len(self.tools),
            "by_category": {
                cat.value: len(self.list_by_category(cat))
                for cat in ToolCategory
            },
            "tools": [t.to_dict() for t in self.tools.values()]
        }


# Singleton
_tool_registry = None

def get_tool_registry() -> ToolRegistry:
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry
