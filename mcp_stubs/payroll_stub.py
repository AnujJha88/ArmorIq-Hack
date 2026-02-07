"""
Payroll Stub
============
Payroll service MCP stub.
"""

from typing import Dict, List, Any
from .base_stub import MCPStub


class PayrollStub(MCPStub):
    """Payroll service stub."""

    def __init__(self):
        super().__init__("Payroll")

    def simulate(self, action: str, args: Dict[str, Any]) -> Dict[str, Any]:
        super().simulate(action, args)

        if action == "get_salary":
            return {
                "status": "success",
                "data": {
                    "salary": 150000,
                    "currency": "USD",
                    "frequency": "annual"
                }
            }

        elif action == "get_compensation":
            return {
                "status": "success",
                "data": {
                    "base_salary": 150000,
                    "bonus_target": 15000,
                    "equity_value": 50000,
                    "benefits_value": 20000
                }
            }

        elif action == "process_expense":
            return {
                "status": "would_process",
                "amount": args.get("amount"),
                "category": args.get("category"),
                "has_receipt": args.get("has_receipt", False)
            }

        elif action == "approve_expense":
            return {
                "status": "would_approve",
                "expense_id": args.get("expense_id"),
                "amount": args.get("amount")
            }

        elif action == "process_payroll":
            return {
                "status": "would_process",
                "period": args.get("period"),
                "employee_count": args.get("employee_count", 1)
            }

        return {"status": "simulated", "action": action}

    def get_capabilities(self, action: str) -> List[str]:
        caps = [f"payroll.{action}"]
        if action in ["get_salary", "get_compensation"]:
            caps.append("payroll.read_sensitive")
        if action in ["process_expense", "approve_expense", "process_payroll"]:
            caps.append("payroll.write")
        return caps
