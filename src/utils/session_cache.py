"""Session-based caching for user data."""

import logging
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
from flask import session, g

logger = logging.getLogger(__name__)


class SessionCache:
    """In-memory session cache for request-level caching."""
    
    @staticmethod
    def get(key: str) -> Optional[Any]:
        """Get value from session cache."""
        if 'cache' not in session:
            session['cache'] = {}
        
        cache_entry = session['cache'].get(key)
        if cache_entry:
            # Check expiration
            if 'expires' in cache_entry:
                if datetime.utcnow() < datetime.fromisoformat(cache_entry['expires']):
                    return cache_entry['value']
                else:
                    # Expired, remove it
                    del session['cache'][key]
        
        return None
    
    @staticmethod
    def set(key: str, value: Any, expire: Optional[int] = None) -> None:
        """Set value in session cache with optional expiration."""
        if 'cache' not in session:
            session['cache'] = {}
        
        cache_entry = {'value': value}
        
        if expire:
            expires = datetime.utcnow() + timedelta(seconds=expire)
            cache_entry['expires'] = expires.isoformat()
        
        session['cache'][key] = cache_entry
        session.modified = True
    
    @staticmethod
    def delete(key: str) -> bool:
        """Delete key from session cache."""
        if 'cache' in session and key in session['cache']:
            del session['cache'][key]
            session.modified = True
            return True
        return False
    
    @staticmethod
    def clear() -> None:
        """Clear all session cache."""
        if 'cache' in session:
            session['cache'] = {}
            session.modified = True


class RequestCache:
    """Request-level cache using Flask g object."""
    
    @staticmethod
    def get(key: str) -> Optional[Any]:
        """Get value from request cache."""
        if not hasattr(g, 'cache'):
            g.cache = {}
        return g.cache.get(key)
    
    @staticmethod
    def set(key: str, value: Any) -> None:
        """Set value in request cache."""
        if not hasattr(g, 'cache'):
            g.cache = {}
        g.cache[key] = value
    
    @staticmethod
    def delete(key: str) -> bool:
        """Delete key from request cache."""
        if hasattr(g, 'cache') and key in g.cache:
            del g.cache[key]
            return True
        return False
    
    @staticmethod
    def clear() -> None:
        """Clear all request cache."""
        g.cache = {}


def cache_user_data(user_id: int, data: Dict[str, Any], expire: int = 1800) -> None:
    """
    Cache user-specific data in session.
    
    Args:
        user_id: User ID
        data: Data to cache
        expire: Expiration time in seconds (default 30 minutes)
    """
    key = f"user_data:{user_id}"
    SessionCache.set(key, data, expire)


def get_cached_user_data(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Get cached user data from session.
    
    Args:
        user_id: User ID
    
    Returns:
        Cached user data or None
    """
    key = f"user_data:{user_id}"
    return SessionCache.get(key)


def cache_project_data(project_id: int, data: Dict[str, Any], expire: int = 900) -> None:
    """
    Cache project data in session.
    
    Args:
        project_id: Project ID
        data: Data to cache
        expire: Expiration time in seconds (default 15 minutes)
    """
    key = f"project_data:{project_id}"
    SessionCache.set(key, data, expire)


def get_cached_project_data(project_id: int) -> Optional[Dict[str, Any]]:
    """
    Get cached project data from session.
    
    Args:
        project_id: Project ID
    
    Returns:
        Cached project data or None
    """
    key = f"project_data:{project_id}"
    return SessionCache.get(key)


def invalidate_user_session_cache(user_id: int) -> None:
    """Invalidate all session cache for a user."""
    keys_to_delete = []
    
    if 'cache' in session:
        for key in session['cache'].keys():
            if key.startswith(f"user_data:{user_id}") or f":user_id:{user_id}" in key:
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            SessionCache.delete(key)


def invalidate_project_session_cache(project_id: int) -> None:
    """Invalidate all session cache for a project."""
    keys_to_delete = []
    
    if 'cache' in session:
        for key in session['cache'].keys():
            if key.startswith(f"project_data:{project_id}") or f":project_id:{project_id}" in key:
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            SessionCache.delete(key)