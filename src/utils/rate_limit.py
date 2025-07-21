"""Rate limiting utilities for IOAgent application."""

from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity
import time
from typing import Dict, Tuple
import threading

# In-memory rate limit storage (consider Redis for production)
rate_limit_storage: Dict[str, list] = {}
storage_lock = threading.Lock()

def get_rate_limit_key() -> str:
    """Generate rate limit key based on IP and user."""
    try:
        identity = get_jwt_identity()
        if identity:
            return f"user:{identity}"
    except:
        pass
    
    # Fall back to IP address
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ',' in ip:
        ip = ip.split(',')[0].strip()
    return f"ip:{ip}"

def rate_limit(max_requests: int = 10, window_seconds: int = 60):
    """
    Rate limiting decorator.
    
    Args:
        max_requests: Maximum number of requests allowed
        window_seconds: Time window in seconds
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            key = get_rate_limit_key()
            current_time = time.time()
            window_start = current_time - window_seconds
            
            with storage_lock:
                # Initialize or get existing timestamps
                if key not in rate_limit_storage:
                    rate_limit_storage[key] = []
                
                # Remove old timestamps outside the window
                rate_limit_storage[key] = [
                    timestamp for timestamp in rate_limit_storage[key]
                    if timestamp > window_start
                ]
                
                # Check if limit exceeded
                if len(rate_limit_storage[key]) >= max_requests:
                    retry_after = int(rate_limit_storage[key][0] + window_seconds - current_time)
                    return jsonify({
                        'success': False,
                        'error': 'Rate limit exceeded',
                        'retry_after': retry_after
                    }), 429
                
                # Add current request timestamp
                rate_limit_storage[key].append(current_time)
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def cleanup_old_entries():
    """Clean up old rate limit entries to prevent memory bloat."""
    current_time = time.time()
    with storage_lock:
        keys_to_remove = []
        for key, timestamps in rate_limit_storage.items():
            # Remove entries older than 5 minutes
            if timestamps and timestamps[-1] < current_time - 300:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del rate_limit_storage[key]

# Rate limit configurations for different endpoints
AUTH_RATE_LIMIT = (5, 60)  # 5 requests per minute
API_RATE_LIMIT = (100, 60)  # 100 requests per minute
UPLOAD_RATE_LIMIT = (10, 300)  # 10 uploads per 5 minutes