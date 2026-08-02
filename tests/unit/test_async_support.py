"""
Unit tests for async support utilities.
"""

import asyncio
import pytest
from mod.async_support import (
    AsyncExecutor, async_route, run_in_executor, async_gather,
    async_sleep, AsyncTask, async_retry, async_timeout,
    measure_async_time, AsyncCache
)


@pytest.mark.unit
class TestAsyncExecutor:
    """Test cases for AsyncExecutor class."""
    
    def test_executor_initialization(self):
        """Test AsyncExecutor initialization."""
        executor = AsyncExecutor(max_workers=2)
        assert executor is not None
        executor.shutdown()
    
    def test_run_async_simple(self):
        """Test running a simple async coroutine."""
        executor = AsyncExecutor()
        
        async def simple_coro():
            return 42
        
        result = executor.run_async(simple_coro())
        assert result == 42
        executor.shutdown()
    
    def test_run_async_with_await(self):
        """Test running async coroutine with await."""
        executor = AsyncExecutor()
        
        async def async_operation():
            await asyncio.sleep(0.01)
            return "completed"
        
        result = executor.run_async(async_operation())
        assert result == "completed"
        executor.shutdown()


@pytest.mark.unit
class TestAsyncRouteDecorator:
    """Test cases for async_route decorator."""
    
    def test_async_route_decorator(self):
        """Test async_route decorator."""
        @async_route
        async def async_handler():
            return {"status": "ok"}
        
        result = async_handler()
        assert result == {"status": "ok"}
    
    def test_async_route_with_args(self):
        """Test async_route decorator with arguments."""
        @async_route
        async def async_handler_with_args(x, y):
            await asyncio.sleep(0.01)
            return x + y
        
        result = async_handler_with_args(5, 3)
        assert result == 8


@pytest.mark.unit
class TestRunInExecutor:
    """Test cases for run_in_executor decorator."""
    
    @pytest.mark.asyncio
    async def test_run_in_executor_simple(self):
        """Test run_in_executor with simple function."""
        @run_in_executor
        def sync_function(x):
            return x * 2
        
        result = await sync_function(21)
        assert result == 42
    
    @pytest.mark.asyncio
    async def test_run_in_executor_cpu_bound(self):
        """Test run_in_executor with CPU-bound operation."""
        @run_in_executor
        def cpu_bound():
            total = sum(range(100000))
            return total
        
        result = await cpu_bound()
        assert result == sum(range(100000))


@pytest.mark.unit
class TestAsyncGather:
    """Test cases for async_gather function."""
    
    @pytest.mark.asyncio
    async def test_gather_multiple_coroutines(self):
        """Test gathering multiple coroutines."""
        async def coro1():
            await asyncio.sleep(0.01)
            return 1
        
        async def coro2():
            await asyncio.sleep(0.01)
            return 2
        
        results = await async_gather(coro1(), coro2())
        assert results == [1, 2]
    
    @pytest.mark.asyncio
    async def test_gather_with_exception(self):
        """Test gathering with exception handling."""
        async def failing_coro():
            raise ValueError("Test error")
        
        async def success_coro():
            return "success"
        
        results = await async_gather(
            failing_coro(),
            success_coro(),
            return_exceptions=True
        )
        assert len(results) == 2
        assert isinstance(results[0], ValueError)
        assert results[1] == "success"


@pytest.mark.unit
class TestAsyncSleep:
    """Test cases for async_sleep function."""
    
    @pytest.mark.asyncio
    async def test_async_sleep(self):
        """Test async sleep function."""
        import time
        start = time.time()
        await async_sleep(0.1)
        duration = time.time() - start
        assert duration >= 0.1


@pytest.mark.unit
class TestAsyncTask:
    """Test cases for AsyncTask class."""
    
    @pytest.mark.asyncio
    async def test_async_task_start(self):
        """Test AsyncTask.start method."""
        async def task_coro():
            await asyncio.sleep(0.01)
            return "task_complete"
        
        task = AsyncTask(task_coro())
        result = await task.start()
        assert result == "task_complete"
    
    @pytest.mark.asyncio
    async def test_async_task_timeout(self):
        """Test AsyncTask with timeout."""
        async def slow_coro():
            await asyncio.sleep(10)
            return "complete"
        
        task = AsyncTask(slow_coro(), timeout=0.1)
        with pytest.raises(asyncio.TimeoutError):
            await task.start()


