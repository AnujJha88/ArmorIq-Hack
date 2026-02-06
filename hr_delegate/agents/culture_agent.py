from base_agent import HRAgent
import json, sys, random
from typing import Dict, List, Tuple
from datetime import datetime

class CultureAgent(HRAgent):
    """Agent 11: Culture/Events - Plans offsites, team events, and ensures safety compliance."""
    
    def __init__(self):
        super().__init__("Culture", "book_venue")
        self.events: Dict[str, Dict] = {}
        self.approved_venues: List[str] = ["The Grand Ballroom", "Tech Hub Conference", "Rooftop Lounge"]
        self.vendor_insurance: Dict[str, bool] = {"The Grand Ballroom": True, "Dive Bar": False}

    def plan_event(self, event_name: str, event_type: str, date: str, 
                   expected_attendees: int, budget: int) -> Dict:
        event = {"id": f"EVT-{random.randint(1000,9999)}", "name": event_name, "type": event_type,
                 "date": date, "attendees": expected_attendees, "budget": budget,
                 "venue": None, "catering": None, "status": "PLANNING"}
        self.events[event["id"]] = event
        self.logger.info(f"🎉 Event created: {event['id']} - {event_name}")
        return event

    def book_venue(self, event_id: str, venue_name: str, has_insurance: bool,
                   alcohol_service: bool = False) -> Tuple[bool, str]:
        event = self.events.get(event_id)
        if not event:
            return False, "Event not found"
        
        # Compliance: Insurance check
        if not has_insurance and not self.vendor_insurance.get(venue_name, False):
            payload = {"event_id": event_id, "venue_name": venue_name, 
                       "has_liability_insurance": False, "alcohol_service": alcohol_service}
            success, reason, _ = self.execute_with_compliance("book_venue", payload, 
                                                              f"Book {venue_name}")
            if not success:
                return False, f"Venue rejected: {reason}"
        
        # Compliance: Alcohol requires licensed service
        if alcohol_service:
            self.logger.warning("🍺 Alcohol service requires licensed bartender confirmation")
        
        event["venue"] = venue_name
        event["status"] = "VENUE_BOOKED"
        self.logger.info(f"📍 Venue booked: {venue_name}")
        return True, f"Venue {venue_name} booked successfully"

    def order_catering(self, event_id: str, vendor: str, menu_type: str, 
                       per_head_cost: float) -> Tuple[bool, str]:
        event = self.events.get(event_id)
        if not event:
            return False, "Event not found"
        
        total_cost = per_head_cost * event["attendees"]
        if total_cost > event["budget"] * 0.6:  # Catering should be < 60% of budget
            return False, f"Catering cost (${total_cost:.0f}) exceeds 60% of budget (${event['budget']})"
        
        event["catering"] = {"vendor": vendor, "menu": menu_type, "cost": total_cost}
        self.logger.info(f"🍽️ Catering ordered: ${total_cost:.0f}")
        return True, f"Catering confirmed: ${total_cost:.0f}"

    def send_invites(self, event_id: str, employee_list: List[str]) -> int:
        event = self.events.get(event_id)
        if not event:
            return 0
        self.logger.info(f"📧 Invites sent to {len(employee_list)} employees")
        return len(employee_list)

    def get_event_summary(self, event_id: str) -> Dict:
        event = self.events.get(event_id)
        if not event:
            return {"error": "Not found"}
        catering_cost = event.get("catering", {}).get("cost", 0)
        return {"event": event["name"], "date": event["date"], "venue": event["venue"],
                "budget": event["budget"], "spent": catering_cost, "status": event["status"]}

if __name__ == "__main__":
    agent = CultureAgent()
    agent.start()
    
    event = agent.plan_event("Summer Offsite", "team_building", "2026-07-15", 50, 10000)
    print("Venue (no insurance):", agent.book_venue(event["id"], "Dive Bar", False, True))
    print("Venue (insured):", agent.book_venue(event["id"], "The Grand Ballroom", True, True))
    print("Catering:", agent.order_catering(event["id"], "Gourmet Co", "Buffet", 45))
    print("Summary:", json.dumps(agent.get_event_summary(event["id"]), indent=2))
    agent.stop()
