#!/usr/bin/env python3
"""
Watchtower One - API Server
============================
FastAPI server exposing Watchtower, TIRS, and Compliance APIs.

Run: uvicorn server:app --reload --port 8000
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import asdict

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WatchtowerServer")

# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class VerifyIntentRequest(BaseModel):
    """Request to verify an intent."""
    agent_id: str = Field(..., description="ID of the agent making the request")
    action: str = Field(..., description="Action to perform")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Action parameters")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class CaptureIntentRequest(BaseModel):
    """Simple intent capture request."""
    action_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    agent_name: str = "default_agent"


class AnalyzeIntentRequest(BaseModel):
    """Request for TIRS analysis."""
    agent_id: str
    intent_text: str
    capabilities: List[str] = Field(default_factory=list)
    was_allowed: bool = True
    policy_triggered: Optional[str] = None


class ComplianceRequest(BaseModel):
    """Request for compliance evaluation."""
    action: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    categories: List[str] = Field(default_factory=list)


class GoalRequest(BaseModel):
    """Request to plan a goal."""
    goal: str
    available_agents: List[str] = Field(
        default=["finance_agent", "hr_agent", "it_agent", "legal_agent", "procurement_agent", "operations_agent"]
    )


class AgentActionRequest(BaseModel):
    """Request to execute an agent action."""
    agent_id: str
    action: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    autonomous: bool = False


# =============================================================================
# FASTAPI APP
# =============================================================================

app = FastAPI(
    title="Watchtower One API",
    description="Enterprise Agentic Security System - Triple-Layer Verification",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# LAZY LOADING (avoid startup delays)
# =============================================================================

_watchtower = None
_tirs = None
_compliance = None
_gateway = None
_llm = None
_planner = None


def get_watchtower():
    global _watchtower
    if _watchtower is None:
        from watchtower import get_watchtower as _get_wt
        _watchtower = _get_wt()
    return _watchtower


def get_tirs():
    global _tirs
    if _tirs is None:
        from watchtower.tirs import get_advanced_tirs
        _tirs = get_advanced_tirs()
    return _tirs


def get_compliance():
    global _compliance
    if _compliance is None:
        from watchtower.compliance import get_compliance_engine
        _compliance = get_compliance_engine()
    return _compliance


def get_gateway():
    global _gateway
    if _gateway is None:
        from watchtower.orchestrator import get_gateway as _get_gw
        _gateway = _get_gw()
    return _gateway


def get_llm():
    global _llm
    if _llm is None:
        from watchtower.llm import get_enterprise_llm
        _llm = get_enterprise_llm()
    return _llm


def get_planner():
    global _planner
    if _planner is None:
        from watchtower.llm import get_planner as _get_pl
        _planner = _get_pl()
    return _planner


# =============================================================================
# HEALTH & STATUS ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint with system info."""
    return {
        "name": "Watchtower One",
        "version": "1.0.0",
        "description": "Enterprise Agentic Security System",
        "docs": "/docs",
        "ui": "/ui",
    }


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/status")
async def status():
    """Get system status."""
    try:
        wt = get_watchtower()
        return {
            "status": "operational",
            "watchtower": wt.get_status(),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"status": "degraded", "error": str(e)}


# =============================================================================
# WATCHTOWER ENDPOINTS
# =============================================================================

@app.post("/api/verify")
async def verify_intent(request: VerifyIntentRequest):
    """
    Verify an intent through all three layers.

    This is the main API for intent verification:
    1. Watchtower IAP (policy check)
    2. TIRS (drift detection)
    3. LLM Reasoning (edge cases)
    """
    try:
        wt = get_watchtower()
        result = wt.verify_intent(
            agent_id=request.agent_id,
            action=request.action,
            payload=request.payload,
            context=request.context,
        )
        return result.to_dict()
    except Exception as e:
        logger.error(f"Verify intent failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/capture")
async def capture_intent(request: CaptureIntentRequest):
    """Simple intent capture (Watchtower layer only)."""
    try:
        wt = get_watchtower()
        result = wt.capture_intent(
            action_type=request.action_type,
            payload=request.payload,
            agent_name=request.agent_name,
        )
        return {
            "intent_id": result.intent_id,
            "allowed": result.allowed,
            "verdict": result.verdict.value,
            "reason": result.reason,
            "policy_triggered": result.policy_triggered,
            "timestamp": result.timestamp.isoformat(),
        }
    except Exception as e:
        logger.error(f"Capture intent failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/audit")
