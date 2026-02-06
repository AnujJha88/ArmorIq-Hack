from base_agent import HRAgent
import json, sys, random
from typing import Dict, List, Tuple
from datetime import datetime, timedelta

class OffboarderAgent(HRAgent):
    """Agent 12: Offboarding Specialist - Manages departures, access revocation, and exit procedures."""
    
    def __init__(self):
        super().__init__("Offboarder", "revoke_access")
        self.offboardings: Dict[str, Dict] = {}
        self.systems = ["email", "slack", "github", "jira", "aws", "vpn", "okta", "card_access"]

    def initiate_offboarding(self, employee_id: str, name: str, last_day: str,
                              reason: str = "resignation") -> Dict:
        offboard = {"id": f"OFF-{random.randint(1000,9999)}", "employee_id": employee_id,
                    "name": name, "last_day": last_day, "reason": reason,
                    "systems_revoked": [], "systems_pending": self.systems.copy(),
                    "exit_interview": None, "equipment_returned": False,
                    "status": "IN_PROGRESS", "initiated_at": datetime.now().isoformat()}
        self.offboardings[offboard["id"]] = offboard
        self.logger.info(f"🔄 Offboarding started: {offboard['id']} - {name}")
        return offboard

    def schedule_exit_interview(self, offboard_id: str, date: str, interviewer: str) -> bool:
        offboard = self.offboardings.get(offboard_id)
        if not offboard:
            return False
        offboard["exit_interview"] = {"date": date, "interviewer": interviewer, "status": "scheduled"}
        self.logger.info(f"📅 Exit interview scheduled: {date}")
        return True

    def revoke_access(self, offboard_id: str, systems: List[str] = None) -> Tuple[bool, str, List[str]]:
        offboard = self.offboardings.get(offboard_id)
        if not offboard:
            return False, "Offboarding not found", []
        
        systems = systems or offboard["systems_pending"]
        last_day = datetime.strptime(offboard["last_day"], "%Y-%m-%d")
        now = datetime.now()
        
        # Security policy: Must revoke by 5 PM on last day
        if now.date() == last_day.date() and now.hour >= 17:
            self.logger.warning("⚠️ Past 5 PM on last day - URGENT revocation")
        elif now.date() > last_day.date():
            self.logger.critical("🚨 OVERDUE: Access should have been revoked!")
        
        payload = {"employee_id": offboard["employee_id"], 
                   "target_revocation_time": f"{offboard['last_day']} 17:00",
                   "systems": systems}
        success, reason, _ = self.execute_with_compliance("revoke_access", payload, 
                                                          f"Revoke for {offboard['name']}")
        
        revoked = []
        for sys in systems:
            if sys in offboard["systems_pending"]:
                offboard["systems_pending"].remove(sys)
                offboard["systems_revoked"].append(sys)
                revoked.append(sys)
        
        self.logger.info(f"🔒 Revoked: {revoked}")
        return True, f"Revoked {len(revoked)} systems", revoked

    def record_equipment_return(self, offboard_id: str, items: List[str]) -> bool:
        offboard = self.offboardings.get(offboard_id)
        if not offboard:
            return False
        offboard["equipment_returned"] = True
        offboard["returned_items"] = items
        self.logger.info(f"📦 Equipment returned: {items}")
        return True

    def trigger_data_wipe(self, offboard_id: str) -> Tuple[bool, str]:
        offboard = self.offboardings.get(offboard_id)
        if not offboard:
            return False, "Not found"
        
        if not offboard.get("equipment_returned"):
            last_day = datetime.strptime(offboard["last_day"], "%Y-%m-%d")
            days_overdue = (datetime.now() - last_day).days
            if days_overdue >= 3:
                self.logger.critical(f"💥 Remote wipe triggered for {offboard['name']} - Equipment not returned")
                return True, "Remote wipe initiated"
            return False, f"Equipment not returned. Wipe in {3 - days_overdue} days."
        return False, "Equipment already returned"

    def complete_offboarding(self, offboard_id: str) -> Tuple[bool, str]:
        offboard = self.offboardings.get(offboard_id)
        if not offboard:
            return False, "Not found"
        
        # Check all steps complete
        if offboard["systems_pending"]:
            return False, f"Systems still pending: {offboard['systems_pending']}"
        if not offboard.get("equipment_returned"):
            return False, "Equipment not returned"
        
        offboard["status"] = "COMPLETED"
        offboard["completed_at"] = datetime.now().isoformat()
        self.logger.info(f"✅ Offboarding complete: {offboard['id']}")
        return True, "Offboarding completed successfully"

    def get_offboarding_status(self, offboard_id: str) -> Dict:
        offboard = self.offboardings.get(offboard_id)
        if not offboard:
            return {"error": "Not found"}
        return {"id": offboard_id, "employee": offboard["name"], "status": offboard["status"],
                "systems_revoked": len(offboard["systems_revoked"]),
                "systems_pending": len(offboard["systems_pending"]),
                "equipment": "Returned" if offboard.get("equipment_returned") else "Pending"}

if __name__ == "__main__":
    agent = OffboarderAgent()
    agent.start()
    
    offboard = agent.initiate_offboarding("emp_003", "John Leaving", "2026-02-10", "resignation")
    print("Exit interview:", agent.schedule_exit_interview(offboard["id"], "2026-02-09", "emp_001"))
    print("Revoke access:", agent.revoke_access(offboard["id"]))
    print("Equipment:", agent.record_equipment_return(offboard["id"], ["MacBook Pro", "Badge"]))
    print("Complete:", agent.complete_offboarding(offboard["id"]))
    print("Status:", json.dumps(agent.get_offboarding_status(offboard["id"]), indent=2))
    agent.stop()
