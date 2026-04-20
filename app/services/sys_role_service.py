"""系统角色服务。"""

from __future__ import annotations

from typing import Any

from fastapi import Request

from app.core.deps import CurrentUser
from app.services.base import SkeletonService


class SysRoleService(SkeletonService):
    """系统角色服务。

    当前文件只放方法骨架和中文注释，便于后续逐个替换为真实实现。
    """

    async def auth_user_allocated_list(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """auth_user_allocated_list 接口对应的业务方法。"""
        return await self.todo('sys_role_service.auth_user_allocated_list', request=request, current_user=current_user, **kwargs)

    async def auth_user_unallocated_list(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """auth_user_unallocated_list 接口对应的业务方法。"""
        return await self.todo('sys_role_service.auth_user_unallocated_list', request=request, current_user=current_user, **kwargs)

    async def auth_user_cancel(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """auth_user_cancel 接口对应的业务方法。"""
        return await self.todo('sys_role_service.auth_user_cancel', request=request, current_user=current_user, **kwargs)

    async def auth_user_cancel_all(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """auth_user_cancel_all 接口对应的业务方法。"""
        return await self.todo('sys_role_service.auth_user_cancel_all', request=request, current_user=current_user, **kwargs)

    async def auth_user_select_all(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """auth_user_select_all 接口对应的业务方法。"""
        return await self.todo('sys_role_service.auth_user_select_all', request=request, current_user=current_user, **kwargs)

    async def list(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """list 接口对应的业务方法。"""
        return await self.todo('sys_role_service.list', request=request, current_user=current_user, **kwargs)

    async def get(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """get 接口对应的业务方法。"""
        return await self.todo('sys_role_service.get', request=request, current_user=current_user, **kwargs)

    async def add(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """add 接口对应的业务方法。"""
        return await self.todo('sys_role_service.add', request=request, current_user=current_user, **kwargs)

    async def update(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """update 接口对应的业务方法。"""
        return await self.todo('sys_role_service.update', request=request, current_user=current_user, **kwargs)

    async def change_status(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """change_status 接口对应的业务方法。"""
        return await self.todo('sys_role_service.change_status', request=request, current_user=current_user, **kwargs)

    async def delete(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """delete 接口对应的业务方法。"""
        return await self.todo('sys_role_service.delete', request=request, current_user=current_user, **kwargs)

    async def export(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """export 接口对应的业务方法。"""
        return await self.todo('sys_role_service.export', request=request, current_user=current_user, **kwargs)
