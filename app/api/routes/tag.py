"""标签路由模块。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from app.core.sqlalchemy_compat import Session

from app.core.database import get_db
from app.core.deps import CurrentUser, get_current_user
from app.services.tag_service import TagService


router = APIRouter()
service = TagService()


@router.post('/md/tag/add', summary='新增标签。')
async def add(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """新增标签。"""
    return await service.add(db=db, request=request, current_user=current_user)


@router.post('/md/tag/delete', summary='删除标签。')
async def delete(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """删除标签。"""
    return await service.delete(db=db, request=request, current_user=current_user)


@router.post('/md/tag/update', summary='更新标签。')
async def update(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """更新标签。"""
    return await service.update(db=db, request=request, current_user=current_user)


@router.get('/md/tag/list', summary='标签列表。')
async def list(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """标签列表。"""
    return await service.list(db=db, request=request, current_user=current_user)


@router.post('/md/tag/updateOrders', summary='批量调整标签顺序。')
async def update_orders(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """批量调整标签顺序。"""
    return await service.update_orders(db=db, request=request, current_user=current_user)
