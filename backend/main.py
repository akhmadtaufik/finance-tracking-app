from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.app.core.database import create_pool, close_pool
from backend.app.routers import auth_router, wallets_router, categories_router, transactions_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_pool()
    yield
    await close_pool()


app = FastAPI(
    title="Finance Tracking API",
    description="A multi-user finance tracking application",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(wallets_router)
app.include_router(categories_router)
app.include_router(transactions_router)


@app.get("/")
async def root():
    return {"message": "Finance Tracking API", "docs": "/docs"}
