import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("usage_logger")

class UsageLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs usage metrics for each request.
    In production/Kubernetes, these logs can be collected by tools like EFK/ELK.
    """
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Get user ID if authenticated
        user_id = getattr(request.state, "user_id", "anonymous")
        request_id = getattr(request.state, "request_id", "N/A")
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Console logging
        logger.info(
            f"Usage: request_id={request_id}, user_id={user_id}, "
            f"endpoint={request.url.path}, "
            f"method={request.method}, "
            f"status={response.status_code}, "
            f"duration={duration:.3f}s"
        )
        
        # Log credit deduction (SaaS auditability)
        if response.status_code == 200 and "/review" in request.url.path:
            # We log a deduction of 1 "credit" for successful reviews
            logger.info(f"AUDIT[CreditDeduction]: request_id={request_id}, user_id={user_id}, amount=1")
        
        return response
