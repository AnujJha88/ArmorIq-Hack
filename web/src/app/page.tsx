'use client';

import { useEffect, useState, useRef } from 'react';

const API_BASE = 'http://localhost:8000';

interface ActionResult {
  tool: string;
  args: Record<string, unknown>;
  allowed: boolean;
  result?: unknown;
  block_reason?: string;
  suggestion?: string;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  actions?: ActionResult[];
  risk_score?: number;
  risk_level?: string;
}

export default function Dashboard() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [riskScore, setRiskScore] = useState(0);
  const [riskLevel, setRiskLevel] = useState('OK');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage }),
      });

      const data = await res.json();

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.message,
        actions: data.actions,
        risk_score: data.risk_score,
        risk_level: data.risk_level,
      }]);

      setRiskScore(data.risk_score);
      setRiskLevel(data.risk_level);
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Failed to connect to backend. Make sure the API is running on port 8000.',
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const getRiskColor = (score: number) => {
    if (score < 0.3) return 'var(--success)';
    if (score < 0.6) return 'var(--warning)';
    return 'var(--danger)';
  };

  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--bg)' }}>
      {/* Header */}
      <header className="border-b px-6 py-4 flex items-center justify-between" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
        <div>
          <h1 className="text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>ArmorIQ</h1>
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>AI Agent with Guardrails</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="text-sm" style={{ color: 'var(--text-muted)' }}>Risk Score</div>
            <div className="text-2xl font-semibold" style={{ color: getRiskColor(riskScore) }}>
              {Math.round(riskScore * 100)}%
            </div>
          </div>
          <div className="px-3 py-1 rounded-full text-sm" style={{
            background: riskLevel === 'OK' ? 'var(--success-light)' : riskLevel === 'WARNING' ? 'var(--warning-light)' : 'var(--danger-light)',
            color: riskLevel === 'OK' ? 'var(--success)' : riskLevel === 'WARNING' ? 'var(--warning)' : 'var(--danger)'
          }}>
            {riskLevel}
          </div>
        </div>
      </header>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-3xl mx-auto space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <h2 className="text-xl font-medium mb-2" style={{ color: 'var(--text-primary)' }}>
                HR Agent Demo
              </h2>
              <p className="mb-6" style={{ color: 'var(--text-muted)' }}>
                Try asking me to do HR tasks. ArmorIQ will check each action.
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                {[
                  'Search for Python developers',
                  'Schedule an interview for Friday at 6pm',
                  'Send an offer for $200,000 to Alice',
                  'Process a $100 expense without receipt',
                ].map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => setInput(prompt)}
                    className="px-3 py-2 rounded-lg text-sm transition-colors"
                    style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text-secondary)' }}
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div
                className="max-w-[80%] rounded-2xl px-4 py-3"
                style={{
                  background: msg.role === 'user' ? 'var(--accent)' : 'var(--surface)',
                  color: msg.role === 'user' ? 'white' : 'var(--text-primary)',
                  border: msg.role === 'user' ? 'none' : '1px solid var(--border)',
                }}
              >
                <p className="whitespace-pre-wrap">{msg.content}</p>

                {/* Show actions */}
                {msg.actions && msg.actions.length > 0 && (
                  <div className="mt-3 space-y-2">
                    {msg.actions.map((action, j) => (
                      <div
                        key={j}
                        className="rounded-lg p-3 text-sm"
                        style={{
                          background: action.allowed ? 'var(--success-light)' : 'var(--danger-light)',
                          border: `1px solid ${action.allowed ? 'var(--success)' : 'var(--danger)'}20`,
                        }}
                      >
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium" style={{ color: action.allowed ? 'var(--success)' : 'var(--danger)' }}>
                            {action.allowed ? '✓' : '✗'} {action.tool}
                          </span>
                        </div>
                        {action.block_reason && (
                          <p style={{ color: 'var(--danger)' }}>Blocked: {action.block_reason}</p>
                        )}
                        {action.suggestion && (
                          <p style={{ color: 'var(--text-secondary)' }}>Suggestion: {action.suggestion}</p>
                        )}
                        {action.result && (
                          <pre className="mt-2 text-xs overflow-x-auto p-2 rounded" style={{ background: 'var(--bg)' }}>
                            {JSON.stringify(action.result, null, 2)}
                          </pre>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* Show risk after assistant message */}
                {msg.role === 'assistant' && msg.risk_score !== undefined && (
                  <div className="mt-2 pt-2 border-t flex items-center gap-2 text-xs" style={{ borderColor: 'var(--border)' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Risk:</span>
                    <span style={{ color: getRiskColor(msg.risk_score) }}>
                      {Math.round(msg.risk_score * 100)}%
                    </span>
                    <span className="px-1.5 py-0.5 rounded" style={{
                      background: msg.risk_level === 'OK' ? 'var(--success-light)' : msg.risk_level === 'WARNING' ? 'var(--warning-light)' : 'var(--danger-light)',
                      color: msg.risk_level === 'OK' ? 'var(--success)' : msg.risk_level === 'WARNING' ? 'var(--warning)' : 'var(--danger)',
                    }}>
                      {msg.risk_level}
                    </span>
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="rounded-2xl px-4 py-3" style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-gray-400 animate-pulse" />
                  <div className="w-2 h-2 rounded-full bg-gray-400 animate-pulse" style={{ animationDelay: '0.2s' }} />
                  <div className="w-2 h-2 rounded-full bg-gray-400 animate-pulse" style={{ animationDelay: '0.4s' }} />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="border-t p-4" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
        <div className="max-w-3xl mx-auto flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask the HR agent to do something..."
            className="flex-1 px-4 py-3 rounded-xl outline-none transition-colors"
            style={{
              background: 'var(--bg)',
              border: '1px solid var(--border)',
              color: 'var(--text-primary)',
            }}
            disabled={loading}
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="px-6 py-3 rounded-xl font-medium transition-opacity disabled:opacity-50"
            style={{ background: 'var(--accent)', color: 'white' }}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
