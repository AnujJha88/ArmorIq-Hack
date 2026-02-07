"""
Enterprise LLM Service
======================
Centralized LLM service for autonomous enterprise agents.
Wraps the existing Gemini LLM client with enterprise-specific capabilities.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# Import the existing LLM client
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from hr_delegate.llm_client import LLMClient, LLMResponse, LLMMode, get_llm

logger = logging.getLogger("Enterprise.LLM")


class DecisionType(Enum):
    """Types of decisions agents can make."""
    APPROVE = "approve"
    DENY = "deny"
    ESCALATE = "escalate"
    MODIFY = "modify"
    DEFER = "defer"
    NEGOTIATE = "negotiate"


@dataclass
class DecisionContext:
    """Complete context for making a decision."""
    situation: str
    action: str
    payload: Dict[str, Any]

    # Constraints and signals
    compliance_signals: Dict[str, Any] = field(default_factory=dict)
    risk_signals: Dict[str, Any] = field(default_factory=dict)

    # Historical context
    agent_history: List[Dict] = field(default_factory=list)
    similar_decisions: List[Dict] = field(default_factory=list)

    # User/request context
    requester: Optional[str] = None
    department: Optional[str] = None
    urgency: str = "normal"

    def to_prompt(self) -> str:
        """Convert context to LLM prompt."""
        parts = [
            f"SITUATION: {self.situation}",
            f"ACTION REQUESTED: {self.action}",
            f"PAYLOAD: {json.dumps(self.payload, indent=2)}",
        ]

        if self.compliance_signals:
            parts.append(f"COMPLIANCE SIGNALS: {json.dumps(self.compliance_signals)}")

        if self.risk_signals:
            parts.append(f"RISK SIGNALS: {json.dumps(self.risk_signals)}")

        if self.requester:
            parts.append(f"REQUESTER: {self.requester} (Dept: {self.department})")

        if self.urgency != "normal":
            parts.append(f"URGENCY: {self.urgency}")

        if self.similar_decisions:
            parts.append(f"SIMILAR PAST DECISIONS: {json.dumps(self.similar_decisions[:3])}")

        return "\n".join(parts)


@dataclass
class AgentDecision:
    """Result of an autonomous decision."""
    decision_type: DecisionType
    action: str
    confidence: float  # 0.0 to 1.0

    # Reasoning
    reasoning: str
    factors_considered: List[str]
    alternatives_rejected: List[Dict[str, str]] = field(default_factory=list)

    # Modifications
    modified_payload: Optional[Dict] = None
    conditions: List[str] = field(default_factory=list)

    # Escalation
    escalate_to: Optional[str] = None
    escalation_reason: Optional[str] = None

    # Audit
    timestamp: datetime = field(default_factory=datetime.now)
    llm_tokens_used: int = 0

    def to_dict(self) -> Dict:
        return {
            "decision_type": self.decision_type.value,
            "action": self.action,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "factors_considered": self.factors_considered,
            "alternatives_rejected": self.alternatives_rejected,
            "modified_payload": self.modified_payload,
            "conditions": self.conditions,
            "escalate_to": self.escalate_to,
            "timestamp": self.timestamp.isoformat(),
        }


class EnterpriseLLM:
    """
    Enterprise LLM Service.

    Provides autonomous decision-making capabilities:
    - Intent understanding
    - Decision reasoning with explanations
    - Goal decomposition
    - Action planning
    - Error recovery suggestions
    - Multi-agent collaboration
    """

    ENTERPRISE_SYSTEM_PROMPT = """You are an autonomous AI agent in an enterprise system.
Your role is to make intelligent decisions about business operations across domains:
- Finance: expenses, budgets, invoices, payments
- Legal: contracts, compliance, IP, NDAs
- IT: access control, security, incidents
- HR: hiring, onboarding, payroll, benefits
- Procurement: vendors, purchases, inventory
- Operations: incidents, changes, SLAs

Decision Guidelines:
1. ALWAYS consider compliance and risk signals when making decisions
2. Be conservative with high-value or high-risk actions
3. Escalate when uncertain (confidence < 70%)
4. Provide clear reasoning for every decision
5. Consider alternatives before deciding
6. Protect PII and sensitive data
7. Follow the principle of least privilege for access decisions

When responding:
- Be precise and structured
- Output valid JSON when requested
- Include confidence scores (0.0-1.0)
- List factors you considered
- Explain rejected alternatives"""

    def __init__(self, llm_client: LLMClient = None):
        self.client = llm_client or get_llm()

        # Override system prompt for enterprise context
        if self.client._model:
            import google.generativeai as genai
            self.client._model = genai.GenerativeModel(
                model_name=self.client.model_name,
                system_instruction=self.ENTERPRISE_SYSTEM_PROMPT
            )

        logger.info(f"Enterprise LLM initialized (mode: {self.client.mode.value})")

    @property
    def mode(self) -> LLMMode:
        return self.client.mode

    def understand_intent(self, user_request: str, available_actions: List[str]) -> Dict[str, Any]:
        """
        Understand what the user really wants.

        Args:
            user_request: Natural language request
            available_actions: List of available action names

        Returns:
            Dict with 'intent', 'actions', 'parameters', 'clarifications_needed'
        """
        actions_list = ", ".join(available_actions)

        prompt = f"""Analyze this user request and determine the intent:

