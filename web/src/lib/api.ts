const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Agent {
  status: 'ACTIVE' | 'PAUSED' | 'BLOCKED';
  risk_score: number;
  actions_today: number;
}

export interface AgentMap {
  [agentId: string]: Agent;
}

export interface DriftPoint {
  time: string;
  score: number;
}

export interface DriftHistory {
  agent_id: string;
  history: DriftPoint[];
}

export interface AuditEvent {
  id: number;
  time: string;
  agent: string;
  event: string;
  details: string;
}

export interface SimulationResult {
  agent_id: string;
  verdict: string;
  step_count?: number;
  blocked_steps?: number;
  error?: string;
}

export async function fetchAgents(): Promise<AgentMap> {
  const res = await fetch(`${API_BASE}/api/agents`);
  if (!res.ok) throw new Error('Failed to fetch agents');
  return res.json();
}

export async function fetchAgent(agentId: string): Promise<Agent & { agent_id: string }> {
  const res = await fetch(`${API_BASE}/api/agents/${agentId}`);
  if (!res.ok) throw new Error('Failed to fetch agent');
  return res.json();
}

export async function fetchDrift(agentId: string): Promise<DriftHistory> {
  const res = await fetch(`${API_BASE}/api/drift/${agentId}`);
  if (!res.ok) throw new Error('Failed to fetch drift');
  return res.json();
}

export async function fetchAuditLog(limit = 50, eventType?: string): Promise<{ events: AuditEvent[]; total: number }> {
  const params = new URLSearchParams({ limit: limit.toString() });
  if (eventType) params.append('event_type', eventType);
  const res = await fetch(`${API_BASE}/api/audit?${params}`);
  if (!res.ok) throw new Error('Failed to fetch audit log');
  return res.json();
}

export async function simulatePlan(agentId: string, plan: object[]): Promise<SimulationResult> {
  const res = await fetch(`${API_BASE}/api/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ agent_id: agentId, plan }),
  });
  if (!res.ok) throw new Error('Failed to simulate plan');
  return res.json();
}

export async function reloadPolicies(): Promise<{ success: boolean; version?: string; error?: string }> {
  const res = await fetch(`${API_BASE}/api/policy/reload`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to reload policies');
  return res.json();
}

export async function fetchTenants(): Promise<{ tenants: Record<string, unknown> }> {
  const res = await fetch(`${API_BASE}/api/tenants`);
  if (!res.ok) throw new Error('Failed to fetch tenants');
  return res.json();
}

export async function healthCheck(): Promise<{ status: string; timestamp: string }> {
  const res = await fetch(`${API_BASE}/api/health`);
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}
