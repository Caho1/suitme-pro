"""系统用户服务。"""

from __future__ import annotations

from typing import Any

from fastapi import Request

from app.core.deps import CurrentUser
from app.services.base import SkeletonService


class SysUserService(SkeletonService):
    """系统用户服务。

    当前文件只放方法骨架和中文注释，便于后续逐个替换为真实实现。
    """

    async def profile_get(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """profile_get 接口对应的业务方法。"""
        return await self.todo('sys_user_service.profile_get', request=request, current_user=current_user, **kwargs)

    async def profile_update(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """profile_update 接口对应的业务方法。"""
        return await self.todo('sys_user_service.profile_update', request=request, current_user=current_user, **kwargs)

    async def profile_update_pwd(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """profile_update_pwd 接口对应的业务方法。"""
        return await self.todo('sys_user_service.profile_update_pwd', request=request, current_user=current_user, **kwargs)

    async def profile_avatar(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """profile_avatar 接口对应的业务方法。"""
        return await self.todo('sys_user_service.profile_avatar', request=request, current_user=current_user, **kwargs)

    async def list(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """list 接口对应的业务方法。"""
        return await self.todo('sys_user_service.list', request=request, current_user=current_user, **kwargs)

    async def get(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """get 接口对应的业务方法。"""
        return await self.todo('sys_user_service.get', request=request, current_user=current_user, **kwargs)

    async def add(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """add 接口对应的业务方法。"""
        return await self.todo('sys_user_service.add', request=request, current_user=current_user, **kwargs)

    async def update(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """update 接口对应的业务方法。"""
        return await self.todo('sys_user_service.update', request=request, current_user=current_user, **kwargs)

    async def delete(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """delete 接口对应的业务方法。"""
        return await self.todo('sys_user_service.delete', request=request, current_user=current_user, **kwargs)

    async def change_status(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """change_status 接口对应的业务方法。"""
        return await self.todo('sys_user_service.change_status', request=request, current_user=current_user, **kwargs)

    async def reset_pwd(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """reset_pwd 接口对应的业务方法。"""
        return await self.todo('sys_user_service.reset_pwd', request=request, current_user=current_user, **kwargs)

    async def auth_role_get(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """auth_role_get 接口对应的业务方法。"""
        return await self.todo('sys_user_service.auth_role_get', request=request, current_user=current_user, **kwargs)

    async def auth_role_update(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """auth_role_update 接口对应的业务方法。"""
        return await self.todo('sys_user_service.auth_role_update', request=request, current_user=current_user, **kwargs)

    async def export(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """export 接口对应的业务方法。"""
        return await self.todo('sys_user_service.export', request=request, current_user=current_user, **kwargs)