@pytest.mark.unit
class TestAsyncRetry:
    """Test cases for async_retry function."""
    
    @pytest.mark.asyncio
    async def test_retry_success_first_try(self):
        """Test retry on first try success."""
        async def success_coro():
            return "success"
        
        result = await async_retry(success_coro, max_retries=2)
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_retry_eventual_success(self):
        """Test retry with eventual success."""
        attempt_count = 0
        
        async def eventually_succeeds():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ValueError("Temporary failure")
            return "success"
        
        result = await async_retry(
            eventually_succeeds,
            max_retries=3,
            delay=0.01
        )
        assert result == "success"
        assert attempt_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_exhausted(self):
        """Test retry when exhausted."""
        async def always_fails():
            raise ValueError("Permanent failure")
        
        with pytest.raises(ValueError):
            await async_retry(
                always_fails,
                max_retries=2,
                delay=0.01
            )


@pytest.mark.unit
class TestAsyncTimeout:
    """Test cases for async_timeout function."""
    
    @pytest.mark.asyncio
    async def test_timeout_success(self):
        """Test async_timeout with successful completion."""
        async def quick_coro():
            await asyncio.sleep(0.01)
            return "result"
        
        result = await async_timeout(quick_coro(), timeout=1.0)
        assert result == "result"
    
    @pytest.mark.asyncio
    async def test_timeout_exceeded(self):
        """Test async_timeout when exceeded."""
        async def slow_coro():
            await asyncio.sleep(1.0)
            return "result"
        
        result = await async_timeout(
            slow_coro(),
            timeout=0.1,
            default="timed_out"
        )
        assert result == "timed_out"


@pytest.mark.unit
class TestMeasureAsyncTime:
    """Test cases for measure_async_time function."""
    
    @pytest.mark.asyncio
    async def test_measure_time_success(self):
        """Test measuring execution time."""
        async def timed_operation():
            await asyncio.sleep(0.05)
            return "complete"
        
        result = await measure_async_time(timed_operation(), "test_op")
        assert result == "complete"
    
    @pytest.mark.asyncio
    async def test_measure_time_with_error(self):
        """Test measuring time with error."""
        async def failing_operation():
            await asyncio.sleep(0.01)
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            await measure_async_time(failing_operation(), "failed_op")


@pytest.mark.unit
class TestAsyncCache:
    """Test cases for AsyncCache class."""
    
    def test_cache_initialization(self):
        """Test AsyncCache initialization."""
        cache = AsyncCache(ttl=300)
        assert cache is not None
        assert cache.ttl == 300
    
    def test_cache_set_and_get(self):
        """Test setting and getting cache values."""
        cache = AsyncCache()
        cache.set("key1", "value1")
        result = cache.get("key1")
        assert result == "value1"
    
    def test_cache_missing_key(self):
        """Test getting missing cache key."""
        cache = AsyncCache()
        result = cache.get("missing")
        assert result is None
    
    def test_cache_clear(self):
        """Test clearing cache."""
        cache = AsyncCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None
    
    @pytest.mark.asyncio
    async def test_cache_get_or_set_hit(self):
        """Test cache hit with get_or_set."""
        cache = AsyncCache()
        
        async def compute():
            return "computed"
        
        cache.set("key", "cached")
        result = await cache.get_or_set("key", compute)
        assert result == "cached"
    
    @pytest.mark.asyncio
    async def test_cache_get_or_set_miss(self):
        """Test cache miss with get_or_set."""
        cache = AsyncCache()
        
        async def compute():
            await asyncio.sleep(0.01)
            return "computed"
        
        result = await cache.get_or_set("key", compute)
        assert result == "computed"
        # Check it was cached
        cached = cache.get("key")
        assert cached == "computed"
