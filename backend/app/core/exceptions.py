import logging
import traceback
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import asyncpg

logger = logging.getLogger("fintrack.exceptions")


class AppException(Exception):
    """Base application exception with code and status."""
    def __init__(self, message: str, code: str, status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


# --- Exception Handlers ---

async def app_exception_handler(request: Request, exc: AppException):
    """Handle custom application exceptions."""
    logger.warning(f"AppException: {exc.code} - {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "code": exc.code}
    )


async def asyncpg_unique_violation_handler(request: Request, exc: asyncpg.UniqueViolationError):
    """Handle duplicate key violations → 409 Conflict"""
    logger.warning(f"UniqueViolation: {exc.detail}")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Resource already exists", "code": "DUPLICATE_RESOURCE"}
    )


async def asyncpg_fk_violation_handler(request: Request, exc: asyncpg.ForeignKeyViolationError):
    """Handle foreign key violations → 400 Bad Request"""
    logger.warning(f"ForeignKeyViolation: {exc.detail}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Invalid reference to related resource", "code": "INVALID_REFERENCE"}
    )


async def asyncpg_not_null_violation_handler(request: Request, exc: asyncpg.NotNullViolationError):
    """Handle not null violations → 400 Bad Request"""
    logger.warning(f"NotNullViolation: {exc.detail}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Required field is missing", "code": "MISSING_REQUIRED_FIELD"}
    )


async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors → 422"""
    errors = exc.errors()
    logger.warning(f"ValidationError on {request.url.path}: {errors}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation failed",
            "code": "VALIDATION_ERROR",
            "errors": [
                {
                    "field": ".".join(str(loc) for loc in err["loc"]),
                    "message": err["msg"],
                    "type": err["type"]
                }
                for err in errors
            ]
        }
    )


async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all handler → 500 Internal Server Error"""
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}: {exc}\n"
        f"{traceback.format_exc()}"
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "code": "INTERNAL_ERROR"}
    )
