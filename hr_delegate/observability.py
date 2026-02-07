"""
Observability Module for HR Agent Swarm
=======================================
Provides distributed tracing, metrics, and logging for agent observability.

Features:
- OpenTelemetry tracing (with graceful fallback)
- Prometheus-style metrics
- Structured logging
- Real-time event streaming

Usage:
    from hr_delegate.observability import get_tracer, get_metrics, trace_agent_action
"""

import os
import time
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps
from contextlib import contextmanager
from collections import defaultdict
import threading

logger = logging.getLogger("Observability")

# ═══════════════════════════════════════════════════════════════════════════════
# OPENTELEMETRY INTEGRATION (with fallback)
# ═══════════════════════════════════════════════════════════════════════════════

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.trace import Status, StatusCode
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    logger.info("OpenTelemetry not installed - using fallback tracing")


@dataclass
class Span:
    """Fallback span when OpenTelemetry not available."""
    name: str
    trace_id: str
    span_id: str
    parent_id: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict] = field(default_factory=list)
    status: str = "OK"
    
    def set_attribute(self, key: str, value: Any):
        self.attributes[key] = value
    
    def add_event(self, name: str, attributes: Dict = None):
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes or {}
        })
    
    def set_status(self, status: str, description: str = None):
        self.status = status
        if description:
            self.attributes["status.description"] = description
    
    def end(self):
        self.end_time = time.time()
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": (self.end_time - self.start_time) * 1000 if self.end_time else None,
            "attributes": self.attributes,
            "events": self.events,
            "status": self.status
        }


class Tracer:
    """
    Unified tracer that uses OpenTelemetry if available, else fallback.
    """
    
    def __init__(self, service_name: str = "hr-agent-swarm"):
        self.service_name = service_name
        self._spans: List[Span] = []
        self._active_spans: Dict[str, Span] = {}
        self._span_counter = 0
        self._lock = threading.Lock()
        
        if OTEL_AVAILABLE:
            # Configure OpenTelemetry
            resource = Resource.create({"service.name": service_name})
            provider = TracerProvider(resource=resource)
            
            # Add console exporter for development
            if os.getenv("OTEL_CONSOLE_EXPORT", "false").lower() == "true":
                provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
            
            trace.set_tracer_provider(provider)
            self._otel_tracer = trace.get_tracer(service_name)
            logger.info(f"✓ OpenTelemetry tracer initialized for {service_name}")
        else:
            self._otel_tracer = None
            logger.info(f"✓ Fallback tracer initialized for {service_name}")
    
    def _generate_id(self) -> str:
        """Generate a unique span/trace ID."""
        import random
        return f"{random.randint(0, 2**64):016x}"
    
    @contextmanager
    def start_span(self, name: str, attributes: Dict = None):
        """Start a new span."""
        if self._otel_tracer:
            with self._otel_tracer.start_as_current_span(name) as span:
                if attributes:
                    for k, v in attributes.items():
                        span.set_attribute(k, str(v) if not isinstance(v, (str, int, float, bool)) else v)
                yield span
        else:
            span = Span(
                name=name,
                trace_id=self._generate_id(),
                span_id=self._generate_id(),
                attributes=attributes or {}
            )
            with self._lock:
                self._active_spans[span.span_id] = span
            
            try:
                yield span
            finally:
                span.end()
                with self._lock:
                    self._active_spans.pop(span.span_id, None)
                    self._spans.append(span)
                    # Keep only last 1000 spans
                    if len(self._spans) > 1000:
                        self._spans = self._spans[-500:]
    
    def get_recent_spans(self, limit: int = 50) -> List[Dict]:
        """Get recent spans for debugging."""
        with self._lock:
            return [s.to_dict() for s in self._spans[-limit:]]


# ═══════════════════════════════════════════════════════════════════════════════
# METRICS COLLECTION
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class MetricValue:
    """A single metric value with labels."""
    value: float
    labels: Dict[str, str]
    timestamp: float = field(default_factory=time.time)


