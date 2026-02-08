"""
Watchtower Enterprise Integration
==============================
Unified verification layer combining:
1. Watchtower SDK - Intent Authentication Protocol (IAP)
2. TIRS - Temporal Intent Risk & Simulation (Drift Detection)
3. LLM Reasoning - Autonomous decision making for edge cases

The Triple-Layer Security Stack:
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Watchtower IAP                                       │
│  - Cryptographic intent verification                        │
│  - Policy enforcement at the protocol level                 │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: TIRS Drift Detection                              │
│  - Behavioral drift scoring                                 │
│  - Intent embedding analysis                                │
│  - Temporal risk tracking                                   │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: LLM Reasoning                                     │
│  - Autonomous risk assessment                               │
│  - Context-aware decision making                            │
│  - Confidence scoring                                       │
└─────────────────────────────────────────────────────────────┘

Install: pip install watchtower-sdk
Get API Key: https://platform.watchtower.io/dashboard/api-keys
"""

import os
import re
import json
import logging
from typing import Dict, Tuple, Optional, List, Any, Set
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("Enterprise.Watchtower")


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

WATCHTOWER_API_KEY = os.getenv("WATCHTOWER_API_KEY")
WATCHTOWER_IAP_ENDPOINT = os.getenv("WATCHTOWER_IAP_ENDPOINT", "https://iap.watchtower.io")
WATCHTOWER_PROXY_ENDPOINT = os.getenv("WATCHTOWER_PROXY_ENDPOINT", "https://proxy.watchtower.io")
WATCHTOWER_USER_ID = os.getenv("WATCHTOWER_USER_ID", "enterprise-system")
WATCHTOWER_AGENT_ID = os.getenv("WATCHTOWER_AGENT_ID", "enterprise-agent")

# Try to import Watchtower SDK
try:
    from watchtower_sdk import (
        WatchtowerClient,
        IntentMismatchException,
        InvalidTokenException,
        TokenExpiredException,
        MCPInvocationException,
        PlanCapture,
        IntentToken
    )
    WATCHTOWER_SDK_AVAILABLE = True
    logger.info("Watchtower SDK v0.2.6 loaded")
except ImportError:
    WATCHTOWER_SDK_AVAILABLE = False
    logger.warning("watchtower-sdk not installed. Run: pip install watchtower-sdk")


class PolicyVerdict(Enum):
    """Watchtower policy verdicts."""
    ALLOW = "ALLOW"
    DENY = "DENY"
    MODIFY = "MODIFY"
    ESCALATE = "ESCALATE"  # Requires human approval


@dataclass
class IntentResult:
    """Result from Watchtower intent verification."""
    intent_id: str
    allowed: bool
    verdict: PolicyVerdict
    reason: str
    policy_triggered: Optional[str] = None
    modified_payload: Optional[Dict] = None
    token: Optional[Any] = None
    plan_hash: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class UnifiedVerificationResult:
    """
    Result from the unified verification stack.
    Combines Watchtower + TIRS + LLM results.
    """
    # Overall decision
    allowed: bool
    confidence: float
    risk_level: str

    # Watchtower layer
    watchtower_result: Optional[IntentResult] = None
    watchtower_passed: bool = True

    # TIRS layer
    tirs_score: float = 0.0
    tirs_level: str = "nominal"
    tirs_passed: bool = True

    # LLM layer
    llm_reasoning: str = ""
    llm_confidence: float = 1.0
    llm_recommendation: str = "proceed"

    # Combined
    blocking_layer: Optional[str] = None
    escalation_required: bool = False
    modified_payload: Optional[Dict] = None

    # Layer health status - indicates which security layers are active
    layers_active: Dict[str, bool] = field(default_factory=lambda: {
        "watchtower": True,
        "tirs": False,
        "llm": False,
    })

    # Audit
    intent_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            "allowed": self.allowed,
            "confidence": self.confidence,
            "risk_level": self.risk_level,
            "watchtower_passed": self.watchtower_passed,
            "tirs_score": self.tirs_score,
            "tirs_level": self.tirs_level,
            "tirs_passed": self.tirs_passed,
            "llm_confidence": self.llm_confidence,
            "llm_recommendation": self.llm_recommendation,
            "blocking_layer": self.blocking_layer,
            "escalation_required": self.escalation_required,
            "layers_active": self.layers_active,
            "intent_id": self.intent_id,
            "timestamp": self.timestamp.isoformat(),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# LOCAL POLICY ENGINE (Demo Mode)
