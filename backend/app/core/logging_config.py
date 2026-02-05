"""
Enterprise-grade JSON logging configuration with PII redaction and request correlation.

Features:
- Structured JSON output (one JSON object per line)
- Automatic PII/sensitive data redaction
- Request correlation via ContextVar (no argument passing needed)
- Non-blocking async-safe logging
"""

import json
import logging
import logging.config
import logging.handlers
import re
import traceback
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ==============================================================================
# LOG FILE CONFIGURATION
# ==============================================================================

LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_FILE = LOG_DIR / "app.log"
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5

# ==============================================================================
# REQUEST CONTEXT
# ==============================================================================

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")
"""
ContextVar to store the current request ID for correlation.
Access from anywhere with: request_id_ctx.get()
Set in middleware with: request_id_ctx.set(request_id)
"""


# ==============================================================================
# PII FILTER
# ==============================================================================


class PIIFilter(logging.Filter):
    """
    Filter that redacts sensitive/PII data from log records.

    Intercepts log records and applies regex-based redaction for:
    - password, token, access_token, refresh_token
    - authorization headers
    - credit card numbers
    """

    # Pattern to match sensitive keys in various formats:
    # JSON: "password": "value" or 'password': 'value'
    # Key-value: password=value
    SENSITIVE_KEYS_PATTERN = re.compile(
        r'(["\']?)(password|token|access_token|refresh_token|authorization|credit_card|secret|api_key)(["\']?\s*[:=]\s*)(["\']?)([^"\',\s}{]+)(["\']?)',
        re.IGNORECASE,
    )

    # Pattern for Authorization header value (Bearer tokens, Basic auth, etc.)
    AUTH_HEADER_PATTERN = re.compile(
        r'(authorization\s*[:=]\s*["\']?)(Bearer\s+\S+|Basic\s+\S+|\S+)(["\']?)',
        re.IGNORECASE,
    )

    # Pattern for credit card numbers (common formats)
    CREDIT_CARD_PATTERN = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")

    REDACTED = "***REDACTED***"

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact sensitive data from the log record message and args."""
        # Redact the message
        if record.msg:
            record.msg = self._redact_string(str(record.msg))

        # Redact args if they exist
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self._redact_value(v) for k, v in record.args.items()}
            elif isinstance(record.args, (list, tuple)):
                record.args = tuple(self._redact_value(arg) for arg in record.args)

        return True  # Always allow the record through after redaction

    def _redact_string(self, text: str) -> str:
        """Apply all redaction patterns to a string."""
        if not isinstance(text, str):
            return text

        # Redact sensitive key-value pairs
        text = self.SENSITIVE_KEYS_PATTERN.sub(rf"\1\2\3\4{self.REDACTED}\6", text)

        # Redact Authorization header values
        text = self.AUTH_HEADER_PATTERN.sub(rf"\1{self.REDACTED}", text)

        # Redact credit card numbers
        text = self.CREDIT_CARD_PATTERN.sub(self.REDACTED, text)

        return text

    def _redact_value(self, value: Any) -> Any:
        """Redact sensitive data from a single value."""
        if isinstance(value, str):
            return self._redact_string(value)
        elif isinstance(value, dict):
            return {k: self._redact_value(v) for k, v in value.items()}
        elif isinstance(value, (list, tuple)):
            return type(value)(self._redact_value(v) for v in value)
        return value


# ==============================================================================
# JSON FORMATTER
# ==============================================================================


class JSONFormatter(logging.Formatter):
    """
    Formats log records as single-line JSON objects.

    Output fields:
    - timestamp: ISO 8601 format with timezone
    - level: Log level name (INFO, WARNING, ERROR, etc.)
    - message: The log message
    - module: Source module name
    - function: Source function name
    - line: Source line number
    - request_id: Correlation ID from ContextVar
    - logger: Logger name
    - exception: Stack trace (only if exception info present)
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string."""
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "request_id": request_id_ctx.get(),
            "logger": record.name,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self._format_exception(record.exc_info)

        # Add extra fields if any (from extra={} in log calls)
        extra_fields = {
            k: v
            for k, v in record.__dict__.items()
            if k
            not in {
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "exc_info",
                "exc_text",
                "thread",
                "threadName",
                "taskName",
                "message",
            }
        }
        if extra_fields:
            log_data["extra"] = extra_fields

        return json.dumps(log_data, default=str, ensure_ascii=False)

    def _format_exception(self, exc_info) -> dict:
        """Format exception info as a structured dict."""
        if not exc_info or exc_info[0] is None:
            return {}

        return {
            "type": exc_info[0].__name__ if exc_info[0] else "Unknown",
            "message": str(exc_info[1]) if exc_info[1] else "",
            "traceback": traceback.format_exception(*exc_info),
        }


# ==============================================================================
# LOGGING SETUP
# ==============================================================================


def setup_logging(level: str = "INFO") -> logging.Logger:
    """
    Configure centralized structured JSON logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        The main application logger instance
    """
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "pii_filter": {
                "()": PIIFilter,
            },
        },
        "formatters": {
            "json": {
                "()": JSONFormatter,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": level.upper(),
                "formatter": "json",
                "filters": ["pii_filter"],
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": level.upper(),
                "formatter": "json",
                "filters": ["pii_filter"],
                "filename": str(LOG_FILE),
                "maxBytes": LOG_MAX_BYTES,
                "backupCount": LOG_BACKUP_COUNT,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            # Main application logger
            "fintrack": {
                "level": level.upper(),
                "handlers": ["console", "file"],
                "propagate": False,
            },
            # Silence noisy third-party loggers
            "uvicorn": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.error": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
            "asyncpg": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
            "httpx": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
        },
        "root": {
            "level": "INFO",
            "handlers": ["console"],
        },
    }

    # Ensure log directory exists
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logging.config.dictConfig(log_config)

    return logging.getLogger("fintrack")


# Initialize the logger on module import
logger = setup_logging()
