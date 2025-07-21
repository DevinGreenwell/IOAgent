"""Cache middleware for Flask routes."""

import logging
from functools import wraps
from typing import Optional, Union, Callable
from datetime import timedelta

from flask import request, jsonify, make_response, g
from flask_jwt_extended import get_jwt_identity

from src.utils.cache import cache_manager, cache_key
from src.services.cached_services import CachedProjectService

logger = logging.getLogger(__name__)


def cache_response(expire: Union[int, timedelta] = 300, 
                  vary_on: Optional[list] = None,
                  unless: Optional[Callable] = None):
    """
    Decorator to cache HTTP responses.
    
    Args:
        expire: Cache expiration time in seconds or timedelta
        vary_on: List of request attributes to vary cache on (e.g., ['args', 'jwt'])
        unless: Callable that returns True to skip caching
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if caching should be skipped
            if unless and unless():
                return func(*args, **kwargs)
            
            # Don't cache non-GET requests
            if request.method != 'GET':
                return func(*args, **kwargs)
            
            # Generate cache key
            cache_key_parts = [
                'response',
                request.endpoint,
                request.path
            ]
            
            if vary_on:
                if 'args' in vary_on and request.args:
                    # Add query parameters to cache key
                    sorted_args = sorted(request.args.items())
                    cache_key_parts.append(str(sorted_args))
                
                if 'jwt' in vary_on:
                    try:
                        user_id = get_jwt_identity()
                        if user_id:
                            cache_key_parts.append(f"user:{user_id}")
                    except:
                        pass
                
                if 'headers' in vary_on:
                    # Add specific headers to cache key
                    for header in ['Accept', 'Accept-Language']:
                        if header in request.headers:
                            cache_key_parts.append(f"{header}:{request.headers[header]}")
            
            cache_key_str = cache_key(*cache_key_parts)
            
            # Try to get from cache
            cached = cache_manager.get(cache_key_str)
            if cached:
                logger.debug(f"Cache hit for {cache_key_str}")
                response = make_response(cached['body'])
                
                # Restore headers
                for header, value in cached.get('headers', {}).items():
                    response.headers[header] = value
                
                # Add cache headers
                response.headers['X-Cache'] = 'HIT'
                return response
            
            # Call function
            logger.debug(f"Cache miss for {cache_key_str}")
            result = func(*args, **kwargs)
            
            # Handle different response types
            if isinstance(result, dict):
                response = jsonify(result)
            elif isinstance(result, tuple) and len(result) == 2:
                # (data, status_code)
                response = make_response(jsonify(result[0]), result[1])
            else:
                response = make_response(result)
            
            # Only cache successful responses
            if response.status_code == 200:
                # Convert timedelta to seconds
                if isinstance(expire, timedelta):
                    expire_seconds = int(expire.total_seconds())
                else:
                    expire_seconds = expire
                
                # Cache the response
                cache_data = {
                    'body': response.get_json(),
                    'headers': dict(response.headers)
                }
                cache_manager.set(cache_key_str, cache_data, expire_seconds)
            
            # Add cache headers
            response.headers['X-Cache'] = 'MISS'
            return response
        
        return wrapper
    return decorator


def invalidate_on_change(*models):
    """
    Decorator to invalidate cache when models change.
    
    Args:
        models: Model names that trigger cache invalidation
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Store current state for comparison
            g.cache_invalidation_models = models
            
            # Call function
            result = func(*args, **kwargs)
            
            # Check if we need to invalidate cache
            if hasattr(g, 'invalidate_cache'):
                for model, entity_id in g.invalidate_cache:
                    if model == 'project':
                        CachedProjectService.invalidate_project(entity_id)
                    elif model == 'user':
                        from src.utils.cache import invalidate_user_cache
                        invalidate_user_cache(entity_id)
            
            return result
        
        return wrapper
    return decorator


def cached_view(expire: Union[int, timedelta] = 300,
                key_prefix: Optional[str] = None,
                unless: Optional[Callable] = None):
    """
    Decorator for caching entire view functions.
    
    Args:
        expire: Cache expiration time
        key_prefix: Optional prefix for cache key
        unless: Callable that returns True to skip caching
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if caching should be skipped
            if unless and unless():
                return func(*args, **kwargs)
            
            # Generate cache key
            if key_prefix:
                cache_key_str = f"{key_prefix}:{request.path}"
            else:
                cache_key_str = f"view:{request.endpoint}:{request.path}"
            
            # Add query string to key if present
            if request.query_string:
                cache_key_str += f":{request.query_string.decode()}"
            
            # Add user ID if authenticated
            try:
                user_id = get_jwt_identity()
                if user_id:
                    cache_key_str += f":user:{user_id}"
            except:
                pass
            
            # Try to get from cache
            cached = cache_manager.get(cache_key_str)
            if cached:
                return cached
            
            # Call function
            result = func(*args, **kwargs)
            
            # Convert timedelta to seconds
            if isinstance(expire, timedelta):
                expire_seconds = int(expire.total_seconds())
            else:
                expire_seconds = expire
            
            # Cache the result
            cache_manager.set(cache_key_str, result, expire_seconds)
            
            return result
        
        return wrapper
    return decorator


# Conditional caching helpers
def skip_cache_if_admin():
    """Skip caching for admin users."""
    try:
        from src.models.user import User
        user_id = get_jwt_identity()
        if user_id:
            user = User.query.get(int(user_id))
            return user and user.role == 'admin'
    except:
        pass
    return False


def skip_cache_if_debug():
    """Skip caching in debug mode."""
    from flask import current_app
    return current_app.debug


def skip_cache_if_no_redis():
    """Skip caching if Redis is not available."""
    return not cache_manager.is_available()