"""
MathBot — Production FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.middleware.logging import LoggingMiddleware
from api.middleware.rate_limit import RateLimitMiddleware
from api.v1.router import v1_router
from core.config import settings
from core.logging import configure_logging
from database.connection import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup and shutdown logic."""
    configure_logging()
    await create_tables()
    yield
    # Shutdown: close DB pools, Redis connections, etc.


app = FastAPI(
    title="MathBot API",
    description="AI-powered math problem solver with OCR, symbolic computation, and step-by-step verification.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# --- Middleware (order matters — outermost runs first) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

# --- Routers ---
app.include_router(v1_router, prefix="/api/v1")
