"""
ArmorIQ SDK Integration for HR Swarm
====================================
This wraps the real ArmorIQ SDK for Intent Authentication Protocol (IAP).

ArmorIQ Flow:
1. capture_plan() - Define what the agent wants to do
2. get_intent_token() - Get cryptographically signed token from ArmorIQ
3. invoke() - Execute action through ArmorIQ proxy with verification

Install: pip install armoriq-sdk
Get API Key: https://platform.armoriq.ai/dashboard/api-keys
"""

import os
import re
import json
import logging
from typing import Dict, Tuple, Optional, List, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logging.basicConfig(level=logging.INFO, format='[ArmorIQ] %(levelname)s: %(message)s')
armoriq_logger = logging.getLogger("ArmorIQ")


# ═══════════════════════════════════════════════════════════════════════════════
# ARMORIQ SDK INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

ARMORIQ_API_KEY = os.getenv("ARMORIQ_API_KEY")
ARMORIQ_USER_ID = os.getenv("USER_ID", "hr-swarm-demo")
ARMORIQ_AGENT_ID = os.getenv("AGENT_ID", "hr-agent")

# Try to import armored client
try:
    from armoriq_sdk import (
        ArmorIQClient, 
        IntentMismatchException, 
        InvalidTokenException,
        PlanCapture,
        IntentToken
    )
    ARMORIQ_SDK_INSTALLED = True
    armoriq_logger.info("✓ armoriq-sdk package found")
except ImportError:
    ARMORIQ_SDK_INSTALLED = False
    armoriq_logger.warning("⚠️  armoriq-sdk not installed. Run: pip install armoriq-sdk")


