from typing import Optional, List, Dict, Any, Union, Callable, TypeVar, Tuple
from typing import Optional, List, Dict, Any, Union
from typing import Optional, List, Dict, Any
"""arq worker entry point — run with:

    arq app.core.worker.WorkerSettings

Managed by supervisor (see /etc/supervisor/conf.d/agent-worker.conf).
"""


# Importing handlers registers them into the HANDLERS dict.
from app.core import handlers  # noqa: F401
from app.core.jobs import ensure_indexes, redis_settings, run_task


async def startup(ctx) -> None:
    await ensure_indexes()


class WorkerSettings:
    functions = [run_task]
    redis_settings = redis_settings()
    on_startup = startup
    max_jobs = 10
    job_timeout = 15 * 60  # 15 minutes per task, generous for report/PDF work
    keep_result_forever = False
