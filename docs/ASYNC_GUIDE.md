# Async/Await Support Guide

This guide explains how to use async/await patterns in the Growing Grubs Flask application.

## Overview

Flask 2.0+ supports native `async`/`await` in route handlers. This guide shows how to leverage async functionality for improved performance, especially for I/O-bound operations like database queries, API calls, and file I/O.

## Prerequisites

- Flask 2.0+
- Python 3.7+
- An async-capable ASGI server like Quart or Hypercorn (for production async support)

## Basic Async Routes

### Simple Async Handler

```python
from flask import Flask
from mod.async_support import async_route

app = Flask(__name__)

@app.route('/data')
@async_route
async def get_data():
    # This can now use async operations
    return {'data': 'value'}
```

### Async with Await

```python
import asyncio

@app.route('/slow-data')
@async_route
async def slow_operation():
    # Simulate async I/O
    await asyncio.sleep(1)
    return {'status': 'complete'}
```

## Using Async Support Utilities

### Running Async Functions in Sync Context

```python
from mod.async_support import async_route, async_gather

@app.route('/multiple-operations')
@async_route
async def multiple_operations():
    # Run multiple async operations concurrently
    results = await async_gather(
        fetch_user_data(),
        fetch_recipe_data(),
        fetch_meal_plans()
    )
    return {'results': results}
```

### Running Sync Functions in Executor

```python
from mod.async_support import run_in_executor

@run_in_executor
def expensive_computation(data):
    # This blocking operation runs in a thread pool
    result = sum(range(1000000))
    return result * len(data)

@app.route('/compute')
@async_route
async def compute():
    result = await expensive_computation([1, 2, 3])
    return {'result': result}
```

### Async Retry with Backoff

```python
from mod.async_support import async_retry

async def call_external_api():
    # This might fail transiently
    return await fetch_from_api()

@app.route('/api-call')
@async_route
async def make_api_call():
    result = await async_retry(
        call_external_api,
        max_retries=3,
        delay=0.5,
        backoff=2.0
    )
    return result
```

### Async Timeout

```python
from mod.async_support import async_timeout

@app.route('/timeout-example')
@async_route
async def timeout_example():
    # Use a default value if operation times out
    result = await async_timeout(
        slow_operation(),
        timeout=5.0,
        default={'error': 'Operation timed out'}
    )
    return result
```

### Async Caching

```python
from mod.async_support import AsyncCache

cache = AsyncCache(ttl=300)  # 5 minute TTL

async def fetch_user_recipes(user_id):
    # Simulate API call
    return {'recipes': []}

@app.route('/user-recipes/<int:user_id>')
@async_route
async def get_user_recipes(user_id):
    recipes = await cache.get_or_set(
        f'recipes:{user_id}',
        lambda: fetch_user_recipes(user_id)
    )
    return recipes
```

## Async Database Operations

### With SQLAlchemy

```python
from mod.async_support import run_in_executor
from mod.models import Recipe

@run_in_executor
def get_recipes_sync(age_group):
    return Recipe.query.filter_by(age_group=age_group).all()

@app.route('/recipes/<age_group>')
@async_route
async def get_recipes(age_group):
    recipes = await get_recipes_sync(age_group)
    return {'recipes': [r.to_dict() for r in recipes]}
```

### Using Query Builder with Executor

```python
from mod.async_support import run_in_executor
from mod.query_builder import RecipeQueryHelper

@run_in_executor
def search_recipes_sync(search_term):
    return RecipeQueryHelper.search_recipes(search_term)

@app.route('/search')
@async_route
async def search(search_term):
    results = await search_recipes_sync(search_term)
    return {'results': results}
```

## Async API Calls

### Concurrent API Calls

```python
from mod.async_support import async_gather
import aiohttp

async def fetch_from_api(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

@app.route('/combined-data')
@async_route
async def combined_data():
    results = await async_gather(
        fetch_from_api('https://api.example.com/users'),
        fetch_from_api('https://api.example.com/recipes'),
        return_exceptions=True
    )
    return {'user_data': results[0], 'recipe_data': results[1]}
```

### With Error Handling

```python
from mod.async_support import async_gather

@app.route('/safe-combined-data')
@async_route
async def safe_combined_data():
    results = await async_gather(
        fetch_from_api('https://api.example.com/users'),
        fetch_from_api('https://api.example.com/recipes'),
        return_exceptions=True
    )
    
    user_data = results[0] if not isinstance(results[0], Exception) else None
    recipe_data = results[1] if not isinstance(results[1], Exception) else None
    
    return {
        'user_data': user_data,
        'recipe_data': recipe_data,
        'errors': [str(r) for r in results if isinstance(r, Exception)]
    }
```

## Performance Timing

```python
from mod.async_support import measure_async_time

async def slow_operation():
    await asyncio.sleep(2)
    return {'result': 'complete'}

@app.route('/timed-operation')
@async_route
async def timed_operation():
    result = await measure_async_time(
        slow_operation(),
        operation_name='slow_operation'
    )
    return result
```

## Async Background Tasks

```python
from mod.async_support import AsyncTask

async def background_work():
    await asyncio.sleep(5)
    # Do work here
    return 'completed'

@app.route('/start-task')
def start_task():
    task = AsyncTask(background_work(), timeout=10.0)
    # Task runs in background
    return {'status': 'task started'}
```

## Production Deployment

### With Quart (Full Async ASGI)

```bash
# Install Quart
pip install quart

# Run async application
quart --app server_main:app run
```

### With Hypercorn

```bash
# Install Hypercorn
pip install hypercorn

# Run with Hypercorn
hypercorn server_main:app --bind 0.0.0.0:5000
```

### Gunicorn with Worker Class

For use with Gunicorn, install async worker support:

```bash
# Install gevent for async support
pip install gevent

# Run with gevent worker
gunicorn -w 4 -k gevent --worker-connections 1000 server_main:app
```

## Best Practices

1. **Use async for I/O-bound operations**: Network calls, database queries, file I/O
2. **Use executors for CPU-bound work**: Keep the event loop free for other requests
3. **Handle timeouts gracefully**: Always provide sensible defaults
4. **Use connection pooling**: Reuse connections for database/API operations
5. **Monitor event loop**: Watch for long-running synchronous code
6. **Error handling**: Always handle exceptions in async code properly
7. **Resource cleanup**: Use try/finally or context managers for cleanup

## Common Issues

### Issue: "RuntimeError: no running event loop"

This usually means you're trying to use async code in a sync context. Use `@async_route` or `run_in_executor` to handle it.

### Issue: Blocking operations in event loop

If you see warnings about blocking calls, wrap blocking operations with `run_in_executor`.

### Issue: Database session conflicts

Ensure each async operation has its own database session, or use the executor pattern.

## Testing Async Routes

```python
import pytest

@pytest.mark.asyncio
async def test_async_route(client):
    response = await client.get('/data')
    assert response.status_code == 200
```

## See Also

- [Flask Async Documentation](https://flask.palletsprojects.com/async-await/)
- [asyncio Documentation](https://docs.python.org/3/library/asyncio.html)
- [Quart Documentation](https://quart.palletsprojects.com/)
