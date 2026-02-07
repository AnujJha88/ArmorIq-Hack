"""
Policy Registry
================
Centralized, thread-safe policy store for hot-reloadable policies.
"""

import json
import logging
import threading
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("TIRS.PolicyRegistry")


class PolicyRegistry:
    """
    Thread-safe registry for hot-reloadable policies.
    
    Provides centralized access to policy values that can be
    updated without restarting the application.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize policy registry.
        
        Args:
            config_path: Path to policies_config.json.
                        Defaults to hr_delegate/data/policies_config.json.
        """
        self._lock = threading.RLock()
        self.policies: Dict[str, Any] = {}
        self.version: int = 0
        
        # Default config path
        if config_path is None:
            self.config_path = Path(__file__).parent.parent / "data" / "policies_config.json"
        else:
            self.config_path = Path(config_path)
        
        # Load initial policies
        self.reload_from_file()

    def get_policy(self, name: str, default: Any = None) -> Any:
        """
        Get a policy value by name.
        
        Args:
            name: Policy name (dot-separated for nested, e.g., "salary_caps.L5")
            default: Default value if not found
        
        Returns:
            Policy value or default
        """
        with self._lock:
            # Support dot notation for nested access
            parts = name.split(".")
            value = self.policies
            
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return default
            
            return value

    def set_policy(self, name: str, value: Any) -> None:
        """
        Set a policy value.
        
        Args:
            name: Policy name (dot-separated for nested)
            value: New value
        """
        with self._lock:
            parts = name.split(".")
            target = self.policies
            
            # Navigate to parent
            for part in parts[:-1]:
                if part not in target:
                    target[part] = {}
                target = target[part]
            
            # Set value
            target[parts[-1]] = value
            self.version += 1
            logger.info(f"Policy '{name}' updated to {value}")

    def reload_from_file(self) -> bool:
        """
        Reload policies from config file.
        
        Returns:
            True if reload successful
        """
        with self._lock:
            try:
                if not self.config_path.exists():
                    logger.warning(f"Policy config not found: {self.config_path}")
                    self._load_defaults()
                    return True
                
                with open(self.config_path, "r") as f:
                    self.policies = json.load(f)
                
                self.version += 1
                logger.info(f"Policies reloaded from {self.config_path} (v{self.version})")
                return True
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in policy config: {e}")
                return False
            except Exception as e:
                logger.error(f"Failed to reload policies: {e}")
                return False

    def _load_defaults(self) -> None:
        """Load default policies."""
        self.policies = {
            "salary_caps": {
                "L3": 140000,
                "L4": 180000,
                "L5": 240000,
                "L6": 320000
            },
            "work_hours": {
                "start": 9,
                "end": 17
            },
            "weekend_blocked": True,
            "bias_terms": ["rockstar", "ninja", "guru", "young", "energetic"],
            "expense_limits": {
                "travel": 5000,
                "equipment": 2000,
                "meals": 200
            }
        }
        logger.info("Loaded default policies")

    def save_to_file(self) -> bool:
        """
        Save current policies to config file.
        
        Returns:
            True if save successful
        """
        with self._lock:
            try:
                self.config_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(self.config_path, "w") as f:
                    json.dump(self.policies, f, indent=2)
                
                logger.info(f"Policies saved to {self.config_path}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to save policies: {e}")
                return False

    def get_all(self) -> Dict[str, Any]:
        """Get all policies."""
        with self._lock:
            return self.policies.copy()


# Singleton registry
_registry: Optional[PolicyRegistry] = None


def get_registry() -> PolicyRegistry:
    """Get the singleton policy registry."""
    global _registry
    if _registry is None:
        _registry = PolicyRegistry()
    return _registry
