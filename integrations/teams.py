"""
Teams Notifier
==============
Microsoft Teams webhook integration for TIRS alerts.
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger("TIRS.Teams")


class TeamsNotifier:
    """Microsoft Teams webhook notifier for TIRS alerts."""

    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize Teams notifier.
        
        Args:
            webhook_url: Teams incoming webhook URL.
                        If None, alerts will be logged but not sent.
        """
        self.webhook_url = webhook_url
        self.enabled = bool(webhook_url)
        
        if not self.enabled:
            logger.warning("Teams notifier initialized without webhook URL - alerts will be logged only")

    def _build_message(
        self,
        level: str,
        agent_id: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build Teams Adaptive Card message.
        
        Args:
            level: Alert level (WARNING, PAUSE, KILL)
            agent_id: Agent identifier
            message: Alert message
            details: Additional details to include
        
        Returns:
            Teams message payload
        """
        # Color coding (Teams uses hex without #)
        colors = {
            "WARNING": "warning",
            "PAUSE": "attention",
            "KILL": "attention"
        }
        
        emojis = {
            "WARNING": "⚠️",
            "PAUSE": "⏸️",
            "KILL": "🛑"
        }
        
        color = colors.get(level, "default")
        emoji = emojis.get(level, "ℹ️")
        
        # Build facts from details
        facts = [
            {"title": "Agent", "value": agent_id},
            {"title": "Time", "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
            {"title": "Level", "value": level}
        ]
        
        if details:
            for k, v in details.items():
                facts.append({"title": k, "value": str(v)})
        
        # Adaptive Card format
        card = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "FF0000" if level == "KILL" else ("FFA500" if level == "WARNING" else "FF6B6B"),
            "summary": f"TIRS Alert: {level} - {agent_id}",
            "sections": [
                {
                    "activityTitle": f"{emoji} TIRS Alert: {level}",
                    "activitySubtitle": f"Agent: {agent_id}",
                    "facts": facts,
                    "markdown": True
                },
                {
                    "text": f"**Message:** {message}"
                }
            ],
            "potentialAction": [
                {
                    "@type": "OpenUri",
                    "name": "View Dashboard",
                    "targets": [
                        {
                            "os": "default",
                            "uri": "http://localhost:8000"
                        }
                    ]
                }
            ]
        }
        
        return card

    def send_alert(
        self,
        level: str,
        agent_id: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send alert to Teams.
        
        Args:
            level: Alert level (WARNING, PAUSE, KILL)
            agent_id: Agent identifier
            message: Alert message
            details: Additional details
        
        Returns:
            True if sent successfully (or logged if no webhook)
        """
        payload = self._build_message(level, agent_id, message, details)
        
        if not self.enabled:
            logger.info(f"[TEAMS] Would send {level} alert for {agent_id}: {message}")
            logger.debug(f"[TEAMS] Payload: {json.dumps(payload, indent=2)}")
            return True
        
        try:
            import urllib.request
            
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                self.webhook_url,
                data=data,
                headers={"Content-Type": "application/json"}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    logger.info(f"[TEAMS] Sent {level} alert for {agent_id}")
                    return True
                else:
                    logger.error(f"[TEAMS] Failed to send: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"[TEAMS] Error sending alert: {e}")
            return False

    def notify_warning(self, agent_id: str, risk_score: float, reason: str) -> bool:
        """Send warning notification."""
        return self.send_alert(
            level="WARNING",
            agent_id=agent_id,
            message=f"Agent behavior drift detected",
            details={
                "Risk Score": f"{risk_score:.2f}",
                "Reason": reason,
                "Action": "Monitoring continues, admin notified"
            }
        )

    def notify_pause(self, agent_id: str, risk_score: float, reason: str) -> bool:
        """Send pause notification."""
        return self.send_alert(
            level="PAUSE",
            agent_id=agent_id,
            message=f"Agent has been PAUSED due to high drift",
            details={
                "Risk Score": f"{risk_score:.2f}",
                "Reason": reason,
                "Action": "Agent suspended, awaiting admin review"
            }
        )

    def notify_kill(self, agent_id: str, risk_score: float, reason: str) -> bool:
        """Send kill notification."""
        return self.send_alert(
            level="KILL",
            agent_id=agent_id,
            message=f"Agent has been TERMINATED due to critical drift",
            details={
                "Risk Score": f"{risk_score:.2f}",
                "Reason": reason,
                "Action": "Agent killed, forensic snapshot captured"
            }
        )
