import asyncio
import functools
import logging
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F")


def with_retry(max_retries: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)):
    """指数バックオフでリトライするデコレータ"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    wait = delay * (2 ** attempt)
                    logger.warning(f"{func.__name__} attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {wait}s")
                    await asyncio.sleep(wait)
            raise last_exc
        return wrapper
    return decorator
