"""
Calendar Stub
=============
Calendar service MCP stub.
"""

from typing import Dict, List, Any
from datetime import datetime
from .base_stub import MCPStub


class CalendarStub(MCPStub):
    """Calendar service stub."""

    def __init__(self):
        super().__init__("Calendar")
        self.mock_availability = {
            "10:00": True,
            "11:00": True,
            "14:00": True,
            "15:00": True,
            "16:00": False  # Already booked
        }

    def simulate(self, action: str, args: Dict[str, Any]) -> Dict[str, Any]:
        super().simulate(action, args)

        if action == "check_availability":
            time = args.get("time", "10:00")
            return {
                "status": "success",
                "available": self.mock_availability.get(time, True)
            }

        elif action == "book":
            return {
                "status": "would_book",
                "date": args.get("date"),
                "time": args.get("time"),
                "duration": args.get("duration", 60),
                "attendees": args.get("attendees", []),
                "room": args.get("room")
            }

        elif action == "find_slots":
            return {
                "status": "success",
                "slots": ["10:00", "11:00", "14:00", "15:00"],
                "date": args.get("date")
            }

        elif action == "cancel":
            return {
                "status": "would_cancel",
                "event_id": args.get("event_id")
            }

        elif action == "reschedule":
            return {
                "status": "would_reschedule",
                "event_id": args.get("event_id"),
                "new_date": args.get("new_date"),
                "new_time": args.get("new_time")
            }

        return {"status": "simulated", "action": action}

    def get_capabilities(self, action: str) -> List[str]:
        caps = [f"calendar.{action}"]
        if action in ["book", "cancel", "reschedule"]:
            caps.append("calendar.write")
        return caps
