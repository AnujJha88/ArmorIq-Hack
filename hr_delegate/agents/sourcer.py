from base_agent import HRAgent
import json
import sys
import os
from typing import List, Dict, Optional
from datetime import datetime

# Compute data directory relative to this file
_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

class SourcerAgent(HRAgent):
    """
    Agent 1: Talent Sourcer
    
    Capabilities:
    - Search candidate databases by skills/keywords
    - Send personalized outreach campaigns
    - Track response rates and optimize messaging
    - Manage "Do Not Contact" lists
    - Rate limiting to prevent spam
    
    Compliance:
    - Anti-Spam: Max 50 emails/day, must include opt-out
    - PII: Redact sensitive info for external comms
    - Bias: Block exclusionary language in outreach
    """
    
    def __init__(self):
        super().__init__("Sourcer", "send_email")
        self.daily_email_count = 0
        self.max_daily_emails = 50
        self.do_not_contact: List[str] = []
        self.outreach_templates: Dict[str, str] = {
            "cold": "Hi {name}, I noticed your experience in {skill}. We have an exciting opportunity...",
            "warm": "Hi {name}, We spoke previously about {topic}. I wanted to follow up...",
            "referral": "Hi {name}, {referrer} suggested I reach out about a role at our company..."
        }

    # ─────────────────────────────────────────────────────────────
    # Core Capabilities
    # ─────────────────────────────────────────────────────────────
    def search_candidates(self, keywords: List[str], filters: Optional[Dict] = None) -> List[Dict]:
        """Search candidate database with optional filters."""
        self.logger.info(f"🔍 Searching candidates: keywords={keywords}, filters={filters}")
        
        # Load mock data
        with open(os.path.join(_DATA_DIR, "resumes.json")) as f:
            candidates = json.load(f)
        
        results = []
        for c in candidates:
            skill_match = any(k.lower() in str(c.get("skills", [])).lower() for k in keywords)
            if skill_match:
                # Apply filters
                if filters:
                    if filters.get("min_experience") and c.get("experience_years", 0) < filters["min_experience"]:
                        continue
                    if filters.get("max_salary") and c.get("salary_expectation", 0) > filters["max_salary"]:
                        continue
                results.append(c)
        
        self.logger.info(f"📊 Found {len(results)} candidates matching criteria")
        return results

    def craft_outreach(self, candidate: Dict, template_type: str = "cold", custom_vars: Dict = None) -> str:
        """Generate personalized outreach message."""
        template = self.outreach_templates.get(template_type, self.outreach_templates["cold"])
        
        # Default variables
        variables = {
            "name": candidate.get("name", "there").split()[0],
            "skill": candidate.get("skills", ["your field"])[0],
            "topic": "opportunities",
            "referrer": "A colleague"
        }
        if custom_vars:
            variables.update(custom_vars)
        
        message = template.format(**variables)
        
        # Always append opt-out (compliance requirement)
        message += "\n\n---\nTo unsubscribe from future messages, reply STOP."
        
        return message

    def send_outreach(self, recipient_email: str, subject: str, body: str) -> Tuple[bool, str]:
        """Send outreach email with full compliance checks."""
        
        # Pre-check: Rate limit
        if self.daily_email_count >= self.max_daily_emails:
            self.logger.warning(f"🚫 Daily email limit ({self.max_daily_emails}) reached")
            return False, "Rate limit exceeded. Try again tomorrow."
        
        # Pre-check: Do Not Contact
        if recipient_email.lower() in [e.lower() for e in self.do_not_contact]:
            self.logger.warning(f"🚫 {recipient_email} is on Do Not Contact list")
            return False, "Recipient has opted out of communications."
        
        # Compliance check via Watchtower
        payload = {
            "recipient": recipient_email,
            "subject": subject,
            "body": body
        }
        
        success, reason, modified_payload = self.execute_with_compliance(
            "send_email", payload, f"Outreach to {recipient_email}"
        )
        
        if success:
            self.daily_email_count += 1
            self.logger.info(f"📧 Email sent ({self.daily_email_count}/{self.max_daily_emails} today)")
            # If body was modified (PII redacted), log it
            if modified_payload.get("body") != body:
                self.logger.info("📝 Body was auto-redacted by compliance engine")
            return True, "Email sent successfully"
        else:
            return False, reason

    def run_campaign(self, keywords: List[str], template_type: str = "cold", max_sends: int = 10) -> Dict:
        """Execute a full outreach campaign."""
        self.start()
        
        results = {
            "searched": 0,
            "sent": 0,
            "blocked": 0,
            "errors": []
        }
        
        candidates = self.search_candidates(keywords)
        results["searched"] = len(candidates)
        
        for candidate in candidates[:max_sends]:
            email = candidate.get("email")
            if not email:
                continue
                
            body = self.craft_outreach(candidate, template_type)
            success, msg = self.send_outreach(email, "Exciting Opportunity", body)
            
            if success:
                results["sent"] += 1
            else:
                results["blocked"] += 1
                results["errors"].append({"email": email, "reason": msg})
        
        self.logger.info(f"📊 Campaign Complete: {results}")
        self.stop()
        return results

    def add_to_dnc(self, email: str):
        """Add email to Do Not Contact list."""
        if email.lower() not in [e.lower() for e in self.do_not_contact]:
            self.do_not_contact.append(email.lower())
            self.logger.info(f"➖ Added {email} to DNC list")

    def get_campaign_stats(self) -> Dict:
        """Return daily campaign statistics."""
        return {
            "emails_sent_today": self.daily_email_count,
            "remaining_quota": self.max_daily_emails - self.daily_email_count,
            "dnc_list_size": len(self.do_not_contact),
            "audit_summary": self.get_audit_summary()
        }


# For compatibility with simple CLI usage
from typing import Tuple

if __name__ == "__main__":
    agent = SourcerAgent()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "campaign":
            keywords = sys.argv[2].split(",") if len(sys.argv) > 2 else ["Python"]
            agent.run_campaign(keywords)
        elif sys.argv[1] == "search":
            agent.start()
            results = agent.search_candidates(sys.argv[2].split(",") if len(sys.argv) > 2 else ["Python"])
            print(json.dumps(results, indent=2))
            agent.stop()
    else:
        # Demo run
        agent.run_campaign(["Python", "React"], max_sends=3)
