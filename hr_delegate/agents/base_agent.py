"""
HR Agent Base Class
====================
All agents inherit from this and use ArmorIQ for intent verification.
"""

import json
import logging
import sys
import os
from typing import Dict, List, Tuple
from datetime import datetime

sys.path.append(r"d:\fun stuff\vibe coding shit\thing 2\hr_delegate\policies")
from armoriq_sdk import ArmorIQWrapper, get_armoriq, PolicyVerdict

logging.basicConfig(level=logging.INFO, format='[%(name)s] %(message)s')


class MockCloveClient:
    """Simulates Clove SDK for standalone operation."""
    def connect(self): return True
    def register_name(self, name): return {"success": True}
    def disconnect(self): pass
    def think(self, prompt): return {"success": True, "content": f"LLM Response..."}
    def exec(self, cmd): return {"success": True, "stdout": "{}"}


class HRAgent:
    """
    Base HR Agent with ArmorIQ Integration
    ======================================
    Every agent action goes through ArmorIQ before execution.
    """
    
    def __init__(self, name: str, primary_intent: str):
        self.name = name
        self.primary_intent = primary_intent
        self.logger = logging.getLogger(name)
        self.clove = MockCloveClient()
        
        # ARMORIQ: Get the shared client
        self.armoriq = get_armoriq()
        
        self.action_log: List[Dict] = []
        self.is_connected = False

    def start(self):
        if not self.clove.connect():
            self.logger.error("Failed to connect to Clove")
            sys.exit(1)
        self.is_connected = True
        self.logger.info(f"🟢 {self.name} Agent ONLINE")

    def stop(self):
        self.clove.disconnect()
        self.is_connected = False
        self.logger.info(f"🔴 {self.name} Agent OFFLINE")
        
        # Print ArmorIQ summary
        report = self.armoriq.get_audit_report()
        self.logger.info(f"📊 ArmorIQ Session: {report['total_intents']} intents | "
                        f"✅ {report['allowed']} | 🛑 {report['denied']} | ⚠️ {report['modified']}")

    def execute_with_armoriq(self, intent_type: str, payload: Dict, description: str) -> Tuple[bool, str, Dict]:
        """
        ═══════════════════════════════════════════════════════════════
        ARMORIQ INTENT VERIFICATION
        ═══════════════════════════════════════════════════════════════
        Every action MUST go through ArmorIQ before execution.
        """
        self.logger.info(f"📋 Requesting ArmorIQ verification: {description}")
        
        # CALL ARMORIQ
        result = self.armoriq.capture_intent(intent_type, payload, self.name)
        
        if not result.allowed:
            self.logger.critical(f"�️  ArmorIQ BLOCKED: {result.reason}")
            return False, result.reason, payload
        
        if result.verdict == PolicyVerdict.MODIFY:
            self.logger.warning(f"🛡️  ArmorIQ MODIFIED: {result.reason}")
            return True, result.reason, result.modified_payload
        
        self.logger.info(f"🛡️  ArmorIQ APPROVED | ID: {result.intent_id}")
        return True, "Approved", payload

    # Backward compatibility
    def execute_with_compliance(self, intent_type: str, payload: Dict, description: str) -> Tuple[bool, str, Dict]:
        return self.execute_with_armoriq(intent_type, payload, description)

    def think(self, prompt: str) -> str:
        """Ask the LLM for reasoning."""
        return self.clove.think(prompt).get("content", "")

    def get_audit_summary(self) -> Dict:
        return self.armoriq.get_audit_report()
