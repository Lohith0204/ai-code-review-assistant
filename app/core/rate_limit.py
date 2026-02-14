import time
import os
from fastapi import HTTPException, Request, status
from collections import defaultdict, deque

class RateLimiter:
    """Sliding window rate limiter pinned to User ID with IP fallback."""
    
    def __init__(self, requests_per_minute: int = None):
        # Use env var if provided, else use the passed value or default to 5
        env_limit = os.getenv("RATE_LIMIT_RPM")
        self.requests_per_minute = int(env_limit) if env_limit else (requests_per_minute or 5)
        self.usage_history = defaultdict(deque)

    async def __call__(self, request: Request):
        # Prefer user_id (authenticated), fallback to IP (unauthenticated/webhooks)
        user_id = getattr(request.state, "user_id", request.client.host)
        
        now = time.time()
        window_start = now - 60
        history = self.usage_history[user_id]
        
        while history and history[0] < window_start:
            history.popleft()
            
        if len(history) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded ({self.requests_per_minute} req/min). Please try again later."
            )
            
        history.append(now)
        return True
