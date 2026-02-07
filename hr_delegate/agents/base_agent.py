"""
HR Agent Base Class with LLM + ArmorIQ Integration
===================================================
All agents inherit from this and use:
- LLM for reasoning and decision-making
- ArmorIQ for intent verification and tool invocation
- TIRS for temporal drift detection
"""

import json
import logging
import sys
import os
from typing import Dict, List, Tuple, Set, Optional, Any
from datetime import datetime

# Add paths for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from hr_delegate.policies.armoriq_sdk import ArmorIQWrapper, get_armoriq, PolicyVerdict

# LLM Integration
try:
    from hr_delegate.llm_client import LLMClient, get_llm, LLMMode
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    LLMMode = None

# TIRS Integration
try:
    from tirs.core import get_tirs, TIRSResult
    from tirs.drift_engine import RiskLevel, AgentStatus
    TIRS_AVAILABLE = True
except ImportError:
    TIRS_AVAILABLE = False
    RiskLevel = None
    AgentStatus = None

# Observability Integration
try:
    from hr_delegate.observability import (
        get_tracer, get_metrics, get_event_stream,
        trace_agent_action, trace_tool_execution, AgentEvent
    )
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False
    trace_agent_action = lambda *args, **kwargs: lambda f: f  # No-op decorator
    trace_tool_execution = lambda f: f

logging.basicConfig(level=logging.INFO, format='[%(name)s] %(message)s')


