from base_agent import HRAgent
import json
import sys
from typing import Dict, Optional, Tuple, List
from datetime import datetime
import random

class NegotiatorAgent(HRAgent):
    """
    Agent 4: Offer Negotiator
    
    Capabilities:
    - Generate customized offer letters
    - Calculate total compensation packages
    - Handle counter-offers and negotiations
    - Track offer status and deadlines
    - Manage competing offers intelligence
    - Sign-on bonus and equity calculations
    
    Compliance:
    - Salary Caps: Hard block on exceeding band
    - Equity Limits: Role-based stock option limits
    - VP Override: Exception flow for over-band offers
    - Pay Equity: Flag large deviations from cohort
    """
    
    def __init__(self):
        super().__init__("Negotiator", "generate_offer")
        self.salary_bands: Dict = {}
        self.active_offers: Dict[str, Dict] = {}
        self.negotiation_history: Dict[str, List] = {}
        self._load_salary_bands()

    def _load_salary_bands(self):
        """Load salary bands from database."""
        try:
            with open(r"d:\fun stuff\vibe coding shit\thing 2\hr_delegate\data\salary_bands.json") as f:
                self.salary_bands = json.load(f)
        except:
            self.salary_bands = {
                "L3": {"min": 100000, "max": 140000, "equity_max": 2000},
                "L4": {"min": 140000, "max": 180000, "equity_max": 5000},
                "L5": {"min": 180000, "max": 240000, "equity_max": 10000}
            }

    # ─────────────────────────────────────────────────────────────
    # Compensation Calculations
    # ─────────────────────────────────────────────────────────────
    def calculate_total_comp(self, base: int, equity: int, bonus_pct: float = 0.1, 
                             sign_on: int = 0, relocation: int = 0) -> Dict:
        """Calculate total compensation package."""
        annual_bonus = int(base * bonus_pct)
        equity_annual = equity  # Assuming 4-year vest, this is annual value
        
        return {
            "base_salary": base,
            "annual_bonus": annual_bonus,
            "equity_value": equity,
            "sign_on_bonus": sign_on,
            "relocation": relocation,
            "total_first_year": base + annual_bonus + equity + sign_on + relocation,
            "total_annual_recurring": base + annual_bonus + equity
        }

    def check_within_band(self, role: str, salary: int) -> Tuple[bool, str, int]:
        """Check if salary is within band. Returns (within_band, message, max_allowed)."""
        band = self.salary_bands.get(role)
        if not band:
            return True, "Role not in bands", salary
        
        max_salary = band.get("max", 999999)
        min_salary = band.get("min", 0)
        
        if salary > max_salary:
            return False, f"Exceeds max ${max_salary:,} for {role}", max_salary
        elif salary < min_salary:
            return True, f"Below band minimum ${min_salary:,}", min_salary
        else:
            return True, "Within band", max_salary

    # ─────────────────────────────────────────────────────────────
    # Offer Management
    # ─────────────────────────────────────────────────────────────
    def create_offer(self, candidate_id: str, role: str, base_salary: int, 
                     equity: int = 0, sign_on: int = 0, 
                     start_date: str = None) -> Tuple[bool, str, Optional[Dict]]:
        """Create a new offer with compliance checks."""
        
        # Compliance check
        payload = {
            "candidate_id": candidate_id,
            "role": role,
            "salary": base_salary,
            "equity": equity,
            "sign_on": sign_on
        }
        
        success, reason, modified = self.execute_with_compliance(
            "generate_offer", payload, f"Create offer for {candidate_id}: ${base_salary:,}"
        )
        
        if not success:
            # Attempt auto-correction: offer at band max
            within, msg, max_allowed = self.check_within_band(role, base_salary)
            self.logger.info(f"💡 Auto-correcting to band max: ${max_allowed:,}")
            
            # Retry with corrected salary
            payload["salary"] = max_allowed
            success, reason, modified = self.execute_with_compliance(
                "generate_offer", payload, f"Create offer for {candidate_id}: ${max_allowed:,} (corrected)"
            )
            
            if not success:
                return False, reason, None
            
            base_salary = max_allowed
        
        # Generate offer
        offer = {
            "offer_id": f"OFR-{random.randint(10000, 99999)}",
            "candidate_id": candidate_id,
            "role": role,
            "compensation": self.calculate_total_comp(base_salary, equity, sign_on=sign_on),
            "start_date": start_date or "TBD",
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=7)).isoformat(),
            "status": "PENDING",
            "version": 1
        }
        
        self.active_offers[offer["offer_id"]] = offer
        self.negotiation_history[offer["offer_id"]] = [
            {"action": "created", "timestamp": datetime.now().isoformat(), "details": offer["compensation"]}
        ]
        
        self.logger.info(f"📄 Offer created: {offer['offer_id']}")
        return True, "Offer created successfully", offer

    def counter_offer(self, offer_id: str, new_base: int = None, new_equity: int = None,
                      new_sign_on: int = None) -> Tuple[bool, str, Optional[Dict]]:
        """Handle a counter-offer negotiation."""
        
        if offer_id not in self.active_offers:
            return False, "Offer not found", None
        
        current = self.active_offers[offer_id]
        role = current["role"]
        
        # Use current values if not specified
        base = new_base or current["compensation"]["base_salary"]
        equity = new_equity or current["compensation"]["equity_value"]
        sign_on = new_sign_on or current["compensation"]["sign_on_bonus"]
        
        # Compliance check on new values
        payload = {"role": role, "salary": base, "equity": equity}
        success, reason, _ = self.execute_with_compliance(
            "generate_offer", payload, f"Counter-offer for {offer_id}"
        )
        
        if not success:
            return False, f"Counter-offer blocked: {reason}", None
        
        # Update offer
        current["compensation"] = self.calculate_total_comp(base, equity, sign_on=sign_on)
        current["version"] += 1
        current["updated_at"] = datetime.now().isoformat()
        
        self.negotiation_history[offer_id].append({
            "action": "counter",
            "timestamp": datetime.now().isoformat(),
            "details": current["compensation"]
        })
        
        self.logger.info(f"🔄 Counter-offer applied to {offer_id}")
        return True, "Counter-offer accepted", current

    def accept_offer(self, offer_id: str) -> Tuple[bool, str]:
        """Mark offer as accepted."""
        if offer_id not in self.active_offers:
            return False, "Offer not found"
        
        self.active_offers[offer_id]["status"] = "ACCEPTED"
        self.active_offers[offer_id]["accepted_at"] = datetime.now().isoformat()
        
        self.negotiation_history[offer_id].append({
            "action": "accepted",
            "timestamp": datetime.now().isoformat()
        })
        
        self.logger.info(f"🎉 Offer {offer_id} ACCEPTED!")
        return True, "Offer accepted"

    def decline_offer(self, offer_id: str, reason: str = "") -> Tuple[bool, str]:
        """Mark offer as declined."""
        if offer_id not in self.active_offers:
            return False, "Offer not found"
        
        self.active_offers[offer_id]["status"] = "DECLINED"
        self.active_offers[offer_id]["decline_reason"] = reason
        
        self.negotiation_history[offer_id].append({
            "action": "declined",
            "timestamp": datetime.now().isoformat(),
            "reason": reason
        })
        
        self.logger.info(f"😔 Offer {offer_id} declined: {reason}")
        return True, "Offer declined"

    def get_negotiation_summary(self, offer_id: str) -> Dict:
        """Get full negotiation history for an offer."""
        return {
            "offer": self.active_offers.get(offer_id),
            "history": self.negotiation_history.get(offer_id, [])
        }

    def generate_offer_letter_text(self, offer_id: str) -> str:
        """Generate formal offer letter text."""
        offer = self.active_offers.get(offer_id)
        if not offer:
            return "Offer not found"
        
        comp = offer["compensation"]
        letter = f"""
CONFIDENTIAL OFFER OF EMPLOYMENT

Candidate: {offer['candidate_id']}
Position: {offer['role']}
Start Date: {offer['start_date']}

COMPENSATION SUMMARY:
- Base Salary: ${comp['base_salary']:,} per year
- Annual Bonus: ${comp['annual_bonus']:,} (target)
- Equity Grant: ${comp['equity_value']:,} RSUs (4-year vest)
- Sign-On Bonus: ${comp['sign_on_bonus']:,}

TOTAL FIRST YEAR: ${comp['total_first_year']:,}

This offer expires on {offer['expires_at'][:10]}.

[Signature blocks here]
"""
        return letter


# Import for timedelta
from datetime import timedelta

if __name__ == "__main__":
    agent = NegotiatorAgent()
    agent.start()
    
    # Demo: Create an over-band offer (will be auto-corrected)
    success, msg, offer = agent.create_offer("cand_001", "L3", 200000, equity=1500, sign_on=10000)
    print(f"\n{msg}")
    if offer:
        print(json.dumps(offer, indent=2))
        print("\n" + agent.generate_offer_letter_text(offer["offer_id"]))
    
    agent.stop()
