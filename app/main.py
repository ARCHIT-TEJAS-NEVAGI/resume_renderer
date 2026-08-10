"""FastAPI application entrypoint for resume-renderer."""
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.config import STATIC_DIR, get_settings, settings
from app.routes import generate_html, generate_pdf
from app.services.pdf_renderer import pdf_renderer
from app.services.template_manager import template_manager


def _configure_logging() -> None:
    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.log_level,
        enqueue=True,
        backtrace=False,
        diagnose=False,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.ensure_directories()
    template_manager.load()
    logger.info("{} v{} started", settings.app_name, settings.app_version)
    try:
        yield
    finally:
        await pdf_renderer.close()
        logger.info("{} shut down", settings.app_name)


def create_app() -> FastAPI:
    _configure_logging()
    settings.ensure_directories()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=settings.api_description,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    allow_credentials = settings.cors_origins not in ("", "*")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(generate_html.router)
    app.include_router(generate_pdf.router)

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    def root() -> dict:
        return {
            "service": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/health",
        }

    @app.get("/health", tags=["system"], summary="Liveness probe")
    def health() -> dict:
        return {
            "status": "ok",
            "service": settings.app_name,
            "version": settings.app_version,
        }

    return app


app = create_app()
