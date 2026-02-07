"""
LLM Client for HR Agent Swarm
=============================
Provides LLM integration for agent reasoning using Google Gemini.

Usage:
    from hr_delegate.llm_client import get_llm
    
    llm = get_llm()
    response = llm.complete("What should I do next?")
    decision = llm.decide(context, options)
"""

import os 
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("LLMClient")

# Load environment
try:
    from pathlib import Path
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if key not in os.environ:
                        os.environ[key] = value
except Exception:
    pass

# Get API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Try to import Gemini SDK
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        logger.info("✓ Gemini SDK configured")
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("⚠️ google-generativeai not installed. Run: pip install google-generativeai")


class LLMMode(Enum):
    LIVE = "live"      # Real LLM calls
    MOCK = "mock"      # Mock responses for testing


@dataclass
class LLMResponse:
    """Response from LLM."""
    content: str
    model: str
    mode: LLMMode
    tokens_used: int = 0
    raw_response: Any = None


class LLMClient:
    """
    LLM Client with Gemini support.
    
    Provides:
    - complete(): Raw text completion
    - reason(): Structured reasoning for agents
    - decide(): Tool/action selection
    - extract(): Extract structured data from text
    
    Falls back to mock mode when no API key or SDK unavailable.
    """
    
    # Default system prompt for HR agents
    HR_AGENT_SYSTEM_PROMPT = """You are an AI assistant for an HR Agent Swarm system.
Your role is to help HR agents make decisions about:
- Candidate screening and evaluation
- Interview scheduling
- Offer generation and negotiation
- Employee onboarding
- Compliance checks

Always be:
- Professional and objective
- Mindful of legal compliance (EEOC, FCRA, etc.)
- Focused on inclusive language
- Protective of PII

When asked to decide between options, respond with JSON containing your choice and reasoning."""

    def __init__(self, api_key: str = None, model: str = "gemini-3-flash-preview"):
        self.api_key = api_key or GEMINI_API_KEY
        self.model_name = model
        self.mode = LLMMode.MOCK
        self._model = None
        self._chat = None
        
        # Initialize if possible
        if GEMINI_AVAILABLE and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self._model = genai.GenerativeModel(
                    model_name=model,
                    system_instruction=self.HR_AGENT_SYSTEM_PROMPT
                )
                self.mode = LLMMode.LIVE
                logger.info(f"🤖 LLM Client initialized in LIVE mode (model: {model})")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize Gemini: {e}")
                logger.info("   Falling back to MOCK mode")
        else:
            if not GEMINI_AVAILABLE:
                logger.info("🤖 LLM Client in MOCK mode (SDK not installed)")
            else:
                logger.info("🤖 LLM Client in MOCK mode (no API key)")
    
    def complete(self, prompt: str, system_prompt: str = None) -> LLMResponse:
        """
        Generate a text completion.
        
        Args:
            prompt: The prompt to complete
            system_prompt: Optional override for system prompt
            
        Returns:
            LLMResponse with generated content
        """
        if self.mode == LLMMode.LIVE and self._model:
            try:
                # Use custom system prompt if provided
                if system_prompt:
                    model = genai.GenerativeModel(
                        model_name=self.model_name,
                        system_instruction=system_prompt
                    )
                else:
                    model = self._model
                
                response = model.generate_content(prompt)
                
                # Handle different SDK response formats for token counting
                tokens = 0
                if hasattr(response, 'usage_metadata'):
                    meta = response.usage_metadata
                    if hasattr(meta, 'total_token_count'):
                        tokens = meta.total_token_count
                    elif isinstance(meta, dict):
                        tokens = meta.get('total_token_count', 0)
                
                return LLMResponse(
                    content=response.text,
                    model=self.model_name,
                    mode=self.mode,
                    tokens_used=tokens,
                    raw_response=response
                )
            except Exception as e:
                logger.error(f"LLM error: {e}")
                return self._mock_response(prompt)
        else:
            return self._mock_response(prompt)
    
    def reason(self, context: str, question: str) -> LLMResponse:
        """
        Ask the LLM to reason about a situation.
        
        Args:
            context: Background context/situation
            question: Specific question to reason about
            
        Returns:
            LLMResponse with reasoning
        """
        prompt = f"""Given this context:
{context}

Please reason through this question:
{question}

Provide your reasoning step by step, then give your conclusion."""
        
        return self.complete(prompt)
    
    def decide(self, context: str, options: List[str], criteria: str = None) -> Dict[str, Any]:
        """
        Ask the LLM to choose between options.
        
        Args:
            context: Situation/context
            options: List of options to choose from
            criteria: Optional criteria for decision
            
        Returns:
            Dict with 'choice' (index), 'option' (text), and 'reasoning'
        """
        options_text = "\n".join(f"{i+1}. {opt}" for i, opt in enumerate(options))
        
        prompt = f"""Given this context:
{context}

Choose the best option from:
{options_text}

{f"Criteria: {criteria}" if criteria else ""}

Respond with a JSON object containing:
- "choice": the option number (1-indexed)
- "reasoning": brief explanation of your choice

Only output the JSON, no other text."""

        response = self.complete(prompt)
        
        try:
            # Try to parse JSON from response
            content = response.content.strip()
            # Handle markdown code blocks
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            result = json.loads(content)
            choice_idx = int(result.get("choice", 1)) - 1
            return {
                "choice": choice_idx,
                "option": options[choice_idx] if 0 <= choice_idx < len(options) else options[0],
                "reasoning": result.get("reasoning", "No reasoning provided"),
                "raw_response": response
            }
        except (json.JSONDecodeError, ValueError, IndexError) as e:
            logger.warning(f"Failed to parse decision: {e}")
            # Default to first option
            return {
                "choice": 0,
                "option": options[0],
                "reasoning": response.content,
                "raw_response": response
            }
    
    def extract(self, text: str, schema: Dict[str, str]) -> Dict[str, Any]:
        """
        Extract structured data from text.
        
        Args:
            text: Text to extract from
            schema: Dict mapping field names to descriptions
            
        Returns:
            Dict with extracted values
        """
        schema_text = "\n".join(f"- {k}: {v}" for k, v in schema.items())
        
        prompt = f"""Extract the following fields from this text:

Text:
{text}

Fields to extract:
{schema_text}

Respond with a JSON object containing only the extracted fields.
If a field cannot be found, set its value to null."""

        response = self.complete(prompt)
        
        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content)
        except json.JSONDecodeError:
            return {k: None for k in schema}
    
    def plan_actions(self, goal: str, available_tools: List[str], context: str = "") -> List[Dict]:
        """
        Generate a plan of actions to achieve a goal.
        
        Args:
            goal: The goal to achieve
            available_tools: List of available tool names
            context: Additional context
            
        Returns:
            List of action dicts with 'tool', 'action', 'params', 'reason'
        """
        tools_text = ", ".join(available_tools)
        
        prompt = f"""Create a plan to achieve this goal:
Goal: {goal}

Available tools: {tools_text}
{f"Context: {context}" if context else ""}

Respond with a JSON array of steps. Each step should have:
- "tool": which tool to use
- "action": what action to perform
- "params": parameters for the action (as object)
- "reason": why this step is needed

Only output the JSON array, no other text."""

        response = self.complete(prompt)
        
        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content)
        except json.JSONDecodeError:
            return []
    
    def _mock_response(self, prompt: str) -> LLMResponse:
        """Generate a mock response for testing."""
        # Simple mock responses based on prompt content
        prompt_lower = prompt.lower()
        
        if "choose" in prompt_lower or "decide" in prompt_lower:
            content = '{"choice": 1, "reasoning": "Mock decision - first option selected"}'
        elif "extract" in prompt_lower:
            content = '{}'
        elif "plan" in prompt_lower:
            content = '[]'
        elif "reason" in prompt_lower:
            content = "Mock reasoning: Based on the context provided, I would recommend proceeding with standard procedures while ensuring compliance with company policies."
        else:
            content = f"[MOCK LLM] Acknowledged: {prompt[:100]}..."
        
        return LLMResponse(
            content=content,
            model="mock",
            mode=LLMMode.MOCK,
            tokens_used=0
        )
    
    def start_chat(self, history: List[Dict] = None) -> "LLMChat":
        """Start a chat session for multi-turn conversations."""
        return LLMChat(self, history)


