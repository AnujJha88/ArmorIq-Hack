from base_agent import HRAgent
import json, sys, random
from typing import Dict, List, Tuple
from datetime import datetime

class PayrollAgent(HRAgent):
    """Agent 10: Payroll/Expenses - Processes reimbursements, bonuses, and detects fraud."""
    
    def __init__(self):
        super().__init__("Payroll", "approve_expense")
        self.expense_claims: Dict[str, Dict] = {}
        self.receipt_required_threshold = 25
        self.alcohol_per_head_limit = 50
        self.pending_approvals: List[Dict] = []

    def submit_expense(self, employee_id: str, amount: float, category: str,
                       description: str, has_receipt: bool, attendees: int = 1) -> Dict:
        claim = {"id": f"EXP-{random.randint(10000,99999)}", "employee": employee_id,
                 "amount": amount, "category": category, "description": description,
                 "has_receipt": has_receipt, "attendees": attendees,
                 "submitted_at": datetime.now().isoformat(), "status": "PENDING"}
        self.expense_claims[claim["id"]] = claim
        self.pending_approvals.append(claim)
        self.logger.info(f"📝 Expense submitted: {claim['id']} - ${amount}")
        return claim

    def process_expense(self, claim_id: str, approver_id: str) -> Tuple[bool, str]:
        claim = self.expense_claims.get(claim_id)
        if not claim:
            return False, "Claim not found"
        
        # Fraud checks
        # 1. Self-approval block
        if claim["employee"] == approver_id:
            return False, "Cannot self-approve expenses"
        
        # 2. Receipt check
        if claim["amount"] > self.receipt_required_threshold and not claim["has_receipt"]:
            payload = {"claim_id": claim_id, "amount": claim["amount"], 
                       "category": claim["category"], "has_receipt": False}
            success, reason, _ = self.execute_with_compliance("approve_expense", payload, 
                                                              f"Process {claim_id}")
            if not success:
                claim["status"] = "REJECTED"
                claim["rejection_reason"] = reason
                return False, reason
        
        # 3. Alcohol limit for team dinners
        if claim["category"].lower() in ["team dinner", "happy hour"]:
            per_head = claim["amount"] / max(claim["attendees"], 1)
            if per_head > self.alcohol_per_head_limit:
                claim["status"] = "FLAGGED"
                return False, f"Per-head amount (${per_head:.2f}) exceeds limit (${self.alcohol_per_head_limit})"
        
        claim["status"] = "APPROVED"
        claim["approved_by"] = approver_id
        claim["approved_at"] = datetime.now().isoformat()
        self.logger.info(f"✅ Expense approved: {claim_id}")
        return True, "Approved for reimbursement"

    def issue_spot_bonus(self, employee_id: str, amount: int, reason: str, 
                         approver_id: str) -> Tuple[bool, str]:
        if amount > 1000:
            return False, "Spot bonuses > $1000 require VP approval"
        
        bonus = {"employee": employee_id, "amount": amount, "reason": reason,
                 "approved_by": approver_id, "issued_at": datetime.now().isoformat()}
        self.logger.info(f"🎁 Spot bonus issued: ${amount} to {employee_id}")
        return True, f"Bonus of ${amount} queued for next payroll"

    def get_pending_approvals(self, approver_id: str) -> List[Dict]:
        # Filter out self-submitted claims
        return [c for c in self.pending_approvals if c["employee"] != approver_id and c["status"] == "PENDING"]

    def generate_expense_report(self, employee_id: str) -> Dict:
        claims = [c for c in self.expense_claims.values() if c["employee"] == employee_id]
        total = sum(c["amount"] for c in claims if c["status"] == "APPROVED")
        pending = sum(c["amount"] for c in claims if c["status"] == "PENDING")
        return {"employee": employee_id, "total_approved": total, "total_pending": pending, "claims": len(claims)}

if __name__ == "__main__":
    agent = PayrollAgent()
    agent.start()
    
    # Submit expenses
    claim1 = agent.submit_expense("emp_001", 75, "Travel", "Flight to NYC", True)
    claim2 = agent.submit_expense("emp_001", 150, "Team Dinner", "Team celebration", True, attendees=2)
    claim3 = agent.submit_expense("emp_002", 100, "Hardware", "Keyboard", False)  # No receipt
    
    # Process
    print("Travel:", agent.process_expense(claim1["id"], "emp_002"))
    print("Dinner (over limit):", agent.process_expense(claim2["id"], "emp_002"))
    print("No receipt:", agent.process_expense(claim3["id"], "emp_001"))
    
    # Self-approval attempt
    print("Self approve:", agent.process_expense(claim1["id"], "emp_001"))
    
    agent.stop()
