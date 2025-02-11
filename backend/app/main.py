#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from starlette.requests import Request

from backend import __version__
from backend.app.core.auth import backendAuthRouter
from backend.app.core.cache import RedisCache
from backend.app.core.config import settings
from backend.app.core.errors import ApplicationError
from backend.app.core.pagination import register_app_filters
from backend.app.core.session import SessionMiddleware
from backend.app.routes import router
from backend.app.utils.initialization import initialization


def get_app(version: str = __version__) -> FastAPI:
    app_kwargs: Dict[str, Any] = {
        "title": settings.PROJECT_NAME,
        "debug": settings.DEBUG,
        "version": version,
    }

    if not settings.DEBUG:  # pragma: no cover
        app_kwargs.update({"redoc_url": None, "docs_url": None, "openapi_url": None})

    if settings.DB_ECHO_LEVEL == "debug":  # pragma: no cover
        logging.getLogger("sqlalchemy").setLevel(level=logging.DEBUG)
    else:
        logging.getLogger("sqlalchemy").setLevel(level=logging.ERROR)

    app = FastAPI(**app_kwargs)
    app.include_router(backendAuthRouter, tags=["auth"])
    app.include_router(router, prefix="/api")

    @app.exception_handler(404)
    async def backend_api_not_found_handler(request: Request, exc: ApplicationError) -> JSONResponse:
        json_resp = {"code": 404, "message": "Not Found"}
        return JSONResponse(
            status_code=200,
            content=json_resp,
        )

    @app.exception_handler(ApplicationError)
    async def backend_default_error_handler(request: Request, exc: ApplicationError) -> JSONResponse:
        json_resp = {"code": exc.code, "message": exc.message}
        return JSONResponse(
            status_code=200,
            content=json_resp,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: ApplicationError) -> JSONResponse:
        json_resp = {"code": 422, "message": f"上传参数有误:{str(exc)}"}
        return JSONResponse(
            status_code=200,
            content=json_resp,
        )

    @app.exception_handler(Exception)
    async def unknown_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        json_resp = {"code": 500, "message": f"服务器异常:{str(exc)}"}
        return JSONResponse(
            status_code=200,
            content=json_resp,
        )

    allowed_hosts = settings.ALLOWED_HOSTS
    if not allowed_hosts and settings.DEBUG:  # pragma: no cover
        allowed_hosts = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_hosts,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["content-disposition"],
    )

    app.add_middleware(GZipMiddleware, minimum_size=512)
    app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY, same_site=settings.SAME_SITE)

    register_app_filters(app)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncGenerator[None]:

        if not settings.TESTING:  # pragma: no cover
            await initialization()

        yield

        await RedisCache.close()

    return app
