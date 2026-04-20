"""穿搭任务服务。"""

from __future__ import annotations

from typing import Any

from fastapi import Request

from app.core.deps import CurrentUser
from app.services.base import SkeletonService


class OutfitService(SkeletonService):
    """穿搭任务服务。

    当前文件只放方法骨架和中文注释，便于后续逐个替换为真实实现。
    """

    async def generate_outfit_img(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """generate_outfit_img 接口对应的业务方法。"""
        return await self.todo('outfit_service.generate_outfit_img', request=request, current_user=current_user, **kwargs)

    async def get_outfit_img(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """get_outfit_img 接口对应的业务方法。"""
        return await self.todo('outfit_service.get_outfit_img', request=request, current_user=current_user, **kwargs)

    async def get_task_status(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """get_task_status 接口对应的业务方法。"""
        return await self.todo('outfit_service.get_task_status', request=request, current_user=current_user, **kwargs)

    async def task_page(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """task_page 接口对应的业务方法。"""
        return await self.todo('outfit_service.task_page', request=request, current_user=current_user, **kwargs)
