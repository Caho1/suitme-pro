"""统一异常处理模块。"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.response import error


class ApiError(Exception):
    """用于主动中断请求并返回若依风格错误体的异常。"""

    def __init__(self, message: str, code: int = 500) -> None:
        self.message = message
        self.code = code
        super().__init__(message)


def register_exception_handlers(app: FastAPI) -> None:
    """向 FastAPI 注册全局异常处理器。"""

    @app.exception_handler(ApiError)
    async def handle_api_error(_: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(status_code=200, content=error(msg=exc.message, code=exc.code))

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(status_code=200, content=error(msg=str(exc), code=500))

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        if exc.status_code == 401:
            return JSONResponse(status_code=401, content=error(msg="认证失败", code=401))
        return JSONResponse(status_code=200, content=error(msg=exc.detail, code=500))

    @app.exception_handler(Exception)
    async def handle_unknown_error(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=200, content=error(msg=str(exc), code=500))
