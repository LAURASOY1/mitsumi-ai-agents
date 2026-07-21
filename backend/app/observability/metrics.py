from typing import Optional, List, Dict, Any, Union, Callable, TypeVar, Tuple
from typing import Optional, List, Dict, Any, Union
from typing import Optional, List, Dict, Any
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time
from typing import Dict, Any
# LLM METRICS
llm_requests = Counter(
    'llm_requests_total',
    'Total number of LLM requests',
    ['provider', 'model', 'status']
)

llm_latency = Histogram(
    'llm_request_duration_seconds',
    'LLM request duration in seconds',
    ['provider', 'model'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

llm_tokens = Counter(
    'llm_tokens_total',
    'Total tokens used by LLM',
    ['provider', 'model', 'type']
)

llm_cost = Gauge(
    'llm_cost_dollars',
    'LLM cost in dollars',
    ['provider', 'model']
)

# WEBSOCKET METRICS
ws_connections = Gauge(
    'websocket_connections_current',
    'Current active WebSocket connections',
    ['agent_name']
)

ws_connections_total = Counter(
    'websocket_connections_total',
    'Total WebSocket connections established',
    ['agent_name']
)

ws_disconnects = Counter(
    'websocket_disconnects_total',
    'Total WebSocket disconnects',
    ['agent_name', 'reason']
)

ws_messages = Counter(
    'websocket_messages_total',
    'Total WebSocket messages',
    ['agent_name', 'direction']
)

ws_message_size = Histogram(
    'websocket_message_size_bytes',
    'WebSocket message size in bytes',
    ['agent_name'],
    buckets=[100, 500, 1000, 5000, 10000, 50000]
)

# API METRICS
api_requests = Counter(
    'api_requests_total',
    'Total API requests',
    ['endpoint', 'method', 'status_code']
)

api_latency = Histogram(
    'api_request_duration_seconds',
    'API request duration in seconds',
    ['endpoint', 'method'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# DATABASE METRICS
db_operations = Counter(
    'db_operations_total',
    'Total database operations',
    ['collection', 'operation', 'status']
)

db_latency = Histogram(
    'db_operation_duration_seconds',
    'Database operation duration in seconds',
    ['collection', 'operation'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
)
# BUSINESS METRICS
active_users = Gauge(
    'active_users_current',
    'Current active users'
)

total_users = Counter(
    'users_total',
    'Total registered users'
)

agent_runs = Counter(
    'agent_runs_total',
    'Total agent runs',
    ['agent_name', 'status']
)

# HELPER FUNCTIONS

def track_llm_request(provider: str, model: str, duration: float, tokens: Dict[str, int], status: str = "success"):
    """Track an LLM request with all metrics"""
    llm_requests.labels(provider=provider, model=model, status=status).inc()
    llm_latency.labels(provider=provider, model=model).observe(duration)
    
    if tokens:
        llm_tokens.labels(provider=provider, model=model, type="prompt").inc(tokens.get('prompt_tokens', 0))
        llm_tokens.labels(provider=provider, model=model, type="completion").inc(tokens.get('completion_tokens', 0))
        llm_tokens.labels(provider=provider, model=model, type="total").inc(tokens.get('total_tokens', 0))
    
    # Update cost estimate (example rates)
    if provider == "openai":
        if model.startswith("gpt-4"):
            cost = (tokens.get('prompt_tokens', 0) * 0.00003 + tokens.get('completion_tokens', 0) * 0.00006) / 1000
        else:
            cost = (tokens.get('prompt_tokens', 0) * 0.0000005 + tokens.get('completion_tokens', 0) * 0.0000015) / 1000
        llm_cost.labels(provider=provider, model=model).set(cost)

def track_websocket_connection(agent_name: str, connected: bool = True, reason: str = ""):
    """Track WebSocket connection events"""
    if connected:
        ws_connections.labels(agent_name=agent_name).inc()
        ws_connections_total.labels(agent_name=agent_name).inc()
    else:
        ws_connections.labels(agent_name=agent_name).dec()
        ws_disconnects.labels(agent_name=agent_name, reason=reason).inc()

def track_api_request(endpoint: str, method: str, status_code: int, duration: float):
    """Track API request"""
    api_requests.labels(endpoint=endpoint, method=method, status_code=str(status_code)).inc()
    api_latency.labels(endpoint=endpoint, method=method).observe(duration)

def track_db_operation(collection: str, operation: str, duration: float, status: str = "success"):
    """Track database operation"""
    db_operations.labels(collection=collection, operation=operation, status=status).inc()
    db_latency.labels(collection=collection, operation=operation).observe(duration)
