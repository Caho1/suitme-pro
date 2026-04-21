"""穿搭任务路由模块。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from app.core.sqlalchemy_compat import Session

from app.core.database import get_db
from app.core.deps import CurrentUser, get_current_user
from app.services.outfit_service import OutfitService


router = APIRouter()
service = OutfitService()


@router.post('/outfit/generateOutfitImg', summary='创建穿搭生图任务。')
async def generate_outfit_img(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """创建穿搭生图任务。"""
    return await service.generate_outfit_img(db=db, request=request, current_user=current_user)


@router.post('/outfit/getOutfitImg', summary='聚合获取穿搭图，并必要时更新任务状态。')
async def get_outfit_img(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """聚合获取穿搭图，并必要时更新任务状态。"""
    return await service.get_outfit_img(db=db, request=request, current_user=current_user)


@router.get('/outfit/getTaskStatus/{taskId}', summary='透传外部任务查询。')
async def get_task_status(
    taskId: str,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """透传外部任务查询。"""
    return await service.get_task_status(db=db, taskId=taskId, request=request, current_user=current_user)


@router.post('/outfit/taskPage', summary='穿搭任务分页。')
async def task_page(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """穿搭任务分页。"""
    return await service.task_page(db=db, request=request, current_user=current_user)


@router.get('/tasks/outfit/users/{userId}', summary='兼容旧前端的试穿记录分页。')
async def legacy_task_page(
    userId: str,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """兼容旧前端的试穿记录分页。"""
    return await service.legacy_task_page(db=db, user_id=userId, request=request, current_user=current_user)
