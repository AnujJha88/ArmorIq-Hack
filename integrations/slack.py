"""
Slack Notifier
==============
Slack webhook integration for TIRS alerts.
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger("TIRS.Slack")


class SlackNotifier:
    """Slack webhook notifier for TIRS alerts."""

    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize Slack notifier.
        
        Args:
            webhook_url: Slack incoming webhook URL.
                        If None, alerts will be logged but not sent.
        """
        self.webhook_url = webhook_url
        self.enabled = bool(webhook_url)
        
        if not self.enabled:
            logger.warning("Slack notifier initialized without webhook URL - alerts will be logged only")

    def _build_message(
        self,
        level: str,
        agent_id: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build Slack Block Kit message.
        
        Args:
            level: Alert level (WARNING, PAUSE, KILL)
            agent_id: Agent identifier
            message: Alert message
            details: Additional details to include
        
        Returns:
            Slack message payload
        """
        # Color coding
        colors = {
            "WARNING": "#FFA500",  # Orange
            "PAUSE": "#FF6B6B",    # Red-orange
            "KILL": "#FF0000"      # Red
        }
        
        emojis = {
            "WARNING": "⚠️",
            "PAUSE": "⏸️",
            "KILL": "🛑"
        }
        
        color = colors.get(level, "#808080")
        emoji = emojis.get(level, "ℹ️")
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} TIRS Alert: {level}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Agent:*\n`{agent_id}`"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Time:*\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Message:*\n{message}"
                }
            }
        ]
        
        # Add details if provided
        if details:
            detail_text = "\n".join([f"• *{k}:* {v}" for k, v in details.items()])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Details:*\n{detail_text}"
                }
            })
        
        blocks.append({"type": "divider"})
        
        return {
            "attachments": [
                {
                    "color": color,
                    "blocks": blocks
                }
            ]
        }

    def send_alert(
        self,
        level: str,
        agent_id: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send alert to Slack.
        
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
            logger.info(f"[SLACK] Would send {level} alert for {agent_id}: {message}")
            logger.debug(f"[SLACK] Payload: {json.dumps(payload, indent=2)}")
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
                    logger.info(f"[SLACK] Sent {level} alert for {agent_id}")
                    return True
                else:
                    logger.error(f"[SLACK] Failed to send: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"[SLACK] Error sending alert: {e}")
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
