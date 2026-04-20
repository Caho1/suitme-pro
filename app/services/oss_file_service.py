"""OSS 文件服务。"""

from __future__ import annotations

from typing import Any

from fastapi import Request

from app.core.deps import CurrentUser
from app.services.base import SkeletonService


class OssFileService(SkeletonService):
    """阿里云 OSS 文件服务。"""

    async def upload(self, request: Request | None = None, current_user: CurrentUser | None = None, **kwargs: Any) -> dict[str, Any]:
        """上传单个文件到 OSS。"""
        return await self.todo('oss.file.upload', request=request, current_user=current_user, **kwargs)

    async def batch_upload(self, request: Request | None = None, current_user: CurrentUser | None = None, **kwargs: Any) -> dict[str, Any]:
        """批量上传文件到 OSS。"""
        return await self.todo('oss.file.batchUpload', request=request, current_user=current_user, **kwargs)

    async def download(
        self,
        fileId: int,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """按 fileId 下载 OSS 文件。"""
        return await self.todo('oss.file.download', request=request, current_user=current_user, fileId=fileId, **kwargs)

    async def check_connection(self, request: Request | None = None, current_user: CurrentUser | None = None, **kwargs: Any) -> dict[str, Any]:
        """检查 OSS 连通性。"""
        return await self.todo('oss.file.checkConnection', request=request, current_user=current_user, **kwargs)
