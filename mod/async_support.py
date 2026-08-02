"""
Async/await support utilities for Flask application.

This module provides helpers for using async/await patterns in Flask,
including async route handlers, async database operations, and async utilities.

Flask 2.0+ supports native async/await in route handlers when using an async
application server like Quart or when using asyncio support.
"""

import asyncio
import functools
from typing import Callable, Any, Optional, Coroutine, TypeVar, Union, List
from concurrent.futures import ThreadPoolExecutor
import time
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class AsyncExecutor:
    """
    Helper for running async operations in a sync Flask context.
    
    Useful for integrating async code into synchronous Flask route handlers.
    """
    
    def __init__(self, max_workers: int = 4):
        """
        Initialize the async executor.
        
        Args:
            max_workers: Maximum number of worker threads
        """
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def run_async(self, coro: Coroutine[Any, Any, T]) -> T:
        """
        Run a coroutine in the thread pool executor.
        
        Args:
            coro: Coroutine to run
            
        Returns:
            Result of the coroutine
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
    
    def shutdown(self) -> None:
        """Shutdown the executor gracefully."""
        self.executor.shutdown(wait=True)


def async_route(func: Callable[..., Coroutine[Any, Any, Any]]) -> Callable[..., Any]:
    """
    Decorator to mark a Flask route handler as async.
    
    This allows using async/await in route handlers.
    
    Example:
        @app.route('/data')
        @async_route
        async def get_data():
            result = await fetch_data()
            return jsonify(result)
    
    Args:
        func: Async function to decorate
        
    Returns:
        Decorated function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        executor = AsyncExecutor()
        try:
            coro = func(*args, **kwargs)
            return executor.run_async(coro)
        finally:
            executor.shutdown()
    
    return wrapper


def run_in_executor(func: Callable[..., T]) -> Callable[..., Coroutine[Any, Any, T]]:
    """
    Decorator to run a synchronous function in a thread executor.
    
    This allows blocking operations to not block the async event loop.
    
    Example:
        @run_in_executor
        def expensive_operation(data):
            return process_data(data)
        
        # In async context:
        result = await expensive_operation(data)
    
    Args:
        func: Synchronous function to run
        
    Returns:
        Async function that runs the sync function in an executor
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> T:
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=1)
        try:
            return await loop.run_in_executor(executor, lambda: func(*args, **kwargs))
        finally:
            executor.shutdown(wait=True)
    
    return wrapper


async def async_gather(*coros: Coroutine[Any, Any, Any], return_exceptions: bool = False) -> List[Any]:
    """
    Run multiple coroutines concurrently and gather results.
    
    Args:
        *coros: Coroutines to run
        return_exceptions: If True, exceptions are returned as results
        
    Returns:
        List of results from coroutines
    """
    return await asyncio.gather(*coros, return_exceptions=return_exceptions)


async def async_sleep(seconds: float) -> None:
    """
    Async sleep function.
    
    Args:
        seconds: Number of seconds to sleep
    """
    await asyncio.sleep(seconds)


class AsyncTask:
    """Helper for running background async tasks."""
    
    def __init__(self, coro: Coroutine[Any, Any, Any], timeout: Optional[float] = None):
        """
        Initialize an async task.
        
        Args:
            coro: Coroutine to run
            timeout: Optional timeout in seconds
        """
        self.coro = coro
        self.timeout = timeout
        self.task: Optional[asyncio.Task] = None
    
    async def start(self) -> Any:
        """
        Start the async task.
        
        Returns:
            Result of the coroutine
        """
        try:
            if self.timeout:
                return await asyncio.wait_for(self.coro, timeout=self.timeout)
            else:
                return await self.coro
        except asyncio.TimeoutError:
            logger.error(f"Async task timed out after {self.timeout} seconds")
            raise
    
    def is_done(self) -> bool:
        """Check if the task is done."""
        return self.task is not None and self.task.done()


async def async_retry(
    func: Callable[..., Coroutine[Any, Any, T]],
    *args,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    **kwargs
) -> T:
    """
    Retry an async function with exponential backoff.
    
    Args:
        func: Async function to retry
        *args: Positional arguments to pass to func
        max_retries: Maximum number of retries
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
        **kwargs: Keyword arguments to pass to func
        
    Returns:
        Result of the function
        
    Raises:
        Exception: If all retries are exhausted
    """
    current_delay = delay
    last_exception: Optional[Exception] = None
    
    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                logger.warning(f"Async function attempt {attempt + 1} failed, retrying in {current_delay}s: {str(e)}")
                await async_sleep(current_delay)
                current_delay *= backoff
            else:
                logger.error(f"Async function failed after {max_retries + 1} attempts: {str(e)}")
    
    raise last_exception or Exception("Async retry failed for unknown reason")


async def async_timeout(
    coro: Coroutine[Any, Any, T],
    timeout: float,
    default: Optional[T] = None
) -> Optional[T]:
    """
    Run a coroutine with a timeout, returning a default value on timeout.
    
    Args:
        coro: Coroutine to run
        timeout: Timeout in seconds
        default: Default value to return on timeout
        
    Returns:
        Result of coroutine or default value
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning(f"Async operation timed out after {timeout} seconds")
        return default


async def measure_async_time(coro: Coroutine[Any, Any, T], operation_name: str = "async operation") -> T:
    """
    Measure the execution time of an async operation.
    
    Args:
        coro: Coroutine to run
        operation_name: Name of the operation for logging
        
    Returns:
        Result of the coroutine
    """
    start = time.time()
    try:
        result = await coro
        duration = time.time() - start
        logger.debug(f"{operation_name} completed in {duration:.3f}s")
        return result
    except Exception as e:
        duration = time.time() - start
        logger.error(f"{operation_name} failed after {duration:.3f}s: {str(e)}")
        raise


class AsyncCache:
    """Simple async cache with TTL support."""
    
    def __init__(self, ttl: float = 300.0):
        """
        Initialize the cache.
        
        Args:
            ttl: Time to live in seconds
        """
        self.ttl = ttl
        self.cache: Dict[str, tuple[Any, float]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache if it exists and hasn't expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if expired/not found
        """
        if key in self.cache:
            value, expiry = self.cache[key]
            if time.time() < expiry:
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        expiry = time.time() + self.ttl
        self.cache[key] = (value, expiry)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
    
    async def get_or_set(self, key: str, func: Callable[..., Coroutine[Any, Any, T]]) -> T:
        """
        Get from cache or compute and cache the result.
        
        Args:
            key: Cache key
            func: Async function to compute value if not cached
            
        Returns:
            Cached or computed value
        """
        cached = self.get(key)
        if cached is not None:
            logger.debug(f"Cache hit for key: {key}")
            return cached
        
        logger.debug(f"Cache miss for key: {key}, computing...")
        result = await func()
        self.set(key, result)
        return result


# Type alias for Dict used in AsyncCache
from typing import Dict
