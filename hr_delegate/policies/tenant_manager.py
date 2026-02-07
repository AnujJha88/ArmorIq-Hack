"""
Tenant Manager
==============
Multi-tenant policy management with per-department overrides.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from .policy_registry import get_registry

logger = logging.getLogger("TIRS.TenantManager")


class TenantManager:
    """
    Manages per-tenant (department/team) policy overrides.
    
    Tenant policies inherit from global defaults and can override
    specific values for their department.
    """

    def __init__(self, tenant_dir: Optional[Path] = None):
        """
        Initialize tenant manager.
        
        Args:
            tenant_dir: Directory containing tenant policy files.
                       Defaults to hr_delegate/data/tenant_policies/.
        """
        if tenant_dir is None:
            self.tenant_dir = Path(__file__).parent.parent / "data" / "tenant_policies"
        else:
            self.tenant_dir = Path(tenant_dir)
        
        self.tenants: Dict[str, Dict[str, Any]] = {}
        self._load_all_tenants()

    def _load_all_tenants(self) -> None:
        """Load all tenant policies from files."""
        self.tenants.clear()
        
        if not self.tenant_dir.exists():
            logger.warning(f"Tenant directory not found: {self.tenant_dir}")
            self.tenant_dir.mkdir(parents=True, exist_ok=True)
            self._create_default_tenants()
            return
        
        for path in self.tenant_dir.glob("*.json"):
            tenant_id = path.stem
            try:
                with open(path, "r") as f:
                    self.tenants[tenant_id] = json.load(f)
                logger.info(f"Loaded tenant: {tenant_id}")
            except Exception as e:
                logger.error(f"Failed to load tenant {tenant_id}: {e}")
        
        if not self.tenants:
            self._create_default_tenants()

    def _create_default_tenants(self) -> None:
        """Create default tenant policies."""
        defaults = {
            "default": {
                "name": "Global Default",
                "description": "Base policy for all tenants",
                "overrides": {}
            },
            "engineering": {
                "name": "Engineering",
                "description": "Engineering department policies",
                "overrides": {
                    "salary_caps.L5": 280000,
                    "work_hours.start": 8,
                    "work_hours.end": 18
                }
            },
            "sales": {
                "name": "Sales",
                "description": "Sales department policies",
                "overrides": {
                    "weekend_blocked": False,
                    "work_hours.start": 8,
                    "work_hours.end": 19
                }
            }
        }
        
        for tenant_id, data in defaults.items():
            self.tenants[tenant_id] = data
            self._save_tenant(tenant_id)
        
        logger.info("Created default tenant policies")

    def _save_tenant(self, tenant_id: str) -> bool:
        """Save a tenant's policy to file."""
        try:
            self.tenant_dir.mkdir(parents=True, exist_ok=True)
            path = self.tenant_dir / f"{tenant_id}.json"
            
            with open(path, "w") as f:
                json.dump(self.tenants[tenant_id], f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Failed to save tenant {tenant_id}: {e}")
            return False

    def get_tenant_policy(self, tenant_id: str, policy_name: str, default: Any = None) -> Any:
        """
        Get a policy value for a specific tenant.
        
        First checks tenant overrides, then falls back to global default.
        
        Args:
            tenant_id: Tenant/department identifier
            policy_name: Policy name (dot-separated for nested)
            default: Default value if not found
        
        Returns:
            Policy value (tenant override or global default)
        """
        # Check tenant-specific override
        tenant = self.tenants.get(tenant_id, {})
        overrides = tenant.get("overrides", {})
        
        if policy_name in overrides:
            return overrides[policy_name]
        
        # Fall back to global registry
        registry = get_registry()
        return registry.get_policy(policy_name, default)

    def set_tenant_policy(self, tenant_id: str, policy_name: str, value: Any) -> bool:
        """
        Set a policy override for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            policy_name: Policy name
            value: Override value
        
        Returns:
            True if successful
        """
        if tenant_id not in self.tenants:
            self.tenants[tenant_id] = {
                "name": tenant_id.title(),
                "description": f"Policy overrides for {tenant_id}",
                "overrides": {}
            }
        
        self.tenants[tenant_id]["overrides"][policy_name] = value
        logger.info(f"Set {tenant_id}.{policy_name} = {value}")
        
        return self._save_tenant(tenant_id)

    def inherit_from_global(self, tenant_id: str) -> None:
        """
        Create/reset a tenant with global defaults.
        
        Args:
            tenant_id: Tenant identifier
        """
        self.tenants[tenant_id] = {
            "name": tenant_id.title(),
            "description": f"Policy overrides for {tenant_id}",
            "overrides": {}
        }
        self._save_tenant(tenant_id)
        logger.info(f"Reset tenant {tenant_id} to inherit from global")

    def list_tenants(self) -> Dict[str, str]:
        """
        List all tenants.
        
        Returns:
            Dict mapping tenant_id to name
        """
        return {
            tid: data.get("name", tid)
            for tid, data in self.tenants.items()
        }

    def get_tenant_overrides(self, tenant_id: str) -> Dict[str, Any]:
        """Get all overrides for a tenant."""
        tenant = self.tenants.get(tenant_id, {})
        return tenant.get("overrides", {}).copy()

    def reload_tenant(self, tenant_id: str) -> bool:
        """Reload a specific tenant from file."""
        path = self.tenant_dir / f"{tenant_id}.json"
        
        if not path.exists():
            logger.warning(f"Tenant file not found: {path}")
            return False
        
        try:
            with open(path, "r") as f:
                self.tenants[tenant_id] = json.load(f)
            logger.info(f"Reloaded tenant: {tenant_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to reload tenant {tenant_id}: {e}")
            return False


# Singleton tenant manager
_manager: Optional[TenantManager] = None


def get_tenant_manager() -> TenantManager:
    """Get the singleton tenant manager."""
    global _manager
    if _manager is None:
        _manager = TenantManager()
    return _manager
