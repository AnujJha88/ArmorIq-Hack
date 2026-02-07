"""
ArmorIQ Agentic Core
====================
Real LLM-powered agent with ArmorIQ guardrails.
"""

import os
import json
from typing import Any
from dataclasses import dataclass, field
from datetime import datetime

# Gemini SDK
from google import genai
from google.genai import types

# ArmorIQ imports
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tirs.core import get_tirs
from tirs.drift_engine import RiskLevel


@dataclass
class ToolCall:
    name: str
    args: dict

@dataclass
class ActionResult:
    tool: str
    args: dict
    allowed: bool
    result: Any = None
    block_reason: str = None
    suggestion: str = None

@dataclass
class AgentResponse:
    message: str
    actions: list[ActionResult] = field(default_factory=list)
    risk_score: float = 0.0
    risk_level: str = "OK"


# Define tools the agent can use
TOOLS = [
    {
        "name": "search_candidates",
        "description": "Search for job candidates matching criteria",
        "parameters": {
            "type": "object",
            "properties": {
                "role": {"type": "string", "description": "Job role to search for"},
                "skills": {"type": "array", "items": {"type": "string"}, "description": "Required skills"},
                "experience_years": {"type": "integer", "description": "Minimum years of experience"}
            },
            "required": ["role"]
        }
    },
    {
        "name": "schedule_interview",
        "description": "Schedule an interview with a candidate",
        "parameters": {
            "type": "object",
            "properties": {
                "candidate_name": {"type": "string", "description": "Name of the candidate"},
                "date": {"type": "string", "description": "Date for the interview (YYYY-MM-DD)"},
                "time": {"type": "string", "description": "Time for the interview (HH:MM)"},
                "interviewer": {"type": "string", "description": "Name of the interviewer"}
            },
            "required": ["candidate_name", "date", "time"]
        }
    },
    {
        "name": "send_offer",
        "description": "Send a job offer to a candidate",
        "parameters": {
            "type": "object",
            "properties": {
                "candidate_name": {"type": "string", "description": "Name of the candidate"},
                "role": {"type": "string", "description": "Job title"},
                "salary": {"type": "integer", "description": "Annual salary in USD"},
                "level": {"type": "string", "description": "Job level (L3, L4, L5, etc.)"},
                "start_date": {"type": "string", "description": "Proposed start date"}
            },
            "required": ["candidate_name", "role", "salary", "level"]
        }
    },
    {
        "name": "send_email",
        "description": "Send an email to someone",
        "parameters": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient email"},
                "subject": {"type": "string", "description": "Email subject"},
                "body": {"type": "string", "description": "Email body content"},
                "is_external": {"type": "boolean", "description": "Whether recipient is external"}
            },
            "required": ["to", "subject", "body"]
        }
    },
    {
        "name": "check_calendar",
        "description": "Check calendar availability for a person",
        "parameters": {
            "type": "object",
            "properties": {
                "person": {"type": "string", "description": "Person to check calendar for"},
                "date": {"type": "string", "description": "Date to check (YYYY-MM-DD)"}
            },
            "required": ["person", "date"]
        }
    },
    {
        "name": "get_employee_info",
        "description": "Get information about an employee",
        "parameters": {
            "type": "object",
            "properties": {
                "employee_id": {"type": "string", "description": "Employee ID or name"}
            },
            "required": ["employee_id"]
        }
    },
    {
        "name": "process_expense",
        "description": "Process an expense reimbursement",
        "parameters": {
            "type": "object",
            "properties": {
                "employee_id": {"type": "string", "description": "Employee submitting expense"},
                "amount": {"type": "number", "description": "Expense amount in USD"},
                "category": {"type": "string", "description": "Expense category"},
                "receipt_attached": {"type": "boolean", "description": "Whether receipt is attached"}
            },
            "required": ["employee_id", "amount", "category"]
        }
    }
]


