from typing import cast
import uvicorn
import logging
import sys
import sentry_sdk
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from alembic.config import Config
import alembic.config
from llama_index.core.node_parser.text.utils import split_by_sentence_tokenizer

from app.api.api import api_router
from app.db.wait_for_db import check_database_connection
from app.core.config import settings, AppEnvironment
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


def __setup_logging(log_level: str):
    log_level = getattr(logging, log_level.upper())
    log_formatter = logging.Formatter(
        "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(log_formatter)
    root_logger.addHandler(stream_handler)
    logger.info("Set up logging with log level %s", log_level)


def __setup_sentry():
    if settings.SENTRY_DSN:
        logger.info("Setting up Sentry")
        if settings.ENVIRONMENT == AppEnvironment.PRODUCTION:
            profiles_sample_rate = None
        else:
            profiles_sample_rate = settings.SENTRY_SAMPLE_RATE
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT.value,
            release=settings.RENDER_GIT_COMMIT,
            debug=settings.VERBOSE,
            traces_sample_rate=settings.SENTRY_SAMPLE_RATE,
            profiles_sample_rate=profiles_sample_rate,
        )
    else:
        logger.info("Skipping Sentry setup")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. 等待 DB 連線
    logger.info("Starting FastAPI application lifespan")
    await check_database_connection()
    logger.info("Database connection verified")

    # 2. 簡化：migration 檢查由 alembic 啟動時負責，這裡只確保 DB 連線
    # （migration 升級應在容器啟動時作為初始化腳本執行）
    logger.info("Lifespan startup complete")

    yield

    logger.info("FastAPI application shutting down")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    lifespan=lifespan,
)


if settings.BACKEND_CORS_ORIGINS:
    origins = [str(origin) for origin in settings.BACKEND_CORS_ORIGINS]

    # allow all origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],      # 允許的來源列表
        allow_credentials=True,     # 允許攜帶 Cookie/Token
        allow_methods=["*"],        # 允許所有方法 (GET, POST, PUT...)
        allow_headers=["*"],        # 允許所有 Header
    )

app.include_router(api_router, prefix=settings.API_PREFIX)


def start():
    print("Running in AppEnvironment: " + settings.ENVIRONMENT.value)
    __setup_logging(settings.LOG_LEVEL)
    __setup_sentry()
    """Launched with `poetry run start` at root level"""
    if settings.RENDER:
        # on render.com deployments, run migrations
        logger.debug("Running migrations")
        alembic_args = ["--raiseerr", "upgrade", "head"]
        alembic.config.main(argv=alembic_args)
        logger.debug("Migrations complete")
    else:
        logger.debug("Skipping migrations")
    live_reload = not settings.RENDER
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=live_reload,
        workers=settings.UVICORN_WORKER_COUNT,
    )
