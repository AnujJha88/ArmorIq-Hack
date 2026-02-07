"""
Base MCP Stub
=============
Base class for all MCP simulation stubs.
"""

from typing import Dict, List, Any
from datetime import datetime
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger("MCP")


class MCPStub(ABC):
    """
    Base class for MCP stubs.
    
    MCP stubs can operate in two modes:
    - simulate(): Dry-run for planning without side effects
    - execute(): Actually perform the action
    """

    def __init__(self, name: str):
        self.name = name
        self.call_log: List[Dict] = []
        self.logger = logging.getLogger(f"MCP.{name}")

    def simulate(self, action: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate an MCP call without real execution.

        Args:
            action: The action to simulate
            args: Arguments for the action

        Returns:
            Dict with simulated result
        """
        self.call_log.append({
            "action": action,
            "args": args,
            "mode": "simulate",
            "timestamp": datetime.now().isoformat()
        })
        return {"status": "simulated", "mcp": self.name, "action": action}

    def execute(self, action: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an MCP action for real.
        
        Subclasses should override this to implement actual behavior.
        Default implementation dispatches to action-specific methods.
        
        Args:
            action: The action to perform
            args: Arguments for the action
            
        Returns:
            Dict with execution result
        """
        self.call_log.append({
            "action": action,
            "args": args,
            "mode": "execute",
            "timestamp": datetime.now().isoformat()
        })
        
        # Try to find a method matching the action
        method_name = f"do_{action}"
        if hasattr(self, method_name):
            method = getattr(self, method_name)
            result = method(args)
            self.logger.info(f"✅ Executed {self.name}.{action}")
            return {
                "status": "success",
                "mcp": self.name,
                "action": action,
                "result": result
            }
        
        # Fallback to simulation if no specific handler
        self.logger.info(f"⚡ Simulating {self.name}.{action} (no handler)")
        return {
            "status": "success",
            "mcp": self.name,
            "action": action,
            "result": {"executed": True, "args": args},
            "note": "No specific handler, generic execution"
        }

    def get_capabilities(self, action: str) -> List[str]:
        """Get capabilities required for an action."""
        return [f"{self.name.lower()}.{action}"]

    def clear_log(self) -> None:
        """Clear the call log."""
        self.call_log.clear()

    def get_call_count(self) -> int:
        """Get the number of calls."""
        return len(self.call_log)

