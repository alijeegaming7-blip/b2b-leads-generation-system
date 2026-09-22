"""
Rate limiting middleware to prevent abuse and DDoS attacks.
Uses sliding window algorithm with in-memory storage (Redis for production).
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import time
from collections import defaultdict
from threading import Lock
from typing import Dict, Tuple

# In-memory rate limit storage (use Redis in production)
_rate_limit_storage: Dict[str, list] = defaultdict(list)
_storage_lock = Lock()

# Configuration
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 60  # requests per window


def get_client_identifier(request: Request) -> str:
    """
    Get unique client identifier for rate limiting.
    Uses IP address + user agent combination.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0]
    else:
        client_ip = request.client.host if request.client else "unknown"
    
    user_agent = request.headers.get("User-Agent", "")[:50]
    return f"{client_ip}:{user_agent}"


async def rate_limit_middleware(request: Request, call_next):
    """
    Middleware that enforces rate limits on all endpoints except health checks.
    
    Returns 429 Too Many Requests if limit exceeded.
    """
    # Skip rate limiting for health check endpoints
    if request.url.path.startswith("/api/health"):
        return await call_next(request)
    
    client_id = get_client_identifier(request)
    current_time = time.time()
    
    with _storage_lock:
        # Get request timestamps for this client
        timestamps = _rate_limit_storage[client_id]
        
        # Remove timestamps older than the window
        timestamps[:] = [ts for ts in timestamps if current_time - ts < RATE_LIMIT_WINDOW]
        
        # Check if limit exceeded
        if len(timestamps) >= RATE_LIMIT_MAX_REQUESTS:
            oldest = timestamps[0]
            retry_after = int(RATE_LIMIT_WINDOW - (current_time - oldest) + 1)
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": retry_after
                },
                headers={"Retry-After": str(retry_after)}
            )
        
        # Add current request timestamp
        timestamps.append(current_time)
    
    response = await call_next(request)
    
    # Add rate limit headers
    remaining = RATE_LIMIT_MAX_REQUESTS - len(timestamps)
    response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_MAX_REQUESTS)
    response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
    response.headers["X-RateLimit-Reset"] = str(int(current_time + RATE_LIMIT_WINDOW))
    
    return response


# Cleanup old entries periodically (call from lifespan or background task)
def cleanup_rate_limit_storage():
    """Remove expired rate limit entries to prevent memory growth."""
    current_time = time.time()
    with _storage_lock:
        for client_id in list(_rate_limit_storage.keys()):
            timestamps = _rate_limit_storage[client_id]
            timestamps[:] = [ts for ts in timestamps if current_time - ts < RATE_LIMIT_WINDOW * 2]
            if not timestamps:
                del _rate_limit_storage[client_id]
