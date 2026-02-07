"""
Reasoning Engine
================
Provides structured reasoning capabilities for autonomous agents.
"""

import logging
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .service import EnterpriseLLM, DecisionContext, AgentDecision, DecisionType, get_enterprise_llm

logger = logging.getLogger("Enterprise.Reasoning")


class ReasoningMode(Enum):
    """How deep should reasoning go."""
    QUICK = "quick"       # Fast, shallow reasoning
    STANDARD = "standard" # Normal depth
    DEEP = "deep"         # Thorough analysis
    CRITICAL = "critical" # Maximum scrutiny (high-risk actions)


@dataclass
class ReasoningResult:
    """Result of reasoning about an action."""
    # Decision
    should_proceed: bool
    decision: AgentDecision

    # Analysis
    risk_assessment: str
    compliance_assessment: str
    business_impact: str

    # Confidence
    overall_confidence: float
    uncertainty_factors: List[str]

    # Recommendations
    recommendations: List[str]
    warnings: List[str]

    # Audit
    reasoning_mode: ReasoningMode
    reasoning_time_ms: float
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            "should_proceed": self.should_proceed,
            "decision": self.decision.to_dict(),
            "risk_assessment": self.risk_assessment,
            "compliance_assessment": self.compliance_assessment,
            "business_impact": self.business_impact,
            "overall_confidence": self.overall_confidence,
            "uncertainty_factors": self.uncertainty_factors,
            "recommendations": self.recommendations,
            "warnings": self.warnings,
            "reasoning_mode": self.reasoning_mode.value,
            "reasoning_time_ms": self.reasoning_time_ms,
            "timestamp": self.timestamp.isoformat(),
        }