# ═══════════════════════════════════════════════════════════════════════════════

class LocalPolicyEngine:
    """
    Local policy engine for demo mode.
    Simulates Watchtower policy enforcement when SDK credentials unavailable.
    """

    POLICIES = {
        # Financial policies
        "expense_limits": {
            "name": "Expense Limits",
            "description": "Enforce expense approval thresholds",
            "thresholds": {
                "self_approval": 500,
                "manager_approval": 5000,
                "director_approval": 25000,
                "cfo_approval": 100000,
            }
        },
        "budget_controls": {
            "name": "Budget Controls",
            "description": "Block overspend beyond budget",
            "overspend_limit": 0.1  # 10%
        },

        # Security policies
        "access_control": {
            "name": "Access Control",
            "description": "Least privilege access enforcement",
            "admin_review_required": ["production", "financial_data", "pii"],
            "contractor_restrictions": ["admin", "root", "superuser"],
        },
        "data_classification": {
            "name": "Data Classification",
            "description": "Enforce data handling by classification",
            "restricted_actions": ["export", "share", "copy"],
            "restricted_classifications": ["confidential", "secret", "top_secret"],
        },

        # HR policies
        "salary_caps": {
            "name": "Salary Caps",
            "description": "Enforce role-based salary limits",
            "bands": {
                "L3": {"min": 100000, "max": 140000},
                "L4": {"min": 140000, "max": 180000},
                "L5": {"min": 180000, "max": 240000},
                "L6": {"min": 240000, "max": 350000},
            }
        },
        "right_to_work": {
            "name": "Right-to-Work",
            "description": "Verify I-9 before onboarding",
            "i9_required": True
        },

        # Communication policies
        "pii_protection": {
            "name": "PII Protection",
            "description": "Redact PII in external communications",
            "patterns": [
                r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",  # Phone
                r"\b\d{3}[-]?\d{2}[-]?\d{4}\b",    # SSN
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
            ]
        },
        "inclusive_language": {
            "name": "Inclusive Language",
            "description": "Block non-inclusive terminology",
            "blocked_terms": ["rockstar", "ninja", "guru", "guys", "manpower"]
        },

        # Procurement policies
        "vendor_approval": {
            "name": "Vendor Approval",
            "description": "Require approved vendor list",
            "require_approval": True
        },
        "spending_limits": {
            "name": "Spending Limits",
            "description": "Enforce departmental spending limits",
            "requires_po_above": 10000
        },

        # Fraud prevention
        "fraud_prevention": {
            "name": "Fraud Prevention",
            "description": "Require receipts for expenses over threshold",
            "receipt_threshold": 50
        },
    }

    def evaluate(self, action: str, payload: Dict, agent_type: str = None) -> IntentResult:
        """Evaluate action against local policies."""
        intent_id = f"LOCAL-{datetime.now().strftime('%H%M%S')}-{id(payload) % 10000:04d}"

        # Financial actions
        if action in ["approve_expense", "process_expense", "submit_expense"]:
            result = self._check_expense(intent_id, payload)
            if result:
                return result

        # Access actions
        if action in ["provision_access", "grant_access", "modify_permissions"]:
            result = self._check_access(intent_id, payload)
            if result:
                return result

        # HR actions
        if action in ["generate_offer", "create_offer", "make_offer"]:
            result = self._check_salary_cap(intent_id, payload)
            if result:
                return result

        if action in ["onboard_employee", "start_onboarding", "hire"]:
            result = self._check_right_to_work(intent_id, payload)
            if result:
                return result

        # Communication actions
        if action in ["send_email", "send_message", "send_notification"]:
            result = self._check_communication(intent_id, payload)
            if result:
                return result

        # Procurement actions
        if action in ["create_purchase_order", "approve_vendor", "process_invoice"]:
            result = self._check_procurement(intent_id, payload)
            if result:
                return result

        return IntentResult(
            intent_id=intent_id,
            allowed=True,
            verdict=PolicyVerdict.ALLOW,
            reason="Policy check passed",
            modified_payload=payload
        )

    def _check_expense(self, intent_id: str, payload: Dict) -> Optional[IntentResult]:
        amount = payload.get("amount", 0)
        has_receipt = payload.get("has_receipt", payload.get("receipt", False))
        policy = self.POLICIES["fraud_prevention"]

        # Receipt requirement
        if amount > policy["receipt_threshold"] and not has_receipt:
            return IntentResult(
                intent_id=intent_id,
                allowed=False,
                verdict=PolicyVerdict.DENY,
                reason=f"Receipt required for expenses over ${policy['receipt_threshold']}",
                policy_triggered=policy["name"]
            )

        # High-value expense escalation
        limits = self.POLICIES["expense_limits"]["thresholds"]
        if amount > limits["cfo_approval"]:
            return IntentResult(
                intent_id=intent_id,
                allowed=False,
                verdict=PolicyVerdict.ESCALATE,
                reason=f"Expense ${amount:,.0f} requires CFO approval",
                policy_triggered="Expense Limits"
            )

        return None

    def _check_access(self, intent_id: str, payload: Dict) -> Optional[IntentResult]:
        role = payload.get("role", "").lower()
        systems = payload.get("systems", [])
        user = payload.get("user", "")
        policy = self.POLICIES["access_control"]

        # Contractor restrictions
        if "@external" in user or "contractor" in user.lower():
            for restricted in policy["contractor_restrictions"]:
                if restricted in role.lower():
                    return IntentResult(
                        intent_id=intent_id,
                        allowed=False,
                        verdict=PolicyVerdict.DENY,
                        reason=f"Contractors cannot have '{restricted}' access",
                        policy_triggered=policy["name"]
                    )

        # Admin review for sensitive systems
        for system in systems:
            if any(sensitive in system.lower() for sensitive in policy["admin_review_required"]):
                return IntentResult(
                    intent_id=intent_id,
                    allowed=False,
                    verdict=PolicyVerdict.ESCALATE,
                    reason=f"Access to '{system}' requires security review",
                    policy_triggered=policy["name"]
                )

        return None

    def _check_salary_cap(self, intent_id: str, payload: Dict) -> Optional[IntentResult]:
        role = payload.get("role", payload.get("level", ""))
        salary = payload.get("salary", payload.get("compensation", 0))
        policy = self.POLICIES["salary_caps"]
        bands = policy["bands"]

        if role in bands:
            band = bands[role]
            if salary > band["max"]:
                return IntentResult(
                    intent_id=intent_id,
                    allowed=False,
                    verdict=PolicyVerdict.DENY,
                    reason=f"Salary ${salary:,} exceeds ${band['max']:,} cap for {role}",
                    policy_triggered=policy["name"]
                )
            if salary < band["min"]:
                return IntentResult(
                    intent_id=intent_id,
                    allowed=False,
                    verdict=PolicyVerdict.DENY,
                    reason=f"Salary ${salary:,} below ${band['min']:,} minimum for {role}",
                    policy_triggered=policy["name"]
                )
        return None

    def _check_right_to_work(self, intent_id: str, payload: Dict) -> Optional[IntentResult]:
        i9_status = payload.get("i9_status", payload.get("i9", ""))
        policy = self.POLICIES["right_to_work"]

        if i9_status != "verified":
            return IntentResult(
                intent_id=intent_id,
                allowed=False,
                verdict=PolicyVerdict.DENY,
                reason="I-9 verification required before onboarding",
                policy_triggered=policy["name"]
            )
        return None

    def _check_communication(self, intent_id: str, payload: Dict) -> Optional[IntentResult]:
        body = payload.get("body", payload.get("message", payload.get("content", "")))
        recipient = payload.get("recipient", payload.get("to", ""))

        # Check inclusive language
        policy = self.POLICIES["inclusive_language"]
        for term in policy["blocked_terms"]:
            if term.lower() in body.lower():
                return IntentResult(
                    intent_id=intent_id,
                    allowed=False,
                    verdict=PolicyVerdict.DENY,
                    reason=f"Non-inclusive term detected: '{term}'",
                    policy_triggered=policy["name"]
                )

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
                if "body" in mod_payload:
                    mod_payload["body"] = modified_body
                elif "message" in mod_payload:
                    mod_payload["message"] = modified_body
                elif "content" in mod_payload:
                    mod_payload["content"] = modified_body

                return IntentResult(
                    intent_id=intent_id,
                    allowed=True,
                    verdict=PolicyVerdict.MODIFY,
                    reason="PII redacted for external recipient",
                    policy_triggered=pii_policy["name"],
                    modified_payload=mod_payload
                )

        return None

    def _check_procurement(self, intent_id: str, payload: Dict) -> Optional[IntentResult]:
        amount = payload.get("amount", payload.get("value", 0))
        has_po = payload.get("purchase_order", payload.get("po_number", False))
        policy = self.POLICIES["spending_limits"]

        if amount > policy["requires_po_above"] and not has_po:
            return IntentResult(
                intent_id=intent_id,
                allowed=False,
                verdict=PolicyVerdict.DENY,
                reason=f"Purchase order required for amounts over ${policy['requires_po_above']:,}",
                policy_triggered=policy["name"]
            )
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# WATCHTOWER ENTERPRISE INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