class Counter:
    """Prometheus-style counter metric."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self._values: Dict[str, float] = defaultdict(float)
        self._lock = threading.Lock()
    
    def inc(self, labels: Dict[str, str] = None, value: float = 1):
        """Increment the counter."""
        key = json.dumps(labels or {}, sort_keys=True)
        with self._lock:
            self._values[key] += value
    
    def get(self, labels: Dict[str, str] = None) -> float:
        """Get current value."""
        key = json.dumps(labels or {}, sort_keys=True)
        return self._values.get(key, 0)
    
    def to_prometheus(self) -> str:
        """Export in Prometheus format."""
        lines = [f"# HELP {self.name} {self.description}", f"# TYPE {self.name} counter"]
        for key, value in self._values.items():
            labels = json.loads(key)
            label_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
            if label_str:
                lines.append(f"{self.name}{{{label_str}}} {value}")
            else:
                lines.append(f"{self.name} {value}")
        return "\n".join(lines)


class Histogram:
    """Prometheus-style histogram metric."""
    
    DEFAULT_BUCKETS = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
    
    def __init__(self, name: str, description: str, buckets: List[float] = None):
        self.name = name
        self.description = description
        self.buckets = buckets or self.DEFAULT_BUCKETS
        self._observations: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()
    
    def observe(self, value: float, labels: Dict[str, str] = None):
        """Record an observation."""
        key = json.dumps(labels or {}, sort_keys=True)
        with self._lock:
            self._observations[key].append(value)
            # Keep only last 10000 observations per label set
            if len(self._observations[key]) > 10000:
                self._observations[key] = self._observations[key][-5000:]
    
    def get_stats(self, labels: Dict[str, str] = None) -> Dict:
        """Get statistics for the histogram."""
        key = json.dumps(labels or {}, sort_keys=True)
        values = self._observations.get(key, [])
        if not values:
            return {"count": 0, "sum": 0, "avg": 0, "p50": 0, "p95": 0, "p99": 0}
        
        sorted_values = sorted(values)
        count = len(values)
        return {
            "count": count,
            "sum": sum(values),
            "avg": sum(values) / count,
            "p50": sorted_values[int(count * 0.5)],
            "p95": sorted_values[int(count * 0.95)] if count > 20 else sorted_values[-1],
            "p99": sorted_values[int(count * 0.99)] if count > 100 else sorted_values[-1]
        }
    
    def to_prometheus(self) -> str:
        """Export in Prometheus format."""
        lines = [f"# HELP {self.name} {self.description}", f"# TYPE {self.name} histogram"]
        for key, values in self._observations.items():
            labels = json.loads(key)
            label_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
            prefix = f"{self.name}{{{label_str}}}" if label_str else self.name
            
            # Bucket counts
            for bucket in self.buckets:
                count = sum(1 for v in values if v <= bucket)
                lines.append(f'{prefix.replace("}", f",le=\"{bucket}\"")}}} {count}' if label_str else f'{self.name}_bucket{{le="{bucket}"}} {count}')
            
            lines.append(f"{prefix}_count {len(values)}" if label_str else f"{self.name}_count {len(values)}")
            lines.append(f"{prefix}_sum {sum(values)}" if label_str else f"{self.name}_sum {sum(values)}")
        return "\n".join(lines)


class Gauge:
    """Prometheus-style gauge metric."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self._values: Dict[str, float] = {}
        self._lock = threading.Lock()
    
    def set(self, value: float, labels: Dict[str, str] = None):
        """Set the gauge value."""
        key = json.dumps(labels or {}, sort_keys=True)
        with self._lock:
            self._values[key] = value
    
    def inc(self, labels: Dict[str, str] = None, value: float = 1):
        """Increment the gauge."""
        key = json.dumps(labels or {}, sort_keys=True)
        with self._lock:
            self._values[key] = self._values.get(key, 0) + value
    
    def dec(self, labels: Dict[str, str] = None, value: float = 1):
        """Decrement the gauge."""
        self.inc(labels, -value)
    
    def get(self, labels: Dict[str, str] = None) -> float:
        """Get current value."""
        key = json.dumps(labels or {}, sort_keys=True)
        return self._values.get(key, 0)
    
    def to_prometheus(self) -> str:
        """Export in Prometheus format."""
        lines = [f"# HELP {self.name} {self.description}", f"# TYPE {self.name} gauge"]
        for key, value in self._values.items():
            labels = json.loads(key)
            label_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
            if label_str:
                lines.append(f"{self.name}{{{label_str}}} {value}")
            else:
                lines.append(f"{self.name} {value}")
        return "\n".join(lines)


