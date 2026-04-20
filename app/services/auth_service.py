"""鉴权服务。"""

from __future__ import annotations

from typing import Any

from fastapi import Request

from app.core.deps import CurrentUser
from app.core.response import captcha_disabled, success
from app.services.base import SkeletonService


class AuthService(SkeletonService):
    """鉴权相关业务。

    当前只把最关键的兼容端点先放好：
    - `/captchaImage`：返回禁用验证码的固定结构
    - `/logout`：纯 JWT 模式下直接返回成功
    其余方法保留待迁移提示，方便逐步替换真实逻辑。
    """

    async def login(self, request: Request | None = None, **kwargs: Any) -> dict[str, Any]:
        """登录接口业务骨架。"""
        return await self.todo('auth.login', request=request, **kwargs)

    async def register(self, request: Request | None = None, **kwargs: Any) -> dict[str, Any]:
        """注册接口业务骨架。"""
        return await self.todo('auth.register', request=request, **kwargs)

    async def captcha_image(self, request: Request | None = None, **kwargs: Any) -> dict[str, Any]:
        """返回关闭验证码的兼容结构。"""
        return captcha_disabled()

    async def get_info(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """获取当前用户信息骨架。"""
        return await self.todo('auth.getInfo', request=request, current_user=current_user, **kwargs)

    async def logout(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """退出登录兼容端点。"""
        return success(msg='退出成功')
