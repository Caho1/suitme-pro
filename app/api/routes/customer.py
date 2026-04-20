"""路由模块。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from app.core.deps import CurrentUser, get_current_user
from app.services.customer_service import CustomerService


router = APIRouter()
service = CustomerService()

@router.post("/customer/add", summary="新增顾客并发起数字形象任务。")
async def add(request: Request, current_user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    """新增顾客并发起数字形象任务。"""
    return await service.add(request=request, current_user=current_user)


@router.get("/customer/get", summary="查询顾客详情。")
async def get(request: Request, current_user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    """查询顾客详情。"""
    return await service.get(request=request, current_user=current_user)


@router.get("/customer/getDigitalImg", summary="查询顾客数字形象，必要时主动轮询外部任务。")
async def get_digital_img(request: Request, current_user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    """查询顾客数字形象，必要时主动轮询外部任务。"""
    return await service.get_digital_img(request=request, current_user=current_user)


@router.post("/customer/page", summary="MyBatis-Plus 风格分页。")
async def page(request: Request, current_user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    """MyBatis-Plus 风格分页。"""
    return await service.page(request=request, current_user=current_user)


@router.post("/customer/delete", summary="逻辑删除顾客。")
async def delete(request: Request, current_user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    """逻辑删除顾客。"""
    return await service.delete(request=request, current_user=current_user)


@router.post("/customer/update", summary="局部更新顾客。")
async def update(request: Request, current_user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    """局部更新顾客。"""
    return await service.update(request=request, current_user=current_user)
