"""FastAPI application factory."""

import json
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import __version__
from app.api.routes import router
from app.config import Settings, get_settings
from app.db import Base, make_engine, make_session_factory
from app.errors import AppError, error_body
from app.logging_config import configure_logging
from app.seed import seed_products

logger = logging.getLogger("tandisc")


class UTF8JSONResponse(JSONResponse):
    media_type = "application/json; charset=utf-8"

    def render(self, content) -> bytes:
        return json.dumps(content, ensure_ascii=False, separators=(",", ":"), default=str).encode("utf-8")


def _validation_message(exc: RequestValidationError) -> str:
    fields: list[str] = []
    for err in exc.errors()[:5]:
        loc = [str(item) for item in err.get("loc", []) if item not in {"body", "query", "path"}]
        fields.append(".".join(loc) or "request")
    if not fields:
        return "请求参数不合法"
    return "请求参数不合法: " + ", ".join(fields)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging()
    engine = make_engine(settings.sqlalchemy_url)
    session_factory = make_session_factory(engine)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        Base.metadata.create_all(bind=engine)
        with session_factory() as session:
            inserted = seed_products(session, update_existing=False)
        logger.info(
            "service started env=%s dialect=%s tz=%s seeded=%s",
            settings.app_env,
            engine.dialect.name,
            settings.app_timezone,
            inserted,
        )
        yield
        engine.dispose()

    app = FastAPI(
        title="探盘 API",
        version=__version__,
        lifespan=lifespan,
        default_response_class=UTF8JSONResponse,
    )
    app.state.settings = settings
    app.state.session_factory = session_factory

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def access_log(request: Request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = int((time.perf_counter() - started) * 1000)
        logging.getLogger("tandisc.access").info(
            "request method=%s path=%s status=%s duration_ms=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        content_type = response.headers.get("content-type", "")
        if content_type.startswith("application/json") and "charset" not in content_type.lower():
            response.headers["content-type"] = "application/json; charset=utf-8"
        return response

    @app.exception_handler(AppError)
    async def app_error(_request: Request, exc: AppError):
        return UTF8JSONResponse(status_code=exc.status_code, content=error_body(exc.code, exc.message))

    @app.exception_handler(RequestValidationError)
    async def validation_error(_request: Request, exc: RequestValidationError):
        return UTF8JSONResponse(
            status_code=400,
            content=error_body("VALIDATION_ERROR", _validation_message(exc)),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error(_request: Request, exc: StarletteHTTPException):
        if exc.status_code == 404:
            body = error_body("NOT_FOUND", "资源不存在")
        elif exc.status_code == 405:
            body = error_body("VALIDATION_ERROR", "请求方法不支持")
        elif 400 <= exc.status_code < 500:
            body = error_body("VALIDATION_ERROR", "请求不合法")
        else:
            body = error_body("INTERNAL_ERROR", "服务器内部错误")
        return UTF8JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(Exception)
    async def unhandled(_request: Request, exc: Exception):
        logger.exception("unhandled error")
        return UTF8JSONResponse(status_code=500, content=error_body("INTERNAL_ERROR", "服务器内部错误"))

    app.include_router(router)
    return app


app = create_app()
