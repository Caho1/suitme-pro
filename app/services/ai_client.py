
"""对接外部 AI 生图服务的客户端封装。"""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import get_settings


class AiClient:
    """外部 AI 服务客户端。

    这里保留与 Java 版一致的三个核心调用：
    1. 数字形象
    2. 穿搭生图
    3. 任务查询
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    def _headers(self) -> dict[str, str]:
        """构建公共请求头。"""
        headers = {"Content-Type": "application/json"}
        if self.settings.suitme_ai_auth_token:
            headers["Authorization"] = f"Bearer {self.settings.suitme_ai_auth_token}"
        return headers

    async def generate_digital_image(self, payload: dict[str, Any]) -> dict[str, Any]:
        """调用外部数字形象接口。"""
        async with httpx.AsyncClient(timeout=httpx.Timeout(300.0, connect=60.0, read=60.0)) as client:
            response = await client.post(
                f"{self.settings.suitme_ai_base_url.rstrip('/')}/models/default",
                json=payload,
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()

    async def generate_outfit_image(self, payload: dict[str, Any]) -> dict[str, Any]:
        """调用外部穿搭生图接口。"""
        async with httpx.AsyncClient(timeout=httpx.Timeout(300.0, connect=60.0, read=60.0)) as client:
            response = await client.post(
                f"{self.settings.suitme_ai_base_url.rstrip('/')}/models/outfit",
                json=payload,
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()

    async def get_task_status(self, task_id: str) -> dict[str, Any]:
        """调用外部任务查询接口。"""
        async with httpx.AsyncClient(timeout=httpx.Timeout(300.0, connect=60.0, read=60.0)) as client:
            response = await client.get(
                f"{self.settings.suitme_ai_base_url.rstrip('/')}/tasks/{task_id}",
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()