class ReasoningEngine:
    """
    Reasoning Engine for autonomous agent decision-making.

    Provides:
    - Multi-step reasoning about actions
    - Risk and compliance analysis
    - Confidence assessment
    - Recommendation generation
    """

    # Thresholds for automatic decisions
    AUTO_APPROVE_CONFIDENCE = 0.85
    AUTO_DENY_RISK_THRESHOLD = 0.8
    ESCALATION_THRESHOLD = 0.5

    def __init__(self, llm: EnterpriseLLM = None):
        self.llm = llm or get_enterprise_llm()
        logger.info("Reasoning Engine initialized")

    def reason_about_action(
        self,
        agent_id: str,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
        compliance_result: Optional[Dict] = None,
        tirs_result: Optional[Dict] = None,
        mode: ReasoningMode = ReasoningMode.STANDARD,
    ) -> ReasoningResult:
        """
        Reason about whether an action should be executed.

        Args:
            agent_id: The agent considering the action
            action: Action to perform
            payload: Action parameters
            context: Request context
            compliance_result: Results from compliance engine
            tirs_result: Results from TIRS engine
            mode: How deep to reason

        Returns:
            ReasoningResult with decision and analysis
        """
        import time
        start_time = time.time()

        # Build decision context
        decision_context = DecisionContext(
            situation=f"Agent {agent_id} wants to execute action '{action}'",
            action=action,
            payload=payload,
            compliance_signals=compliance_result or {},
            risk_signals=tirs_result or {},
            requester=context.get("user") or context.get("requester"),
            department=context.get("department"),
            urgency=context.get("urgency", "normal"),
        )

        # Check for automatic decisions based on signals
        auto_decision = self._check_automatic_decision(
            compliance_result, tirs_result, action, payload
        )

        if auto_decision and mode != ReasoningMode.CRITICAL:
            # Use automatic decision for non-critical mode
            reasoning_time = (time.time() - start_time) * 1000
            return ReasoningResult(
                should_proceed=auto_decision.decision_type == DecisionType.APPROVE,
                decision=auto_decision,
                risk_assessment=auto_decision.reasoning,
                compliance_assessment="Automatic check passed" if auto_decision.decision_type == DecisionType.APPROVE else "Compliance concern",
                business_impact="Low - routine action" if auto_decision.decision_type == DecisionType.APPROVE else "Action blocked",
                overall_confidence=auto_decision.confidence,
                uncertainty_factors=[],
                recommendations=[],
                warnings=auto_decision.conditions,
                reasoning_mode=mode,
                reasoning_time_ms=reasoning_time,
            )

        # Use LLM for deeper reasoning
        decision = self.llm.make_decision(decision_context)

        # Analyze results
        risk_assessment = self._assess_risk(tirs_result, decision)
        compliance_assessment = self._assess_compliance(compliance_result, decision)
        business_impact = self._assess_business_impact(action, payload, decision)

        # Calculate overall confidence
        overall_confidence = self._calculate_confidence(
            decision.confidence,
            compliance_result,
            tirs_result,
        )

        # Identify uncertainties
        uncertainty_factors = self._identify_uncertainties(
            decision, compliance_result, tirs_result
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            decision, action, payload, context
        )

        # Generate warnings
        warnings = self._generate_warnings(
            decision, compliance_result, tirs_result, overall_confidence
        )

        # Determine if we should proceed
        should_proceed = self._should_proceed(
            decision, overall_confidence, compliance_result, tirs_result
        )

        reasoning_time = (time.time() - start_time) * 1000

        logger.info(
            f"Reasoning complete for {agent_id}/{action}: "
            f"proceed={should_proceed}, confidence={overall_confidence:.2f}, "
            f"time={reasoning_time:.1f}ms"
        )

        return ReasoningResult(
            should_proceed=should_proceed,
            decision=decision,
            risk_assessment=risk_assessment,
            compliance_assessment=compliance_assessment,
            business_impact=business_impact,
            overall_confidence=overall_confidence,
            uncertainty_factors=uncertainty_factors,
            recommendations=recommendations,
            warnings=warnings,
            reasoning_mode=mode,
            reasoning_time_ms=reasoning_time,
        )

    def _check_automatic_decision(
        self,
        compliance_result: Optional[Dict],
        tirs_result: Optional[Dict],
        action: str,
        payload: Dict,
    ) -> Optional[AgentDecision]:
        """Check if we can make an automatic decision without LLM."""

        # Auto-deny if compliance blocked
        if compliance_result and not compliance_result.get("allowed", True):
            return AgentDecision(
                decision_type=DecisionType.DENY,
                action=action,
                confidence=0.95,
                reasoning="Compliance policy blocked this action",
                factors_considered=["compliance_violation"],
                conditions=compliance_result.get("policies_triggered", []),
            )

        # Auto-deny if TIRS risk is terminal
        if tirs_result:
            risk_level = tirs_result.get("risk_level", "nominal")
            if risk_level in ["terminal", "critical"]:
                return AgentDecision(
                    decision_type=DecisionType.DENY,
                    action=action,
                    confidence=0.9,
                    reasoning=f"TIRS risk level is {risk_level}",
                    factors_considered=["high_risk_score"],
                    escalate_to="security_team",
                    escalation_reason="High drift risk detected",
                )

        # Auto-approve for low-risk, compliant actions
        if compliance_result and tirs_result:
            is_compliant = compliance_result.get("allowed", True)
            risk_score = tirs_result.get("risk_score", 0)

            if is_compliant and risk_score < 0.3:
                # Check if it's a low-value action
                amount = payload.get("amount", 0)
                if isinstance(amount, (int, float)) and amount < 500:
                    return AgentDecision(
                        decision_type=DecisionType.APPROVE,
                        action=action,
                        confidence=0.9,
                        reasoning="Low-risk, compliant action with low value",
                        factors_considered=["low_value", "compliant", "low_risk"],
                    )

        return None

    def _assess_risk(self, tirs_result: Optional[Dict], decision: AgentDecision) -> str:
        """Generate risk assessment text."""
        if not tirs_result:
            return "No TIRS data available for risk assessment"

        risk_score = tirs_result.get("risk_score", 0)
        risk_level = tirs_result.get("risk_level", "unknown")

        if risk_score < 0.3:
            return f"LOW RISK: Score {risk_score:.2f} ({risk_level}). Action appears routine."
        elif risk_score < 0.5:
            return f"MODERATE RISK: Score {risk_score:.2f} ({risk_level}). Some deviation from normal patterns."
        elif risk_score < 0.7:
            return f"ELEVATED RISK: Score {risk_score:.2f} ({risk_level}). Significant behavioral drift detected."
        else:
            return f"HIGH RISK: Score {risk_score:.2f} ({risk_level}). Action requires careful scrutiny."

    def _assess_compliance(self, compliance_result: Optional[Dict], decision: AgentDecision) -> str:
        """Generate compliance assessment text."""
        if not compliance_result:
            return "No compliance data available"

        if compliance_result.get("allowed", True):
            policies = compliance_result.get("policies_checked", [])
            return f"COMPLIANT: Passed {len(policies)} policy checks"
        else:
            triggered = compliance_result.get("policies_triggered", [])
            return f"NON-COMPLIANT: Blocked by policies: {', '.join(triggered)}"

    def _assess_business_impact(
        self, action: str, payload: Dict, decision: AgentDecision
    ) -> str:
        """Assess potential business impact."""
        amount = payload.get("amount", 0)

        if isinstance(amount, (int, float)):
            if amount > 100000:
                return f"HIGH IMPACT: Large financial transaction (${amount:,.2f})"
            elif amount > 10000:
                return f"MODERATE IMPACT: Significant transaction (${amount:,.2f})"
            elif amount > 1000:
                return f"LOW-MODERATE IMPACT: Standard transaction (${amount:,.2f})"

        # Check for sensitive operations
        sensitive_actions = [
            "provision_access", "revoke_access", "terminate", "offboard",
            "approve_vendor", "sign_contract", "release_payment"
        ]
        if action in sensitive_actions:
            return "MODERATE IMPACT: Sensitive operation requiring verification"

        return "LOW IMPACT: Routine operation"

    def _calculate_confidence(
        self,
        llm_confidence: float,
        compliance_result: Optional[Dict],
        tirs_result: Optional[Dict],
    ) -> float:
        """Calculate overall confidence in the decision."""
        # Start with LLM confidence
        confidence = llm_confidence

        # Boost if compliance is clear
        if compliance_result:
            if compliance_result.get("allowed", True):
                confidence = min(confidence + 0.1, 1.0)
            else:
                confidence = min(confidence + 0.15, 1.0)  # Clear denial is also confident

        # Reduce if risk is elevated
        if tirs_result:
            risk_score = tirs_result.get("risk_score", 0)
            if risk_score > 0.5:
                confidence = confidence * (1 - risk_score * 0.3)

        return round(confidence, 3)

    def _identify_uncertainties(
        self,
        decision: AgentDecision,
        compliance_result: Optional[Dict],
        tirs_result: Optional[Dict],
    ) -> List[str]:
        """Identify factors creating uncertainty."""
        uncertainties = []

        if decision.confidence < 0.7:
            uncertainties.append("LLM confidence below 70%")

        if not compliance_result:
            uncertainties.append("No compliance data available")

        if not tirs_result:
            uncertainties.append("No TIRS risk data available")

        if tirs_result and tirs_result.get("risk_level") == "elevated":
            uncertainties.append("Behavioral drift detected")

        if decision.escalate_to:
            uncertainties.append(f"Decision suggests escalation to {decision.escalate_to}")

        return uncertainties

    def _generate_recommendations(
        self,
        decision: AgentDecision,
        action: str,
        payload: Dict,
        context: Dict,
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        if decision.decision_type == DecisionType.MODIFY:
            recommendations.append("Consider the suggested payload modifications")

        if decision.conditions:
            recommendations.append(f"Ensure conditions are met: {', '.join(decision.conditions)}")

        if decision.decision_type == DecisionType.ESCALATE:
            recommendations.append(f"Escalate to {decision.escalate_to} before proceeding")

        # Add context-specific recommendations
        amount = payload.get("amount", 0)
        if isinstance(amount, (int, float)) and amount > 10000:
            recommendations.append("Consider requiring dual approval for large amounts")

        return recommendations

    def _generate_warnings(
        self,
        decision: AgentDecision,
        compliance_result: Optional[Dict],
        tirs_result: Optional[Dict],
        confidence: float,
    ) -> List[str]:
        """Generate warning messages."""
        warnings = []

        if confidence < self.ESCALATION_THRESHOLD:
            warnings.append(f"LOW CONFIDENCE ({confidence:.0%}): Consider manual review")

        if tirs_result:
            risk_score = tirs_result.get("risk_score", 0)
            if risk_score > 0.5:
                warnings.append(f"ELEVATED RISK SCORE: {risk_score:.2f}")

        if decision.alternatives_rejected:
            warnings.append(f"Rejected {len(decision.alternatives_rejected)} alternative approaches")

        if decision.decision_type == DecisionType.DENY:
            warnings.append("ACTION WILL BE BLOCKED")

        return warnings

    def _should_proceed(
        self,
        decision: AgentDecision,
        confidence: float,
        compliance_result: Optional[Dict],
        tirs_result: Optional[Dict],
    ) -> bool:
        """Determine if the action should proceed."""

        # Never proceed if compliance blocked
        if compliance_result and not compliance_result.get("allowed", True):
            return False

        # Never proceed if TIRS risk is terminal
        if tirs_result and tirs_result.get("risk_level") in ["terminal", "killed"]:
            return False

        # Check decision type
        if decision.decision_type == DecisionType.DENY:
            return False

        if decision.decision_type == DecisionType.ESCALATE:
            return False  # Needs human approval

        if decision.decision_type == DecisionType.DEFER:
            return False  # Needs to wait

        # Check confidence
        if confidence < self.ESCALATION_THRESHOLD:
            return False  # Too uncertain

        # Approve or Modify can proceed
        return decision.decision_type in [DecisionType.APPROVE, DecisionType.MODIFY]

    def reflect_on_outcome(
        self,
        reasoning_result: ReasoningResult,
        actual_outcome: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Reflect on a decision after seeing the outcome.

        Args:
            reasoning_result: Original reasoning
            actual_outcome: What actually happened

        Returns:
            Reflection with lessons learned
        """
        prompt = f"""Reflect on this decision and its outcome:

ORIGINAL DECISION: {reasoning_result.decision.decision_type.value}
REASONING: {reasoning_result.decision.reasoning}
CONFIDENCE: {reasoning_result.overall_confidence:.0%}

ACTUAL OUTCOME:
{actual_outcome}

Analyze:
1. Was the decision correct?
2. What did we learn?
3. How should we adjust future decisions?

Respond with JSON:
{{
    "decision_quality": "correct|partially_correct|incorrect",
    "lessons_learned": ["lesson1", "lesson2"],
    "adjustment_recommendations": ["rec1", "rec2"],
    "confidence_calibration": "overconfident|calibrated|underconfident"
}}"""

        response = self.llm.client.complete(prompt)

        try:
            import json
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content)
        except:
            return {
                "decision_quality": "unknown",
                "lessons_learned": [],
                "adjustment_recommendations": [],
                "confidence_calibration": "unknown"
            }


# Singleton
_reasoning_engine: Optional[ReasoningEngine] = None


def get_reasoning_engine() -> ReasoningEngine:
    """Get the singleton reasoning engine."""
    global _reasoning_engine
    if _reasoning_engine is None:
        _reasoning_engine = ReasoningEngine()
    return _reasoning_engine


def reset_reasoning_engine():
    """Reset the singleton (for testing)."""
    global _reasoning_engine
    _reasoning_engine = None