USER REQUEST: {user_request}

AVAILABLE ACTIONS: {actions_list}

Respond with JSON:
{{
    "intent": "brief description of what user wants",
    "primary_action": "best matching action from available list",
    "secondary_actions": ["other actions that may be needed"],
    "extracted_parameters": {{"key": "value"}},
    "confidence": 0.0-1.0,
    "clarifications_needed": ["questions if anything is unclear"],
    "reasoning": "why you interpreted it this way"
}}

Only output the JSON."""

        response = self.client.complete(prompt, self.ENTERPRISE_SYSTEM_PROMPT)

        try:
            content = self._extract_json(response.content)
            return json.loads(content)
        except json.JSONDecodeError:
            return {
                "intent": user_request,
                "primary_action": available_actions[0] if available_actions else "unknown",
                "secondary_actions": [],
                "extracted_parameters": {},
                "confidence": 0.3,
                "clarifications_needed": ["Could not parse request clearly"],
                "reasoning": response.content
            }

    def make_decision(self, context: DecisionContext) -> AgentDecision:
        """
        Make an autonomous decision about an action.

        Args:
            context: Full decision context

        Returns:
            AgentDecision with reasoning
        """
        prompt = f"""Make a decision about this enterprise action:

{context.to_prompt()}

Consider:
1. Is this action appropriate given the context?
2. Are there compliance or risk concerns?
3. Should this be approved, denied, modified, or escalated?
4. What conditions should apply?

Respond with JSON:
{{
    "decision": "approve|deny|escalate|modify|defer",
    "confidence": 0.0-1.0,
    "reasoning": "detailed explanation",
    "factors_considered": ["factor1", "factor2"],
    "alternatives_rejected": [
        {{"option": "description", "why_rejected": "reason"}}
    ],
    "modified_payload": null or {{"key": "new_value"}},
    "conditions": ["condition if any"],
    "escalate_to": null or "role/person",
    "escalation_reason": null or "why escalation needed"
}}

