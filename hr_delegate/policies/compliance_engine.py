import re
import datetime
import json
import logging

class ComplianceEngine:
    def __init__(self):
        self.logger = logging.getLogger("ArmorIQ_Policy_Engine")
        # Load policies if needed (for now hardcoded for demo speed)
        self.weekend_blocked = True
        self.work_hours = (9, 17) # 9 AM to 5 PM
        self.pii_patterns = {
            "phone": r"\+?1?[-.]?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}",
            "email": r"[\w\.-]+@[\w\.-]+",
            "ssn": r"\d{3}-\d{2}-\d{4}"
        }
        self.bias_terms = ["rockstar", "ninja", "guru", "crush code", "guys", "salesman", "manpower"]

    def check_intent(self, intent_type, payload, user_role="agent"):
        """
        Main entry point for ArmorIQ Intent Verification.
        Returns: (allowed: bool, reason: str, modified_payload: dict)
        """
        if intent_type == "schedule_interview":
            return self._check_scheduling(payload)
        elif intent_type == "send_email":
            return self._check_outbound_comm(payload)
        elif intent_type == "generate_offer":
            return self._check_offer_cap(payload)
        elif intent_type == "approve_expense":
            return self._check_expense(payload)
        elif intent_type == "onboard_employee":
            return self._check_legal_status(payload)
        
        return True, "Allowed", payload

    def _check_scheduling(self, payload):
        time_str = payload.get("time")
        if not time_str:
            return False, "Missing time", payload
        
        try:
            # Parse ISO format or simple string
            # Simplified for demo: Assume "YR-MON-DAY HH:MM"
            dt = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M")
            
            # 1. Weekend Check
            if dt.weekday() >= 5: # 5=Sat, 6=Sun
                return False, "Policy Violation: No interviews on Weekends.", payload

            # 2. Hours Check
            if not (self.work_hours[0] <= dt.hour < self.work_hours[1]):
                 return False, f"Policy Violation: Interviews must be between {self.work_hours[0]}:00 and {self.work_hours[1]}:00.", payload
                 
            return True, "Schedule Approved", payload
        except ValueError:
            return False, "Invalid time format (Use YYYY-MM-DD HH:MM)", payload

    def _check_outbound_comm(self, payload):
        recipient = payload.get("recipient", "")
        body = payload.get("body", "")
        
        # 1. Bias Check
        for term in self.bias_terms:
            if term in body.lower():
                return False, f"Policy Violation: Non-inclusive language detected ('{term}'). Please rephrase.", payload

        # 2. PII Check
        # If sending to external domain (not @company.com)
        if not recipient.endswith("@company.com"):
            redacted_body = body
            redacted_count = 0
            for label, pattern in self.pii_patterns.items():
                # Don't redact the recipient's own email if it appears in body, but redact others
                matches = re.findall(pattern, body)
                for m in matches:
                    if m != recipient:
                        redacted_body = redacted_body.replace(m, f"[{label.upper()}_REDACTED]")
                        redacted_count += 1
            
            if redacted_count > 0:
                payload["body"] = redacted_body
                return True, f"Modifying Intent: Redacted {redacted_count} PII fields for external transmission.", payload

        return True, "Communication Approved", payload

    def _check_offer_cap(self, payload):
        role = payload.get("role")
        salary = payload.get("salary")
        
        # Load bands (mock)
        bands = {
            "L3": 140000,
            "L4": 180000,
            "L5": 240000
        }
        
        cap = bands.get(role, 100000)
        if salary > cap:
            return False, f"Policy Violation: Offer ${salary} exceeds cap ${cap} for role {role}.", payload
            
        return True, "Offer Approved", payload

    def _check_expense(self, payload):
        amount = payload.get("amount", 0)
        category = payload.get("category", "General")
        has_receipt = payload.get("has_receipt", False)
        
        if amount > 50 and not has_receipt:
            return False, "Policy Violation: Expenses > $50 require a receipt.", payload
            
        return True, "Expense Approved", payload

    def _check_legal_status(self, payload):
        i9_status = payload.get("i9_status")
        if i9_status != "verified":
             return False, "Legal Violation: Cannot onboard without verified I-9.", payload
        return True, "Onboarding Approved", payload
