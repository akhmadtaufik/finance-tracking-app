import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("fintrack.middleware")

SENSITIVE_FIELDS = {"password", "token", "access_token", "secret", "authorization"}


def mask_sensitive_data(data: dict) -> dict:
    """Mask sensitive fields in request/response data."""
    if not isinstance(data, dict):
        return data
    return {
        k: "***MASKED***" if k.lower() in SENSITIVE_FIELDS else v
        for k, v in data.items()
    }


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all incoming requests and outgoing responses."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        client_ip = request.client.host if request.client else "unknown"
        
        # Log incoming request
        logger.info(f"→ {request.method} {request.url.path} | IP: {client_ip}")
        
        response = await call_next(request)
        
        # Calculate latency
        latency_ms = (time.perf_counter() - start_time) * 1000
        
        # Log response with status and latency
        log_level = logging.WARNING if response.status_code >= 400 else logging.INFO
        logger.log(
            log_level,
            f"← {request.method} {request.url.path} | "
            f"Status: {response.status_code} | {latency_ms:.2f}ms"
        )
        
        return response
