import asyncio
import concurrent.futures
from typing import Any, Coroutine


def run_coro_sync(coro: Coroutine[Any, Any, Any]) -> Any:
    """
    Safely executes an async coroutine from synchronous Celery worker contexts,
    handling both standalone thread loops and active event loops.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(lambda: asyncio.run(coro))
            return future.result()
    else:
        return asyncio.run(coro)
