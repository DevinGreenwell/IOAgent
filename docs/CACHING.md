# IOAgent Caching Implementation

This document describes the caching strategy implemented in IOAgent to improve performance and reduce load on the database and external APIs.

## Overview

IOAgent uses a multi-layer caching strategy:
1. **Redis Cache** - Distributed cache for application data
2. **Session Cache** - User-specific cache stored in Flask sessions
3. **Request Cache** - Request-level cache using Flask's `g` object

## Redis Cache

### Configuration

Redis is configured in `src/config/config.py`:
```python
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
```

### Cache Manager

The `CacheManager` class in `src/utils/cache.py` provides a unified interface for Redis operations:

```python
from src.utils.cache import cache_manager

# Set a value
cache_manager.set('key', 'value', expire=3600)  # 1 hour expiration

# Get a value
value = cache_manager.get('key')

# Delete a key
cache_manager.delete('key')

# Clear by pattern
cache_manager.clear_pattern('project:*')
```

### Cache Decorators

Use the `@cached` decorator for automatic caching:

```python
from src.utils.cache import cached
from datetime import timedelta

@cached(expire=timedelta(hours=1), prefix="myservice")
def expensive_operation(param1, param2):
    # This result will be cached
    return perform_calculation(param1, param2)
```

## Cached Services

The `src/services/cached_services.py` module provides pre-configured cached services:

### CachedProjectService

```python
from src.services.cached_services import CachedProjectService

# Get cached project summary (15 min cache)
summary = CachedProjectService.get_project_summary(project_id)

# Get cached timeline (30 min cache)
timeline = CachedProjectService.get_project_timeline(project_id)

# Invalidate all project caches
CachedProjectService.invalidate_project(project_id)
```

### CachedUserService

```python
from src.services.cached_services import CachedUserService

# Get cached user projects (1 hour cache)
projects = CachedUserService.get_user_projects(user_id)

# Get cached user statistics (2 hour cache)
stats = CachedUserService.get_user_statistics(user_id)
```

### CachedAIService

```python
from src.services.cached_services import CachedAIService

ai_service = CachedAIService()

# Get cached timeline suggestions (24 hour cache)
suggestions = ai_service.get_timeline_suggestions(project_id, context)

# Get cached causal analysis (24 hour cache)
analysis = ai_service.get_causal_analysis_suggestions(project_id)
```

## API Endpoints

### Cached API Endpoints

New cached endpoints are available at `/api/cached/`:

- `GET /api/cached/projects/<id>/summary` - Cached project summary
- `GET /api/cached/projects/<id>/timeline-cached` - Cached timeline
- `GET /api/cached/projects/<id>/causal-analysis-cached` - Cached causal analysis
- `GET /api/cached/users/<id>/projects-cached` - Cached user projects
- `GET /api/cached/users/<id>/statistics` - Cached user statistics

### Cache Management Endpoints (Admin Only)

Available at `/api/admin/`:

- `GET /api/admin/cache/status` - Get cache statistics
- `POST /api/admin/cache/clear` - Clear cache by pattern
- `POST /api/projects/<id>/cache/invalidate` - Invalidate project cache
- `POST /api/cache/warm/<id>` - Warm up project cache

## Cache Middleware

The `cache_response` decorator can cache entire HTTP responses:

```python
from src.middleware.cache_middleware import cache_response
from datetime import timedelta

@app.route('/api/data')
@cache_response(expire=timedelta(minutes=10), vary_on=['args', 'jwt'])
def get_data():
    return expensive_data_operation()
```

## Cache Invalidation

### Automatic Invalidation

Cache is automatically invalidated when:
- Project data is updated
- New evidence is uploaded
- Timeline entries are added/modified
- Causal factors are changed

### Manual Invalidation

```python
from src.utils.cache import invalidate_project_cache, invalidate_user_cache

# Invalidate all caches for a project
invalidate_project_cache(project_id)

# Invalidate all caches for a user
invalidate_user_cache(user_id)
```

## Session Cache

For user-specific data that doesn't need Redis:

```python
from src.utils.session_cache import SessionCache

# Set in session (30 min default)
SessionCache.set('user_preference', 'dark_mode', expire=1800)

# Get from session
preference = SessionCache.get('user_preference')

# Clear session cache
SessionCache.clear()
```

## Performance Benefits

- **Reduced Database Load**: Frequently accessed data is served from cache
- **Faster Response Times**: Cache hits are 10-100x faster than database queries
- **AI Cost Reduction**: AI-generated suggestions are cached for 24 hours
- **Scalability**: Redis cache can be shared across multiple app instances

## Best Practices

1. **Cache Keys**: Use consistent naming patterns
   - Project data: `ioagent:project:{id}:*`
   - User data: `ioagent:user:{id}:*`
   - AI results: `ioagent:ai_{type}:{id}:*`

2. **Expiration Times**:
   - Static data: 1-2 hours
   - Dynamic data: 15-30 minutes
   - AI results: 24 hours
   - User sessions: 30 minutes

3. **Cache Warming**: Pre-populate cache for frequently accessed data
   ```python
   # Warm cache after project creation
   CachedProjectService.get_project_summary(project_id)
   CachedProjectService.get_project_timeline(project_id)
   ```

4. **Monitor Cache Performance**:
   ```bash
   # Check cache statistics
   curl -H "Authorization: Bearer $TOKEN" http://localhost:5001/api/admin/cache/status
   ```

## Docker Setup

Redis is included in the Docker Compose configuration:

```bash
# Start all services including Redis
docker-compose up -d

# Check Redis logs
docker-compose logs redis

# Connect to Redis CLI
docker-compose exec redis redis-cli
```

## Monitoring

Use Flower to monitor Celery tasks that interact with cache:

```bash
# Access Flower at http://localhost:5555
docker-compose up flower
```

## Troubleshooting

### Cache Not Working

1. Check Redis connection:
   ```python
   from src.utils.cache import cache_manager
   print(cache_manager.is_available())  # Should return True
   ```

2. Check Redis logs:
   ```bash
   docker-compose logs redis
   ```

3. Verify environment variables:
   ```bash
   echo $REDIS_URL
   echo $CELERY_BROKER_URL
   ```

### Cache Invalidation Issues

1. Manually clear cache:
   ```bash
   redis-cli FLUSHDB
   ```

2. Check cache patterns:
   ```bash
   redis-cli KEYS "ioagent:*"
   ```

### Performance Issues

1. Monitor cache hit rate:
   - Check `X-Cache` header in responses
   - Use Redis `INFO stats` command

2. Adjust expiration times based on usage patterns

3. Consider implementing cache warming for critical data