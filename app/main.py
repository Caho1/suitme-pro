"""FastAPI 应用入口。"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logger import configure_logger
from app.core.response import success


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用实例。"""
    configure_logger()
    settings = get_settings()
    settings.upload_profile_path.mkdir(parents=True, exist_ok=True)

    app = FastAPI(
        title='SuitMe Python',
        docs_url='/swagger-ui.html',
        openapi_url='/v3/api-docs',
        redoc_url='/redoc',
    )

    # 配置 CORS 跨域
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.mount(
        settings.upload_base_uri,
        StaticFiles(directory=str(settings.upload_profile_path)),
        name='profile',
    )
    app.include_router(api_router)
    register_exception_handlers(app)

    @app.get('/', summary='健康检查')
    async def root() -> dict[str, object]:
        """返回一个简单的健康检查结果。"""
        return success(data={'service': 'suitme-python', 'status': 'ok'})

    return app


app = create_app()
