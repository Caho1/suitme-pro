"""顾客服务。"""

from __future__ import annotations

from typing import Any

from fastapi import Request

from app.core.deps import CurrentUser
from app.services.base import SkeletonService


class CustomerService(SkeletonService):
    """顾客服务。

    当前文件只放方法骨架和中文注释，便于后续逐个替换为真实实现。
    """

    async def add(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """add 接口对应的业务方法。"""
        return await self.todo('customer_service.add', request=request, current_user=current_user, **kwargs)

    async def get(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """get 接口对应的业务方法。"""
        return await self.todo('customer_service.get', request=request, current_user=current_user, **kwargs)

    async def get_digital_img(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """get_digital_img 接口对应的业务方法。"""
        return await self.todo('customer_service.get_digital_img', request=request, current_user=current_user, **kwargs)

    async def page(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """page 接口对应的业务方法。"""
        return await self.todo('customer_service.page', request=request, current_user=current_user, **kwargs)

    async def delete(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """delete 接口对应的业务方法。"""
        return await self.todo('customer_service.delete', request=request, current_user=current_user, **kwargs)

    async def update(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """update 接口对应的业务方法。"""
        return await self.todo('customer_service.update', request=request, current_user=current_user, **kwargs)
