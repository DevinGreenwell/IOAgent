"""Redis caching utilities for IOAgent."""

import os
import json
import pickle
import logging
from typing import Any, Optional, Union, Callable
from functools import wraps
from datetime import timedelta
import hashlib

import redis
from flask import current_app

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages Redis cache connections and operations."""
    
    def __init__(self, redis_url: Optional[str] = None):
        """Initialize cache manager with Redis connection."""
        self.redis_url = redis_url or os.environ.get('REDIS_URL', 'redis://localhost:6379/1')
        self._redis_client = None
        self._connect()
    
    def _connect(self):
        """Establish Redis connection."""
        try:
            self._redis_client = redis.from_url(
                self.redis_url,
                decode_responses=False,  # We'll handle encoding/decoding
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            # Test connection
            self._redis_client.ping()
            logger.info("Redis cache connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis cache: {str(e)}")
            self._redis_client = None
    
    @property
    def client(self) -> Optional[redis.Redis]:
        """Get Redis client, reconnecting if necessary."""
        if self._redis_client is None:
            self._connect()
        return self._redis_client
    
    def is_available(self) -> bool:
        """Check if Redis cache is available."""
        try:
            if self.client:
                self.client.ping()
                return True
        except:
            pass
        return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.is_available():
            return None
        
        try:
            value = self.client.get(key)
            if value is None:
                return None
            
            # Try to deserialize as JSON first, then pickle
            try:
                return json.loads(value)
            except:
                try:
                    return pickle.loads(value)
                except:
                    # Return as string if can't deserialize
                    return value.decode('utf-8')
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {str(e)}")
            return None
    
    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set value in cache with optional expiration (in seconds)."""
        if not self.is_available():
            return False
        
        try:
            # Serialize value
            if isinstance(value, (dict, list, tuple, bool, int, float)):
                serialized = json.dumps(value)
            elif isinstance(value, str):
                serialized = value
            else:
                # Use pickle for complex objects
                serialized = pickle.dumps(value)
            
            if expire:
                return self.client.setex(key, expire, serialized)
            else:
                return self.client.set(key, serialized)
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.is_available():
            return False
        
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {str(e)}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.is_available():
            return False
        
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {str(e)}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        if not self.is_available():
            return 0
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {str(e)}")
            return 0
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a counter in cache."""
        if not self.is_available():
            return None
        
        try:
            return self.client.incr(key, amount)
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {str(e)}")
            return None
    
    def expire(self, key: str, seconds: int) -> bool:
        """Set expiration time for a key."""
        if not self.is_available():
            return False
        
        try:
            return bool(self.client.expire(key, seconds))
        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {str(e)}")
            return False


# Global cache instance
cache_manager = CacheManager()


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments."""
    key_parts = []
    
    # Add args
    for arg in args:
        if isinstance(arg, (str, int, float, bool)):
            key_parts.append(str(arg))
        else:
            # Hash complex objects
            key_parts.append(hashlib.md5(str(arg).encode()).hexdigest()[:8])
    
    # Add kwargs
    for k, v in sorted(kwargs.items()):
        if isinstance(v, (str, int, float, bool)):
            key_parts.append(f"{k}:{v}")
        else:
            key_parts.append(f"{k}:{hashlib.md5(str(v).encode()).hexdigest()[:8]}")
    
    return ":".join(key_parts)


def cached(expire: Union[int, timedelta] = 3600, prefix: str = "ioagent", 
          key_func: Optional[Callable] = None):
    """
    Decorator to cache function results.
    
    Args:
        expire: Expiration time in seconds or timedelta
        prefix: Cache key prefix
        key_func: Custom function to generate cache key
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Convert timedelta to seconds
            if isinstance(expire, timedelta):
                expire_seconds = int(expire.total_seconds())
            else:
                expire_seconds = expire
            
            # Generate cache key
            if key_func:
                cache_key_str = key_func(*args, **kwargs)
            else:
                # Default key generation
                func_name = f"{func.__module__}.{func.__name__}"
                arg_key = cache_key(*args, **kwargs)
                cache_key_str = f"{prefix}:{func_name}:{arg_key}"
            
            # Try to get from cache
            cached_value = cache_manager.get(cache_key_str)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key_str}")
                return cached_value
            
            # Call function and cache result
            logger.debug(f"Cache miss for {cache_key_str}")
            result = func(*args, **kwargs)
            
            # Cache the result
            cache_manager.set(cache_key_str, result, expire_seconds)
            
            return result
        
        # Add method to clear cache for this function
        def clear_cache(*args, **kwargs):
            if key_func:
                cache_key_str = key_func(*args, **kwargs)
            else:
                func_name = f"{func.__module__}.{func.__name__}"
                arg_key = cache_key(*args, **kwargs)
                cache_key_str = f"{prefix}:{func_name}:{arg_key}"
            
            return cache_manager.delete(cache_key_str)
        
        wrapper.clear_cache = clear_cache
        return wrapper
    
    return decorator


def invalidate_cache(pattern: str) -> int:
    """Invalidate cache entries matching pattern."""
    return cache_manager.clear_pattern(pattern)


# Cache key generators for specific use cases
def project_cache_key(project_id: int) -> str:
    """Generate cache key for project data."""
    return f"ioagent:project:{project_id}"


def user_cache_key(user_id: int) -> str:
    """Generate cache key for user data."""
    return f"ioagent:user:{user_id}"


def evidence_cache_key(evidence_id: int) -> str:
    """Generate cache key for evidence data."""
    return f"ioagent:evidence:{evidence_id}"


def timeline_cache_key(project_id: int) -> str:
    """Generate cache key for project timeline."""
    return f"ioagent:timeline:{project_id}"


def analysis_cache_key(project_id: int, analysis_type: str) -> str:
    """Generate cache key for analysis results."""
    return f"ioagent:analysis:{project_id}:{analysis_type}"


# Cache invalidation helpers
def invalidate_project_cache(project_id: int) -> None:
    """Invalidate all cache entries for a project."""
    patterns = [
        f"ioagent:project:{project_id}*",
        f"ioagent:timeline:{project_id}*",
        f"ioagent:analysis:{project_id}:*",
        f"ioagent:*:project_id:{project_id}:*"
    ]
    
    for pattern in patterns:
        invalidate_cache(pattern)


def invalidate_user_cache(user_id: int) -> None:
    """Invalidate all cache entries for a user."""
    patterns = [
        f"ioagent:user:{user_id}*",
        f"ioagent:*:user_id:{user_id}:*"
    ]
    
    for pattern in patterns:
        invalidate_cache(pattern)