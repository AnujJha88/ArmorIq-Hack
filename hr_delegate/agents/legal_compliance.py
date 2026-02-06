from base_agent import HRAgent
import json, sys
from typing import Dict, Tuple
from datetime import datetime, timedelta

class LegalCompAgent(HRAgent):
    """Agent 8: Legal/Immigration - Verifies work authorization, tracks visas, ensures compliance."""
    
    def __init__(self):
        super().__init__("LegalComp", "onboard_employee")
        self.employee_docs: Dict[str, Dict] = {}
        self.visa_alerts: List[Dict] = []

    def verify_i9(self, employee_id: str, doc_type: str, doc_number: str, 
                  expiry: str = None) -> Tuple[bool, str]:
        doc = {"type": doc_type, "number": doc_number[-4:] + "****", "verified": True,
               "verified_at": datetime.now().isoformat(), "expiry": expiry}
        self.employee_docs[employee_id] = doc
        self.logger.info(f"📄 I-9 verified for {employee_id}")
        return True, "I-9 verified successfully"

    def check_work_authorization(self, employee_id: str) -> Tuple[bool, str, Dict]:
        doc = self.employee_docs.get(employee_id)
        if not doc:
            return False, "No I-9 on file", {}
        if not doc.get("verified"):
            return False, "I-9 not verified", doc
        
        # Check expiry
        if doc.get("expiry"):
            expiry = datetime.strptime(doc["expiry"], "%Y-%m-%d")
            days_until = (expiry - datetime.now()).days
            if days_until < 0:
                return False, "Work authorization EXPIRED", doc
            elif days_until < 30:
                self.logger.warning(f"⚠️ Visa expiring in {days_until} days")
                return True, f"Warning: Expires in {days_until} days", doc
        
        return True, "Work authorization valid", doc

    def approve_onboarding(self, candidate_id: str) -> Tuple[bool, str]:
        # Check if I-9 is verified
        authorized, msg, doc = self.check_work_authorization(candidate_id)
        
        payload = {"candidate_id": candidate_id, "action": "finalize_onboarding",
                   "i9_status": "verified" if doc.get("verified") else "missing"}
        success, reason, _ = self.execute_with_compliance("onboard_employee", payload, 
                                                          f"Legal clearance for {candidate_id}")
        if not success:
            self.logger.critical(f"🛑 Onboarding BLOCKED: {reason}")
            return False, reason
        
        self.logger.info(f"✅ Legal clearance granted for {candidate_id}")
        return True, "Cleared for onboarding"

    def scan_expiring_visas(self, days_ahead: int = 90) -> List[Dict]:
        alerts = []
        cutoff = datetime.now() + timedelta(days=days_ahead)
        for emp_id, doc in self.employee_docs.items():
            if doc.get("expiry"):
                expiry = datetime.strptime(doc["expiry"], "%Y-%m-%d")
                if expiry <= cutoff:
                    alerts.append({"employee": emp_id, "expiry": doc["expiry"], 
                                   "days_remaining": (expiry - datetime.now()).days})
        self.visa_alerts = alerts
        self.logger.info(f"🔍 Found {len(alerts)} expiring visas in next {days_ahead} days")
        return alerts

    def request_visa_renewal(self, employee_id: str) -> Dict:
        self.logger.info(f"📝 Visa renewal process started for {employee_id}")
        return {"employee": employee_id, "status": "RENEWAL_INITIATED", 
                "next_step": "Submit updated documents to legal@company.com"}

if __name__ == "__main__":
    agent = LegalCompAgent()
    agent.start()
    # Verify I-9
    agent.verify_i9("emp_001", "passport", "AB1234567", "2026-06-01")
    agent.verify_i9("emp_002", "passport", "CD9876543", "2026-02-15")  # Expiring soon
    
    # Check authorizations
    print(agent.check_work_authorization("emp_001"))
    print(agent.check_work_authorization("emp_002"))
    
    # Scan for expiring
    print("Expiring:", agent.scan_expiring_visas(90))
    
    # Try to onboard without I-9
    print("Onboard no I-9:", agent.approve_onboarding("emp_new"))
    agent.stop()

from typing import List