class LLMChat:
    """Multi-turn chat session."""
    
    def __init__(self, client: LLMClient, history: List[Dict] = None):
        self.client = client
        self.history = history or []
        self._gemini_chat = None
        
        if client.mode == LLMMode.LIVE and client._model:
            try:
                self._gemini_chat = client._model.start_chat(
                    history=[
                        {"role": h["role"], "parts": [h["content"]]}
                        for h in self.history
                    ]
                )
            except Exception as e:
                logger.warning(f"Failed to start chat: {e}")
    
    def send(self, message: str) -> LLMResponse:
        """Send a message and get response."""
        self.history.append({"role": "user", "content": message})
        
        if self._gemini_chat:
            try:
                response = self._gemini_chat.send_message(message)
                result = LLMResponse(
                    content=response.text,
                    model=self.client.model_name,
                    mode=LLMMode.LIVE,
                    raw_response=response
                )
                self.history.append({"role": "model", "content": response.text})
                return result
            except Exception as e:
                logger.error(f"Chat error: {e}")
        
        # Fallback to mock
        result = self.client._mock_response(message)
        self.history.append({"role": "model", "content": result.content})
        return result


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON & EXPORTS
# ═══════════════════════════════════════════════════════════════════════════════

_llm: Optional[LLMClient] = None


def get_llm() -> LLMClient:
    """Get the singleton LLM client."""
    global _llm
    if _llm is None:
        _llm = LLMClient()
    return _llm


def reset_llm():
    """Reset the singleton (for testing)."""
    global _llm
    _llm = None


# Quick test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='[%(name)s] %(message)s')
    
    llm = get_llm()
    print(f"\nMode: {llm.mode.value}")
    
    # Test complete
    print("\n--- Testing complete() ---")
    resp = llm.complete("What are the key steps in onboarding a new employee?")
    print(f"Response: {resp.content[:200]}...")
    
    # Test decide
    print("\n--- Testing decide() ---")
    decision = llm.decide(
        context="A candidate has 5 years of experience but is asking for 20% above the salary band.",
        options=[
            "Reject the candidate",
            "Negotiate within the band",
            "Escalate to compensation committee"
        ]
    )
    print(f"Decision: Option {decision['choice']+1} - {decision['option']}")
    print(f"Reasoning: {decision['reasoning']}")
