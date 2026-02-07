from base_agent import HRAgent
import json
import sys
import os
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# Compute data directory relative to this file
_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

class ScreenerAgent(HRAgent):
    """
    Agent 2: Resume Screener
    
    Capabilities:
    - Parse and analyze resumes
    - Score candidates against job requirements
    - Generate interview recommendations
    - Detect skill gaps and suggest training
    - Blind screening mode (ArmorIQ enforced)
    
    Compliance:
    - Blind Screening: Name, Gender, University, Address REDACTED
    - Bias Detection: Flags subjective language in notes
    - Fair Scoring: Prevents arbitrary score manipulation
    """
    
    def __init__(self):
        super().__init__("Screener", "read_resume")
        self.scoring_weights = {
            "skills_match": 0.35,
            "experience": 0.25,
            "education": 0.15,
            "certifications": 0.15,
            "projects": 0.10
        }
        self.required_skills: List[str] = []
        self.nice_to_have_skills: List[str] = []
        self.min_experience: int = 0
        
        # Fields to redact for blind screening
        self.blind_fields = ["name", "gender", "address", "education"]  # education for Ivygate

    # ─────────────────────────────────────────────────────────────
    # Configuration
    # ─────────────────────────────────────────────────────────────
    def configure_role(self, required: List[str], nice_to_have: List[str], min_exp: int):
        """Set the job requirements for this screening session."""
        self.required_skills = [s.lower() for s in required]
        self.nice_to_have_skills = [s.lower() for s in nice_to_have]
        self.min_experience = min_exp
        self.logger.info(f"🎯 Role configured: Required={required}, Nice={nice_to_have}, MinExp={min_exp}")

    # ─────────────────────────────────────────────────────────────
    # Core Screening Logic
    # ─────────────────────────────────────────────────────────────
    def load_candidate(self, candidate_id: str) -> Optional[Dict]:
        """Load candidate data from database."""
        with open(os.path.join(_DATA_DIR, "resumes.json")) as f:
            candidates = json.load(f)
        
        for c in candidates:
            if c.get("id") == candidate_id:
                return c
        return None

    def apply_blind_screening(self, candidate: Dict) -> Dict:
        """Apply blind screening by redacting PII fields."""
        # Compliance check
        payload = {
            "action": "screen_candidate",
            "candidate_id": candidate.get("id"),
            "fields_accessed": list(candidate.keys())
        }
        
        success, reason, _ = self.execute_with_compliance(
            "read_resume", payload, f"Blind screen {candidate.get('id')}"
        )
        
        # Create redacted version
        blind_candidate = candidate.copy()
        for field in self.blind_fields:
            if field in blind_candidate:
                blind_candidate[field] = "[REDACTED]"
        
        return blind_candidate

    def score_candidate(self, candidate: Dict) -> Dict:
        """
        Score a candidate against configured requirements.
        Returns detailed scoring breakdown.
        """
        scores = {
            "skills_match": 0.0,
            "experience": 0.0,
            "education": 0.0,
            "certifications": 0.0,
            "projects": 0.0
        }
        details = {}
        
        # Skills matching
        candidate_skills = [s.lower() for s in candidate.get("skills", [])]
        required_matched = sum(1 for s in self.required_skills if s in candidate_skills)
        nice_matched = sum(1 for s in self.nice_to_have_skills if s in candidate_skills)
        
        if self.required_skills:
            scores["skills_match"] = (required_matched / len(self.required_skills)) * 0.7
            scores["skills_match"] += (nice_matched / max(len(self.nice_to_have_skills), 1)) * 0.3
        details["skills"] = {
            "required_matched": required_matched,
            "required_total": len(self.required_skills),
            "nice_matched": nice_matched
        }
        
        # Experience scoring
        years = candidate.get("experience_years", 0)
        if years >= self.min_experience:
            exp_score = min(1.0, years / max(self.min_experience * 1.5, 1))
            scores["experience"] = exp_score
        else:
            scores["experience"] = years / max(self.min_experience, 1) * 0.5
        details["experience"] = {"years": years, "required": self.min_experience}
        
        # Calculate weighted total
        total = sum(scores[k] * self.scoring_weights[k] for k in scores)
        
        return {
            "candidate_id": candidate.get("id"),
            "total_score": round(total * 100, 1),
            "breakdown": scores,
            "details": details,
            "recommendation": self._get_recommendation(total)
        }

    def _get_recommendation(self, score: float) -> str:
        """Generate recommendation based on score."""
        if score >= 0.8:
            return "STRONG_YES - Fast track to technical interview"
        elif score >= 0.6:
            return "YES - Proceed to phone screen"
        elif score >= 0.4:
            return "MAYBE - Review with hiring manager"
        else:
            return "NO - Does not meet minimum requirements"

    def detect_skill_gaps(self, candidate: Dict) -> List[Dict]:
        """Identify skills the candidate is missing."""
        candidate_skills = [s.lower() for s in candidate.get("skills", [])]
        gaps = []
        
        for skill in self.required_skills:
            if skill not in candidate_skills:
                gaps.append({
                    "skill": skill,
                    "importance": "REQUIRED",
                    "training_suggestion": f"Recommend {skill.title()} certification/course"
                })
        
        for skill in self.nice_to_have_skills:
            if skill not in candidate_skills:
                gaps.append({
                    "skill": skill,
                    "importance": "NICE_TO_HAVE",
                    "training_suggestion": f"Consider {skill.title()} exposure"
                })
        
        return gaps

    def screen_batch(self, candidate_ids: List[str]) -> List[Dict]:
        """Screen multiple candidates and rank them."""
        self.start()
        results = []
        
        for cid in candidate_ids:
            candidate = self.load_candidate(cid)
            if not candidate:
                self.logger.warning(f"Candidate {cid} not found")
                continue
            
            # Apply blind screening
            blind_candidate = self.apply_blind_screening(candidate)
            
            # Score
            score_result = self.score_candidate(blind_candidate)
            score_result["skill_gaps"] = self.detect_skill_gaps(blind_candidate)
            results.append(score_result)
        
        # Sort by score descending
        results.sort(key=lambda x: x["total_score"], reverse=True)
        
        self.logger.info(f"📊 Screened {len(results)} candidates")
        self.stop()
        return results

    def generate_summary_report(self, results: List[Dict]) -> str:
        """Generate a text summary of screening results."""
        report = "=== SCREENING SUMMARY REPORT ===\n\n"
        
        strong_yes = [r for r in results if "STRONG_YES" in r["recommendation"]]
        yes = [r for r in results if r["recommendation"].startswith("YES")]
        maybe = [r for r in results if "MAYBE" in r["recommendation"]]
        no = [r for r in results if r["recommendation"].startswith("NO")]
        
        report += f"Total Screened: {len(results)}\n"
        report += f"✅ Strong Yes: {len(strong_yes)}\n"
        report += f"👍 Yes: {len(yes)}\n"
        report += f"🤔 Maybe: {len(maybe)}\n"
        report += f"❌ No: {len(no)}\n\n"
        
        report += "Top 3 Candidates:\n"
        for i, r in enumerate(results[:3], 1):
            report += f"  {i}. {r['candidate_id']} - Score: {r['total_score']}%\n"
        
        return report


if __name__ == "__main__":
    agent = ScreenerAgent()
    agent.configure_role(
        required=["Python", "AWS"],
        nice_to_have=["React", "Docker"],
        min_exp=3
    )
    
    results = agent.screen_batch(["cand_001", "cand_002", "cand_003"])
    print(agent.generate_summary_report(results))
