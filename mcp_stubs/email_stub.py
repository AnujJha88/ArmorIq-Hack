"""
Email Stub
==========
Email service MCP stub.
"""

from typing import Dict, List, Any
from .base_stub import MCPStub


class EmailStub(MCPStub):
    """Email service stub."""

    def __init__(self):
        super().__init__("Email")

    def simulate(self, action: str, args: Dict[str, Any]) -> Dict[str, Any]:
        super().simulate(action, args)

        if action == "send":
            return {
                "status": "would_send",
                "to": args.get("to"),
                "cc": args.get("cc"),
                "subject": args.get("subject", "(no subject)"),
                "body_length": len(args.get("body", ""))
            }

        elif action == "draft":
            return {"status": "drafted", "draft_id": "DRAFT-001"}

        elif action == "schedule":
            return {
                "status": "would_schedule",
                "to": args.get("to"),
                "send_at": args.get("send_at")
            }

        elif action == "template":
            return {
                "status": "template_rendered",
                "template": args.get("template_name"),
                "variables": list(args.get("variables", {}).keys())
            }

        return {"status": "simulated", "action": action}

    def get_capabilities(self, action: str) -> List[str]:
        caps = [f"email.{action}"]
        # Check if sending to external domain
        if self.call_log:
            to = self.call_log[-1]["args"].get("to", "")
            if to and not to.endswith("@company.com"):
                caps.append("email.external")
        return caps
