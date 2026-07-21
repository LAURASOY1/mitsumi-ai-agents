from typing import Optional, List, Dict, Any, Union, Callable, TypeVar, Tuple
from typing import Optional, List, Dict, Any, Union
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import settings


def build_engine(url: str) -> AsyncEngine:
    return create_async_engine(url, pool_pre_ping=True, future=True)


postgres_engine = build_engine(settings.POSTGRES_URL)