class HRAgent:
    """
    Base HR Agent with LLM + ArmorIQ + TIRS Integration
    =====================================================
    
    Every agent action goes through:
    1. LLM - Reasoning and decision-making
    2. ArmorIQ - Policy verification + tool invocation
    3. TIRS - Temporal drift detection & plan simulation
    
    Key methods:
    - reason(question): Ask LLM to reason about something
    - decide(options): Ask LLM to choose between options
    - plan(goal): Ask LLM to create a plan
    - execute_tool(mcp, action, params): Execute tool through ArmorIQ
    """

    def __init__(self, name: str, primary_intent: str):
        self.name = name
        self.primary_intent = primary_intent
        self.logger = logging.getLogger(name)
        
        # LLM: Get the LLM client for reasoning
        self.llm = get_llm() if LLM_AVAILABLE else None
        if self.llm:
            mode = self.llm.mode.value if hasattr(self.llm.mode, 'value') else 'unknown'
            self.logger.info(f"🤖 LLM enabled ({mode} mode)")

        # ARMORIQ: Get the shared client for intent verification + tool invocation
        self.armoriq = get_armoriq()

        # TIRS: Get temporal intent risk engine
        self.tirs = get_tirs() if TIRS_AVAILABLE else None
        if self.tirs:
            self.logger.info(f"🛡️  TIRS enabled for {name}")

        self.action_log: List[Dict] = []
        self.is_connected = False
        self._paused = False
        self._killed = False
        
        # Observability: Register metrics
        if OBSERVABILITY_AVAILABLE:
            self._metrics = get_metrics()
            self._events = get_event_stream()
            self.logger.info(f"📊 Observability enabled")
        else:
            self._metrics = None
            self._events = None

    def start(self):
        self.is_connected = True
        self.logger.info(f"🟢 {self.name} Agent ONLINE")
        
        # Track active agents
        if self._metrics:
            self._metrics.gauge("active_agents").inc({"agent": self.name})

    def stop(self):
        self.is_connected = False
        self.logger.info(f"🔴 {self.name} Agent OFFLINE")
        
        # Track active agents
        if self._metrics:
            self._metrics.gauge("active_agents").dec({"agent": self.name})

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

    # ═══════════════════════════════════════════════════════════════════════════════
    # LLM-POWERED REASONING METHODS
    # ═══════════════════════════════════════════════════════════════════════════════

    def think(self, prompt: str) -> str:
        """Ask the LLM for reasoning (legacy method, use reason() instead)."""
        if self.llm:
            response = self.llm.complete(prompt)
            return response.content
        return f"[No LLM] {prompt[:50]}..."

    def reason(self, question: str, context: str = "") -> str:
        """
        Ask the LLM to reason about a question.
        
        Args:
            question: The question to reason about
            context: Additional context for the LLM
            
        Returns:
            LLM's reasoning as a string
        """
        if not self.llm:
            return f"[No LLM available] Question: {question}"
        
        agent_context = f"""You are the {self.name} agent in an HR system.
Your primary function is: {self.primary_intent}

{context}"""
        
        response = self.llm.reason(agent_context, question)
        self.logger.info(f"🧠 LLM Reasoning: {response.content[:100]}...")
        return response.content

    def decide(self, options: List[str], context: str = "", criteria: str = None) -> Dict[str, Any]:
        """
        Ask the LLM to choose between options.
        
        Args:
            options: List of options to choose from
            context: Situation/context
            criteria: Optional decision criteria
            
        Returns:
            Dict with 'choice' (index), 'option' (text), and 'reasoning'
        """
        if not self.llm:
            return {"choice": 0, "option": options[0], "reasoning": "No LLM - defaulting to first option"}
        
        agent_context = f"""You are the {self.name} agent.
Primary function: {self.primary_intent}

{context}"""
        
        decision = self.llm.decide(agent_context, options, criteria)
        self.logger.info(f"🎯 LLM Decision: Option {decision['choice']+1} - {decision['option'][:50]}")
        return decision

    def plan(self, goal: str, available_tools: List[str] = None) -> List[Dict]:
        """
        Ask the LLM to create a plan to achieve a goal.
        
        Args:
            goal: The goal to achieve
            available_tools: List of available tool names
            
        Returns:
            List of planned action dicts
        """
        if not self.llm:
            return []
        
        # Default tools based on agent type
        if available_tools is None:
            available_tools = ["email", "calendar", "hris", "offer", "payroll"]
        
        context = f"You are the {self.name} agent. Primary function: {self.primary_intent}"
        
        plan = self.llm.plan_actions(goal, available_tools, context)
        self.logger.info(f"📋 LLM Plan: {len(plan)} steps to achieve: {goal[:50]}")
        return plan

    # ═══════════════════════════════════════════════════════════════════════════════
    # TOOL EXECUTION THROUGH ARMORIQ
    # ═══════════════════════════════════════════════════════════════════════════════

    def execute_tool(self, mcp: str, action: str, params: Dict, description: str = None) -> Dict[str, Any]:
        """
        Execute a tool through ArmorIQ's invoke() proxy.
        
        This is the PROPER way to execute tools in an agentic system:
        1. Agent decides to use a tool (via LLM or programmatically)
        2. ArmorIQ verifies the intent and gets a token
        3. Tool is executed through ArmorIQ.invoke()
        4. Result is returned to agent
        
        Args:
            mcp: MCP name (e.g., "email", "calendar", "hris")
            action: Action to perform (e.g., "send", "book", "lookup")
            params: Parameters for the action
            description: Human-readable description of what we're doing
            
        Returns:
            Dict with 'success', 'result', and optional 'error'
        """
        import time
        start_time = time.time()
        
        # Check if agent can continue
        can_continue, reason = self.check_status()
        if not can_continue:
            return {"success": False, "error": reason}
        
        # Build intent type
        intent_type = f"{mcp}.{action}"
        desc = description or f"{self.name} executing {intent_type}"
        
        self.logger.info(f"🔧 Executing tool: {intent_type}")
        
        # Track ArmorIQ intent
        if self._metrics:
            self._metrics.counter("armoriq_intents_total").inc({"agent": self.name, "mcp": mcp})
        
        # Step 1: Verify intent with ArmorIQ
        result = self.armoriq.capture_intent(intent_type, params, self.name)
        
        # Step 2: Track with TIRS
        if self.tirs:
            capabilities = self._extract_capabilities(intent_type, params)
            risk_score, risk_level = self.tirs.verify_intent(
                agent_id=self.name,
                intent_text=desc,
                capabilities=capabilities,
                was_allowed=result.allowed,
                policy_triggered=result.policy_triggered
            )
            
            # Track risk in metrics
            if self._metrics:
                self._metrics.gauge("agent_risk_score").set(risk_score, {"agent": self.name})
            
            if risk_level == RiskLevel.KILL:
                self._killed = True
                return {"success": False, "error": "Agent killed by TIRS"}
            elif risk_level == RiskLevel.PAUSE:
                self._paused = True
                return {"success": False, "error": "Agent paused by TIRS"}
        
        # Step 3: Check if allowed
        if not result.allowed:
            self.logger.warning(f"🛑 Tool blocked: {result.reason}")
            if self._metrics:
                self._metrics.counter("armoriq_denials_total").inc({"agent": self.name, "mcp": mcp})
            return {"success": False, "error": result.reason, "policy": result.policy_triggered}
        
        # Step 4: Use modified payload if ArmorIQ modified it
        final_params = result.modified_payload or params
        
        # Step 5: Execute through ArmorIQ.invoke()
        self.logger.info(f"⚡ Invoking {mcp}.{action} through ArmorIQ...")
        invoke_result = self.armoriq.invoke(
            mcp=mcp,
            action=action,
            params=final_params,
            intent_token=result.token
        )
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log the action
        self.action_log.append({
            "timestamp": datetime.now().isoformat(),
            "mcp": mcp,
            "action": action,
            "params": final_params,
            "intent_id": result.intent_id,
            "result": invoke_result,
            "duration_ms": duration * 1000
        })
        
        # Track metrics
        success = invoke_result.get("status") == "success"
        labels = {"agent": self.name, "mcp": mcp, "action": action}
        
        if self._metrics:
            self._metrics.counter("tool_executions_total").inc(labels)
            self._metrics.histogram("tool_execution_seconds").observe(duration, labels)
        
        # Emit observability event
        if self._events and OBSERVABILITY_AVAILABLE:
            self._events.emit(AgentEvent(
                event_type="tool_execution",
                agent_name=self.name,
                action=intent_type,
                duration_ms=duration * 1000,
                success=success,
                error=invoke_result.get("error") if not success else None,
                data={"intent_id": result.intent_id}
            ))
        
        if success:
            self.logger.info(f"✅ Tool executed successfully ({duration*1000:.0f}ms)")
            return {"success": True, "result": invoke_result.get("result", invoke_result)}
        else:
            return {"success": False, "error": invoke_result.get("error", "Unknown error")}

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
