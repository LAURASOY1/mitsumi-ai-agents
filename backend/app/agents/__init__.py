from typing import Optional, List, Dict, Any, Union, Callable, TypeVar, Tuple
from typing import Optional, List, Dict, Any, Union
from typing import Optional, List, Dict, Any
from app.agents.finance import FinanceAgent
from app.agents.marketing import MarketingAgent
from app.agents.ops import OpsAgent
from app.agents.sales import SalesAgent

AGENT_REGISTRY = {
    "sales": SalesAgent,
    "marketing": MarketingAgent,
    "finance": FinanceAgent,
    "ops": OpsAgent,
}
