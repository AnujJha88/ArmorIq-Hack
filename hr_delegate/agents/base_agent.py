"""
HR Agent Base Class with TIRS Integration
==========================================
All agents inherit from this and use ArmorIQ + TIRS for intent verification
and temporal drift detection.
"""

import json
import logging
import sys
import os
from typing import Dict, List, Tuple, Set, Optional
from datetime import datetime

# Add paths for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from hr_delegate.policies.armoriq_sdk import ArmorIQWrapper, get_armoriq, PolicyVerdict

# TIRS Integration
try:
    from tirs.core import get_tirs, TIRSResult
    from tirs.drift_engine import RiskLevel, AgentStatus
    TIRS_AVAILABLE = True
except ImportError:
    TIRS_AVAILABLE = False
    RiskLevel = None
    AgentStatus = None

logging.basicConfig(level=logging.INFO, format='[%(name)s] %(message)s')


class MockCloveClient:
    """Simulates Clove SDK for standalone operation."""
    def connect(self): return True
    def register_name(self, name): return {"success": True}
    def disconnect(self): pass
    def think(self, prompt): return {"success": True, "content": f"LLM Response..."}
    def exec(self, cmd): return {"success": True, "stdout": "{}"}
    def pause(self): return {"success": True}
    def kill(self): return {"success": True}