async def get_audit_report():
    """Get audit report."""
    try:
        wt = get_watchtower()
        return wt.get_audit_report()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# TIRS ENDPOINTS
# =============================================================================

@app.post("/api/tirs/analyze")
async def analyze_intent(request: AnalyzeIntentRequest):
    """Analyze an intent for drift using TIRS."""
    try:
        tirs = get_tirs()
        result = tirs.analyze_intent(
            agent_id=request.agent_id,
            intent_text=request.intent_text,
            capabilities=set(request.capabilities),
            was_allowed=request.was_allowed,
            policy_triggered=request.policy_triggered,
        )
        return result.to_dict()
    except Exception as e:
        logger.error(f"TIRS analyze failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tirs/agent/{agent_id}")
async def get_agent_status(agent_id: str):
    """Get TIRS status for an agent."""
    try:
        tirs = get_tirs()
        return tirs.get_agent_status(agent_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tirs/dashboard")
async def get_risk_dashboard():
    """Get system-wide risk dashboard."""
    try:
        tirs = get_tirs()
        return tirs.get_risk_dashboard()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tirs/resurrect/{agent_id}")
async def resurrect_agent(agent_id: str, admin_id: str = "admin", reason: str = "Manual resurrection"):
    """Resurrect a killed agent."""
    try:
        tirs = get_tirs()
        success, message = tirs.resurrect_agent(agent_id, admin_id, reason)
        return {"success": success, "message": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# COMPLIANCE ENDPOINTS
# =============================================================================

@app.post("/api/compliance/evaluate")
async def evaluate_compliance(request: ComplianceRequest):
    """Evaluate an action against compliance policies."""
    try:
        engine = get_compliance()
        result = engine.evaluate(
            action=request.action,
            payload=request.payload,
            context=request.context,
        )
        return {
            "allowed": result.allowed,
            "action": result.action.value,
            "severity": result.severity.value if result.severity else None,
            "primary_blocker": str(result.primary_blocker) if result.primary_blocker else None,
            "suggestions": result.suggestions,
            "evaluation_time_ms": result.evaluation_time_ms,
            "results_count": len(result.results),
        }
    except Exception as e:
        logger.error(f"Compliance evaluate failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/compliance/policies")
async def list_policies():
    """List all compliance policies."""
    try:
        engine = get_compliance()
        policies = []
        for policy_id, policy in engine.policies.items():
            policies.append({
                "id": policy_id,
                "name": policy.name,
                "category": policy.category.value,
                "severity": policy.severity.value,
                "description": policy.description,
                "enabled": policy.enabled,
            })
        return {"policies": policies, "count": len(policies)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# LLM ENDPOINTS
# =============================================================================

@app.post("/api/llm/understand")
async def understand_intent(text: str):
    """Parse natural language into structured intent."""
    try:
        llm = get_llm()
        result = llm.understand_intent(text)
        return result
    except Exception as e:
        logger.error(f"LLM understand failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/llm/plan")
async def plan_goal(request: GoalRequest):
    """Create an action plan for a goal."""
    try:
        planner = get_planner()
        plan = planner.create_plan(
            goal=request.goal,
            available_agents=request.available_agents,
        )
        return plan.to_dict()
    except Exception as e:
        logger.error(f"LLM plan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# AGENT ENDPOINTS
# =============================================================================

@app.get("/api/agents")
async def list_agents():
    """List all available agents."""
    return {
        "agents": [
            {"id": "finance_agent", "name": "Finance Agent", "capabilities": ["process_expense", "approve_expense", "create_budget", "verify_invoice"]},
            {"id": "hr_agent", "name": "HR Agent", "capabilities": ["search_candidates", "schedule_interview", "generate_offer", "onboard_employee"]},
            {"id": "it_agent", "name": "IT Agent", "capabilities": ["provision_access", "revoke_access", "create_ticket", "resolve_incident"]},
            {"id": "legal_agent", "name": "Legal Agent", "capabilities": ["review_contract", "draft_nda", "check_ip"]},
            {"id": "procurement_agent", "name": "Procurement Agent", "capabilities": ["approve_vendor", "create_po", "manage_bid"]},
            {"id": "operations_agent", "name": "Operations Agent", "capabilities": ["create_incident", "manage_change", "sla_monitoring"]},
        ]
    }


# =============================================================================
# STATIC FILES & UI
# =============================================================================

# Serve static files if web directory exists
web_dir = Path(__file__).parent / "web_ui"
if web_dir.exists():
    app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")


@app.get("/ui", response_class=HTMLResponse)
async def serve_ui():
    """Serve the web UI."""
    ui_path = Path(__file__).parent / "web_ui" / "index.html"
    if ui_path.exists():
        return FileResponse(ui_path)
    else:
        # Return inline UI if no file exists
        return get_inline_ui()


def get_inline_ui():
    """Return inline HTML UI."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Watchtower One</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        body { font-family: 'Inter', system-ui, sans-serif; }
        .gradient-bg { background: linear-gradient(135deg, #1e3a5f 0%, #0f1c2e 100%); }
        .card { background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); }
        .risk-nominal { color: #10b981; }
        .risk-elevated { color: #f59e0b; }
        .risk-warning { color: #f97316; }
        .risk-critical { color: #ef4444; }
        .risk-terminal { color: #7f1d1d; }
    </style>
</head>
<body class="gradient-bg min-h-screen text-white">
    <div id="app" class="container mx-auto px-4 py-8">
        <!-- Header -->
        <header class="mb-8">
            <h1 class="text-4xl font-bold mb-2">🛡️ Watchtower One</h1>
            <p class="text-gray-400">Enterprise Agentic Security System</p>
        </header>

        <!-- Status Cards -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div class="card rounded-lg p-6 border border-gray-700">
                <h3 class="text-lg font-semibold mb-2">System Status</h3>
                <div id="system-status" class="text-2xl font-bold text-green-400">Loading...</div>
            </div>
            <div class="card rounded-lg p-6 border border-gray-700">
                <h3 class="text-lg font-semibold mb-2">Intents Processed</h3>
                <div id="intents-count" class="text-2xl font-bold">0</div>
            </div>
            <div class="card rounded-lg p-6 border border-gray-700">
                <h3 class="text-lg font-semibold mb-2">Active Layers</h3>
                <div id="layers-status" class="text-sm">Loading...</div>
            </div>
        </div>

        <!-- Main Content -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <!-- Verify Intent Panel -->
            <div class="card rounded-lg p-6 border border-gray-700">
                <h2 class="text-xl font-bold mb-4">🔍 Verify Intent</h2>
                <form id="verify-form" class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium mb-1">Agent ID</label>
                        <select id="agent-id" class="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2">
                            <option value="finance_agent">Finance Agent</option>
                            <option value="hr_agent">HR Agent</option>
                            <option value="it_agent">IT Agent</option>
                            <option value="legal_agent">Legal Agent</option>
                            <option value="procurement_agent">Procurement Agent</option>
                            <option value="operations_agent">Operations Agent</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-1">Action</label>
                        <input type="text" id="action" placeholder="approve_expense"
                               class="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2">
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-1">Payload (JSON)</label>
                        <textarea id="payload" rows="3"
                                  placeholder='{"amount": 500, "department": "engineering"}'
                                  class="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 font-mono text-sm"></textarea>
                    </div>
                    <button type="submit"
                            class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
                        Verify Intent
                    </button>
                </form>
                <div id="verify-result" class="mt-4 hidden">
                    <h3 class="font-semibold mb-2">Result:</h3>
                    <pre class="bg-gray-900 p-4 rounded text-sm overflow-auto max-h-64"></pre>
                </div>
            </div>

            <!-- Quick Actions Panel -->
            <div class="card rounded-lg p-6 border border-gray-700">
                <h2 class="text-xl font-bold mb-4">⚡ Quick Tests</h2>
                <div class="space-y-3">
                    <button onclick="testExpenseApproval()"
                            class="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded text-left">
                        ✓ Test: Approve $500 Expense (should pass)
                    </button>
                    <button onclick="testExpenseNoReceipt()"
                            class="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded text-left">
                        ✗ Test: Expense without Receipt (should deny)
                    </button>
                    <button onclick="testSalaryOverCap()"
                            class="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded text-left">
                        ✗ Test: Salary over Cap (should deny)
                    </button>
                    <button onclick="testScheduleInterview()"
                            class="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded text-left">
                        ✓ Test: Schedule Interview (should pass)
                    </button>
                    <button onclick="testDriftDetection()"
                            class="w-full bg-yellow-600 hover:bg-yellow-700 text-white font-bold py-2 px-4 rounded text-left">
                        ⚠ Test: TIRS Drift Detection (multiple calls)
                    </button>
                </div>
                <div id="quick-result" class="mt-4 hidden">
                    <h3 class="font-semibold mb-2">Result:</h3>
                    <pre class="bg-gray-900 p-4 rounded text-sm overflow-auto max-h-64"></pre>
                </div>
            </div>
        </div>

        <!-- Risk Dashboard -->
        <div class="card rounded-lg p-6 border border-gray-700 mt-8">
            <h2 class="text-xl font-bold mb-4">📊 TIRS Risk Dashboard</h2>
            <button onclick="loadDashboard()" class="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded mb-4">
                Refresh Dashboard
            </button>
            <div id="dashboard" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <p class="text-gray-400">Click refresh to load agent data...</p>
            </div>
        </div>

        <!-- Audit Log -->
        <div class="card rounded-lg p-6 border border-gray-700 mt-8">
            <h2 class="text-xl font-bold mb-4">📋 Audit Log</h2>
            <button onclick="loadAudit()" class="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded mb-4">
                Refresh Audit Log
            </button>
            <div id="audit-log" class="space-y-2">
                <p class="text-gray-400">Click refresh to load audit entries...</p>
            </div>
        </div>
    </div>

    <script>
        const API_BASE = '';

        // Load status on page load
        async function loadStatus() {
            try {
                const res = await fetch(`${API_BASE}/status`);
                const data = await res.json();

                document.getElementById('system-status').textContent =
                    data.status === 'operational' ? '✓ Operational' : '⚠ Degraded';
                document.getElementById('system-status').className =
                    'text-2xl font-bold ' + (data.status === 'operational' ? 'text-green-400' : 'text-yellow-400');

                if (data.watchtower) {
                    document.getElementById('intents-count').textContent = data.watchtower.intents_processed || 0;

                    const layers = data.watchtower.layers || {};
                    document.getElementById('layers-status').innerHTML = `
                        <div>Watchtower: ${layers.watchtower?.mode || 'N/A'}</div>
                        <div>TIRS: ${layers.tirs?.available ? '✓' : '✗'}</div>
                        <div>LLM: ${layers.llm?.available ? '✓' : '✗'}</div>
                    `;
                }
            } catch (e) {
                document.getElementById('system-status').textContent = '✗ Error';
                document.getElementById('system-status').className = 'text-2xl font-bold text-red-400';
            }
        }

        // Verify intent form
        document.getElementById('verify-form').addEventListener('submit', async (e) => {
            e.preventDefault();

            let payload = {};
            try {
                payload = JSON.parse(document.getElementById('payload').value || '{}');
            } catch (e) {
                alert('Invalid JSON in payload');
                return;
            }

            const request = {
                agent_id: document.getElementById('agent-id').value,
                action: document.getElementById('action').value,
                payload: payload,
                context: {}
            };

            try {
                const res = await fetch(`${API_BASE}/api/verify`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(request)
                });
                const data = await res.json();

                const resultDiv = document.getElementById('verify-result');
                resultDiv.classList.remove('hidden');
                resultDiv.querySelector('pre').textContent = JSON.stringify(data, null, 2);

                loadStatus();
            } catch (e) {
                alert('Error: ' + e.message);
            }
        });

        // Quick test functions
        async function runQuickTest(agentId, action, payload) {
            try {
                const res = await fetch(`${API_BASE}/api/verify`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({agent_id: agentId, action: action, payload: payload, context: {}})
                });
                const data = await res.json();

                const resultDiv = document.getElementById('quick-result');
                resultDiv.classList.remove('hidden');
                resultDiv.querySelector('pre').textContent = JSON.stringify(data, null, 2);

                loadStatus();
            } catch (e) {
                alert('Error: ' + e.message);
            }
        }

        function testExpenseApproval() {
            runQuickTest('finance_agent', 'approve_expense', {amount: 500, department: 'engineering', has_receipt: true});
        }

        function testExpenseNoReceipt() {
            runQuickTest('finance_agent', 'approve_expense', {amount: 100, has_receipt: false});
        }

        function testSalaryOverCap() {
            runQuickTest('hr_agent', 'generate_offer', {role: 'L4', salary: 200000});
        }

        function testScheduleInterview() {
            runQuickTest('hr_agent', 'schedule_interview', {candidate: 'Jane Doe', time: '2024-02-15 10:00'});
        }

        async function testDriftDetection() {
            const results = [];
            for (let i = 0; i < 5; i++) {
                const res = await fetch(`${API_BASE}/api/tirs/analyze`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        agent_id: 'test_drift_agent',
                        intent_text: `action_${i}`,
                        capabilities: [`cap_${i}`],
                        was_allowed: i % 2 === 0
                    })
                });
                results.push(await res.json());
            }

            const resultDiv = document.getElementById('quick-result');
            resultDiv.classList.remove('hidden');
            resultDiv.querySelector('pre').textContent = JSON.stringify(results, null, 2);
        }

        // Dashboard
        async function loadDashboard() {
            try {
                const res = await fetch(`${API_BASE}/api/tirs/dashboard`);
                const data = await res.json();

                const dashboard = document.getElementById('dashboard');
                const agents = data.agents?.agents || [];

                if (agents.length === 0) {
                    dashboard.innerHTML = '<p class="text-gray-400">No agents tracked yet. Run some tests first!</p>';
                    return;
                }

                dashboard.innerHTML = agents.map(agent => `
                    <div class="bg-gray-800 rounded p-4">
                        <h4 class="font-bold">${agent.agent_id}</h4>
                        <div class="text-sm mt-2">
                            <div>Status: <span class="font-mono">${agent.status}</span></div>
                            <div>Risk: <span class="risk-${agent.risk_level || 'nominal'}">${(agent.risk_score * 100).toFixed(1)}%</span></div>
                            <div>Intents: ${agent.total_intents}</div>
                        </div>
                    </div>
                `).join('');
            } catch (e) {
                document.getElementById('dashboard').innerHTML = '<p class="text-red-400">Error loading dashboard</p>';
            }
        }

        // Audit log
        async function loadAudit() {
            try {
                const res = await fetch(`${API_BASE}/api/audit`);
                const data = await res.json();

                const auditLog = document.getElementById('audit-log');
                const entries = data.recent_entries || [];

                if (entries.length === 0) {
                    auditLog.innerHTML = '<p class="text-gray-400">No audit entries yet.</p>';
                    return;
                }

                auditLog.innerHTML = entries.reverse().map(entry => `
                    <div class="bg-gray-800 rounded p-3 text-sm">
                        <div class="flex justify-between">
                            <span class="font-mono">${entry.intent_id}</span>
                            <span class="${entry.allowed ? 'text-green-400' : 'text-red-400'}">
                                ${entry.allowed ? 'ALLOWED' : 'DENIED'}
                            </span>
                        </div>
                        <div class="text-gray-400">${entry.agent_id} → ${entry.action}</div>
                        <div class="text-xs text-gray-500">${entry.timestamp}</div>
                    </div>
                `).join('');
            } catch (e) {
                document.getElementById('audit-log').innerHTML = '<p class="text-red-400">Error loading audit log</p>';
            }
        }

        // Initialize
        loadStatus();
        setInterval(loadStatus, 10000);
    </script>
</body>
</html>
    """


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    print("\n" + "="*60)
    print("  WATCHTOWER ONE - API SERVER")
    print("="*60)
    print("\n  Starting server on http://localhost:8000")
    print("  API Docs: http://localhost:8000/docs")
    print("  Web UI: http://localhost:8000/ui")
    print("\n" + "="*60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)
