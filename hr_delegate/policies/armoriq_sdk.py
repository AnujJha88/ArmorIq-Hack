"""
ArmorIQ SDK Integration for HR Swarm
====================================
Real ArmorIQ SDK integration with Intent Authentication Protocol (IAP).

ArmorIQ Flow:
1. capture_plan() - Define what the agent wants to do (CSRG format)
2. get_intent_token() - Get cryptographically signed token from ArmorIQ IAP
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
from dataclasses import dataclass, field
from enum import Enum

logging.basicConfig(level=logging.INFO, format='[ArmorIQ] %(levelname)s: %(message)s')
armoriq_logger = logging.getLogger("ArmorIQ")


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

ARMORIQ_API_KEY = os.getenv("ARMORIQ_API_KEY")
ARMORIQ_IAP_ENDPOINT = os.getenv("ARMORIQ_IAP_ENDPOINT", "https://iap.armoriq.ai")
ARMORIQ_PROXY_ENDPOINT = os.getenv("ARMORIQ_PROXY_ENDPOINT", "https://proxy.armoriq.ai")
ARMORIQ_USER_ID = os.getenv("ARMORIQ_USER_ID", "hr-swarm-demo")
ARMORIQ_AGENT_ID = os.getenv("ARMORIQ_AGENT_ID", "hr-agent")

# Try to import ArmorIQ SDK
try:
    from armoriq_sdk import (
        ArmorIQClient,
        IntentMismatchException,
        InvalidTokenException,
        TokenExpiredException,
        MCPInvocationException,
        PlanCapture,
        IntentToken
    )
    ARMORIQ_SDK_AVAILABLE = True
    armoriq_logger.info("✓ armoriq-sdk v0.2.6 loaded")
except ImportError:
    ARMORIQ_SDK_AVAILABLE = False
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
    token: Optional[Any] = None  # IntentToken when using real SDK
    plan_hash: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# LOCAL POLICY ENGINE (Demo Mode)
# ═══════════════════════════════════════════════════════════════════════════════

class LocalPolicyEngine:
    """
    Local policy engine for demo mode.
    Simulates ArmorIQ policy enforcement when SDK credentials unavailable.
    """

    POLICIES = {
        "work_life_balance": {
            "name": "Work-Life Balance",
            "description": "No scheduling outside work hours (9-5) or weekends",
            "work_hours": (9, 17),
        },
        "salary_caps": {
            "name": "Salary Caps",
            "description": "Enforce role-based salary limits",
            "bands": {
                "L3": {"min": 100000, "max": 140000},
                "L4": {"min": 140000, "max": 180000},
                "L5": {"min": 180000, "max": 240000},
            }
        },
        "pii_protection": {
            "name": "PII Protection",
            "description": "Redact PII in external communications",
            "patterns": [
                r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",  # Phone
                r"\b\d{3}[-]?\d{2}[-]?\d{4}\b",    # SSN
            ]
        },
        "inclusive_language": {
            "name": "Inclusive Language",
            "description": "Block non-inclusive terminology",
            "blocked_terms": ["rockstar", "ninja", "guru", "guys", "manpower", "salesman"]
        },
        "fraud_prevention": {
            "name": "Fraud Prevention",
            "description": "Require receipts for expenses over threshold",
            "receipt_threshold": 50
        },
        "right_to_work": {
            "name": "Right-to-Work",
            "description": "Verify I-9 before onboarding",
            "i9_required": True
        }
    }

    def evaluate(self, action: str, payload: Dict) -> IntentResult:
        """Evaluate action against local policies."""
        intent_id = f"LOCAL-{datetime.now().strftime('%H%M%S')}-{id(payload) % 10000:04d}"

        # Work-Life Balance
        if action in ["schedule_interview", "book_meeting"]:
            time_str = payload.get("time", payload.get("datetime", ""))
            result = self._check_work_hours(intent_id, time_str)
            if result:
                return result

        # Salary Caps
        if action in ["generate_offer", "create_offer", "make_offer"]:
            result = self._check_salary_cap(intent_id, payload)
            if result:
                return result

        # Inclusive Language & PII
        if action in ["send_email", "send_message", "send_outreach"]:
            result = self._check_communication(intent_id, payload)
            if result:
                return result

        # Fraud Prevention
        if action in ["approve_expense", "submit_expense", "process_reimbursement"]:
            result = self._check_expense(intent_id, payload)
            if result:
                return result

        # Right-to-Work
        if action in ["onboard_employee", "start_onboarding", "hire"]:
            result = self._check_right_to_work(intent_id, payload)
            if result:
                return result

        return IntentResult(intent_id, True, PolicyVerdict.ALLOW, "Policy check passed", None, payload)

    def _check_work_hours(self, intent_id: str, time_str: str) -> Optional[IntentResult]:
        if not time_str:
            return None
        try:
            dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
            policy = self.POLICIES["work_life_balance"]

            if dt.weekday() >= 5:
                return IntentResult(intent_id, False, PolicyVerdict.DENY,
                    f"Weekend scheduling blocked ({dt.strftime('%A')})",
                    policy["name"])

            h = policy["work_hours"]
            if not (h[0] <= dt.hour < h[1]):
                return IntentResult(intent_id, False, PolicyVerdict.DENY,
                    f"Outside work hours ({h[0]}:00-{h[1]}:00)",
                    policy["name"])
        except ValueError:
            pass
        return None

    def _check_salary_cap(self, intent_id: str, payload: Dict) -> Optional[IntentResult]:
        role = payload.get("role", "")
        salary = payload.get("salary", 0)
        policy = self.POLICIES["salary_caps"]
        bands = policy["bands"]

        if role in bands:
            band = bands[role]
            if salary > band["max"]:
                return IntentResult(intent_id, False, PolicyVerdict.DENY,
                    f"Salary ${salary:,} exceeds ${band['max']:,} cap for {role}",
                    policy["name"])
        return None

    def _check_communication(self, intent_id: str, payload: Dict) -> Optional[IntentResult]:
        body = payload.get("body", payload.get("message", ""))
        recipient = payload.get("recipient", payload.get("to", ""))

        # Check inclusive language
        policy = self.POLICIES["inclusive_language"]
        for term in policy["blocked_terms"]:
            if term.lower() in body.lower():
                return IntentResult(intent_id, False, PolicyVerdict.DENY,
                    f"Non-inclusive term detected: '{term}'",
                    policy["name"])

        # PII redaction for external emails
        if recipient and not recipient.endswith("@company.com"):
            pii_policy = self.POLICIES["pii_protection"]
            modified_body = body
            pii_found = False

            for pattern in pii_policy["patterns"]:
                if re.search(pattern, modified_body):
                    modified_body = re.sub(pattern, "[REDACTED]", modified_body)
                    pii_found = True

            if pii_found:
                mod_payload = payload.copy()
                mod_payload["body"] = modified_body
                return IntentResult(intent_id, True, PolicyVerdict.MODIFY,
                    "PII redacted for external recipient",
                    pii_policy["name"], mod_payload)

        return None

    def _check_expense(self, intent_id: str, payload: Dict) -> Optional[IntentResult]:
        amount = payload.get("amount", 0)
        has_receipt = payload.get("has_receipt", payload.get("receipt", False))
        policy = self.POLICIES["fraud_prevention"]

        if amount > policy["receipt_threshold"] and not has_receipt:
            return IntentResult(intent_id, False, PolicyVerdict.DENY,
                f"Receipt required for expenses over ${policy['receipt_threshold']}",
                policy["name"])
        return None

    def _check_right_to_work(self, intent_id: str, payload: Dict) -> Optional[IntentResult]:
        i9_status = payload.get("i9_status", payload.get("i9", ""))
        policy = self.POLICIES["right_to_work"]

        if i9_status != "verified":
            return IntentResult(intent_id, False, PolicyVerdict.DENY,
                "I-9 verification required before onboarding",
                policy["name"])
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# ARMORIQ WRAPPER (Main Interface)
# ═══════════════════════════════════════════════════════════════════════════════

class ArmorIQWrapper:
    """
    ArmorIQ SDK Wrapper for HR Swarm
    =================================

    LIVE MODE (with API key):
        Uses real ArmorIQ SDK with cryptographic Intent Authentication Protocol.
        All actions verified through ArmorIQ's IAP before execution.

    DEMO MODE (no API key):
        Uses local policy engine for demonstrations.
        Simulates ArmorIQ behavior with configurable policies.

    Environment Variables:
        ARMORIQ_API_KEY - Your ArmorIQ API key (ak_live_* or ak_test_*)
        ARMORIQ_IAP_ENDPOINT - IAP endpoint (default: https://iap.armoriq.ai)
        ARMORIQ_PROXY_ENDPOINT - Proxy endpoint (default: https://proxy.armoriq.ai)
        ARMORIQ_USER_ID - User identifier
        ARMORIQ_AGENT_ID - Agent identifier

    Get API Key: https://platform.armoriq.ai/dashboard/api-keys
    """

    def __init__(self,
                 api_key: str = None,
                 user_id: str = None,
                 agent_id: str = None,
                 iap_endpoint: str = None,
                 proxy_endpoint: str = None,
                 project_id: str = "hr-swarm"):

        self.project_id = project_id
        self.api_key = api_key or ARMORIQ_API_KEY
        self.user_id = user_id or ARMORIQ_USER_ID
        self.agent_id = agent_id or ARMORIQ_AGENT_ID
        self.iap_endpoint = iap_endpoint or ARMORIQ_IAP_ENDPOINT
        self.proxy_endpoint = proxy_endpoint or ARMORIQ_PROXY_ENDPOINT

        self.audit_log: List[Dict] = []
        self._intent_counter = 0
        self.client = None
        self.mode = "DEMO"

        # Try to initialize real ArmorIQ SDK
        if ARMORIQ_SDK_AVAILABLE and self.api_key:
            if self.api_key.startswith("ak_live_") or self.api_key.startswith("ak_test_"):
                try:
                    self.client = ArmorIQClient(
                        api_key=self.api_key,
                        iap_endpoint=self.iap_endpoint,
                        proxy_endpoint=self.proxy_endpoint,
                        user_id=self.user_id,
                        agent_id=self.agent_id
                    )
                    self.mode = "LIVE"
                    armoriq_logger.info("═" * 60)
                    armoriq_logger.info("  🛡️  ArmorIQ LIVE MODE - Intent Authentication Active")
                    armoriq_logger.info("═" * 60)
                    armoriq_logger.info(f"  IAP Endpoint: {self.iap_endpoint}")
                    armoriq_logger.info(f"  User: {self.user_id}")
                    armoriq_logger.info(f"  Agent: {self.agent_id}")
                    armoriq_logger.info("═" * 60)
                except Exception as e:
                    armoriq_logger.warning(f"⚠️  ArmorIQ SDK init failed: {e}")
                    armoriq_logger.info("   Falling back to DEMO mode")
            else:
                armoriq_logger.warning(f"⚠️  Invalid API key format. Must start with 'ak_live_' or 'ak_test_'")

        if self.mode == "DEMO":
            armoriq_logger.info("═" * 60)
            armoriq_logger.info("  🛡️  ArmorIQ DEMO MODE - Local Policy Engine")
            armoriq_logger.info("═" * 60)
            armoriq_logger.info(f"  Project: {project_id}")
            if not self.api_key:
                armoriq_logger.info("  Set ARMORIQ_API_KEY for live mode")
                armoriq_logger.info("  Get key: https://platform.armoriq.ai/dashboard/api-keys")
            armoriq_logger.info("═" * 60)

        self._local_engine = LocalPolicyEngine()

    # ═══════════════════════════════════════════════════════════════════════════
    # MAIN INTENT VERIFICATION API
    # ═══════════════════════════════════════════════════════════════════════════

    def capture_intent(self, action_type: str, payload: Dict, agent_name: str = None) -> IntentResult:
        """
        Verify an intent through ArmorIQ before execution.

        Args:
            action_type: The action to perform (e.g., "send_email", "generate_offer")
            payload: Action parameters
            agent_name: Name of the agent making the request

        Returns:
            IntentResult with verdict (ALLOW, DENY, or MODIFY)
        """
        self._intent_counter += 1
        agent_name = agent_name or self.agent_id

        # Log the verification attempt
        self._log_verification_start(action_type, agent_name, payload)

        # Use real SDK or local engine
        if self.mode == "LIVE" and self.client:
            result = self._verify_with_armoriq(action_type, payload, agent_name)
        else:
            result = self._local_engine.evaluate(action_type, payload)

        # Log the result
        self._log_verification_result(result)
        self._record_audit(result, agent_name, action_type, payload)

        return result

    def _verify_with_armoriq(self, action: str, payload: Dict, agent_name: str) -> IntentResult:
        """Use real ArmorIQ SDK for verification + local policy enforcement."""
        intent_id = f"ARMOR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self._intent_counter:04d}"

        try:
            # Build the plan structure for ArmorIQ
            plan_structure = {
                "goal": f"{agent_name} executing {action}",
                "steps": [{
                    "mcp": "hr-tools",
                    "action": action,
                    "params": payload
                }]
            }

            # Capture the plan with explicit plan structure
            plan = self.client.capture_plan(
                llm=agent_name,
                prompt=f"Execute {action}: {json.dumps(payload)[:100]}",
                plan=plan_structure
            )

            # Get intent token (cryptographic verification)
            token = self.client.get_intent_token(plan)
            token_id = token.token_id if hasattr(token, 'token_id') else intent_id
            plan_hash = token.plan_hash if hasattr(token, 'plan_hash') else None

            # ArmorIQ approved the intent structure - now apply local policy rules
            # This combines cryptographic verification with business policy enforcement
            local_result = self._local_engine.evaluate(action, payload)

            if not local_result.allowed:
                # Local policy denied - return with ArmorIQ token info
                return IntentResult(
                    intent_id=token_id,
                    allowed=False,
                    verdict=local_result.verdict,
                    reason=local_result.reason,
                    policy_triggered=local_result.policy_triggered,
                    token=token,
                    plan_hash=plan_hash
                )

            if local_result.verdict == PolicyVerdict.MODIFY:
                # Local policy modified the payload
                return IntentResult(
                    intent_id=token_id,
                    allowed=True,
                    verdict=PolicyVerdict.MODIFY,
                    reason=local_result.reason,
                    policy_triggered=local_result.policy_triggered,
                    modified_payload=local_result.modified_payload,
                    token=token,
                    plan_hash=plan_hash
                )

            # Both ArmorIQ and local policies approved
            return IntentResult(
                intent_id=token_id,
                allowed=True,
                verdict=PolicyVerdict.ALLOW,
                reason=f"ArmorIQ verified + policy passed",
                modified_payload=payload,
                token=token,
                plan_hash=plan_hash
            )

        except IntentMismatchException as e:
            return IntentResult(
                intent_id=intent_id,
                allowed=False,
                verdict=PolicyVerdict.DENY,
                reason=f"Intent mismatch: {str(e)}",
                policy_triggered="ArmorIQ Intent Verification"
            )
        except InvalidTokenException as e:
            return IntentResult(
                intent_id=intent_id,
                allowed=False,
                verdict=PolicyVerdict.DENY,
                reason=f"Invalid token: {str(e)}",
                policy_triggered="ArmorIQ Token Validation"
            )
        except TokenExpiredException as e:
            return IntentResult(
                intent_id=intent_id,
                allowed=False,
                verdict=PolicyVerdict.DENY,
                reason=f"Token expired: {str(e)}",
                policy_triggered="ArmorIQ Token Expiry"
            )
        except Exception as e:
            armoriq_logger.warning(f"ArmorIQ error: {e}, falling back to local")
            return self._local_engine.evaluate(action, payload)

    def invoke(self, mcp: str, action: str, params: Dict, intent_token: Any = None) -> Dict:
        """
        Execute an action through ArmorIQ proxy (LIVE mode only).

        In DEMO mode, simulates the invocation.
        """
        if self.mode == "LIVE" and self.client and intent_token:
            try:
                result = self.client.invoke(
                    mcp=mcp,
                    action=action,
                    intent_token=intent_token,
                    params=params,
                    user_email=f"{self.user_id}@company.com"
                )
                return {"status": "success", "result": result}
            except MCPInvocationException as e:
                return {"status": "error", "error": str(e)}
        else:
            # Demo mode: simulate success
            return {
                "status": "success",
                "mode": "demo",
                "action": action,
                "params": params,
                "timestamp": datetime.now().isoformat()
            }

    # ═══════════════════════════════════════════════════════════════════════════
    # LOGGING & AUDIT
    # ═══════════════════════════════════════════════════════════════════════════

    def _log_verification_start(self, action: str, agent: str, payload: Dict):
        armoriq_logger.info(f"╔{'═'*65}╗")
        armoriq_logger.info(f"║  🛡️  ARMORIQ INTENT VERIFICATION                               ║")
        armoriq_logger.info(f"╠{'═'*65}╣")
        armoriq_logger.info(f"║  Agent:  {agent:<55}║")
        armoriq_logger.info(f"║  Action: {action:<55}║")
        armoriq_logger.info(f"║  Mode:   {self.mode:<55}║")
        armoriq_logger.info(f"╠{'═'*65}╣")

    def _log_verification_result(self, result: IntentResult):
        if result.verdict == PolicyVerdict.DENY:
            armoriq_logger.warning(f"║  🛑 DENIED                                                      ║")
            armoriq_logger.warning(f"║  Policy: {str(result.policy_triggered or 'N/A')[:54]:<54}║")
            armoriq_logger.warning(f"║  Reason: {result.reason[:54]:<54}║")
        elif result.verdict == PolicyVerdict.MODIFY:
            armoriq_logger.info(f"║  ⚠️  MODIFIED                                                    ║")
            armoriq_logger.info(f"║  Policy: {str(result.policy_triggered or 'N/A')[:54]:<54}║")
            armoriq_logger.info(f"║  Reason: {result.reason[:54]:<54}║")
        else:
            armoriq_logger.info(f"║  ✅ ALLOWED                                                      ║")
        armoriq_logger.info(f"╚{'═'*65}╝")

    def _record_audit(self, result: IntentResult, agent: str, action: str, payload: Dict):
        self.audit_log.append({
            "intent_id": result.intent_id,
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "action": action,
            "verdict": result.verdict.value,
            "policy": result.policy_triggered,
            "reason": result.reason,
            "mode": self.mode,
            "plan_hash": result.plan_hash
        })

    def get_audit_report(self) -> Dict:
        """Generate audit report summary."""
        total = len(self.audit_log)
        denied = sum(1 for e in self.audit_log if e["verdict"] == "DENY")
        modified = sum(1 for e in self.audit_log if e["verdict"] == "MODIFY")

        by_policy = {}
        for e in self.audit_log:
            p = e.get("policy") or "None"
            by_policy[p] = by_policy.get(p, 0) + 1

        return {
            "project": self.project_id,
            "mode": self.mode,
            "total_intents": total,
            "allowed": total - denied - modified,
            "denied": denied,
            "modified": modified,
            "by_policy": by_policy,
            "audit_entries": self.audit_log[-10:]  # Last 10
        }

    def close(self):
        """Close the ArmorIQ client connection."""
        if self.client:
            try:
                self.client.close()
            except:
                pass


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON & EXPORTS
# ═══════════════════════════════════════════════════════════════════════════════

_armoriq: Optional[ArmorIQWrapper] = None

def get_armoriq() -> ArmorIQWrapper:
    """Get the global ArmorIQ wrapper instance."""
    global _armoriq
    if _armoriq is None:
        _armoriq = ArmorIQWrapper()
    return _armoriq

def reset_armoriq():
    """Reset the global instance (for testing)."""
    global _armoriq
    if _armoriq:
        _armoriq.close()
    _armoriq = None

# Backward compatibility
ComplianceEngine = ArmorIQWrapper
