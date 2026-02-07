"""
Email Stub
==========
Email service MCP stub with execute handlers.
"""

import random
from typing import Dict, List, Any
from datetime import datetime
from .base_stub import MCPStub


class EmailStub(MCPStub):
    """Email service stub with execute handlers."""

    def __init__(self):
        super().__init__("Email")
        self.sent_emails: List[Dict] = []

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

    # ═══════════════════════════════════════════════════════════════════════════
    # EXECUTE HANDLERS (called by base class execute() method)
    # ═══════════════════════════════════════════════════════════════════════════

    def do_send(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Actually send an email (in demo mode, logs it)."""
        email = {
            "message_id": f"MSG-{random.randint(10000, 99999)}",
            "to": args.get("to", args.get("recipient")),
            "cc": args.get("cc"),
            "subject": args.get("subject", "(no subject)"),
            "body": args.get("body", args.get("message", "")),
            "sent_at": datetime.now().isoformat()
        }
        self.sent_emails.append(email)
        self.logger.info(f"📧 Email sent to {email['to']}: {email['subject']}")
        return {
            "message_id": email["message_id"],
            "recipient": email["to"],
            "subject": email["subject"],
            "sent_at": email["sent_at"]
        }

    def do_draft(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create an email draft."""
        draft_id = f"DRAFT-{random.randint(10000, 99999)}"
        self.logger.info(f"📝 Draft created: {draft_id}")
        return {
            "draft_id": draft_id,
            "to": args.get("to"),
            "subject": args.get("subject"),
            "created_at": datetime.now().isoformat()
        }

    def do_schedule(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule an email for later."""
        schedule_id = f"SCHED-{random.randint(10000, 99999)}"
        self.logger.info(f"⏰ Email scheduled: {schedule_id} for {args.get('send_at')}")
        return {
            "schedule_id": schedule_id,
            "to": args.get("to"),
            "send_at": args.get("send_at"),
            "created_at": datetime.now().isoformat()
        }

    def get_capabilities(self, action: str) -> List[str]:
        caps = [f"email.{action}"]
        # Check if sending to external domain
        if self.call_log:
            to = self.call_log[-1]["args"].get("to", "")
            if to and not to.endswith("@company.com"):
                caps.append("email.external")
        return caps

