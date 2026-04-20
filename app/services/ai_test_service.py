"""AI 连通性测试服务。"""

from __future__ import annotations

from typing import Any

from fastapi import Request

from app.services.ai_client import AiClient
from app.services.base import SkeletonService


class AiTestService(SkeletonService):
    """测试外部 AI 服务连通性。

    这里先保留接口形状，真实实现时可以决定是否完全透传 Java 的行为。
    """

    def __init__(self) -> None:
        self.ai_client = AiClient()

    async def generate_digital_image(self, request: Request | None = None, **kwargs: Any) -> dict[str, Any]:
        """测试数字形象接口。"""
        return await self.todo('api_test.generateDigitalImage', request=request, **kwargs)

    async def generate_outfit_img(self, request: Request | None = None, **kwargs: Any) -> dict[str, Any]:
        """测试穿搭生图接口。"""
        return await self.todo('api_test.generateOutfitImg', request=request, **kwargs)

    async def get_task_status(self, taskId: str, **kwargs: Any) -> dict[str, Any]:
        """测试任务查询接口。"""
        return await self.todo('api_test.getTaskStatus', taskId=taskId, **kwargs)