class HRAgent:
    """AI-powered HR Agent with ArmorIQ guardrails."""

    def __init__(self, agent_id: str = "hr-agent-001"):
        self.agent_id = agent_id
        self.tirs = get_tirs()

        # Initialize Gemini client
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = None
            print("Warning: GEMINI_API_KEY not set. Using mock responses.")

        self.conversation_history = []

    def _get_system_prompt(self) -> str:
        return """You are an AI HR Assistant for a company. You help with:
- Searching and screening candidates
- Scheduling interviews
- Sending job offers
- Managing employee information
- Processing expenses

You have access to various HR tools. Use them to help users with their requests.

IMPORTANT RULES:
- Always be professional and helpful
- When sending offers, respect salary bands for levels (L3: up to $140K, L4: up to $180K, L5: up to $240K)
- Don't schedule interviews on weekends or outside 9 AM - 5 PM
- Protect employee PII - don't share SSN or personal phone externally
- Use inclusive language - avoid terms like "rockstar", "ninja", "guru"

When you need to take an action, use the appropriate tool. Explain what you're doing to the user."""

    def _convert_tools_for_gemini(self) -> list:
        """Convert our tool definitions to Gemini format."""
        gemini_tools = []
        for tool in TOOLS:
            gemini_tools.append(types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(
                        name=tool["name"],
                        description=tool["description"],
                        parameters=tool["parameters"]
                    )
                ]
            ))
        return gemini_tools

    def _check_with_armoriq(self, tool_name: str, args: dict) -> tuple[bool, str, str]:
        """Check if action is allowed by ArmorIQ policies."""

        # Policy checks
        if tool_name == "send_offer":
            salary = args.get("salary", 0)
            level = args.get("level", "L3")

            caps = {"L3": 140000, "L4": 180000, "L5": 240000, "L6": 320000}
            cap = caps.get(level, 140000)

            if salary > cap:
                return False, f"Salary ${salary:,} exceeds cap for {level} (${cap:,})", f"Reduce salary to ${cap:,} or escalate to VP for approval"

        if tool_name == "schedule_interview":
            date_str = args.get("date", "")
            time_str = args.get("time", "")

            try:
                from datetime import datetime
                dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

                # Weekend check
                if dt.weekday() >= 5:
                    return False, "Cannot schedule interviews on weekends", "Choose a weekday (Monday-Friday)"

                # Hours check
                if dt.hour < 9 or dt.hour >= 17:
                    return False, "Interviews must be between 9 AM and 5 PM", "Choose a time between 9:00 and 17:00"
            except:
                pass

        if tool_name == "send_email":
            body = args.get("body", "")
            is_external = args.get("is_external", False)

            # Check for PII in external emails
            if is_external:
                import re
                if re.search(r'\b\d{3}-\d{2}-\d{4}\b', body):  # SSN pattern
                    return False, "Cannot send SSN in external emails", "Remove or redact the SSN before sending"
                if re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', body):  # Phone pattern
                    return False, "Cannot send personal phone numbers externally", "Use company contact info instead"

            # Inclusive language check
            bad_terms = ["rockstar", "ninja", "guru", "wizard", "superhero"]
            for term in bad_terms:
                if term.lower() in body.lower():
                    return False, f"Term '{term}' is not inclusive", f"Replace '{term}' with a professional alternative"

        if tool_name == "process_expense":
            amount = args.get("amount", 0)
            receipt = args.get("receipt_attached", False)

            if amount > 50 and not receipt:
                return False, "Receipt required for expenses over $50", "Attach receipt documentation"

        return True, None, None

    def _execute_tool(self, tool_name: str, args: dict) -> dict:
        """Execute tool via MCP stubs (simulated)."""

        # Simulated responses
        if tool_name == "search_candidates":
            return {
                "candidates": [
                    {"name": "Alice Chen", "experience": 5, "skills": args.get("skills", []), "match_score": 92},
                    {"name": "Bob Smith", "experience": 3, "skills": args.get("skills", []), "match_score": 85},
                    {"name": "Carol Davis", "experience": 7, "skills": args.get("skills", []), "match_score": 78}
                ]
            }

        if tool_name == "schedule_interview":
            return {
                "success": True,
                "interview_id": "INT-2024-001",
                "calendar_invite_sent": True,
                "details": f"Interview scheduled with {args.get('candidate_name')} on {args.get('date')} at {args.get('time')}"
            }

        if tool_name == "send_offer":
            return {
                "success": True,
                "offer_id": "OFR-2024-001",
                "status": "sent",
                "details": f"Offer sent to {args.get('candidate_name')} for {args.get('role')} at ${args.get('salary'):,}"
            }

        if tool_name == "send_email":
            return {
                "success": True,
                "message_id": "MSG-2024-001",
                "status": "delivered"
            }

        if tool_name == "check_calendar":
            return {
                "person": args.get("person"),
                "date": args.get("date"),
                "available_slots": ["09:00", "10:30", "14:00", "15:30"]
            }

        if tool_name == "get_employee_info":
            return {
                "employee_id": args.get("employee_id"),
                "name": "John Doe",
                "department": "Engineering",
                "level": "L4",
                "manager": "Jane Smith"
            }

        if tool_name == "process_expense":
            return {
                "success": True,
                "expense_id": "EXP-2024-001",
                "status": "approved",
                "amount": args.get("amount")
            }

        return {"error": f"Unknown tool: {tool_name}"}

    def _record_to_tirs(self, tool_name: str, allowed: bool):
        """Record action to TIRS for drift monitoring."""
        self.tirs.record_intent(
            agent_id=self.agent_id,
            action=tool_name,
            capabilities=[tool_name],
            was_violation=not allowed
        )

    def _get_mock_response(self, user_message: str) -> AgentResponse:
        """Generate mock response when Gemini is not available."""

        message_lower = user_message.lower()

        # Simple keyword matching for demo
        if "search" in message_lower or "find" in message_lower or "candidate" in message_lower:
            tool_name = "search_candidates"
            args = {"role": "Software Engineer", "skills": ["Python", "JavaScript"]}
        elif "schedule" in message_lower or "interview" in message_lower:
            tool_name = "schedule_interview"
            args = {"candidate_name": "Alice Chen", "date": "2024-02-15", "time": "10:00"}
        elif "offer" in message_lower or "salary" in message_lower:
            # Check if they're asking for too much
            if "200k" in message_lower or "200000" in message_lower or "$200" in message_lower:
                tool_name = "send_offer"
                args = {"candidate_name": "Alice Chen", "role": "Senior Engineer", "salary": 200000, "level": "L4"}
            else:
                tool_name = "send_offer"
                args = {"candidate_name": "Alice Chen", "role": "Senior Engineer", "salary": 150000, "level": "L4"}
        elif "email" in message_lower:
            tool_name = "send_email"
            args = {"to": "alice@example.com", "subject": "Follow up", "body": "Thank you for your interest.", "is_external": True}
        elif "expense" in message_lower:
            tool_name = "process_expense"
            args = {"employee_id": "EMP001", "amount": 75, "category": "Travel", "receipt_attached": False}
        else:
            return AgentResponse(
                message="I can help you with searching candidates, scheduling interviews, sending offers, managing emails, and processing expenses. What would you like to do?",
                actions=[],
                risk_score=0.0,
                risk_level="OK"
            )

        # Check with ArmorIQ
        allowed, block_reason, suggestion = self._check_with_armoriq(tool_name, args)

        # Record to TIRS
        self._record_to_tirs(tool_name, allowed)

        # Get risk score
        risk_score = self.tirs.get_risk_score(self.agent_id)
        risk_level = self.tirs.get_risk_level(self.agent_id).name

        if allowed:
            result = self._execute_tool(tool_name, args)
            action = ActionResult(
                tool=tool_name,
                args=args,
                allowed=True,
                result=result
            )
            message = f"Done! I've executed {tool_name}. Result: {json.dumps(result, indent=2)}"
        else:
            action = ActionResult(
                tool=tool_name,
                args=args,
                allowed=False,
                block_reason=block_reason,
                suggestion=suggestion
            )
            message = f"I tried to execute {tool_name}, but it was blocked.\n\nReason: {block_reason}\n\nSuggestion: {suggestion}"

        return AgentResponse(
            message=message,
            actions=[action],
            risk_score=risk_score,
            risk_level=risk_level
        )

    async def chat(self, user_message: str) -> AgentResponse:
        """Process user message and return response with actions."""

        if not self.client:
            return self._get_mock_response(user_message)

        # Build conversation
        self.conversation_history.append({
            "role": "user",
            "parts": [user_message]
        })

        try:
            # Call Gemini with tools
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                config=types.GenerateContentConfig(
                    system_instruction=self._get_system_prompt(),
                    tools=self._convert_tools_for_gemini()
                ),
                contents=self.conversation_history
            )

            actions = []
            final_message = ""

            # Process response
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        # Tool call
                        tool_name = part.function_call.name
                        args = dict(part.function_call.args) if part.function_call.args else {}

                        # Check with ArmorIQ
                        allowed, block_reason, suggestion = self._check_with_armoriq(tool_name, args)

                        # Record to TIRS
                        self._record_to_tirs(tool_name, allowed)

                        if allowed:
                            result = self._execute_tool(tool_name, args)
                            actions.append(ActionResult(
                                tool=tool_name,
                                args=args,
                                allowed=True,
                                result=result
                            ))
                        else:
                            actions.append(ActionResult(
                                tool=tool_name,
                                args=args,
                                allowed=False,
                                block_reason=block_reason,
                                suggestion=suggestion
                            ))

                    elif hasattr(part, 'text') and part.text:
                        final_message += part.text

            # Get risk assessment
            risk_score = self.tirs.get_risk_score(self.agent_id)
            risk_level = self.tirs.get_risk_level(self.agent_id).name

            # Add to history
            self.conversation_history.append({
                "role": "model",
                "parts": [final_message] if final_message else ["Action executed."]
            })

            return AgentResponse(
                message=final_message or "Action completed.",
                actions=actions,
                risk_score=risk_score,
                risk_level=risk_level
            )

        except Exception as e:
            return AgentResponse(
                message=f"Error: {str(e)}",
                actions=[],
                risk_score=0.0,
                risk_level="OK"
            )

    def get_status(self) -> dict:
        """Get current agent status."""
        risk_score = self.tirs.get_risk_score(self.agent_id)
        risk_level = self.tirs.get_risk_level(self.agent_id)

        return {
            "agent_id": self.agent_id,
            "risk_score": risk_score,
            "risk_level": risk_level.name,
            "is_paused": risk_level in [RiskLevel.PAUSE, RiskLevel.KILL],
            "conversation_length": len(self.conversation_history)
        }


# Singleton instance
_agent = None

def get_agent() -> HRAgent:
    global _agent
    if _agent is None:
        _agent = HRAgent()
    return _agent