Only output the JSON."""

        response = self.client.complete(prompt, self.ENTERPRISE_SYSTEM_PROMPT)

        try:
            content = self._extract_json(response.content)
            result = json.loads(content)

            decision_map = {
                "approve": DecisionType.APPROVE,
                "deny": DecisionType.DENY,
                "escalate": DecisionType.ESCALATE,
                "modify": DecisionType.MODIFY,
                "defer": DecisionType.DEFER,
                "negotiate": DecisionType.NEGOTIATE,
            }

            return AgentDecision(
                decision_type=decision_map.get(result.get("decision", "deny"), DecisionType.DENY),
                action=context.action,
                confidence=float(result.get("confidence", 0.5)),
                reasoning=result.get("reasoning", "No reasoning provided"),
                factors_considered=result.get("factors_considered", []),
                alternatives_rejected=result.get("alternatives_rejected", []),
                modified_payload=result.get("modified_payload"),
                conditions=result.get("conditions", []),
                escalate_to=result.get("escalate_to"),
                escalation_reason=result.get("escalation_reason"),
                llm_tokens_used=response.tokens_used,
            )
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse decision: {e}")
            # Default to safe decision
            return AgentDecision(
                decision_type=DecisionType.ESCALATE,
                action=context.action,
                confidence=0.3,
                reasoning=f"Could not parse LLM response: {response.content[:200]}",
                factors_considered=["parsing_error"],
                escalate_to="human_operator",
                escalation_reason="LLM response could not be parsed",
            )

    def decompose_goal(
        self,
        goal: str,
        available_agents: Dict[str, Set[str]],
        constraints: List[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Decompose a high-level goal into agent actions.

        Args:
            goal: High-level goal description
            available_agents: Dict mapping agent_id to set of capabilities
            constraints: List of constraints to consider

        Returns:
            List of action steps with agent assignments
        """
        agents_desc = "\n".join([
            f"- {agent_id}: {', '.join(caps)}"
            for agent_id, caps in available_agents.items()
        ])

        constraints_text = "\n".join(f"- {c}" for c in (constraints or []))
        constraints_section = f"CONSTRAINTS:\n{constraints_text}" if constraints else ""

        prompt = f"""Decompose this goal into a sequence of agent actions:

GOAL: {goal}

AVAILABLE AGENTS AND CAPABILITIES:
{agents_desc}

{constraints_section}

Create a step-by-step plan. Respond with JSON array:
[
    {{
        "step": 1,
        "agent_id": "which agent",
        "action": "action to perform",
        "parameters": {{}},
        "depends_on": [],
        "reason": "why this step",
        "can_parallelize": false
    }}
]

Order steps logically. Identify dependencies. Mark parallelizable steps.
Only output the JSON array."""

        response = self.client.complete(prompt, self.ENTERPRISE_SYSTEM_PROMPT)

        try:
            content = self._extract_json(response.content)
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning("Failed to parse goal decomposition")
            return []

    def suggest_recovery(
        self,
        failed_action: str,
        error: str,
        available_alternatives: List[str],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Suggest recovery options when an action fails.

        Args:
            failed_action: The action that failed
            error: Error message
            available_alternatives: Alternative actions available
            context: Current context

        Returns:
            Dict with recovery suggestions
        """
        alternatives_list = ", ".join(available_alternatives)

        prompt = f"""An enterprise action failed. Suggest recovery options:

FAILED ACTION: {failed_action}
ERROR: {error}
CONTEXT: {json.dumps(context)}
AVAILABLE ALTERNATIVES: {alternatives_list}

Respond with JSON:
{{
    "analysis": "what went wrong",
    "recoverable": true/false,
    "suggestions": [
        {{
            "option": "description",
            "action": "alternative action or null",
            "parameters": {{}},
            "success_probability": 0.0-1.0,
            "tradeoffs": "what we give up"
        }}
    ],
    "escalation_needed": true/false,
    "escalation_reason": "if escalation needed, why"
}}

Only output the JSON."""

        response = self.client.complete(prompt, self.ENTERPRISE_SYSTEM_PROMPT)

        try:
            content = self._extract_json(response.content)
            return json.loads(content)
        except json.JSONDecodeError:
            return {
                "analysis": "Could not analyze failure",
                "recoverable": False,
                "suggestions": [],
                "escalation_needed": True,
                "escalation_reason": "Automated recovery not available"
            }

    def negotiate_constraints(
        self,
        agent1_position: Dict[str, Any],
        agent2_position: Dict[str, Any],
        shared_goal: str,
    ) -> Dict[str, Any]:
        """
        Help agents negotiate conflicting constraints.

        Args:
            agent1_position: First agent's constraints and requirements
            agent2_position: Second agent's constraints and requirements
            shared_goal: What both agents are trying to achieve

        Returns:
            Negotiation result with compromise
        """
        prompt = f"""Two enterprise agents have conflicting constraints. Find a compromise:

SHARED GOAL: {shared_goal}

AGENT 1 POSITION:
{json.dumps(agent1_position, indent=2)}

AGENT 2 POSITION:
{json.dumps(agent2_position, indent=2)}

Find a solution that:
1. Achieves the shared goal
2. Respects hard constraints from both agents
3. Compromises on flexible constraints

Respond with JSON:
{{
    "resolution_possible": true/false,
    "compromise": {{
        "description": "what the compromise is",
        "agent1_concessions": ["what agent1 gives up"],
        "agent2_concessions": ["what agent2 gives up"],
        "modified_parameters": {{}}
    }},
    "blocking_constraints": ["constraints that cannot be resolved"],
    "escalation_recommendation": "if not resolvable, who to escalate to"
}}

Only output the JSON."""

        response = self.client.complete(prompt, self.ENTERPRISE_SYSTEM_PROMPT)

        try:
            content = self._extract_json(response.content)
            return json.loads(content)
        except json.JSONDecodeError:
            return {
                "resolution_possible": False,
                "compromise": None,
                "blocking_constraints": ["Could not analyze constraints"],
                "escalation_recommendation": "human_operator"
            }

    def explain_decision(self, decision: AgentDecision) -> str:
        """
        Generate a human-readable explanation of a decision.

        Args:
            decision: The decision to explain

        Returns:
            Human-readable explanation
        """
        prompt = f"""Explain this enterprise decision in plain language for a human operator:

DECISION: {decision.decision_type.value}
ACTION: {decision.action}
CONFIDENCE: {decision.confidence * 100:.0f}%
REASONING: {decision.reasoning}
FACTORS: {', '.join(decision.factors_considered)}
CONDITIONS: {', '.join(decision.conditions) if decision.conditions else 'None'}

Write a clear, concise explanation (2-3 sentences) that a business user would understand.
Do not use technical jargon. Focus on the "why" not the "how"."""

        response = self.client.complete(prompt, self.ENTERPRISE_SYSTEM_PROMPT)
        return response.content.strip()

    def _extract_json(self, content: str) -> str:
        """Extract JSON from LLM response (handles markdown code blocks)."""
        content = content.strip()
        if content.startswith("```"):
            parts = content.split("```")
            if len(parts) >= 2:
                content = parts[1]
                if content.startswith("json"):
                    content = content[4:]
        return content.strip()


# Singleton
_enterprise_llm: Optional[EnterpriseLLM] = None


def get_enterprise_llm() -> EnterpriseLLM:
    """Get the singleton Enterprise LLM."""
    global _enterprise_llm
    if _enterprise_llm is None:
        _enterprise_llm = EnterpriseLLM()
    return _enterprise_llm


def reset_enterprise_llm():
    """Reset the singleton (for testing)."""
    global _enterprise_llm
    _enterprise_llm = None
