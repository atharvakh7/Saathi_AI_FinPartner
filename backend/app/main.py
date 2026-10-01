"""Saathi API entry point.

Run locally (from backend/):  .venv/Scripts/uvicorn app.main:app --reload
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ai.warmup import warm_up
from app.core.config import settings
from app.core.db import engine
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging
from app.core.middleware import BodySizeLimitMiddleware, RateLimitMiddleware, RequestContextMiddleware
from app.core.redis import redis_client
from app.modules.admin.router import router as admin_router
from app.modules.auth.router import router as auth_router
from app.modules.chat.orchestrator import drain_background
from app.modules.chat.router import router as chat_router
from app.modules.finance.router import router as finance_router
from app.modules.fraud.router import router as fraud_router
from app.modules.goals.router import router as goals_router
from app.modules.insights.router import router as insights_router
from app.modules.learn.router import router as learn_router
from app.modules.learn.translate import translate_missing
from app.modules.memory.router import router as memory_router
from app.modules.notifications.router import router as notifications_router
from app.modules.planner.router import risk_router
from app.modules.planner.router import router as planner_router
from app.modules.schemes.router import router as schemes_router
from app.modules.schemes.translate import translate_missing as translate_missing_schemes
from app.modules.system.router import router as system_router
from app.modules.users.router import legal_router
from app.modules.users.router import router as users_router
from app.modules.voice.router import router as voice_router

configure_logging()
log = logging.getLogger("saathi")


async def _startup_jobs() -> None:
    if settings.AI_WARMUP:
        await warm_up()  # preload models first
    if settings.TRANSLATE_ON_STARTUP:
        await translate_missing()  # glossary.translate_missing (spec §5.8); no-op when complete
        await translate_missing_schemes()  # schemes.translate_missing (spec §5.10)


@asynccontextmanager
async def lifespan(_: FastAPI):
    log.info("startup", extra={"env": settings.APP_ENV})
    # Background start-up work, so the API accepts requests immediately.
    background = asyncio.create_task(_startup_jobs())
    yield
    if not background.done():
        background.cancel()
    await drain_background(timeout=10)  # finish in-process jobs; delayed ones are dropped
    await redis_client.aclose()
    await engine.dispose()
    log.info("shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Saathi API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None,
        openapi_url=None if settings.is_production else "/openapi.json",
    )

    register_error_handlers(app)

    # Starlette runs the last-added middleware first: RequestContext -> CORS -> BodySize -> RateLimit.
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(BodySizeLimitMiddleware)
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    app.add_middleware(RequestContextMiddleware)

    for router in (
        system_router, auth_router, users_router, legal_router, finance_router, goals_router, planner_router,
        risk_router, learn_router, memory_router, schemes_router, fraud_router, voice_router,
        chat_router, insights_router, notifications_router, admin_router,
    ):
        app.include_router(router, prefix=settings.API_PREFIX)
    return app


app = create_app()
