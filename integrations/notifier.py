"""
Alert Notifier
==============
Unified alert dispatcher that routes to configured channels.
"""

import logging
from typing import Dict, Any, Optional, List

from .config import get_config, IntegrationConfig
from .slack import SlackNotifier
from .teams import TeamsNotifier

logger = logging.getLogger("TIRS.Notifier")


class AlertNotifier:
    """
    Unified alert notifier that dispatches to all configured channels.
    
    Routes alerts to Slack, Teams, or both based on configuration.
    """

    def __init__(self, config: Optional[IntegrationConfig] = None):
        """
        Initialize alert notifier.
        
        Args:
            config: Integration config. If None, loads from environment.
        """
        self.config = config or get_config()
        
        # Initialize notifiers
        self.slack = SlackNotifier(self.config.slack_webhook_url) if self.config.slack_enabled else None
        self.teams = TeamsNotifier(self.config.teams_webhook_url) if self.config.teams_enabled else None
        
        self._notifiers: List = []
        if self.slack:
            self._notifiers.append(("Slack", self.slack))
        if self.teams:
            self._notifiers.append(("Teams", self.teams))
        
        if not self._notifiers:
            logger.warning("No notification channels configured - alerts will be logged only")
            # Create log-only notifiers
            self.slack = SlackNotifier(None)
            self.teams = TeamsNotifier(None)

    def send_alert(
        self,
        level: str,
        agent_id: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Send alert to all configured channels.
        
        Args:
            level: Alert level (WARNING, PAUSE, KILL)
            agent_id: Agent identifier
            message: Alert message
            details: Additional details
        
        Returns:
            Dict mapping channel name to success status
        """
        results = {}
        
        if not self._notifiers:
            # Log-only mode
            logger.info(f"[ALERT] {level} for {agent_id}: {message}")
            if details:
                logger.info(f"[ALERT] Details: {details}")
            return {"log": True}
        
        for name, notifier in self._notifiers:
            try:
                success = notifier.send_alert(level, agent_id, message, details)
                results[name] = success
            except Exception as e:
                logger.error(f"Failed to send alert via {name}: {e}")
                results[name] = False
        
        return results

    def notify_warning(self, agent_id: str, risk_score: float, reason: str) -> Dict[str, bool]:
        """Send warning to all channels."""
        return self.send_alert(
            level="WARNING",
            agent_id=agent_id,
            message="Agent behavior drift detected",
            details={
                "Risk Score": f"{risk_score:.2f}",
                "Reason": reason,
                "Action": "Monitoring continues, admin notified"
            }
        )

    def notify_pause(self, agent_id: str, risk_score: float, reason: str) -> Dict[str, bool]:
        """Send pause notification to all channels."""
        return self.send_alert(
            level="PAUSE",
            agent_id=agent_id,
            message="Agent has been PAUSED due to high drift",
            details={
                "Risk Score": f"{risk_score:.2f}",
                "Reason": reason,
                "Action": "Agent suspended, awaiting admin review"
            }
        )

    def notify_kill(self, agent_id: str, risk_score: float, reason: str) -> Dict[str, bool]:
        """Send kill notification to all channels."""
        return self.send_alert(
            level="KILL",
            agent_id=agent_id,
            message="Agent has been TERMINATED due to critical drift",
            details={
                "Risk Score": f"{risk_score:.2f}",
                "Reason": reason,
                "Action": "Agent killed, forensic snapshot captured"
            }
        )


# Singleton notifier
_notifier: Optional[AlertNotifier] = None


def get_notifier() -> AlertNotifier:
    """Get the singleton alert notifier."""
    global _notifier
    if _notifier is None:
        _notifier = AlertNotifier()
    return _notifier
