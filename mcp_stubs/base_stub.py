"""
Base MCP Stub
=============
Base class for all MCP simulation stubs.
"""

from typing import Dict, List, Any
from datetime import datetime
from abc import ABC, abstractmethod


class MCPStub(ABC):
    """
    Base class for MCP stubs.
    
    MCP stubs simulate real MCP calls without executing them,
    allowing TIRS to test plans before execution.
    """

    def __init__(self, name: str):
        self.name = name
        self.call_log: List[Dict] = []

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
            "timestamp": datetime.now().isoformat()
        })
        return {"status": "simulated", "mcp": self.name, "action": action}

    def get_capabilities(self, action: str) -> List[str]:
        """Get capabilities required for an action."""
        return [f"{self.name.lower()}.{action}"]

    def clear_log(self) -> None:
        """Clear the call log."""
        self.call_log.clear()

    def get_call_count(self) -> int:
        """Get the number of simulated calls."""
        return len(self.call_log)
