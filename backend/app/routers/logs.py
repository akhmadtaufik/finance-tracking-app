"""
Frontend logs endpoint - receives logs from frontend applications.

This endpoint allows frontend applications to send structured logs
to the backend for centralized logging and monitoring.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

logger = logging.getLogger("fintrack.frontend")

router = APIRouter(prefix="/logs", tags=["Logs"])


class FrontendLogEntry(BaseModel):
    """Schema for frontend log entries."""

    level: str = Field(
        ..., pattern="^(debug|info|warn|error)$", description="Log level"
    )
    message: str = Field(..., max_length=2000)
    context: Optional[dict] = Field(default=None, description="Additional context data")
    component: Optional[str] = Field(
        default=None, max_length=100, description="Vue component name"
    )
    url: Optional[str] = Field(
        default=None, max_length=500, description="Current page URL"
    )
    user_agent: Optional[str] = Field(default=None, max_length=500, alias="userAgent")
    timestamp: Optional[str] = Field(default=None, description="Client-side timestamp")
    request_id: Optional[str] = Field(
        default=None, alias="requestId", description="Correlation ID from API responses"
    )


class BatchLogRequest(BaseModel):
    """Schema for batch log requests."""

    logs: list[FrontendLogEntry] = Field(
        ..., max_length=50, description="Batch of log entries (max 50)"
    )


@router.post("")
async def receive_frontend_log(log_entry: FrontendLogEntry, request: Request):
    """
    Receive a single log entry from frontend.

    This endpoint is rate-limited to prevent abuse.
    """
    _process_log(log_entry, request)
    return {"status": "ok"}


@router.post("/batch")
async def receive_frontend_logs_batch(batch: BatchLogRequest, request: Request):
    """
    Receive multiple log entries from frontend in a single request.

    Useful for batched logging to reduce HTTP overhead.
    Max 50 entries per batch.
    """
    for log_entry in batch.logs:
        _process_log(log_entry, request)

    return {"status": "ok", "count": len(batch.logs)}


def _process_log(log_entry: FrontendLogEntry, request: Request):
    """Process and log a frontend log entry."""
    # Map frontend log levels to Python logging levels
    level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warn": logging.WARNING,
        "error": logging.ERROR,
    }

    log_level = level_map.get(log_entry.level, logging.INFO)

    # Build extra data for structured logging
    extra = {
        "source": "frontend",
        "component": log_entry.component,
        "url": log_entry.url,
        "client_timestamp": log_entry.timestamp,
        "correlation_id": log_entry.request_id,
    }

    # Add context if present
    if log_entry.context:
        extra["context"] = log_entry.context

    # Add client IP
    if request.client:
        extra["client_ip"] = request.client.host

    # Log with appropriate level
    logger.log(log_level, f"[FRONTEND] {log_entry.message}", extra=extra)
