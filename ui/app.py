"""
TIRS Dashboard
==============
FastAPI web application for the TIRS monitoring dashboard.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from typing import Dict, Any, List, Optional
import json
import logging

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TIRS.Dashboard")

# Create FastAPI app
app = FastAPI(
    title="TIRS Dashboard",
    description="Temporal Intent Regression Sandbox - Monitoring Dashboard",
    version="1.0.0"
)

# Mount static files
static_path = Path(__file__).parent / "static"
static_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Setup templates
templates_path = Path(__file__).parent / "templates"
templates_path.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(templates_path))

# In-memory state (in production, use proper storage)
agent_states: Dict[str, Dict[str, Any]] = {
    "sourcer-001": {"status": "ACTIVE", "risk_score": 0.15, "actions_today": 12},
    "screener-002": {"status": "ACTIVE", "risk_score": 0.28, "actions_today": 45},
    "scheduler-003": {"status": "PAUSED", "risk_score": 0.72, "actions_today": 8},
    "negotiator-004": {"status": "ACTIVE", "risk_score": 0.35, "actions_today": 6},
    "onboarder-005": {"status": "ACTIVE", "risk_score": 0.10, "actions_today": 3},
}

drift_history: Dict[str, List[Dict]] = {
    "sourcer-001": [
        {"time": "09:00", "score": 0.10},
        {"time": "10:00", "score": 0.12},
        {"time": "11:00", "score": 0.14},
        {"time": "12:00", "score": 0.15},
    ],
    "screener-002": [
        {"time": "09:00", "score": 0.20},
        {"time": "10:00", "score": 0.25},
        {"time": "11:00", "score": 0.26},
        {"time": "12:00", "score": 0.28},
    ],
    "scheduler-003": [
        {"time": "09:00", "score": 0.35},
        {"time": "10:00", "score": 0.48},
        {"time": "11:00", "score": 0.62},
        {"time": "12:00", "score": 0.72},
    ],
}

audit_log: List[Dict[str, Any]] = [
    {"id": 1, "time": "12:45:32", "agent": "scheduler-003", "event": "DRIFT_WARNING", "details": "Risk score exceeded 0.6"},
    {"id": 2, "time": "12:46:01", "agent": "scheduler-003", "event": "AGENT_PAUSED", "details": "Automatic pause triggered"},
    {"id": 3, "time": "12:30:15", "agent": "screener-002", "event": "INTENT_CAPTURED", "details": "screen_resume action"},
    {"id": 4, "time": "12:15:22", "agent": "sourcer-001", "event": "POLICY_ALLOW", "details": "LinkedIn search approved"},
    {"id": 5, "time": "11:45:10", "agent": "negotiator-004", "event": "PLAN_SIMULATED", "details": "Offer generation plan OK"},
]


# Pydantic models
class SimulationRequest(BaseModel):
    agent_id: str
    plan: List[Dict[str, Any]]


# Routes
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page."""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "agents": agent_states,
        "audit_recent": audit_log[:5],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })


@app.get("/drift", response_class=HTMLResponse)
async def drift_page(request: Request):
    """Drift visualization page."""
    return templates.TemplateResponse("drift_graph.html", {
        "request": request,
        "agents": list(agent_states.keys())
    })


@app.get("/audit", response_class=HTMLResponse)
async def audit_page(request: Request):
    """Audit log viewer page."""
    return templates.TemplateResponse("audit_viewer.html", {
        "request": request,
        "events": audit_log
    })


# API Routes
@app.get("/api/agents")
async def get_agents():
    """Get all agent statuses."""
    return agent_states


@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get specific agent status."""
    if agent_id not in agent_states:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"agent_id": agent_id, **agent_states[agent_id]}


@app.get("/api/drift/{agent_id}")
async def get_drift(agent_id: str):
    """Get drift history for an agent."""
    if agent_id not in drift_history:
        return {"agent_id": agent_id, "history": []}
    return {"agent_id": agent_id, "history": drift_history[agent_id]}


@app.get("/api/audit")
async def get_audit(limit: int = 50, event_type: Optional[str] = None):
    """Get audit log entries."""
    events = audit_log
    
    if event_type:
        events = [e for e in events if e["event"] == event_type]
    
    return {"events": events[:limit], "total": len(events)}


@app.post("/api/simulate")
async def simulate_plan(req: SimulationRequest):
    """Run what-if simulation."""
    try:
        from tirs import get_simulator
        simulator = get_simulator()
        result = simulator.simulate_plan(req.agent_id, req.plan)
        
        return {
            "agent_id": req.agent_id,
            "verdict": result.overall_verdict,
            "step_count": len(result.step_results),
            "blocked_steps": sum(1 for s in result.step_results if s.verdict == "BLOCKED")
        }
    except Exception as e:
        logger.error(f"Simulation error: {e}")
        return {
            "agent_id": req.agent_id,
            "verdict": "ERROR",
            "error": str(e)
        }


@app.post("/api/policy/reload")
async def reload_policies():
    """Trigger policy hot-reload."""
    try:
        from hr_delegate.policies.policy_registry import get_registry
        registry = get_registry()
        success = registry.reload_from_file()
        
        return {"success": success, "version": registry.version}
    except Exception as e:
        logger.error(f"Policy reload error: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/tenants")
async def get_tenants():
    """List all tenants."""
    try:
        from hr_delegate.policies.tenant_manager import get_tenant_manager
        manager = get_tenant_manager()
        return {"tenants": manager.list_tenants()}
    except Exception as e:
        logger.error(f"Tenant list error: {e}")
        return {"tenants": {}, "error": str(e)}


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
