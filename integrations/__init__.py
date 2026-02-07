"""
Integrations Module
===================
Slack and Teams webhook integrations for TIRS alerts.
"""

from .config import IntegrationConfig, get_config
from .slack import SlackNotifier
from .teams import TeamsNotifier
from .notifier import AlertNotifier, get_notifier

__all__ = [
    "IntegrationConfig",
    "get_config",
    "SlackNotifier",
    "TeamsNotifier",
    "AlertNotifier",
    "get_notifier"
]
