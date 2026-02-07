"""
Integration Configuration
=========================
Configuration for Slack and Teams integrations.
Reads from environment variables.
"""

import os
import logging
from dataclasses import dataclass
from typing import Optional, List

logger = logging.getLogger("TIRS.Integrations")


@dataclass
class IntegrationConfig:
    """Configuration for external integrations."""
    
    # Slack settings
    slack_webhook_url: Optional[str] = None
    slack_enabled: bool = False
    
    # Teams settings
    teams_webhook_url: Optional[str] = None
    teams_enabled: bool = False
    
    # General settings
    alert_channels: List[str] = None  # ["slack", "teams"]
    
    def __post_init__(self):
        if self.alert_channels is None:
            self.alert_channels = []


def get_config() -> IntegrationConfig:
    """
    Load integration config from environment variables.
    
    Environment Variables:
        SLACK_WEBHOOK_URL: Slack incoming webhook URL
        TEAMS_WEBHOOK_URL: Microsoft Teams incoming webhook URL
        ALERT_CHANNELS: Comma-separated list of enabled channels (e.g., "slack,teams")
    """
    slack_url = os.environ.get("SLACK_WEBHOOK_URL")
    teams_url = os.environ.get("TEAMS_WEBHOOK_URL")
    channels_str = os.environ.get("ALERT_CHANNELS", "")
    
    # Parse channels
    channels = [c.strip().lower() for c in channels_str.split(",") if c.strip()]
    
    # Auto-enable based on URL presence if no explicit channels set
    if not channels:
        if slack_url:
            channels.append("slack")
        if teams_url:
            channels.append("teams")
    
    config = IntegrationConfig(
        slack_webhook_url=slack_url,
        slack_enabled="slack" in channels and bool(slack_url),
        teams_webhook_url=teams_url,
        teams_enabled="teams" in channels and bool(teams_url),
        alert_channels=channels
    )
    
    logger.info(f"Integration config loaded: Slack={config.slack_enabled}, Teams={config.teams_enabled}")
    
    return config


# Singleton config
_config: Optional[IntegrationConfig] = None


def get_cached_config() -> IntegrationConfig:
    """Get cached integration config."""
    global _config
    if _config is None:
        _config = get_config()
    return _config
