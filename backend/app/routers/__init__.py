"""
Routers module - Python 3.8 compatible
"""
# Import auth router
from app.routers.auth import router as auth_router

# Import other routers (uncomment as needed)
# from app.routers.agents import router as agent_router
# from app.routers.websocket import router as websocket_router

__all__ = ["auth_router"]
