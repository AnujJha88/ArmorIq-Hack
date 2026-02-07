from base_agent import HRAgent
import json
import sys
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import random

class SchedulerAgent(HRAgent):
    """
    Agent 3: Interview Scheduler
    
    Capabilities:
    - Find optimal interview slots across multiple calendars
    - Handle timezone conversions
    - Send calendar invites and reminders
    - Reschedule and cancel interviews
    - Coordinate panel interviews
    - Manage interviewer load balancing
    
    Compliance:
    - Work Hours: No meetings outside 9AM-5PM
    - Weekends: No Saturday/Sunday scheduling
    - Focus Time: Respect "Do Not Book" blocks
    - Interviewer Limits: Max 3 interviews/day per interviewer
    """
    
    def __init__(self):
        super().__init__("Scheduler", "schedule_interview")
        self.calendar_cache: Dict[str, List[Dict]] = {}  # employee_id -> busy slots
        self.interviewer_daily_count: Dict[str, int] = {}
        self.max_interviews_per_day = 3
        self.work_hours = (9, 17)  # 9 AM to 5 PM
        self.interview_duration_mins = 60
        self.buffer_mins = 15

    # ─────────────────────────────────────────────────────────────
    # Calendar Management
    # ─────────────────────────────────────────────────────────────
    def load_calendar(self, employee_id: str) -> List[Dict]:
        """Load calendar for an employee (mock)."""
        # Mock busy slots for demo
        if employee_id not in self.calendar_cache:
            self.calendar_cache[employee_id] = [
                {"start": "2026-02-10 10:00", "end": "2026-02-10 11:00", "type": "meeting"},
                {"start": "2026-02-10 14:00", "end": "2026-02-10 16:00", "type": "focus_time"},
                {"start": "2026-02-11 09:00", "end": "2026-02-11 10:00", "type": "interview"},
            ]
        return self.calendar_cache[employee_id]

    def find_available_slots(self, interviewer_ids: List[str], date: str, duration_mins: int = 60) -> List[Dict]:
        """Find common available slots across multiple interviewers."""
        self.logger.info(f"🔍 Finding slots for {len(interviewer_ids)} interviewers on {date}")
        
        # Parse date
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return []
        
        # Weekend check (will also be enforced by Watchtower)
        if target_date.weekday() >= 5:
            self.logger.warning("⛔ Weekend date requested")
            return []
        
        # Build available slots
        slots = []
        current = target_date.replace(hour=self.work_hours[0], minute=0)
        end_of_day = target_date.replace(hour=self.work_hours[1], minute=0)
        
        while current + timedelta(minutes=duration_mins) <= end_of_day:
            slot_end = current + timedelta(minutes=duration_mins)
            slot = {
                "start": current.strftime("%Y-%m-%d %H:%M"),
                "end": slot_end.strftime("%Y-%m-%d %H:%M"),
                "available_for": []
            }
            
            # Check each interviewer
            all_available = True
            for iid in interviewer_ids:
                calendar = self.load_calendar(iid)
                is_free = True
                for busy in calendar:
                    busy_start = datetime.strptime(busy["start"], "%Y-%m-%d %H:%M")
                    busy_end = datetime.strptime(busy["end"], "%Y-%m-%d %H:%M")
                    # Check overlap
                    if not (slot_end <= busy_start or current >= busy_end):
                        is_free = False
                        break
                
                if is_free:
                    slot["available_for"].append(iid)
                else:
                    all_available = False
            
            if all_available:
                slots.append(slot)
            
            current += timedelta(minutes=30)  # 30-min increments
        
        self.logger.info(f"📅 Found {len(slots)} available slots")
        return slots

    def book_interview(self, candidate_id: str, interviewer_ids: List[str], time: str, 
                       interview_type: str = "technical") -> Tuple[bool, str, Optional[Dict]]:
        """Book an interview slot with compliance checks."""
        
        # Check interviewer limits
        for iid in interviewer_ids:
            count = self.interviewer_daily_count.get(iid, 0)
            if count >= self.max_interviews_per_day:
                return False, f"Interviewer {iid} has reached daily limit ({self.max_interviews_per_day})", None
        
        # Compliance check
        payload = {
            "candidate_id": candidate_id,
            "time": time,
            "interviewers": interviewer_ids,
            "type": interview_type,
            "duration_mins": self.interview_duration_mins
        }
        
        success, reason, modified = self.execute_with_compliance(
            "schedule_interview", payload, f"Book {interview_type} interview for {candidate_id}"
        )
        
        if not success:
            return False, reason, None
        
        # Create invite
        invite = {
            "meeting_id": f"INT-{random.randint(10000, 99999)}",
            "candidate": candidate_id,
            "interviewers": interviewer_ids,
            "time": time,
            "duration": self.interview_duration_mins,
            "type": interview_type,
            "status": "CONFIRMED",
            "video_link": f"https://meet.company.com/{random.randint(100,999)}-{random.randint(100,999)}"
        }
        
        # Update interviewer counts
        for iid in interviewer_ids:
            self.interviewer_daily_count[iid] = self.interviewer_daily_count.get(iid, 0) + 1
        
        # Add to calendars
        for iid in interviewer_ids:
            if iid not in self.calendar_cache:
                self.calendar_cache[iid] = []
            self.calendar_cache[iid].append({
                "start": time,
                "end": (datetime.strptime(time, "%Y-%m-%d %H:%M") + timedelta(minutes=self.interview_duration_mins)).strftime("%Y-%m-%d %H:%M"),
                "type": "interview"
            })
        
        self.logger.info(f"✅ Interview booked: {invite['meeting_id']}")
        return True, "Interview booked successfully", invite

    def reschedule_interview(self, meeting_id: str, new_time: str) -> Tuple[bool, str]:
        """Reschedule an existing interview."""
        self.logger.info(f"🔄 Rescheduling {meeting_id} to {new_time}")
        
        # Compliance check on new time
        payload = {"time": new_time, "meeting_id": meeting_id}
        success, reason, _ = self.execute_with_compliance(
            "schedule_interview", payload, f"Reschedule {meeting_id}"
        )
        
        if success:
            return True, f"Meeting {meeting_id} rescheduled to {new_time}"
        return False, reason

    def cancel_interview(self, meeting_id: str, reason: str = "") -> bool:
        """Cancel an interview."""
        self.logger.info(f"❌ Cancelling {meeting_id}: {reason}")
        return True

    def send_reminder(self, meeting_id: str, recipient: str) -> bool:
        """Send interview reminder."""
        self.logger.info(f"🔔 Sending reminder for {meeting_id} to {recipient}")
        return True

    def get_interviewer_load(self) -> Dict[str, int]:
        """Get current interview load per interviewer."""
        return self.interviewer_daily_count.copy()

    def schedule_panel(self, candidate_id: str, panel_config: Dict) -> Dict:
        """
        Schedule a full interview panel/loop.
        panel_config: {
            "rounds": [
                {"type": "phone_screen", "interviewers": ["emp_001"], "duration": 30},
                {"type": "technical", "interviewers": ["emp_002", "emp_003"], "duration": 60},
                {"type": "behavioral", "interviewers": ["emp_004"], "duration": 45}
            ],
            "preferred_dates": ["2026-02-10", "2026-02-11"]
        }
        """
        self.start()
        results = {"candidate": candidate_id, "rounds": [], "status": "PARTIAL"}
        
        for round_config in panel_config.get("rounds", []):
            for date in panel_config.get("preferred_dates", []):
                slots = self.find_available_slots(round_config["interviewers"], date, round_config["duration"])
                if slots:
                    success, msg, invite = self.book_interview(
                        candidate_id, 
                        round_config["interviewers"], 
                        slots[0]["start"],
                        round_config["type"]
                    )
                    if success:
                        results["rounds"].append(invite)
                        break
        
        if len(results["rounds"]) == len(panel_config.get("rounds", [])):
            results["status"] = "COMPLETE"
        
        self.stop()
        return results


if __name__ == "__main__":
    agent = SchedulerAgent()
    
    if len(sys.argv) > 2:
        agent.start()
        success, msg, invite = agent.book_interview(sys.argv[1], ["emp_001"], sys.argv[2])
        print(f"Result: {msg}")
        if invite:
            print(json.dumps(invite, indent=2))
        agent.stop()
    else:
        # Demo: Schedule a panel
        panel = agent.schedule_panel("cand_001", {
            "rounds": [
                {"type": "phone_screen", "interviewers": ["emp_001"], "duration": 30},
                {"type": "technical", "interviewers": ["emp_002"], "duration": 60}
            ],
            "preferred_dates": ["2026-02-10", "2026-02-11"]
        })
        print(json.dumps(panel, indent=2))