class PolicyVerdict(Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    MODIFY = "MODIFY"


@dataclass
class IntentResult:
    """Result from ArmorIQ intent verification."""
    intent_id: str
    allowed: bool
    verdict: PolicyVerdict
    reason: str
    policy_triggered: Optional[str] = None
    modified_payload: Optional[Dict] = None


class ArmorIQWrapper:
    """
    ArmorIQ SDK Wrapper for HR Swarm
    =================================
    
    LIVE MODE (API key set):
        Uses real ArmorIQ SDK with cryptographic Intent Authentication Protocol.
        All actions go through ArmorIQ's IAP for verification.
        
    DEMO MODE (no API key):
        Uses local policy engine for hackathon demonstrations.
        Simulates ArmorIQ behavior with configurable policies.
    
    Required Environment Variables for LIVE mode:
        ARMORIQ_API_KEY - Get from https://platform.armoriq.ai/dashboard/api-keys
        USER_ID - Your user identifier
        AGENT_ID - Your agent identifier
    """
    
    def __init__(self, 
                 api_key: str = None,
                 user_id: str = None,
                 agent_id: str = None,
                 project_id: str = "hr-swarm"):
        
        self.project_id = project_id
        self.api_key = api_key or ARMORIQ_API_KEY
        self.user_id = user_id or ARMORIQ_USER_ID
        self.agent_id = agent_id or ARMORIQ_AGENT_ID
        self.audit_log: List[Dict] = []
        self._intent_counter = 0
        
        # Initialize real SDK if credentials available
        if ARMORIQ_SDK_INSTALLED and self.api_key:
            try:
                self.client = ArmorIQClient(
                    api_key=self.api_key,
                    user_id=self.user_id,
                    agent_id=self.agent_id
                )
                self.mode = "LIVE"
                armoriq_logger.info(f"🛡️  ArmorIQ LIVE MODE")
                armoriq_logger.info(f"   User: {self.user_id}, Agent: {self.agent_id}")
            except Exception as e:
                armoriq_logger.warning(f"⚠️  ArmorIQ SDK init failed: {e}")
                armoriq_logger.info(f"   Falling back to DEMO mode")
                self.client = None
                self.mode = "DEMO"
        else:
            self.client = None
            self.mode = "DEMO"
            armoriq_logger.info(f"🛡️  ArmorIQ DEMO MODE | Project: {project_id}")
            if not self.api_key:
                armoriq_logger.info(f"   Set ARMORIQ_API_KEY for live mode")
                armoriq_logger.info(f"   Get key: https://platform.armoriq.ai/dashboard/api-keys")
        
        self._local_policies = self._load_local_policies()

    def _load_local_policies(self) -> Dict:
        """Local policies for DEMO mode."""
        return {
            "scheduling": {"name": "Work-Life Balance", "work_hours": (9, 17)},
            "financial": {"name": "Salary Caps", "bands": {"L3": 140000, "L4": 180000, "L5": 240000}},
            "communication": {"name": "PII Protection", "bias_terms": ["rockstar", "ninja", "guru", "guys"]},
            "expense": {"name": "Fraud Prevention", "receipt_threshold": 50},
            "legal": {"name": "Right-to-Work", "i9_required": True},
            "hipaa": {"name": "Medical Privacy", "redact": ["surgery", "cancer", "pregnancy"]}
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # ARMORIQ INTENT VERIFICATION (Main Entry Point)
    # ═══════════════════════════════════════════════════════════════════════════

    def capture_intent(self, action_type: str, payload: Dict, agent_name: str) -> IntentResult:
        """
        ╔═══════════════════════════════════════════════════════════════════════╗
        ║  A R M O R I Q   I N T E N T   V E R I F I C A T I O N                ║
        ╠═══════════════════════════════════════════════════════════════════════╣
        ║  Every agent action goes through ArmorIQ before execution.            ║
        ║  LIVE: Cryptographic verification via ArmorIQ IAP                     ║
        ║  DEMO: Local policy engine for hackathon demo                         ║
        ╚═══════════════════════════════════════════════════════════════════════╝
        """
        self._intent_counter += 1
        intent_id = f"ARMOR-{self.project_id}-{self._intent_counter:06d}"
        
        # Pretty logging
        armoriq_logger.info(f"╔{'═'*65}╗")
        armoriq_logger.info(f"║  🛡️  ARMORIQ INTENT VERIFICATION                               ║")
        armoriq_logger.info(f"╠{'═'*65}╣")
        armoriq_logger.info(f"║  ID:     {intent_id:<55}║")
        armoriq_logger.info(f"║  Agent:  {agent_name:<55}║")
        armoriq_logger.info(f"║  Action: {action_type:<55}║")
        armoriq_logger.info(f"║  Mode:   {self.mode:<55}║")
        armoriq_logger.info(f"╠{'═'*65}╣")
        
        # LIVE mode: Use real ArmorIQ SDK
        if self.mode == "LIVE" and self.client:
            result = self._verify_with_armoriq(action_type, payload, agent_name, intent_id)
        else:
            # DEMO mode: Local policy evaluation
            result = self._evaluate_locally(action_type, payload, intent_id)
        
        # Log verdict
        if result.verdict == PolicyVerdict.DENY:
            armoriq_logger.warning(f"║  🛑 VERDICT: DENIED                                            ║")
            armoriq_logger.warning(f"║  Policy:  {str(result.policy_triggered)[:53]:<53}║")
            armoriq_logger.warning(f"║  Reason:  {result.reason[:53]:<53}║")
        elif result.verdict == PolicyVerdict.MODIFY:
            armoriq_logger.info(f"║  ⚠️  VERDICT: MODIFIED                                          ║")
            armoriq_logger.info(f"║  Policy:  {str(result.policy_triggered)[:53]:<53}║")
        else:
            armoriq_logger.info(f"║  ✅ VERDICT: ALLOWED                                            ║")
        
        armoriq_logger.info(f"╚{'═'*65}╝")
        
        self._record_audit(result, agent_name, action_type)
        return result

    def _verify_with_armoriq(self, action_type: str, payload: Dict, 
                              agent_name: str, intent_id: str) -> IntentResult:
        """
        LIVE MODE: Use real ArmorIQ SDK for cryptographic verification.
        
        ArmorIQ Flow:
        1. capture_plan() - Define what we want to do
        2. get_intent_token() - Get signed token from ArmorIQ IAP
        3. Token allows action OR denies with policy violation
        """
        try:
            # Build plan structure for ArmorIQ
            plan = {
                "goal": f"HR Agent {agent_name} executing {action_type}",
                "steps": [{
                    "action": action_type,
                    "mcp": "hr-tools",
                    "params": payload
                }]
            }
            
            # Capture the plan with ArmorIQ
            plan_capture = self.client.capture_plan(
                llm="hr-agent",
                prompt=f"Execute {action_type} for HR operations",
                plan=plan
            )
            
            # Get intent token (this is where policy enforcement happens)
            token = self.client.get_intent_token(plan_capture)
            
            # If we got here, ArmorIQ approved the intent
            return IntentResult(
                intent_id=token.token_id or intent_id,
                allowed=True,
                verdict=PolicyVerdict.ALLOW,
                reason="ArmorIQ IAP approved",
                modified_payload=payload
            )
            
        except IntentMismatchException as e:
            return IntentResult(
                intent_id=intent_id,
                allowed=False,
                verdict=PolicyVerdict.DENY,
                reason=str(e),
                policy_triggered="ArmorIQ Policy"
            )
        except InvalidTokenException as e:
            return IntentResult(
                intent_id=intent_id,
                allowed=False,
                verdict=PolicyVerdict.DENY,
                reason=str(e),
                policy_triggered="ArmorIQ Token Validation"
            )
        except Exception as e:
            armoriq_logger.warning(f"ArmorIQ SDK error: {e}, falling back to local")
            return self._evaluate_locally(action_type, payload, intent_id)

    def _evaluate_locally(self, action_type: str, payload: Dict, intent_id: str) -> IntentResult:
        """DEMO MODE: Local policy evaluation."""
        
        # Scheduling Policy
        if action_type == "schedule_interview":
            time_str = payload.get("time", "")
            try:
                dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                if dt.weekday() >= 5:
                    return IntentResult(intent_id, False, PolicyVerdict.DENY, 
                                        "No interviews on weekends", "Work-Life Balance")
                h = self._local_policies["scheduling"]["work_hours"]
                if not (h[0] <= dt.hour < h[1]):
                    return IntentResult(intent_id, False, PolicyVerdict.DENY,
                                        f"Outside hours ({h[0]}-{h[1]})", "Work-Life Balance")
            except ValueError:
                pass
        
        # Financial Policy
        if action_type == "generate_offer":
            role, salary = payload.get("role", ""), payload.get("salary", 0)
            cap = self._local_policies["financial"]["bands"].get(role, 100000)
            if salary > cap:
                return IntentResult(intent_id, False, PolicyVerdict.DENY,
                                    f"${salary:,} exceeds ${cap:,} cap", "Salary Caps")
        
        # Communication Policy
        if action_type == "send_email":
            body = payload.get("body", "")
            for term in self._local_policies["communication"]["bias_terms"]:
                if term in body.lower():
                    return IntentResult(intent_id, False, PolicyVerdict.DENY,
                                        f"Non-inclusive: '{term}'", "PII Protection")
            
            # PII redaction for external
            recipient = payload.get("recipient", "")
            if not recipient.endswith("@company.com"):
                redacted = re.sub(r"\d{3}[-.]?\d{3}[-.]?\d{4}", "[REDACTED]", body)
                if redacted != body:
                    mod = payload.copy()
                    mod["body"] = redacted
                    return IntentResult(intent_id, True, PolicyVerdict.MODIFY,
                                        "PII redacted", "PII Protection", mod)
        
        # Expense Policy
        if action_type == "approve_expense":
            amt = payload.get("amount", 0)
            thr = self._local_policies["expense"]["receipt_threshold"]
            if amt > thr and not payload.get("has_receipt"):
                return IntentResult(intent_id, False, PolicyVerdict.DENY,
                                    f"Receipt required > ${thr}", "Fraud Prevention")
        
        # Legal Policy
        if action_type == "onboard_employee":
            if payload.get("i9_status") != "verified":
                return IntentResult(intent_id, False, PolicyVerdict.DENY,
                                    "I-9 required", "Right-to-Work")
        
        # HIPAA
        if action_type == "file_leave_request":
            notes = payload.get("medical_notes", "")
            for term in self._local_policies["hipaa"]["redact"]:
                if term in notes.lower():
                    mod = payload.copy()
                    mod["medical_notes"] = "[HIPAA_REDACTED]"
                    return IntentResult(intent_id, True, PolicyVerdict.MODIFY,
                                        "Medical info redacted", "Medical Privacy", mod)
        
        return IntentResult(intent_id, True, PolicyVerdict.ALLOW, "Approved", None, payload)

    def _record_audit(self, result: IntentResult, agent: str, action: str):
        self.audit_log.append({
            "intent_id": result.intent_id,
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "action": action,
            "verdict": result.verdict.value,
            "mode": self.mode
        })

    def get_audit_report(self) -> Dict:
        total = len(self.audit_log)
        denied = sum(1 for e in self.audit_log if e["verdict"] == "DENY")
        modified = sum(1 for e in self.audit_log if e["verdict"] == "MODIFY")
        return {
            "project": self.project_id,
            "mode": self.mode,
            "total": total,
            "allowed": total - denied - modified,
            "denied": denied,
            "modified": modified
        }

    def close(self):
        if self.client:
            self.client.close()


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON & EXPORTS
# ═══════════════════════════════════════════════════════════════════════════════

_armoriq: Optional[ArmorIQWrapper] = None

def get_armoriq() -> ArmorIQWrapper:
    global _armoriq
    if _armoriq is None:
        _armoriq = ArmorIQWrapper()
    return _armoriq

# Backward compat
ComplianceEngine = ArmorIQWrapper
