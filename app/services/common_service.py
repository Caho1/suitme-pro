"""通用文件服务。"""

from __future__ import annotations

from typing import Any

from fastapi import Request

from app.core.deps import CurrentUser
from app.services.base import SkeletonService


class CommonService(SkeletonService):
    """本地上传与下载服务。"""

    async def download(self, request: Request | None = None, current_user: CurrentUser | None = None, **kwargs: Any) -> dict[str, Any]:
        """通用下载接口。"""
        return await self.todo('common.download', request=request, current_user=current_user, **kwargs)

    async def upload(self, request: Request | None = None, current_user: CurrentUser | None = None, **kwargs: Any) -> dict[str, Any]:
        """本地上传接口。"""
        return await self.todo('common.upload', request=request, current_user=current_user, **kwargs)

    async def uploads(self, request: Request | None = None, current_user: CurrentUser | None = None, **kwargs: Any) -> dict[str, Any]:
        """本地静态资源读取接口。"""
        return await self.todo('common.uploads', request=request, current_user=current_user, **kwargs)

    async def download_resource(self, request: Request | None = None, current_user: CurrentUser | None = None, **kwargs: Any) -> dict[str, Any]:
        """下载本地资源接口。"""
        return await self.todo('common.download.resource', request=request, current_user=current_user, **kwargs)
