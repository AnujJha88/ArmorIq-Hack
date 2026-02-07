"""
Context-Aware Thresholds
========================
Adjusts risk thresholds based on business context.
"""

import logging
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, time
from enum import Enum

logger = logging.getLogger("TIRS.Context")


class BusinessHours(Enum):
    """Business hours classification."""
    BUSINESS = "business"
    AFTER_HOURS = "after_hours"
    WEEKEND = "weekend"
    HOLIDAY = "holiday"


class RiskSeason(Enum):
    """Seasonal risk adjustments."""
    NORMAL = "normal"
    QUARTER_END = "quarter_end"
    YEAR_END = "year_end"
    AUDIT_PERIOD = "audit_period"
    PEAK_SEASON = "peak_season"


@dataclass
class BusinessContext:
    """Current business context for threshold adjustment."""
    time_of_day: BusinessHours = BusinessHours.BUSINESS
    season: RiskSeason = RiskSeason.NORMAL
    department: str = "general"
    user_role: str = "standard"
    is_sensitive_operation: bool = False
    custom_multipliers: Dict[str, float] = field(default_factory=dict)

    @classmethod
    def from_current(cls, department: str = "general", role: str = "standard") -> "BusinessContext":
        """Create context from current time."""
        now = datetime.now()

        # Determine time of day
        hour = now.hour
        weekday = now.weekday()

        if weekday >= 5:  # Saturday, Sunday
            time_of_day = BusinessHours.WEEKEND
        elif 9 <= hour < 17:
            time_of_day = BusinessHours.BUSINESS
        else:
            time_of_day = BusinessHours.AFTER_HOURS

        # Determine season
        month = now.month
        day = now.day

        if month in [3, 6, 9, 12] and day >= 20:
            season = RiskSeason.QUARTER_END
        elif month == 12 and day >= 15:
            season = RiskSeason.YEAR_END
        else:
            season = RiskSeason.NORMAL

        return cls(
            time_of_day=time_of_day,
            season=season,
            department=department,
            user_role=role,
        )


@dataclass
class ThresholdConfig:
    """Base threshold configuration."""
    warning: float = 0.5
    critical: float = 0.7
    terminal: float = 0.85


class ContextualThresholds:
    """
    Adjusts risk thresholds based on business context.

    Higher sensitivity during:
    - After hours
    - Weekends
    - Quarter/year end
    - Sensitive operations
    """

    # Multipliers (lower = more sensitive)
    TIME_MULTIPLIERS = {
        BusinessHours.BUSINESS: 1.0,
        BusinessHours.AFTER_HOURS: 0.85,
        BusinessHours.WEEKEND: 0.75,
        BusinessHours.HOLIDAY: 0.7,
    }

    SEASON_MULTIPLIERS = {
        RiskSeason.NORMAL: 1.0,
        RiskSeason.QUARTER_END: 0.9,
        RiskSeason.YEAR_END: 0.85,
        RiskSeason.AUDIT_PERIOD: 0.8,
        RiskSeason.PEAK_SEASON: 0.95,
    }

    ROLE_MULTIPLIERS = {
        "admin": 0.9,
        "manager": 0.95,
        "standard": 1.0,
        "contractor": 0.85,
        "external": 0.75,
    }

    DEPARTMENT_MULTIPLIERS = {
        "finance": 0.9,
        "legal": 0.85,
        "hr": 0.9,
        "it": 0.95,
        "security": 0.8,
        "general": 1.0,
    }

    def __init__(self, base_config: Optional[ThresholdConfig] = None):
        self.base = base_config or ThresholdConfig()
        self._custom_rules: List[Dict] = []

    def add_custom_rule(
        self,
        name: str,
        condition: callable,
        multiplier: float,
        priority: int = 0
    ):
        """Add a custom threshold adjustment rule."""
        self._custom_rules.append({
            "name": name,
            "condition": condition,
            "multiplier": multiplier,
            "priority": priority,
        })
        self._custom_rules.sort(key=lambda x: x["priority"], reverse=True)

    def get_adjusted_thresholds(self, context: BusinessContext) -> ThresholdConfig:
        """
        Get thresholds adjusted for current context.

        Args:
            context: Current business context

        Returns:
            Adjusted threshold configuration
        """
        # Calculate composite multiplier
        multiplier = 1.0

        # Time of day
        multiplier *= self.TIME_MULTIPLIERS.get(context.time_of_day, 1.0)

        # Season
        multiplier *= self.SEASON_MULTIPLIERS.get(context.season, 1.0)

        # Role
        multiplier *= self.ROLE_MULTIPLIERS.get(context.user_role, 1.0)

        # Department
        multiplier *= self.DEPARTMENT_MULTIPLIERS.get(context.department, 1.0)

        # Sensitive operation
        if context.is_sensitive_operation:
            multiplier *= 0.85

        # Custom multipliers
        for key, value in context.custom_multipliers.items():
            multiplier *= value

        # Apply custom rules
        for rule in self._custom_rules:
            try:
                if rule["condition"](context):
                    multiplier *= rule["multiplier"]
            except Exception as e:
                logger.warning(f"Custom rule '{rule['name']}' failed: {e}")

        # Apply multiplier to thresholds
        return ThresholdConfig(
            warning=self.base.warning * multiplier,
            critical=self.base.critical * multiplier,
            terminal=self.base.terminal * multiplier,
        )

    def get_threshold_explanation(self, context: BusinessContext) -> Dict:
        """
        Get explanation of threshold adjustments.

        Returns:
            Dict with factors and their contributions
        """
        factors = []

        # Time
        time_mult = self.TIME_MULTIPLIERS.get(context.time_of_day, 1.0)
        if time_mult != 1.0:
            factors.append({
                "factor": "time_of_day",
                "value": context.time_of_day.value,
                "multiplier": time_mult,
                "reason": f"{'Heightened' if time_mult < 1 else 'Standard'} sensitivity during {context.time_of_day.value}",
            })

        # Season
        season_mult = self.SEASON_MULTIPLIERS.get(context.season, 1.0)
        if season_mult != 1.0:
            factors.append({
                "factor": "season",
                "value": context.season.value,
                "multiplier": season_mult,
                "reason": f"{'Tighter' if season_mult < 1 else 'Normal'} controls during {context.season.value}",
            })

        # Role
        role_mult = self.ROLE_MULTIPLIERS.get(context.user_role, 1.0)
        if role_mult != 1.0:
            factors.append({
                "factor": "user_role",
                "value": context.user_role,
                "multiplier": role_mult,
                "reason": f"Role-based sensitivity for {context.user_role}",
            })

        # Department
        dept_mult = self.DEPARTMENT_MULTIPLIERS.get(context.department, 1.0)
        if dept_mult != 1.0:
            factors.append({
                "factor": "department",
                "value": context.department,
                "multiplier": dept_mult,
                "reason": f"Department-specific controls for {context.department}",
            })

        adjusted = self.get_adjusted_thresholds(context)

        return {
            "base_thresholds": {
                "warning": self.base.warning,
                "critical": self.base.critical,
                "terminal": self.base.terminal,
            },
            "adjusted_thresholds": {
                "warning": adjusted.warning,
                "critical": adjusted.critical,
                "terminal": adjusted.terminal,
            },
            "factors": factors,
            "context": {
                "time_of_day": context.time_of_day.value,
                "season": context.season.value,
                "department": context.department,
                "role": context.user_role,
            },
        }
