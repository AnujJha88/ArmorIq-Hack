from base_agent import HRAgent
import json, sys, random
from typing import Dict, List, Tuple
from datetime import datetime

class BenefitsCoordAgent(HRAgent):
    """Agent 7: Benefits Coordinator - Handles leave, health plans, and benefits enrollment."""
    
    def __init__(self):
        super().__init__("BenefitsCoord", "file_leave_request")
        self.leave_balances: Dict[str, Dict] = {}  # emp_id -> {"pto": 20, "sick": 10}
        self.leave_requests: Dict[str, List] = {}
        self.medical_keywords = ["surgery", "cancer", "tumor", "pregnancy", "abortion", "std", 
                                  "hiv", "mental health", "therapy", "rehab"]

    def get_leave_balance(self, employee_id: str) -> Dict:
        if employee_id not in self.leave_balances:
            self.leave_balances[employee_id] = {"pto": 20, "sick": 10, "personal": 3}
        return self.leave_balances[employee_id]

    def request_leave(self, employee_id: str, leave_type: str, days: int, 
                      start_date: str, notes: str = "") -> Tuple[bool, str, Dict]:
        balance = self.get_leave_balance(employee_id)
        
        # Check accrual
        if leave_type not in balance or balance[leave_type] < days:
            return False, f"Insufficient {leave_type} balance (have: {balance.get(leave_type, 0)}, need: {days})", {}
        
        # HIPAA: Redact medical details
        redacted_notes = notes
        for kw in self.medical_keywords:
            if kw in notes.lower():
                redacted_notes = "[MEDICAL_DETAILS_REDACTED]"
                self.logger.warning(f"⚕️ HIPAA: Redacted medical details from leave request")
                break
        
        payload = {"employee_id": employee_id, "leave_type": leave_type, 
                   "days_requested": days, "medical_notes": redacted_notes}
        success, reason, modified = self.execute_with_compliance("file_leave_request", payload, 
                                                                  f"{days} days {leave_type} for {employee_id}")
        if not success:
            return False, reason, {}
        
        # Approve and deduct
        balance[leave_type] -= days
        request = {"id": f"LV-{random.randint(10000,99999)}", "employee": employee_id,
                   "type": leave_type, "days": days, "start": start_date,
                   "status": "APPROVED", "notes": redacted_notes}
        
        if employee_id not in self.leave_requests:
            self.leave_requests[employee_id] = []
        self.leave_requests[employee_id].append(request)
        
        self.logger.info(f"✅ Leave approved: {request['id']}")
        return True, "Leave approved", request

    def get_leave_history(self, employee_id: str) -> List[Dict]:
        return self.leave_requests.get(employee_id, [])

    def enroll_benefits(self, employee_id: str, plan_type: str, tier: str) -> Dict:
        enrollment = {"employee": employee_id, "plan": plan_type, "tier": tier,
                      "effective_date": "2026-01-01", "status": "ENROLLED"}
        self.logger.info(f"🏥 Benefits enrolled: {plan_type} - {tier}")
        return enrollment

    def answer_faq(self, question: str) -> str:
        faqs = {
            "pto": "You accrue 1.67 PTO days per month. Check your balance in the HR portal.",
            "health": "Open enrollment is in November. You can change plans during life events.",
            "401k": "Company matches up to 6% of your salary. Vesting is immediate."
        }
        for key, answer in faqs.items():
            if key in question.lower():
                return answer
        return "Please contact hr@company.com for detailed benefits questions."

if __name__ == "__main__":
    agent = BenefitsCoordAgent()
    agent.start()
    print("Balance:", agent.get_leave_balance("emp_001"))
    success, msg, req = agent.request_leave("emp_001", "pto", 5, "2026-03-15", "Vacation")
    print(f"Leave: {msg}")
    # Test HIPAA redaction
    success, msg, req = agent.request_leave("emp_001", "sick", 3, "2026-04-01", "Surgery for back issues")
    print(f"Medical Leave: {msg}")
    agent.stop()
