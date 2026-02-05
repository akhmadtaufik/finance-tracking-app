"""
Request correlation and logging middleware for FastAPI.

Features:
- Automatic request ID generation/propagation (X-Request-ID header)
- Structured JSON logging for request lifecycle events
- Exception handling with full stack trace logging
- PII-safe logging (skips body for auth endpoints)
"""

import logging
import time
import traceback
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from backend.app.core.logging_config import request_id_ctx

logger = logging.getLogger("fintrack.middleware")

# Endpoints where we should NEVER log request body (auth data)
SENSITIVE_ENDPOINTS = {"/auth/login", "/auth/register", "/login", "/register"}


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request correlation and structured JSON logging.

    Responsibilities:
    1. Extract or generate X-Request-ID for request correlation
    2. Store request ID in ContextVar for global access
    3. Log request_started and request_finished events
    4. Handle unhandled exceptions with full stack trace
    5. Add X-Request-ID to response headers
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Extract or generate request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # Set the request ID in ContextVar for the logger to access
        token = request_id_ctx.set(request_id)

        # Request metadata
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path

        start_time = time.perf_counter()

        try:
            # Log request start
            logger.info(
                "Request started",
                extra={
                    "event": "request_started",
                    "method": method,
                    "path": path,
                    "client_ip": client_ip,
                    "query_params": (
                        str(request.query_params) if request.query_params else None
                    ),
                },
            )

            # Process the request
            response = await call_next(request)

            # Calculate processing time
            process_time_ms = (time.perf_counter() - start_time) * 1000

            # Log request completion
            log_level = logging.WARNING if response.status_code >= 400 else logging.INFO
            logger.log(
                log_level,
                "Request finished",
                extra={
                    "event": "request_finished",
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "process_time_ms": round(process_time_ms, 2),
                },
            )

            # Add request ID to response headers for client correlation
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as exc:
            # Calculate time even for errors
            process_time_ms = (time.perf_counter() - start_time) * 1000

            # Log the error with full stack trace
            logger.error(
                "Request failed with unhandled exception",
                extra={
                    "event": "request_error",
                    "method": method,
                    "path": path,
                    "process_time_ms": round(process_time_ms, 2),
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "traceback": traceback.format_exc(),
                },
                exc_info=True,  # Include exception info in the log record
            )

            # Return a 500 response
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
                headers={"X-Request-ID": request_id},
            )

        finally:
            # Reset the context variable
            request_id_ctx.reset(token)


def mask_sensitive_data(data: dict) -> dict:
    """
    Mask sensitive fields in request/response data.

    Note: This is a backup utility. The PIIFilter in logging_config.py
    handles most redaction automatically at the logging level.
    """
    SENSITIVE_FIELDS = {
        "password",
        "token",
        "access_token",
        "refresh_token",
        "secret",
        "authorization",
        "api_key",
        "credit_card",
    }

    if not isinstance(data, dict):
        return data

    return {
        k: (
            "***REDACTED***"
            if k.lower() in SENSITIVE_FIELDS
            else (mask_sensitive_data(v) if isinstance(v, dict) else v)
        )
        for k, v in data.items()
    }
