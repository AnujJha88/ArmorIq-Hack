"""
Offer Stub
==========
Offer generation MCP stub.
"""

from typing import Dict, List, Any
from .base_stub import MCPStub


class OfferStub(MCPStub):
    """Offer generation stub."""

    def __init__(self):
        super().__init__("Offer")

    def simulate(self, action: str, args: Dict[str, Any]) -> Dict[str, Any]:
        super().simulate(action, args)

        if action == "generate":
            return {
                "status": "would_generate",
                "role": args.get("role"),
                "salary": args.get("salary"),
                "equity": args.get("equity", 0),
                "signing_bonus": args.get("signing_bonus", 0),
                "start_date": args.get("start_date")
            }

        elif action == "send":
            return {
                "status": "would_send",
                "to": args.get("candidate_email"),
                "offer_id": args.get("offer_id", "OFFER-001")
            }

        elif action == "approve":
            return {
                "status": "would_approve",
                "offer_id": args.get("offer_id"),
                "approver": args.get("approver")
            }

        elif action == "revoke":
            return {
                "status": "would_revoke",
                "offer_id": args.get("offer_id"),
                "reason": args.get("reason")
            }

        elif action == "negotiate":
            return {
                "status": "would_negotiate",
                "offer_id": args.get("offer_id"),
                "counter_salary": args.get("counter_salary"),
                "counter_equity": args.get("counter_equity")
            }

        return {"status": "simulated", "action": action}

    def get_capabilities(self, action: str) -> List[str]:
        caps = [f"offer.{action}"]
        if action in ["generate", "send", "approve"]:
            caps.append("offer.write")
        if action == "revoke":
            caps.append("offer.admin")
        return caps
