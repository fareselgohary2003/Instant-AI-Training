from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.agents import router as agents_router
from app.api.analytics import router as analytics_router
from app.api.approvals import router as approvals_router
from app.api.data_analysis import router as data_analysis_router
from app.api.settings import router as settings_router
from app.api.workflows import router as workflows_router
from app.config import APP_NAME, APP_VERSION, CORS_ORIGINS
from app.core.logging import logger
from app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize database tables and run migrations on startup."""
    init_db()
    logger.info(f"{APP_NAME} v{APP_VERSION} initialized successfully.")
    yield


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=(
        "Enterprise-grade multi-agent AI platform for task planning, "
        "orchestrated tool execution, human-in-the-loop approvals, and workflow history."
    ),
    lifespan=lifespan,
)

# Configure CORS for local development and authorized frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["System"])
def root() -> dict[str, Any]:
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "status": "running",
        "description": "AI Task Agent API",
    }


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": APP_NAME,
    }


# Include all modular routers
app.include_router(workflows_router)
app.include_router(approvals_router)
app.include_router(agents_router)
app.include_router(analytics_router)
app.include_router(data_analysis_router)
app.include_router(settings_router)
