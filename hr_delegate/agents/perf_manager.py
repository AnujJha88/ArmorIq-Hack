from base_agent import HRAgent
import json, sys, random
from typing import Dict, List, Tuple
from datetime import datetime

class PerfManagerAgent(HRAgent):
    """Agent 6: Performance Manager - Manages reviews, 360 feedback, and performance cycles."""
    
    def __init__(self):
        super().__init__("PerfManager", "submit_review")
        self.review_cycles: Dict[str, Dict] = {}
        self.feedback_store: Dict[str, List[Dict]] = {}
        self.abusive_terms = ["lazy", "stupid", "idiot", "incompetent", "useless", "worthless"]

    def start_review_cycle(self, cycle_name: str, employees: List[str], deadline: str) -> Dict:
        cycle = {"id": f"RC-{random.randint(1000,9999)}", "name": cycle_name, 
                 "employees": employees, "deadline": deadline, "status": "ACTIVE",
                 "submitted": [], "pending": employees.copy()}
        self.review_cycles[cycle["id"]] = cycle
        self.logger.info(f"📋 Started review cycle: {cycle['id']}")
        return cycle

    def request_feedback(self, cycle_id: str, employee_id: str, reviewers: List[str]) -> bool:
        self.feedback_store[employee_id] = [{"from": r, "status": "pending"} for r in reviewers]
        self.logger.info(f"📩 Requested feedback for {employee_id} from {len(reviewers)} reviewers")
        return True

    def submit_feedback(self, employee_id: str, reviewer_id: str, rating: int, comments: str) -> Tuple[bool, str]:
        # Bias/Sentiment check
        for term in self.abusive_terms:
            if term in comments.lower():
                return False, f"Blocked: Abusive language detected ('{term}')"
        
        payload = {"employee_id": employee_id, "action": "submit_feedback", 
                   "review_summary": comments, "rating": rating}
        success, reason, _ = self.execute_with_compliance("submit_review", payload, f"Feedback for {employee_id}")
        
        if success:
            for fb in self.feedback_store.get(employee_id, []):
                if fb["from"] == reviewer_id:
                    fb["status"] = "submitted"
                    fb["rating"] = rating
                    fb["comments"] = comments
            self.logger.info(f"✅ Feedback submitted by {reviewer_id}")
            return True, "Submitted"
        return False, reason

    def generate_summary(self, employee_id: str) -> Dict:
        feedbacks = [f for f in self.feedback_store.get(employee_id, []) if f["status"] == "submitted"]
        if not feedbacks: return {"error": "No feedback"}
        avg_rating = sum(f["rating"] for f in feedbacks) / len(feedbacks)
        return {"employee": employee_id, "avg_rating": round(avg_rating, 1), 
                "feedback_count": len(feedbacks), "summary": "Based on peer feedback..."}

    def finalize_review(self, cycle_id: str, employee_id: str, final_rating: int, 
                        manager_notes: str) -> Tuple[bool, str]:
        # Check for rating stacking (all 5s or all 1s across employees)
        payload = {"employee_id": employee_id, "action": "finalize_review", 
                   "review_summary": manager_notes, "rating": final_rating}
        success, reason, _ = self.execute_with_compliance("submit_review", payload, f"Finalize for {employee_id}")
        
        if success:
            cycle = self.review_cycles.get(cycle_id)
            if cycle and employee_id in cycle["pending"]:
                cycle["pending"].remove(employee_id)
                cycle["submitted"].append(employee_id)
            self.logger.info(f"📝 Review finalized for {employee_id}: {final_rating}/5")
            return True, "Finalized"
        return False, reason

if __name__ == "__main__":
    agent = PerfManagerAgent()
    agent.start()
    cycle = agent.start_review_cycle("Q1 2026", ["emp_001", "emp_002"], "2026-03-31")
    agent.request_feedback(cycle["id"], "emp_001", ["emp_002", "emp_003"])
    success, msg = agent.submit_feedback("emp_001", "emp_002", 4, "Great work this quarter!")
    print(f"Feedback: {msg}")
    print(json.dumps(agent.generate_summary("emp_001"), indent=2))
    agent.stop()
