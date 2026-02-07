"""
HRIS Stub
=========
Human Resource Information System MCP stub.
"""

from typing import Dict, List, Any
from .base_stub import MCPStub


class HRISStub(MCPStub):
    """HRIS (Human Resource Information System) stub."""

    def __init__(self):
        super().__init__("HRIS")
        self.mock_employees = {
            "E001": {"name": "John Doe", "role": "L4", "department": "Engineering"},
            "E002": {"name": "Jane Smith", "role": "L5", "department": "Product"},
            "E003": {"name": "Bob Wilson", "role": "L3", "department": "Sales"},
            "E004": {"name": "Alice Brown", "role": "L4", "department": "Engineering"},
            "E005": {"name": "Charlie Davis", "role": "L3", "department": "Marketing"}
        }

    def simulate(self, action: str, args: Dict[str, Any]) -> Dict[str, Any]:
        super().simulate(action, args)

        if action == "get_employee":
            emp_id = args.get("employee_id")
            if emp_id in self.mock_employees:
                return {"status": "success", "data": self.mock_employees[emp_id]}
            return {"status": "not_found"}

        elif action == "get_salary_band":
            role = args.get("role", "L3")
            bands = {
                "L3": (100000, 140000),
                "L4": (130000, 180000),
                "L5": (170000, 240000),
                "L6": (220000, 320000)
            }
            return {"status": "success", "data": {"role": role, "range": bands.get(role, (80000, 100000))}}

        elif action == "query":
            department = args.get("department")
            if department:
                filtered = {k: v for k, v in self.mock_employees.items() if v["department"] == department}
                return {"status": "success", "data": list(filtered.values())}
            return {"status": "success", "data": list(self.mock_employees.values())}

        elif action == "export":
            return {"status": "success", "data": {"exported": len(self.mock_employees)}}

        elif action == "create_employee":
            return {"status": "would_create", "data": args}

        elif action == "update_employee":
            return {"status": "would_update", "employee_id": args.get("employee_id")}

        elif action == "delete_employee":
            return {"status": "would_delete", "employee_id": args.get("employee_id")}

        return {"status": "simulated", "action": action}

    def get_capabilities(self, action: str) -> List[str]:
        caps = [f"hris.{action}"]
        if action == "export":
            caps.append("hris.bulk_read")
        if action in ["update_employee", "delete_employee", "create_employee"]:
            caps.append("hris.write")
        return caps
