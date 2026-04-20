"""搭配服务。"""

from __future__ import annotations

from typing import Any

from fastapi import Request

from app.core.deps import CurrentUser
from app.services.base import SkeletonService


class MatchingService(SkeletonService):
    """搭配服务。

    当前文件只放方法骨架和中文注释，便于后续逐个替换为真实实现。
    """

    async def add_or_update(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """add_or_update 接口对应的业务方法。"""
        return await self.todo('matching_service.add_or_update', request=request, current_user=current_user, **kwargs)

    async def list(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """list 接口对应的业务方法。"""
        return await self.todo('matching_service.list', request=request, current_user=current_user, **kwargs)

    async def delete(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """delete 接口对应的业务方法。"""
        return await self.todo('matching_service.delete', request=request, current_user=current_user, **kwargs)

    async def tag_add_or_update(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """tag_add_or_update 接口对应的业务方法。"""
        return await self.todo('matching_service.tag_add_or_update', request=request, current_user=current_user, **kwargs)

    async def tag_list(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """tag_list 接口对应的业务方法。"""
        return await self.todo('matching_service.tag_list', request=request, current_user=current_user, **kwargs)

    async def tag_delete(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """tag_delete 接口对应的业务方法。"""
        return await self.todo('matching_service.tag_delete', request=request, current_user=current_user, **kwargs)
