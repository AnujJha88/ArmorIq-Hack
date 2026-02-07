"""
HR Agent
========
Handles hiring, onboarding, payroll, benefits.
"""

from typing import Dict, Any
from .base_agent import EnterpriseAgent, AgentConfig, AgentCapability
from ..compliance.policies.base import PolicyCategory


class HRAgent(EnterpriseAgent):
    """
    HR domain agent.

    Capabilities:
    - Candidate sourcing and screening
    - Interview scheduling
    - Offer generation
    - I-9 verification
    - Onboarding and offboarding
    - Payroll processing
    """

    SALARY_BANDS = {
        "L1": (50000, 75000),
        "L2": (65000, 95000),
        "L3": (85000, 125000),
        "L4": (110000, 165000),
        "L5": (145000, 210000),
        "L6": (180000, 280000),
    }

    def __init__(self):
        config = AgentConfig(
            name="HR",
            agent_type="hr",
            capabilities={
                AgentCapability.SEARCH_CANDIDATES,
                AgentCapability.SCREEN_RESUME,
                AgentCapability.SCHEDULE_INTERVIEW,
                AgentCapability.GENERATE_OFFER,
                AgentCapability.VERIFY_I9,
                AgentCapability.ONBOARD_EMPLOYEE,
                AgentCapability.OFFBOARD_EMPLOYEE,
                AgentCapability.PROCESS_PAYROLL,
            },
            policy_categories=[
                PolicyCategory.HIRING_COMPLIANCE,
                PolicyCategory.COMPENSATION,
                PolicyCategory.TERMINATION,
                PolicyCategory.PII_PROTECTION,
            ],
            description="Handles HR operations including hiring, onboarding, and payroll",
        )
        super().__init__(config)

    async def _execute_action(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute HR action."""
        action_lower = action.lower()

        if "candidate" in action_lower or "search" in action_lower:
            return await self._search_candidates(payload)
        elif "screen" in action_lower or "resume" in action_lower:
            return await self._screen_resume(payload)
        elif "schedule" in action_lower or "interview" in action_lower:
            return await self._schedule_interview(payload)
        elif "offer" in action_lower:
            return await self._generate_offer(payload)
        elif "i9" in action_lower or "verify" in action_lower:
            return await self._verify_i9(payload)
        elif "onboard" in action_lower:
            return await self._onboard_employee(payload)
        elif "offboard" in action_lower:
            return await self._offboard_employee(payload)
        elif "payroll" in action_lower:
            return await self._process_payroll(payload)
        else:
            return {"status": "completed", "action": action}

    async def _search_candidates(self, payload: Dict) -> Dict:
        """Search for candidates."""
        role = payload.get("role", "")
        skills = payload.get("skills", [])
        count = payload.get("count", 10)

        return {
            "status": "completed",
            "search_id": f"SRC-{self._action_count:06d}",
            "role": role,
            "skills_matched": skills,
            "candidates_found": count,
            "candidates": [{"id": f"CND-{i:04d}", "match_score": 0.8 - i * 0.05} for i in range(min(count, 5))],
        }

    async def _screen_resume(self, payload: Dict) -> Dict:
        """Screen a resume."""
        candidate_id = payload.get("candidate_id", "")
        criteria = payload.get("criteria", [])

        return {
            "status": "screened",
            "candidate_id": candidate_id,
            "criteria_met": criteria,
            "overall_score": 0.85,
            "recommendation": "proceed",
            "notes": "Strong technical background",
        }

    async def _schedule_interview(self, payload: Dict) -> Dict:
        """Schedule an interview."""
        candidate_id = payload.get("candidate_id", "")
        interviewer = payload.get("interviewer", "Hiring Manager")
        time = payload.get("time", "TBD")

        return {
            "status": "scheduled",
            "interview_id": f"INT-{self._action_count:06d}",
            "candidate_id": candidate_id,
            "interviewer": interviewer,
            "scheduled_time": time,
            "calendar_invite_sent": True,
        }

    async def _generate_offer(self, payload: Dict) -> Dict:
        """Generate a job offer."""
        candidate_id = payload.get("candidate_id", "")
        role = payload.get("role", "")
        level = payload.get("level", "L3")
        salary = payload.get("salary", 100000)

        # Check salary band
        band = self.SALARY_BANDS.get(level, (0, float("inf")))
        in_band = band[0] <= salary <= band[1]

        return {
            "status": "generated",
            "offer_id": f"OFR-{self._action_count:06d}",
            "candidate_id": candidate_id,
            "role": role,
            "level": level,
            "salary": salary,
            "salary_in_band": in_band,
            "band_range": band,
            "equity_included": level in ["L4", "L5", "L6"],
        }

    async def _verify_i9(self, payload: Dict) -> Dict:
        """Verify I-9 documentation."""
        employee_id = payload.get("employee_id", "")
        documents = payload.get("documents", [])

        return {
            "status": "verified",
            "verification_id": f"I9V-{self._action_count:06d}",
            "employee_id": employee_id,
            "documents_verified": len(documents),
            "i9_status": "verified",
            "everify_submitted": True,
        }

    async def _onboard_employee(self, payload: Dict) -> Dict:
        """Onboard a new employee."""
        employee_id = payload.get("employee_id", "")
        start_date = payload.get("start_date", "")
        department = payload.get("department", "")

        return {
            "status": "onboarded",
            "onboarding_id": f"ONB-{self._action_count:06d}",
            "employee_id": employee_id,
            "start_date": start_date,
            "department": department,
            "equipment_ordered": True,
            "accounts_created": True,
            "training_scheduled": True,
        }

    async def _offboard_employee(self, payload: Dict) -> Dict:
        """Offboard an employee."""
        employee_id = payload.get("employee_id", "")
        last_day = payload.get("last_day", "")
        reason = payload.get("reason", "voluntary")

        return {
            "status": "offboarded",
            "offboarding_id": f"OFF-{self._action_count:06d}",
            "employee_id": employee_id,
            "last_day": last_day,
            "reason": reason,
            "access_revoked": True,
            "equipment_returned": False,
            "exit_interview_scheduled": True,
        }

    async def _process_payroll(self, payload: Dict) -> Dict:
        """Process payroll."""
        period = payload.get("period", "current")
        department = payload.get("department", "all")

        return {
            "status": "processed",
            "payroll_id": f"PAY-{self._action_count:06d}",
            "period": period,
            "department": department,
            "employees_processed": 50,
            "total_amount": 500000,
        }