class MetricsRegistry:
    """Central registry for all metrics."""
    
    def __init__(self):
        self._counters: Dict[str, Counter] = {}
        self._histograms: Dict[str, Histogram] = {}
        self._gauges: Dict[str, Gauge] = {}
        self._lock = threading.Lock()
        
        # Pre-register common metrics
        self._init_default_metrics()
    
    def _init_default_metrics(self):
        """Initialize default HR agent metrics."""
        # Counters
        self.counter("agent_actions_total", "Total number of agent actions")
        self.counter("armoriq_intents_total", "Total ArmorIQ intent verifications")
        self.counter("armoriq_denials_total", "Total ArmorIQ denials")
        self.counter("llm_requests_total", "Total LLM API requests")
        self.counter("tool_executions_total", "Total tool executions")
        self.counter("errors_total", "Total errors")
        
        # Histograms
        self.histogram("action_duration_seconds", "Agent action duration")
        self.histogram("llm_latency_seconds", "LLM API latency")
        self.histogram("tool_execution_seconds", "Tool execution duration")
        
        # Gauges
        self.gauge("active_agents", "Number of active agents")
        self.gauge("active_pipelines", "Number of active pipelines")
        self.gauge("agent_risk_score", "Current agent risk score")
    
    def counter(self, name: str, description: str = "") -> Counter:
        """Get or create a counter."""
        with self._lock:
            if name not in self._counters:
                self._counters[name] = Counter(name, description)
            return self._counters[name]
    
    def histogram(self, name: str, description: str = "", buckets: List[float] = None) -> Histogram:
        """Get or create a histogram."""
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = Histogram(name, description, buckets)
            return self._histograms[name]
    
    def gauge(self, name: str, description: str = "") -> Gauge:
        """Get or create a gauge."""
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = Gauge(name, description)
            return self._gauges[name]
    
    def to_prometheus(self) -> str:
        """Export all metrics in Prometheus format."""
        sections = []
        for counter in self._counters.values():
            sections.append(counter.to_prometheus())
        for histogram in self._histograms.values():
            sections.append(histogram.to_prometheus())
        for gauge in self._gauges.values():
            sections.append(gauge.to_prometheus())
        return "\n\n".join(sections)
    
    def get_summary(self) -> Dict:
        """Get a summary of all metrics."""
        summary = {"counters": {}, "histograms": {}, "gauges": {}}
        
        for name, counter in self._counters.items():
            summary["counters"][name] = dict(counter._values)
        
        for name, histogram in self._histograms.items():
            summary["histograms"][name] = {
                k: histogram.get_stats(json.loads(k)) 
                for k in histogram._observations
            }
        
        for name, gauge in self._gauges.items():
            summary["gauges"][name] = dict(gauge._values)
        
        return summary


# ═══════════════════════════════════════════════════════════════════════════════
# EVENT STREAMING
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class AgentEvent:
    """An observable event from an agent."""
    event_type: str
    agent_name: str
    action: str
    timestamp: float = field(default_factory=time.time)
    data: Dict[str, Any] = field(default_factory=dict)
    duration_ms: Optional[float] = None
    success: bool = True
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "event_type": self.event_type,
            "agent": self.agent_name,
            "action": self.action,
            "timestamp": self.timestamp,
            "timestamp_iso": datetime.fromtimestamp(self.timestamp).isoformat(),
            "data": self.data,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error": self.error
        }


class EventStream:
    """Real-time event streaming for observability."""
    
    def __init__(self, max_events: int = 1000):
        self._events: List[AgentEvent] = []
        self._subscribers: List[Callable[[AgentEvent], None]] = []
        self._max_events = max_events
        self._lock = threading.Lock()
    
    def emit(self, event: AgentEvent):
        """Emit an event."""
        with self._lock:
            self._events.append(event)
            if len(self._events) > self._max_events:
                self._events = self._events[-500:]
        
        # Notify subscribers
        for subscriber in self._subscribers:
            try:
                subscriber(event)
            except Exception as e:
                logger.error(f"Event subscriber error: {e}")
    
    def subscribe(self, callback: Callable[[AgentEvent], None]):
        """Subscribe to events."""
        self._subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable[[AgentEvent], None]):
        """Unsubscribe from events."""
        self._subscribers.remove(callback)
    
    def get_recent(self, limit: int = 50, agent: str = None, event_type: str = None) -> List[Dict]:
        """Get recent events with optional filtering."""
        with self._lock:
            events = self._events[-limit * 2:]  # Get extra for filtering
        
        if agent:
            events = [e for e in events if e.agent_name == agent]
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        return [e.to_dict() for e in events[-limit:]]


# ═══════════════════════════════════════════════════════════════════════════════
# DECORATORS FOR INSTRUMENTATION
# ═══════════════════════════════════════════════════════════════════════════════

