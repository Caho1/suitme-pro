
"""服务层基础类。"""

from __future__ import annotations

from typing import Any

from fastapi import Request

from app.core.deps import CurrentUser
from app.core.response import not_implemented


class SkeletonService:
    """服务层基础类。

    当前阶段用于快速搭建完整的接口骨架；
    后续逐个方法替换成真实业务逻辑即可。
    """

    async def todo(
        self,
        feature: str,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """返回统一的“待迁移”响应。"""
        return not_implemented(feature)
