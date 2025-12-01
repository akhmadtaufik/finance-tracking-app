from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import asyncpg

from backend.app.core.database import create_pool, close_pool
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

# Middleware (order matters: first added = outermost)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(asyncpg.UniqueViolationError, asyncpg_unique_violation_handler)
app.add_exception_handler(asyncpg.ForeignKeyViolationError, asyncpg_fk_violation_handler)
app.add_exception_handler(asyncpg.NotNullViolationError, asyncpg_not_null_violation_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, global_exception_handler)

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
