"""
Performance Stub
================
Performance review MCP stub.
"""

from typing import Dict, List, Any
from .base_stub import MCPStub


class PerformanceStub(MCPStub):
    """Performance review stub."""

    def __init__(self):
        super().__init__("Performance")
        self.mock_reviews = {
            "E001": [{"rating": 4, "period": "Q4 2025"}, {"rating": 4, "period": "Q3 2025"}],
            "E002": [{"rating": 5, "period": "Q4 2025"}],
            "E003": [{"rating": 3, "period": "Q4 2025"}]
        }

    def simulate(self, action: str, args: Dict[str, Any]) -> Dict[str, Any]:
        super().simulate(action, args)

        if action == "get_reviews":
            emp_id = args.get("employee_id")
            reviews = self.mock_reviews.get(emp_id, [])
            return {"status": "success", "data": reviews}

        elif action == "get_ratings":
            emp_id = args.get("employee_id")
            reviews = self.mock_reviews.get(emp_id, [])
            if reviews:
                avg = sum(r["rating"] for r in reviews) / len(reviews)
                return {"status": "success", "data": {"average_rating": avg}}
            return {"status": "success", "data": {"average_rating": None}}

        elif action == "submit_feedback":
            return {
                "status": "would_submit",
                "employee_id": args.get("employee_id"),
                "reviewer": args.get("reviewer"),
                "rating": args.get("rating")
            }

        elif action == "create_review_cycle":
            return {
                "status": "would_create",
                "period": args.get("period"),
                "participants": args.get("participants", [])
            }

        elif action == "get_goals":
            return {
                "status": "success",
                "data": [
                    {"goal": "Complete project X", "progress": 75},
                    {"goal": "Improve code coverage", "progress": 60}
                ]
            }

        return {"status": "simulated", "action": action}

    def get_capabilities(self, action: str) -> List[str]:
        caps = [f"perf.{action}"]
        if action in ["get_reviews", "get_ratings"]:
            caps.append("perf.read")
        if action in ["submit_feedback", "create_review_cycle"]:
            caps.append("perf.write")
        return caps