class WatchtowerOne:
    """
    Watchtower Enterprise Integration
    ==============================

    Unified verification layer combining:
    1. Watchtower SDK - Intent Authentication Protocol (IAP)
    2. TIRS - Temporal Intent Risk & Simulation (Drift Detection)
    3. LLM Reasoning - Autonomous decision making for edge cases

    The Triple-Layer Security Stack ensures:
    - Cryptographic intent verification (Watchtower)
    - Behavioral drift detection (TIRS)
    - Intelligent reasoning for edge cases (LLM)

    LIVE MODE (with API key):
        Uses real Watchtower SDK with cryptographic IAP.
        All actions verified through Watchtower before execution.

    DEMO MODE (no API key):
        Uses local policy engine for demonstrations.
        Simulates Watchtower behavior with configurable policies.

    Environment Variables:
        WATCHTOWER_API_KEY - Your Watchtower API key (ak_live_* or ak_test_*)
        WATCHTOWER_IAP_ENDPOINT - IAP endpoint
        WATCHTOWER_PROXY_ENDPOINT - Proxy endpoint
        WATCHTOWER_USER_ID - User identifier
        WATCHTOWER_AGENT_ID - Agent identifier

    Get API Key: https://platform.watchtower.io/dashboard/api-keys
    """

    def __init__(
        self,
        api_key: str = None,
        user_id: str = None,
        agent_id: str = None,
        iap_endpoint: str = None,
        proxy_endpoint: str = None,
        project_id: str = "watchtower-enterprise",
        enable_tirs: bool = True,
        enable_llm: bool = True,
    ):
        self.project_id = project_id
        self.api_key = api_key or WATCHTOWER_API_KEY
        self.user_id = user_id or WATCHTOWER_USER_ID
        self.agent_id = agent_id or WATCHTOWER_AGENT_ID
        self.iap_endpoint = iap_endpoint or WATCHTOWER_IAP_ENDPOINT
        self.proxy_endpoint = proxy_endpoint or WATCHTOWER_PROXY_ENDPOINT

        self.enable_tirs = enable_tirs
        self.enable_llm = enable_llm

        self.audit_log: List[Dict] = []
        self._intent_counter = 0
        self.client = None
        self.mode = "DEMO"

        # Initialize TIRS and LLM if available
        self._tirs = None
        self._llm = None
        self._reasoning = None

        # Try to initialize real Watchtower SDK
        if WATCHTOWER_SDK_AVAILABLE and self.api_key:
            if self.api_key.startswith("ak_live_") or self.api_key.startswith("ak_test_"):
                try:
                    self.client = WatchtowerClient(
                        api_key=self.api_key,
                        iap_endpoint=self.iap_endpoint,
                        proxy_endpoint=self.proxy_endpoint,
                        user_id=self.user_id,
                        agent_id=self.agent_id
                    )
                    self.mode = "LIVE"
                    logger.info("=" * 60)
                    logger.info("  Watchtower LIVE MODE - Intent Authentication Active")
                    logger.info("=" * 60)
                except Exception as e:
                    logger.warning(f"Watchtower SDK init failed: {e}")

        if self.mode == "DEMO":
            logger.info("=" * 60)
            logger.info("  Watchtower DEMO MODE - Local Policy Engine")
            logger.info(f"  Project: {project_id}")
            logger.info("=" * 60)

        self._local_engine = LocalPolicyEngine()
        self._initialize_layers()

    def _initialize_layers(self):
        """Initialize TIRS and LLM layers."""
        # Initialize TIRS
        if self.enable_tirs:
            try:
                from ..tirs import get_advanced_tirs
                self._tirs = get_advanced_tirs()
                logger.info("  TIRS Layer: ENABLED (Advanced)")
            except ImportError as e:
                logger.warning(f"  TIRS Layer: UNAVAILABLE ({e})")
                self._tirs = None
            except Exception as e:
                logger.warning(f"  TIRS Layer: ERROR ({e})")
                self._tirs = None

        # Initialize LLM
        if self.enable_llm:
            try:
                from ..llm import get_enterprise_llm, get_reasoning_engine
                self._llm = get_enterprise_llm()
                self._reasoning = get_reasoning_engine()
                logger.info("  LLM Layer: ENABLED")
            except ImportError as e:
                logger.warning(f"  LLM Layer: UNAVAILABLE ({e})")
                self._llm = None
                self._reasoning = None
            except Exception as e:
                logger.warning(f"  LLM Layer: ERROR ({e})")
                self._llm = None
                self._reasoning = None

    # ═══════════════════════════════════════════════════════════════════════════
    # UNIFIED VERIFICATION API (Watchtower + TIRS + LLM)
    # ═══════════════════════════════════════════════════════════════════════════

    def verify_intent(
        self,
        agent_id: str,
        action: str,
        payload: Dict,
        context: Dict = None,
    ) -> UnifiedVerificationResult:
        """
        Unified intent verification through all three layers.

        Flow:
        1. Watchtower: Verify intent with IAP
        2. TIRS: Check for behavioral drift
        3. LLM: Assess risk and provide reasoning (for edge cases)

        Args:
            agent_id: ID of the agent making the request
            action: Action to perform
            payload: Action parameters
            context: Additional context

        Returns:
            UnifiedVerificationResult with combined assessment
        """
        self._intent_counter += 1
        intent_id = f"ENT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self._intent_counter:04d}"
        context = context or {}

        logger.info(f"Verifying intent {intent_id}: {agent_id}.{action}")

        # Initialize result with layer status
        result = UnifiedVerificationResult(
            allowed=True,
            confidence=1.0,
            risk_level="low",
            intent_id=intent_id,
            layers_active={
                "watchtower": True,  # Always active (uses local engine as fallback)
                "tirs": self._tirs is not None,
                "llm": self._reasoning is not None,
            },
        )

        # ─────────────────────────────────────────────────────────────────────
        # Layer 1: Watchtower IAP
        # ─────────────────────────────────────────────────────────────────────
        watchtower_result = self._verify_watchtower(agent_id, action, payload)
        result.watchtower_result = watchtower_result
        result.watchtower_passed = watchtower_result.allowed

        # ─────────────────────────────────────────────────────────────────────
        # Layer 2: TIRS Drift Detection (ALWAYS run - even for blocked intents)
        # ─────────────────────────────────────────────────────────────────────
        # TIRS must analyze ALL intents to properly track behavioral drift.
        # Blocked intents are often the most revealing for risk assessment!
        tirs_data = None
        if self._tirs:
            tirs_data = self._check_tirs(
                agent_id, action, payload, context,
                was_allowed=watchtower_result.allowed
            )
            result.tirs_score = tirs_data.get("risk_score", 0.0)
            result.tirs_level = tirs_data.get("risk_level", "nominal")
            result.tirs_passed = result.tirs_score < 0.85

        # Handle Watchtower blocking (now with TIRS data populated)
        if not watchtower_result.allowed:
            result.allowed = False
            result.blocking_layer = "Watchtower"
            result.confidence = 1.0
            
            # Use TIRS risk level if available and higher than default
            if result.tirs_score >= 0.85:
                result.risk_level = "terminal"
            elif result.tirs_score >= 0.7:
                result.risk_level = "critical"
            elif result.tirs_score >= 0.5:
                result.risk_level = "high"
            else:
                result.risk_level = "high"  # Default for Watchtower blocks

            if watchtower_result.verdict == PolicyVerdict.ESCALATE:
                result.escalation_required = True
                if result.risk_level not in ["terminal", "critical"]:
                    result.risk_level = "critical"

            self._record_audit(result, agent_id, action, payload)
            return result

        if watchtower_result.verdict == PolicyVerdict.MODIFY:
            result.modified_payload = watchtower_result.modified_payload
            payload = watchtower_result.modified_payload or payload

            # TIRS blocking thresholds
            if result.tirs_score >= 0.85:
                result.allowed = False
                result.tirs_passed = False
                result.blocking_layer = "TIRS"
                result.risk_level = "critical"
                result.confidence = result.tirs_score
                self._record_audit(result, agent_id, action, payload)
                return result
            elif result.tirs_score >= 0.7:
                result.tirs_passed = False
                result.escalation_required = True
                result.risk_level = "high"
            elif result.tirs_score >= 0.5:
                result.risk_level = "medium"

        # ─────────────────────────────────────────────────────────────────────
        # Layer 3: LLM Reasoning (for edge cases)
        # ─────────────────────────────────────────────────────────────────────
        if self._reasoning and (result.escalation_required or result.tirs_score >= 0.5):
            llm_result = self._assess_with_llm(agent_id, action, payload, context, result, tirs_data)
            result.llm_reasoning = llm_result.get("reasoning", "")
            result.llm_confidence = llm_result.get("confidence", 1.0)
            result.llm_recommendation = llm_result.get("recommendation", "proceed")

            # LLM can override TIRS for edge cases with high confidence
            if result.llm_recommendation == "deny":
                result.allowed = False
                result.blocking_layer = "LLM"
            elif result.llm_recommendation == "escalate":
                result.escalation_required = True
            elif result.llm_recommendation == "proceed" and result.llm_confidence >= 0.9:
                # LLM confident it's safe - allow even if TIRS flagged
                if result.tirs_score < 0.85:  # Never override critical TIRS
                    result.allowed = True
                    result.escalation_required = False

                    # Record LLM override in TIRS for learning
                    if self._tirs and result.tirs_score >= 0.5:
                        self._record_llm_override(
                            agent_id=agent_id,
                            action=action,
                            tirs_score=result.tirs_score,
                            llm_confidence=result.llm_confidence,
                            llm_reasoning=result.llm_reasoning,
                        )

        # ─────────────────────────────────────────────────────────────────────
        # Final Decision
        # ─────────────────────────────────────────────────────────────────────
        if result.allowed:
            # Calculate combined confidence
            watchtower_conf = 1.0 if result.watchtower_passed else 0.0
            tirs_conf = 1.0 - result.tirs_score
            llm_conf = result.llm_confidence

            result.confidence = (watchtower_conf * 0.4 + tirs_conf * 0.4 + llm_conf * 0.2)

        self._record_audit(result, agent_id, action, payload)
        return result

    def _verify_watchtower(self, agent_id: str, action: str, payload: Dict) -> IntentResult:
        """Verify intent through Watchtower (or local engine in demo mode)."""
        if self.mode == "LIVE" and self.client:
            return self._verify_with_sdk(agent_id, action, payload)
        else:
            return self._local_engine.evaluate(action, payload, agent_id)

    def _verify_with_sdk(self, agent_id: str, action: str, payload: Dict) -> IntentResult:
        """Use real Watchtower SDK for verification."""
        intent_id = f"ARMOR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self._intent_counter:04d}"

        try:
            plan_structure = {
                "goal": f"{agent_id} executing {action}",
                "steps": [{
                    "mcp": "enterprise-tools",
                    "action": action,
                    "params": payload
                }]
            }

            plan = self.client.capture_plan(
                llm=agent_id,
                prompt=f"Execute {action}: {json.dumps(payload)[:100]}",
                plan=plan_structure
            )

            token = self.client.get_intent_token(plan)
            token_id = token.token_id if hasattr(token, 'token_id') else intent_id
            plan_hash = token.plan_hash if hasattr(token, 'plan_hash') else None

            # Apply local policies on top of Watchtower verification
            local_result = self._local_engine.evaluate(action, payload, agent_id)

            if not local_result.allowed:
                return IntentResult(
                    intent_id=token_id,
                    allowed=False,
                    verdict=local_result.verdict,
                    reason=local_result.reason,
                    policy_triggered=local_result.policy_triggered,
                    token=token,
                    plan_hash=plan_hash
                )

            return IntentResult(
                intent_id=token_id,
                allowed=True,
                verdict=local_result.verdict,
                reason="Watchtower verified + policy passed",
                modified_payload=local_result.modified_payload or payload,
                token=token,
                plan_hash=plan_hash
            )

        except Exception as e:
            logger.warning(f"Watchtower error: {e}, falling back to local")
            return self._local_engine.evaluate(action, payload, agent_id)

    def _check_tirs(
        self,
        agent_id: str,
        action: str,
        payload: Dict,
        context: Dict,
        was_allowed: bool = True,
    ) -> Dict:
        """Check intent through TIRS drift detection."""
        if not self._tirs:
            return {"risk_score": 0.0, "risk_level": "nominal"}

        try:
            # Build intent text from action and payload
            intent_text = f"{action}: {json.dumps(payload)[:200]}"

            # Extract capabilities from action
            capabilities = {action}

            # Analyze the intent with Advanced TIRS
            result = self._tirs.analyze_intent(
                agent_id=agent_id,
                intent_text=intent_text,
                capabilities=capabilities,
                was_allowed=was_allowed,
            )

            # Return TIRS result data
            return {
                "risk_score": result.risk_score,
                "risk_level": result.risk_level.value,
                "drift_detected": result.risk_score > 0.3,
                "explanation": result.explanation.summary if result.explanation else "",
                "signals": [
                    {"name": s.name, "value": s.raw_value, "contribution": s.contribution}
                    for s in result.drift_result.signals
                ] if result.drift_result else [],
                "tirs_result": result,  # Store full result for LLM
            }
        except Exception as e:
            logger.warning(f"TIRS error: {e}")
            import traceback
            traceback.print_exc()
            return {"risk_score": 0.0, "risk_level": "nominal"}

    def _assess_with_llm(
        self,
        agent_id: str,
        action: str,
        payload: Dict,
        context: Dict,
        current_result: UnifiedVerificationResult,
        tirs_data: Dict = None,
    ) -> Dict:
        """Use LLM reasoning for edge case assessment."""
        if not self._reasoning:
            return {"recommendation": "proceed", "confidence": 0.5, "reasoning": ""}

        try:
            # Build TIRS result dict for LLM (JSON serializable only)
            tirs_result = {
                "risk_score": current_result.tirs_score,
                "risk_level": current_result.tirs_level,
                "passed": current_result.tirs_passed,
            }
            # Add serializable parts from tirs_data
            if tirs_data:
                tirs_result["drift_detected"] = tirs_data.get("drift_detected", False)
                tirs_result["explanation"] = tirs_data.get("explanation", "")
                tirs_result["signals"] = tirs_data.get("signals", [])

            # Build context for reasoning
            reasoning_context = {
                "agent_id": agent_id,
                "watchtower_passed": current_result.watchtower_passed,
                **context,
            }

            # Call the reasoning engine
            result = self._reasoning.reason_about_action(
                agent_id=agent_id,
                action=action,
                payload=payload,
                context=reasoning_context,
                tirs_result=tirs_result,
            )

            # Map reasoning result to our format
            if result.should_proceed:
                recommendation = "proceed"
            elif result.decision.decision_type.value == "escalate":
                recommendation = "escalate"
            else:
                recommendation = "deny"

            return {
                "recommendation": recommendation,
                "confidence": result.overall_confidence,
                "reasoning": result.risk_assessment,
                "business_impact": result.business_impact,
                "warnings": result.warnings,
                "recommendations": result.recommendations,
            }
        except Exception as e:
            logger.warning(f"LLM reasoning error: {e}")
            import traceback
            traceback.print_exc()
            return {"recommendation": "proceed", "confidence": 0.5, "reasoning": ""}

    def _record_llm_override(
        self,
        agent_id: str,
        action: str,
        tirs_score: float,
        llm_confidence: float,
        llm_reasoning: str,
    ):
        """
        Record when LLM overrides a TIRS warning.

        This creates a feedback loop so TIRS can learn from LLM decisions
        and potentially adjust its thresholds or behavioral profiles.
        """
        if not self._tirs:
            return

        try:
            # Record in TIRS timeline for analysis
            from ..tirs.forensics.timeline import EventCategory, EventSeverity
            self._tirs.timeline.record_event(
                EventCategory.SYSTEM,
                EventSeverity.INFO,
                agent_id=agent_id,
                action="llm_override",
                description=f"LLM approved action that TIRS flagged (score={tirs_score:.2f})",
                details={
                    "action": action,
                    "tirs_score": tirs_score,
                    "llm_confidence": llm_confidence,
                    "llm_reasoning": llm_reasoning[:200] if llm_reasoning else "",
                },
            )

            # Record in audit chain if available
            if self._tirs.audit:
                from ..tirs.forensics.audit import AuditEventType
                self._tirs.audit.log(
                    event_type=AuditEventType.THRESHOLD_ADJUSTED,
                    agent_id=agent_id,
                    data={
                        "override_type": "llm_approved_tirs_warning",
                        "tirs_score": tirs_score,
                        "llm_confidence": llm_confidence,
                        "action": action,
                    },
                )

            logger.info(
                f"LLM override recorded for {agent_id}: "
                f"TIRS={tirs_score:.2f}, LLM_conf={llm_confidence:.2f}"
            )

        except Exception as e:
            logger.warning(f"Failed to record LLM override: {e}")

    # ═══════════════════════════════════════════════════════════════════════════
    # SIMPLE CAPTURE API (Backward Compatible)
    # ═══════════════════════════════════════════════════════════════════════════

    def capture_intent(
        self,
        action_type: str,
        payload: Dict,
        agent_name: str = None,
    ) -> IntentResult:
        """
        Simple intent verification (Watchtower only, for backward compatibility).

        For full verification including TIRS and LLM, use verify_intent().
        """
        agent_name = agent_name or self.agent_id
        return self._verify_watchtower(agent_name, action_type, payload)

    def invoke(
        self,
        mcp: str,
        action: str,
        params: Dict,
        intent_token: Any = None,
    ) -> Dict:
        """
        Execute an action through Watchtower proxy.

        In LIVE mode: Routes through Watchtower's secure proxy.
        In DEMO mode: Returns simulated success.
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
            except Exception as e:
                return {"status": "error", "error": str(e)}
        else:
            # DEMO mode: Simulate success
            return {
                "status": "success",
                "mode": "demo",
                "mcp": mcp,
                "action": action,
                "params": params,
                "result": {"simulated": True},
                "timestamp": datetime.now().isoformat()
            }

    # ═══════════════════════════════════════════════════════════════════════════
    # AUDIT & REPORTING
    # ═══════════════════════════════════════════════════════════════════════════

    def _record_audit(
        self,
        result: UnifiedVerificationResult,
        agent_id: str,
        action: str,
        payload: Dict,
    ):
        """Record verification in audit log."""
        self.audit_log.append({
            "intent_id": result.intent_id,
            "timestamp": result.timestamp.isoformat(),
            "agent_id": agent_id,
            "action": action,
            "allowed": result.allowed,
            "confidence": result.confidence,
            "risk_level": result.risk_level,
            "blocking_layer": result.blocking_layer,
            "watchtower_passed": result.watchtower_passed,
            "tirs_score": result.tirs_score,
            "tirs_level": result.tirs_level,
            "llm_recommendation": result.llm_recommendation,
            "escalation_required": result.escalation_required,
            "mode": self.mode,
        })

    def get_audit_report(self) -> Dict:
        """Generate audit report summary."""
        total = len(self.audit_log)
        denied = sum(1 for e in self.audit_log if not e["allowed"])
        escalated = sum(1 for e in self.audit_log if e["escalation_required"])

        by_layer = {"Watchtower": 0, "TIRS": 0, "LLM": 0}
        for e in self.audit_log:
            if e.get("blocking_layer"):
                by_layer[e["blocking_layer"]] = by_layer.get(e["blocking_layer"], 0) + 1

        by_risk = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for e in self.audit_log:
            level = e.get("risk_level", "low")
            by_risk[level] = by_risk.get(level, 0) + 1

        return {
            "project": self.project_id,
            "mode": self.mode,
            "layers": {
                "watchtower": True,
                "tirs": self._tirs is not None,
                "llm": self._llm is not None,
            },
            "total_intents": total,
            "allowed": total - denied,
            "denied": denied,
            "escalated": escalated,
            "by_blocking_layer": by_layer,
            "by_risk_level": by_risk,
            "recent_entries": self.audit_log[-10:],
        }

    def get_status(self) -> Dict:
        """Get integration status."""
        return {
            "mode": self.mode,
            "project": self.project_id,
            "layers": {
                "watchtower": {
                    "enabled": True,
                    "mode": self.mode,
                    "sdk_available": WATCHTOWER_SDK_AVAILABLE,
                },
                "tirs": {
                    "enabled": self.enable_tirs,
                    "available": self._tirs is not None,
                },
                "llm": {
                    "enabled": self.enable_llm,
                    "available": self._llm is not None,
                },
            },
            "intents_processed": self._intent_counter,
            "audit_entries": len(self.audit_log),
        }

    def close(self):
        """Close the Watchtower client connection."""
        if self.client:
            try:
                self.client.close()
            except Exception as e:
                logger.debug(f"Error closing Watchtower client: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON & EXPORTS
# ═══════════════════════════════════════════════════════════════════════════════

_watchtower: Optional[WatchtowerOne] = None


def get_watchtower() -> WatchtowerOne:
    """Get the global Watchtower Enterprise instance."""
    global _watchtower
    if _watchtower is None:
        _watchtower = WatchtowerOne()
    return _watchtower


def reset_watchtower():
    """Reset the global instance (for testing)."""
    global _watchtower
    if _watchtower:
        _watchtower.close()
    _watchtower = None
