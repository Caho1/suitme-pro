"""服装分类服务。"""

from __future__ import annotations

from typing import Any

from fastapi import Request

from app.core.deps import CurrentUser
from app.services.base import SkeletonService


class CategoryService(SkeletonService):
    """服装分类服务。

    当前文件只放方法骨架和中文注释，便于后续逐个替换为真实实现。
    """

    async def add(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """add 接口对应的业务方法。"""
        return await self.todo('category_service.add', request=request, current_user=current_user, **kwargs)

    async def update(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """update 接口对应的业务方法。"""
        return await self.todo('category_service.update', request=request, current_user=current_user, **kwargs)

    async def delete(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """delete 接口对应的业务方法。"""
        return await self.todo('category_service.delete', request=request, current_user=current_user, **kwargs)

    async def list(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """list 接口对应的业务方法。"""
        return await self.todo('category_service.list', request=request, current_user=current_user, **kwargs)