class HRAgent:
    """
    Base HR Agent with ArmorIQ + TIRS Integration
    ==============================================
    Every agent action goes through:
    1. ArmorIQ - Policy verification
    2. TIRS - Temporal drift detection & plan simulation
    """

    def __init__(self, name: str, primary_intent: str):
        self.name = name
        self.primary_intent = primary_intent
        self.logger = logging.getLogger(name)
        self.clove = MockCloveClient()

        # ARMORIQ: Get the shared client
        self.armoriq = get_armoriq()

        # TIRS: Get temporal intent risk engine
        self.tirs = get_tirs() if TIRS_AVAILABLE else None
        if self.tirs:
            self.logger.info(f"🛡️  TIRS enabled for {name}")

        self.action_log: List[Dict] = []
        self.is_connected = False
        self._paused = False
        self._killed = False

    def start(self):
        if not self.clove.connect():
            self.logger.error("Failed to connect to Clove")
            sys.exit(1)
        self.is_connected = True
        self.logger.info(f"🟢 {self.name} Agent ONLINE")

    def stop(self):
        self.clove.disconnect()
        self.is_connected = False
        self.logger.info(f"🔴 {self.name} Agent OFFLINE")

        # Print ArmorIQ summary
        report = self.armoriq.get_audit_report()
        self.logger.info(f"📊 ArmorIQ Session: {report['total']} intents | "
                        f"✅ {report['allowed']} | 🛑 {report['denied']} | ⚠️ {report['modified']}")

        # Print TIRS summary
        if self.tirs:
            status = self.tirs.get_agent_status(self.name)
            if status.get("status") != "unknown":
                self.logger.info(f"📈 TIRS Risk: {status.get('current_risk_score', 0):.2f} | "
                               f"Status: {status.get('status', 'unknown')}")

    def check_status(self) -> Tuple[bool, str]:
        """
        Check if agent can continue operating.

        Returns:
            (can_continue, reason)
        """
        if self._killed:
            return False, "Agent has been killed"
        if self._paused:
            return False, "Agent is paused - awaiting admin approval"

        if self.tirs:
            status = self.tirs.get_agent_status(self.name)
            agent_status = status.get("status", "active")
            if agent_status == "killed":
                self._killed = True
                return False, "Agent killed by TIRS due to risk threshold"
            if agent_status == "paused":
                self._paused = True
                return False, "Agent paused by TIRS - risk threshold exceeded"

        return True, "OK"

    def execute_with_armoriq(self, intent_type: str, payload: Dict, description: str) -> Tuple[bool, str, Dict]:
        """
        ═══════════════════════════════════════════════════════════════
        ARMORIQ + TIRS INTENT VERIFICATION
        ═══════════════════════════════════════════════════════════════
        Every action MUST go through ArmorIQ and TIRS before execution.
        """
        # Check if agent can continue
        can_continue, reason = self.check_status()
        if not can_continue:
            self.logger.critical(f"🛑 Agent cannot continue: {reason}")
            return False, reason, payload

        self.logger.info(f"📋 Requesting ArmorIQ verification: {description}")

        # CALL ARMORIQ
        result = self.armoriq.capture_intent(intent_type, payload, self.name)

        # Determine capabilities from intent type
        capabilities = self._extract_capabilities(intent_type, payload)

        # TIRS: Track intent for drift detection
        if self.tirs:
            risk_score, risk_level = self.tirs.verify_intent(
                agent_id=self.name,
                intent_text=description,
                capabilities=capabilities,
                was_allowed=result.allowed,
                policy_triggered=result.policy_triggered
            )

            # Log risk info
            self.logger.info(f"📈 TIRS Risk: {risk_score:.2f} ({risk_level.value if risk_level else 'N/A'})")

            # Handle TIRS enforcement
            if risk_level == RiskLevel.KILL:
                self._killed = True
                self.logger.critical(f"☠️  TIRS KILLED agent - risk too high!")
                return False, "Agent killed by TIRS", payload
            elif risk_level == RiskLevel.PAUSE:
                self._paused = True
                self.logger.warning(f"⏸️  TIRS PAUSED agent - risk threshold exceeded")
                return False, "Agent paused by TIRS", payload

        if not result.allowed:
            self.logger.critical(f"🛡️  ArmorIQ BLOCKED: {result.reason}")
            return False, result.reason, payload

        if result.verdict == PolicyVerdict.MODIFY:
            self.logger.warning(f"🛡️  ArmorIQ MODIFIED: {result.reason}")
            return True, result.reason, result.modified_payload

        self.logger.info(f"🛡️  ArmorIQ APPROVED | ID: {result.intent_id}")
        return True, "Approved", payload

    def simulate_plan(self, plan: List[Dict]) -> Optional[TIRSResult]:
        """
        Simulate a multi-step plan before execution.

        Args:
            plan: List of plan steps, each with mcp, action, args

        Returns:
            TIRSResult with simulation details, or None if TIRS unavailable
        """
        if not self.tirs:
            self.logger.warning("TIRS not available - cannot simulate plan")
            return None

        # Check if agent can continue
        can_continue, reason = self.check_status()
        if not can_continue:
            self.logger.critical(f"🛑 Cannot simulate: {reason}")
            return None

        self.logger.info(f"🔮 Simulating plan with {len(plan)} steps...")

        result = self.tirs.simulate_plan(self.name, plan)

        # Log results
        if result.allowed:
            self.logger.info(f"✅ Plan ALLOWED - all {result.simulation.total_steps} steps pass")
        else:
            self.logger.warning(f"🛑 Plan BLOCKED - {result.simulation.blocked_count} steps denied")
            if result.remediation:
                self.logger.info(f"💡 Remediation: {result.remediation.recommended.description if result.remediation.recommended else 'None'}")

        return result

    def _extract_capabilities(self, intent_type: str, payload: Dict) -> Set[str]:
        """Extract capability requirements from intent."""
        caps = {intent_type}

        # Add specific capabilities based on intent
        if "email" in intent_type.lower():
            caps.add("email.send")
            if payload.get("to", "").find("@company.com") == -1:
                caps.add("email.external")

        if "salary" in intent_type.lower() or "offer" in intent_type.lower():
            caps.add("payroll.read_sensitive")

        if "hris" in intent_type.lower():
            caps.add("hris.read")
            if "export" in intent_type.lower():
                caps.add("hris.export")

        if "schedule" in intent_type.lower():
            caps.add("calendar.write")

        return caps

    # Backward compatibility
    def execute_with_compliance(self, intent_type: str, payload: Dict, description: str) -> Tuple[bool, str, Dict]:
        return self.execute_with_armoriq(intent_type, payload, description)

    def think(self, prompt: str) -> str:
        """Ask the LLM for reasoning."""
        return self.clove.think(prompt).get("content", "")

    def get_audit_summary(self) -> Dict:
        return self.armoriq.get_audit_report()

    def get_tirs_status(self) -> Optional[Dict]:
        """Get TIRS status for this agent."""
        if not self.tirs:
            return None
        return self.tirs.get_agent_status(self.name)

    def get_risk_score(self) -> float:
        """Get current TIRS risk score."""
        if not self.tirs:
            return 0.0
        status = self.tirs.get_agent_status(self.name)
        return status.get("current_risk_score", 0.0)
