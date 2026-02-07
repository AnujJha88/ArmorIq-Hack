"""
Watchtower API Server
==================
FastAPI backend for the Watchtower demo.
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Any
import asyncio

from agent.core import get_agent, HRAgent
from tirs.core import get_tirs

app = FastAPI(
    title="Watchtower API",
    description="AI Agent Security Monitoring API",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class ChatRequest(BaseModel):
    message: str
    agent_id: Optional[str] = "hr-agent-001"

class ActionResponse(BaseModel):
    tool: str
    args: dict
    allowed: bool
    result: Optional[Any] = None
    block_reason: Optional[str] = None
    suggestion: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    actions: list[ActionResponse]
    risk_score: float
    risk_level: str

class AgentStatus(BaseModel):
    agent_id: str
    status: str
    risk_score: float
    actions_today: int


# Store agents
agents: dict[str, HRAgent] = {}

def get_or_create_agent(agent_id: str) -> HRAgent:
    if agent_id not in agents:
        from agent.core import HRAgent
        agents[agent_id] = HRAgent(agent_id)
    return agents[agent_id]


@app.get("/")
async def root():
    return {"status": "ok", "service": "Watchtower API"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to the AI agent."""
    agent = get_or_create_agent(request.agent_id)

    response = await agent.chat(request.message)

    return ChatResponse(
        message=response.message,
        actions=[
            ActionResponse(
                tool=a.tool,
                args=a.args,
                allowed=a.allowed,
                result=a.result,
                block_reason=a.block_reason,
                suggestion=a.suggestion
            )
            for a in response.actions
        ],
        risk_score=response.risk_score,
        risk_level=response.risk_level
    )


@app.get("/api/agents")
async def get_agents():
    """Get all agent statuses."""
    tirs = get_tirs()

    # Return demo agents if none exist
    if not agents:
        return {
            "hr-agent-001": {
                "status": "ACTIVE",
                "risk_score": 0.15,
                "actions_today": 0
            }
        }

    result = {}
    for agent_id, agent in agents.items():
        status = agent.get_status()
        result[agent_id] = {
            "status": "PAUSED" if status["is_paused"] else "ACTIVE",
            "risk_score": status["risk_score"],
            "actions_today": status["conversation_length"]
        }

    return result


@app.get("/api/agents/{agent_id}")
async def get_agent_status(agent_id: str):
    """Get specific agent status."""
    if agent_id in agents:
        agent = agents[agent_id]
        status = agent.get_status()
        return {
            "agent_id": agent_id,
            "status": "PAUSED" if status["is_paused"] else "ACTIVE",
            "risk_score": status["risk_score"],
            "actions_today": status["conversation_length"],
            "risk_level": status["risk_level"]
        }

    return {
        "agent_id": agent_id,
        "status": "ACTIVE",
        "risk_score": 0.0,
        "actions_today": 0,
        "risk_level": "OK"
    }


@app.get("/api/drift/{agent_id}")
async def get_drift(agent_id: str):
    """Get drift history for an agent."""
    tirs = get_tirs()

    # Get history from TIRS
    history = tirs.get_drift_history(agent_id)

    return {
        "agent_id": agent_id,
        "history": [
            {"time": h["time"], "score": h["score"]}
            for h in history
        ]
    }


@app.get("/api/audit")
async def get_audit(limit: int = 50):
    """Get audit log entries."""
    tirs = get_tirs()

    events = tirs.get_audit_log(limit)

    return {
        "events": events,
        "total": len(events)
    }


@app.get("/api/health")
async def health():
    """Health check."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
