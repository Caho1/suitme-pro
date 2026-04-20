"""AI 测试路由模块。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from app.services.ai_test_service import AiTestService


router = APIRouter()
service = AiTestService()


@router.post('/api/test/generateDigitalImage', summary='匿名测试外部数字形象接口。')
async def generate_digital_image(request: Request) -> dict[str, Any]:
    """匿名测试外部数字形象接口。"""
    return await service.generate_digital_image(request=request)


@router.post('/api/test/generateOutfitImg', summary='匿名测试外部穿搭生图接口。')
async def generate_outfit_img(request: Request) -> dict[str, Any]:
    """匿名测试外部穿搭生图接口。"""
    return await service.generate_outfit_img(request=request)


@router.get('/api/test/getTaskStatus/{taskId}', summary='匿名测试外部任务查询接口。')
async def get_task_status(taskId: str) -> dict[str, Any]:
    """匿名测试外部任务查询接口。"""
    return await service.get_task_status(taskId=taskId)
