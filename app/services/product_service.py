"""主数据服务。"""

from __future__ import annotations

from typing import Any

from fastapi import Request

from app.core.deps import CurrentUser
from app.services.base import SkeletonService


class ProductService(SkeletonService):
    """主数据服务。

    当前文件只放方法骨架和中文注释，便于后续逐个替换为真实实现。
    """

    async def add(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """add 接口对应的业务方法。"""
        return await self.todo('product_service.add', request=request, current_user=current_user, **kwargs)

    async def update(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """update 接口对应的业务方法。"""
        return await self.todo('product_service.update', request=request, current_user=current_user, **kwargs)

    async def delete(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """delete 接口对应的业务方法。"""
        return await self.todo('product_service.delete', request=request, current_user=current_user, **kwargs)

    async def update_display_flag(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """update_display_flag 接口对应的业务方法。"""
        return await self.todo('product_service.update_display_flag', request=request, current_user=current_user, **kwargs)

    async def page(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """page 接口对应的业务方法。"""
        return await self.todo('product_service.page', request=request, current_user=current_user, **kwargs)

    async def product_color_add(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """product_color_add 接口对应的业务方法。"""
        return await self.todo('product_service.product_color_add', request=request, current_user=current_user, **kwargs)

    async def product_color_delete(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """product_color_delete 接口对应的业务方法。"""
        return await self.todo('product_service.product_color_delete', request=request, current_user=current_user, **kwargs)
