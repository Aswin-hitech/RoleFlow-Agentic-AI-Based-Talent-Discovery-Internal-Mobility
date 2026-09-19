"""Thread-safe sliding-window in-memory rate limiter without Redis dependency."""

import time
import threading
from collections import defaultdict, deque
from functools import wraps
from typing import Callable, Optional
from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity


class InMemoryRateLimiter:
    """Sliding-window in-memory rate limiter with lock protection."""

    def __init__(self):
        self._records = defaultdict(deque)
        self._lock = threading.Lock()

    def is_allowed(self, key: str, max_requests: int, window_seconds: float) -> tuple[bool, int]:
        """Check if request for key is allowed under the sliding window.
        
        Returns:
            (allowed: bool, retry_after_seconds: int)
        """
        now = time.time()
        window_start = now - window_seconds

        with self._lock:
            timestamps = self._records[key]

            # Evict timestamps outside the window
            while timestamps and timestamps[0] < window_start:
                timestamps.popleft()

            if len(timestamps) < max_requests:
                timestamps.append(now)
                return True, 0
            else:
                oldest = timestamps[0]
                retry_after = max(1, int(oldest + window_seconds - now))
                return False, retry_after

    def reset(self):
        """Clear all rate limit tracking (useful for unit tests)."""
        with self._lock:
            self._records.clear()


# Global limiter instance
limiter = InMemoryRateLimiter()


def get_rate_limit_key() -> str:
    """Derive rate limit key based on JWT identity (if logged in) or client IP."""
    try:
        identity = get_jwt_identity()
        if identity:
            return f"user:{identity}"
    except Exception:
        pass

    # Client IP fallback
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return f"ip:{forwarded.split(',')[0].strip()}"
    return f"ip:{request.remote_addr or '127.0.0.1'}"


def rate_limit(max_requests: int = 120, window_seconds: float = 60.0, key_func: Optional[Callable[[], str]] = None):
    """Decorator to enforce sliding-window rate limits on a Flask endpoint.
    
    Args:
        max_requests: Maximum allowed requests within the window.
        window_seconds: Window duration in seconds (default 60s).
        key_func: Optional custom key generator.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            key_fn = key_func or get_rate_limit_key
            key = f"{fn.__name__}:{key_fn()}"

            allowed, retry_after = limiter.is_allowed(key, max_requests, window_seconds)
            if not allowed:
                response = jsonify(
                    error="rate_limited",
                    message=f"Rate limit exceeded: maximum {max_requests} requests per {int(window_seconds)}s. Try again in {retry_after}s.",
                    retry_after=retry_after,
                )
                response.status_code = 429
                response.headers["Retry-After"] = str(retry_after)
                return response

            return fn(*args, **kwargs)

        return wrapper

    return decorator


rate_limiter = limiter
