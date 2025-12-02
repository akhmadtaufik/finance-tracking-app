from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncpg

from backend.app.core.database import create_pool, close_pool
from backend.app.core.config import settings
from backend.app.core.security import limiter
from backend.app.core.logging_config import logger
from backend.app.core.middleware import RequestLoggingMiddleware
from backend.app.core.exceptions import (
    AppException,
    app_exception_handler,
    asyncpg_unique_violation_handler,
    asyncpg_fk_violation_handler,
    asyncpg_not_null_violation_handler,
    validation_error_handler,
    global_exception_handler
)
from backend.app.routers import auth_router, wallets_router, categories_router, transactions_router, analytics_router, reports_router, admin_router
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Finance Tracking API...")
    await create_pool()
    logger.info("Database connection pool created")
    yield
    await close_pool()
    logger.info("Database connection pool closed")


app = FastAPI(
    title="Finance Tracking API",
    description="""
## Personal Finance Management API

A high-performance financial tracking application with:
- **Multi-wallet support** (Cash, Bank, E-Wallet)
- **Income & Expense tracking** with categories
- **Wallet-to-wallet transfers**
- **Analytics & Reporting**

### Authentication
All endpoints (except `/auth/*`) require a valid JWT token in the `Authorization` header.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.state.limiter = limiter
if settings.RATE_LIMIT_ENABLED:
    # Middleware (order matters: first added = outermost)
    app.add_middleware(SlowAPIMiddleware)
else:
    limiter.enabled = False
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,  # Required for cookies
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Request-ID"],
)

# Exception Handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(asyncpg.UniqueViolationError, asyncpg_unique_violation_handler)
app.add_exception_handler(asyncpg.ForeignKeyViolationError, asyncpg_fk_violation_handler)
app.add_exception_handler(asyncpg.NotNullViolationError, asyncpg_not_null_violation_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, global_exception_handler)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Rate limit exceeded"}
    )

app.include_router(auth_router)
app.include_router(wallets_router)
app.include_router(categories_router)
app.include_router(transactions_router)
app.include_router(analytics_router)
app.include_router(reports_router)
app.include_router(admin_router)


@app.get("/")
async def root():
    return {"message": "Finance Tracking API", "docs": "/docs"}
