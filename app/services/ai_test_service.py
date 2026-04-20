"""AI 连通性测试服务。"""

from __future__ import annotations

from typing import Any

from fastapi import Request
import httpx

from app.core.response import error, success
from app.services.ai_client import AiClient
from app.services.base import SkeletonService


class AiTestService(SkeletonService):
    """测试外部 AI 服务连通性。"""

    def __init__(self) -> None:
        self.ai_client = AiClient()

    async def generate_digital_image(self, request: Request | None = None, **kwargs: Any) -> dict[str, Any]:
        """测试数字形象接口。"""
        if request is None:
            return error(msg='请求对象不能为空')
        payload = await request.json()
        try:
            data = await self.ai_client.generate_digital_image(payload=payload)
            return success(data=data)
        except httpx.HTTPError as exc:
            return error(msg=f'外部 AI 服务调用失败: {exc}')

    async def generate_outfit_img(self, request: Request | None = None, **kwargs: Any) -> dict[str, Any]:
        """测试穿搭生图接口。"""
        if request is None:
            return error(msg='请求对象不能为空')
        payload = await request.json()
        try:
            data = await self.ai_client.generate_outfit_image(payload=payload)
            return success(data=data)
        except httpx.HTTPError as exc:
            return error(msg=f'外部 AI 服务调用失败: {exc}')

    async def get_task_status(self, taskId: str, **kwargs: Any) -> dict[str, Any]:
        """测试任务查询接口。"""
        try:
            data = await self.ai_client.get_task_status(task_id=taskId)
            return success(data=data)
        except httpx.HTTPError as exc:
            return error(msg=f'外部 AI 服务调用失败: {exc}')
