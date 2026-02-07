/**
 * TIRS Dashboard - API Client
 * JavaScript client for TIRS API calls
 */

const TIRS_API = {
    baseUrl: '',

    /**
     * Fetch all agents
     * @returns {Promise<Object>} Agent states
     */
    async getAgents() {
        const response = await fetch(`${this.baseUrl}/api/agents`);
        return response.json();
    },

    /**
     * Fetch a specific agent
     * @param {string} agentId - Agent identifier
     * @returns {Promise<Object>} Agent state
     */
    async getAgent(agentId) {
        const response = await fetch(`${this.baseUrl}/api/agents/${agentId}`);
        if (!response.ok) throw new Error('Agent not found');
        return response.json();
    },

    /**
     * Fetch drift history for an agent
     * @param {string} agentId - Agent identifier
     * @returns {Promise<Object>} Drift history
     */
    async getDrift(agentId) {
        const response = await fetch(`${this.baseUrl}/api/drift/${agentId}`);
        return response.json();
    },

    /**
     * Fetch audit log entries
     * @param {Object} options - Filter options
     * @returns {Promise<Object>} Audit entries
     */
    async getAuditLog(options = {}) {
        const params = new URLSearchParams();
        if (options.limit) params.set('limit', options.limit);
        if (options.eventType) params.set('event_type', options.eventType);
        
        const url = `${this.baseUrl}/api/audit${params.toString() ? '?' + params.toString() : ''}`;
        const response = await fetch(url);
        return response.json();
    },

    /**
     * Run a what-if simulation
     * @param {string} agentId - Agent identifier
     * @param {Array} plan - Plan steps
     * @returns {Promise<Object>} Simulation result
     */
    async simulate(agentId, plan) {
        const response = await fetch(`${this.baseUrl}/api/simulate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ agent_id: agentId, plan: plan })
        });
        return response.json();
    },

    /**
     * Trigger policy reload
     * @returns {Promise<Object>} Reload result
     */
    async reloadPolicies() {
        const response = await fetch(`${this.baseUrl}/api/policy/reload`, {
            method: 'POST'
        });
        return response.json();
    },

    /**
     * Get list of tenants
     * @returns {Promise<Object>} Tenant list
     */
    async getTenants() {
        const response = await fetch(`${this.baseUrl}/api/tenants`);
        return response.json();
    },

    /**
     * Health check
     * @returns {Promise<Object>} Health status
     */
    async healthCheck() {
        const response = await fetch(`${this.baseUrl}/api/health`);
        return response.json();
    }
};

// Helper functions
function formatRiskScore(score) {
    const percentage = (score * 100).toFixed(1);
    let level = 'low';
    if (score >= 0.6) level = 'high';
    else if (score >= 0.3) level = 'medium';
    
    return { percentage, level };
}

function getStatusColor(status) {
    switch (status.toUpperCase()) {
        case 'ACTIVE': return '#00ff88';
        case 'PAUSED': return '#ff6b6b';
        case 'KILLED': return '#ff0000';
        default: return '#808080';
    }
}

function formatTimestamp(timestamp) {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleString();
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { TIRS_API, formatRiskScore, getStatusColor, formatTimestamp };
}
