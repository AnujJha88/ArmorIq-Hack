from base_agent import HRAgent
import json, sys, random
from typing import Dict, List, Tuple
from datetime import datetime

class LnDManagerAgent(HRAgent):
    """Agent 9: L&D Manager - Assigns training, tracks certifications, manages learning budgets."""
    
    def __init__(self):
        super().__init__("LnDManager", "approve_budget")
        self.mandatory_courses = {"all": ["Security Awareness", "Code of Conduct"],
                                   "Engineering": ["Secure Coding 101"],
                                   "Sales": ["GDPR Training"]}
        self.training_records: Dict[str, List[str]] = {}
        self.budget_usage: Dict[str, int] = {}
        self.yearly_budget_cap = 1500

    def assign_mandatory_training(self, employee_id: str, department: str) -> List[str]:
        courses = self.mandatory_courses.get("all", []) + self.mandatory_courses.get(department, [])
        self.training_records[employee_id] = []
        self.logger.info(f"📚 Assigned {len(courses)} courses to {employee_id}")
        return courses

    def record_completion(self, employee_id: str, course: str) -> bool:
        if employee_id not in self.training_records:
            self.training_records[employee_id] = []
        self.training_records[employee_id].append(course)
        self.logger.info(f"✅ {employee_id} completed: {course}")
        return True

    def check_compliance(self, employee_id: str, department: str) -> Tuple[bool, List[str]]:
        required = self.mandatory_courses.get("all", []) + self.mandatory_courses.get(department, [])
        completed = self.training_records.get(employee_id, [])
        missing = [c for c in required if c not in completed]
        return len(missing) == 0, missing

    def request_learning_budget(self, employee_id: str, request_type: str, 
                                 amount: int, description: str) -> Tuple[bool, str]:
        used = self.budget_usage.get(employee_id, 0)
        remaining = self.yearly_budget_cap - used
        
        if amount > remaining:
            return False, f"Exceeds remaining budget (${remaining} left of ${self.yearly_budget_cap})"
        
        payload = {"employee_id": employee_id, "request_type": request_type, "amount": amount}
        success, reason, _ = self.execute_with_compliance("approve_budget", payload, 
                                                          f"${amount} for {request_type}")
        if not success:
            return False, reason
        
        self.budget_usage[employee_id] = used + amount
        self.logger.info(f"💰 Approved ${amount} for {employee_id}")
        return True, f"Approved. Remaining: ${remaining - amount}"

    def check_system_access(self, employee_id: str, system: str, department: str) -> Tuple[bool, str]:
        """Block access to sensitive systems until training complete."""
        sensitive_systems = {"aws": "Security Awareness", "prod": "Secure Coding 101", "crm": "GDPR Training"}
        required_course = sensitive_systems.get(system.lower())
        
        if required_course:
            completed = self.training_records.get(employee_id, [])
            if required_course not in completed:
                return False, f"Access to {system} requires completion of '{required_course}'"
        
        return True, "Access granted"

if __name__ == "__main__":
    agent = LnDManagerAgent()
    agent.start()
    
    courses = agent.assign_mandatory_training("emp_001", "Engineering")
    print(f"Assigned: {courses}")
    
    # Try accessing AWS without training
    print("AWS access:", agent.check_system_access("emp_001", "aws", "Engineering"))
    
    # Complete training
    agent.record_completion("emp_001", "Security Awareness")
    print("AWS access after training:", agent.check_system_access("emp_001", "aws", "Engineering"))
    
    # Request budget
    print("Budget request:", agent.request_learning_budget("emp_001", "conference", 1200, "AWS re:Invent"))
    print("Budget request:", agent.request_learning_budget("emp_001", "course", 500, "ML Certification"))
    agent.stop()
