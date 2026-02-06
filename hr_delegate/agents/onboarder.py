from base_agent import HRAgent
import json, sys, random
from typing import Dict, List, Tuple
from datetime import datetime, timedelta

class OnboarderAgent(HRAgent):
    """Agent 5: Onboarding Specialist - Provisions accounts, hardware, and tracks new hire setup."""
    
    def __init__(self):
        super().__init__("Onboarder", "order_equipment")
        self.hardware_standards = {
            "Engineering": {"laptop": "MacBook Pro 16", "budget": 4000},
            "Sales": {"laptop": "MacBook Air", "budget": 2500},
            "HR": {"laptop": "Dell Latitude", "budget": 1800}
        }
        self.systems = ["email", "slack", "github", "jira", "okta", "vpn"]
        self.active_onboardings: Dict[str, Dict] = {}

    def start_onboarding(self, emp_id: str, name: str, dept: str, role: str, start_date: str) -> Dict:
        onboard = {
            "id": f"ONB-{random.randint(10000,99999)}", "employee_id": emp_id, "name": name,
            "department": dept, "role": role, "start_date": start_date,
            "accounts_created": [], "accounts_pending": self.systems.copy(),
            "hardware_ordered": False, "mentor": None, "spend": 0,
            "budget": self.hardware_standards.get(dept, {}).get("budget", 2000)
        }
        self.active_onboardings[onboard["id"]] = onboard
        self.logger.info(f"🚀 Started onboarding: {onboard['id']}")
        return onboard

    def provision_accounts(self, onboard_id: str) -> Dict[str, str]:
        onboard = self.active_onboardings.get(onboard_id)
        if not onboard: return {"error": "Not found"}
        results = {}
        for sys in list(onboard["accounts_pending"]):
            results[sys] = f"{onboard['name'].lower().replace(' ','.')}@company.com"
            onboard["accounts_pending"].remove(sys)
            onboard["accounts_created"].append(sys)
        self.logger.info(f"🔑 Provisioned {len(results)} accounts")
        return results

    def order_hardware(self, onboard_id: str, custom_laptop: str = None) -> Tuple[bool, str, Dict]:
        onboard = self.active_onboardings.get(onboard_id)
        if not onboard: return False, "Not found", {}
        
        std = self.hardware_standards.get(onboard["department"], {"laptop": "Dell", "budget": 2000})
        laptop = custom_laptop or std["laptop"]
        costs = {"MacBook Pro 16": 2500, "MacBook Air": 1200, "Dell Latitude": 800}
        cost = costs.get(laptop, 1000) + 500  # +accessories
        
        payload = {"recipient_id": onboard["employee_id"], "department": onboard["department"],
                   "item_type": laptop, "estimated_cost": cost}
        success, reason, _ = self.execute_with_compliance("order_equipment", payload, f"Order {laptop}")
        
        if not success:
            laptop, cost = std["laptop"], costs.get(std["laptop"], 800) + 500
            self.logger.warning(f"⚠️ Falling back to standard: {laptop}")
        
        onboard["hardware_ordered"] = True
        onboard["spend"] += cost
        order = {"order_id": f"HW-{random.randint(10000,99999)}", "laptop": laptop, "cost": cost}
        self.logger.info(f"📦 Ordered: {order['order_id']}")
        return True, "Ordered", order

    def assign_mentor(self, onboard_id: str, mentor_id: str) -> bool:
        onboard = self.active_onboardings.get(onboard_id)
        if onboard: onboard["mentor"] = mentor_id; return True
        return False

    def get_progress(self, onboard_id: str) -> Dict:
        o = self.active_onboardings.get(onboard_id)
        if not o: return {"error": "Not found"}
        done = len(o["accounts_created"]) + (1 if o["hardware_ordered"] else 0) + (1 if o["mentor"] else 0)
        return {"id": onboard_id, "progress": f"{done}/{len(self.systems)+2}", 
                "spend": o["spend"], "budget_left": o["budget"] - o["spend"]}

if __name__ == "__main__":
    agent = OnboarderAgent()
    agent.start()
    onb = agent.start_onboarding("emp_new", "Jane Dev", "Engineering", "L4", "2026-03-01")
    agent.provision_accounts(onb["id"])
    agent.order_hardware(onb["id"])
    print(json.dumps(agent.get_progress(onb["id"]), indent=2))
    agent.stop()