def trace_agent_action(action_name: str = None):
    """Decorator to trace agent actions."""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            name = action_name or func.__name__
            agent_name = getattr(self, 'name', 'unknown')
            
            tracer = get_tracer()
            metrics = get_metrics()
            events = get_event_stream()
            
            start = time.time()
            success = True
            error_msg = None
            result = None
            
            with tracer.start_span(f"{agent_name}.{name}", {
                "agent.name": agent_name,
                "action": name
            }) as span:
                try:
                    result = func(self, *args, **kwargs)
                    return result
                except Exception as e:
                    success = False
                    error_msg = str(e)
                    if hasattr(span, 'set_status'):
                        span.set_status("ERROR", str(e))
                    raise
                finally:
                    duration = time.time() - start
                    
                    # Record metrics
                    labels = {"agent": agent_name, "action": name}
                    metrics.counter("agent_actions_total").inc(labels)
                    metrics.histogram("action_duration_seconds").observe(duration, labels)
                    if not success:
                        metrics.counter("errors_total").inc(labels)
                    
                    # Emit event
                    events.emit(AgentEvent(
                        event_type="agent_action",
                        agent_name=agent_name,
                        action=name,
                        duration_ms=duration * 1000,
                        success=success,
                        error=error_msg,
                        data={"args_count": len(args), "has_result": result is not None}
                    ))
        return wrapper
    return decorator


def trace_llm_call(func):
    """Decorator to trace LLM API calls."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        metrics = get_metrics()
        start = time.time()
        
        try:
            result = func(*args, **kwargs)
            metrics.counter("llm_requests_total").inc({"status": "success"})
            return result
        except Exception as e:
            metrics.counter("llm_requests_total").inc({"status": "error"})
            raise
        finally:
            duration = time.time() - start
            metrics.histogram("llm_latency_seconds").observe(duration)
    
    return wrapper


def trace_tool_execution(func):
    """Decorator to trace tool executions."""
    @wraps(func)
    def wrapper(self, mcp: str, action: str, *args, **kwargs):
        metrics = get_metrics()
        events = get_event_stream()
        agent_name = getattr(self, 'name', 'unknown')
        
        start = time.time()
        success = True
        error_msg = None
        
        try:
            result = func(self, mcp, action, *args, **kwargs)
            success = result.get("success", True) if isinstance(result, dict) else True
            if not success:
                error_msg = result.get("error", "Unknown error")
            return result
        except Exception as e:
            success = False
            error_msg = str(e)
            raise
        finally:
            duration = time.time() - start
            labels = {"mcp": mcp, "action": action, "agent": agent_name}
            
            metrics.counter("tool_executions_total").inc(labels)
            metrics.histogram("tool_execution_seconds").observe(duration, labels)
            
            events.emit(AgentEvent(
                event_type="tool_execution",
                agent_name=agent_name,
                action=f"{mcp}.{action}",
                duration_ms=duration * 1000,
                success=success,
                error=error_msg
            ))
    
    return wrapper


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETONS & EXPORTS
# ═══════════════════════════════════════════════════════════════════════════════

_tracer: Optional[Tracer] = None
_metrics: Optional[MetricsRegistry] = None
_events: Optional[EventStream] = None


def get_tracer() -> Tracer:
    """Get the singleton tracer."""
    global _tracer
    if _tracer is None:
        _tracer = Tracer()
    return _tracer


def get_metrics() -> MetricsRegistry:
    """Get the singleton metrics registry."""
    global _metrics
    if _metrics is None:
        _metrics = MetricsRegistry()
    return _metrics


def get_event_stream() -> EventStream:
    """Get the singleton event stream."""
    global _events
    if _events is None:
        _events = EventStream()
    return _events


def get_prometheus_metrics() -> str:
    """Get all metrics in Prometheus format."""
    return get_metrics().to_prometheus()


def get_observability_summary() -> Dict:
    """Get a summary of all observability data."""
    return {
        "metrics": get_metrics().get_summary(),
        "recent_events": get_event_stream().get_recent(20),
        "recent_spans": get_tracer().get_recent_spans(20)
    }


# Quick test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='[%(name)s] %(message)s')
    
    # Test metrics
    metrics = get_metrics()
    metrics.counter("test_counter").inc({"label": "test"})
    metrics.histogram("test_histogram").observe(0.1)
    metrics.gauge("test_gauge").set(42)
    
    print("\n=== Prometheus Metrics ===")
    print(get_prometheus_metrics()[:500])
    
    # Test tracing
    tracer = get_tracer()
    with tracer.start_span("test_span", {"key": "value"}) as span:
        time.sleep(0.01)
        span.add_event("test_event")
    
    print(f"\n=== Recent Spans ===")
    print(json.dumps(tracer.get_recent_spans(5), indent=2))
    
    # Test events
    events = get_event_stream()
    events.emit(AgentEvent("test", "TestAgent", "test_action"))
    
    print(f"\n=== Recent Events ===")
    print(json.dumps(events.get_recent(5), indent=2))
