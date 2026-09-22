"""
Database retry logic for handling transient errors.
"""
from __future__ import annotations
import asyncio
import logging
from typing import TypeVar, Callable, Any
from functools import wraps

logger = logging.getLogger(__name__)
T = TypeVar("T")


async def retry_on_db_error(
    func: Callable[..., Any],
    *args: Any,
    max_attempts: int = 3,
    backoff_base: float = 1.0,
    **kwargs: Any,
) -> Any:
    """Retry async function on transient database errors with exponential backoff."""
    last_exc: Exception = RuntimeError("no attempts made")
    for attempt in range(max_attempts):
        try:
            return await func(*args, **kwargs)
        except Exception as exc:
            last_exc = exc
            msg = str(exc).lower()
            transient = any(kw in msg for kw in [
                "timeout", "connection", "locked", "deadlock",
                "too many connections", "server closed", "broken pipe",
            ])
            if not transient or attempt == max_attempts - 1:
                raise
            wait = backoff_base * (2 ** attempt)
            logger.warning(f"DB transient error attempt {attempt+1}/{max_attempts}: {exc}. Retry in {wait}s")
            await asyncio.sleep(wait)
    raise last_exc


def with_db_retry(max_attempts: int = 3, backoff_base: float = 1.0):
    """Decorator to add retry logic to async DB functions."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await retry_on_db_error(func, *args,
                                           max_attempts=max_attempts,
                                           backoff_base=backoff_base, **kwargs)
        return wrapper
    return decorator
