from typing import Optional, List, Dict, Any, Union, Callable, TypeVar, Tuple
from typing import Optional, List, Dict, Any, Union
from typing import Optional, List, Dict, Any
"""
Observability module for metrics, logging and monitoring.

This module provides:
- Prometheus metrics for LLM, WebSocket, API and Database
- Helper functions to track requests and operations
- Health check endpoints
"""

from app.observability.metrics import (
    # LLM Metrics
    llm_requests,
    llm_latency,
    llm_tokens,
    llm_cost,
    # WebSocket Metrics
    ws_connections,
    ws_connections_total,
    ws_disconnects,
    ws_messages,
    ws_message_size,
    # API Metrics
    api_requests,
    api_latency,
    # Database Metrics
    db_operations,
    db_latency,
    # Business Metrics
    active_users,
    total_users,
    agent_runs,
    # Helper Functions
    track_llm_request,
    track_websocket_connection,
    track_api_request,
    track_db_operation,
)

__all__ = [
    # LLM Metrics
    'llm_requests',
    'llm_latency',
    'llm_tokens',
    'llm_cost',
    # WebSocket Metrics
    'ws_connections',
    'ws_connections_total',
    'ws_disconnects',
    'ws_messages',
    'ws_message_size',
    # API Metrics
    'api_requests',
    'api_latency',
    # Database Metrics
    'db_operations',
    'db_latency',
    # Business Metrics
    'active_users',
    'total_users',
    'agent_runs',
    # Helper Functions
    'track_llm_request',
    'track_websocket_connection',
    'track_api_request',
    'track_db_operation',
]