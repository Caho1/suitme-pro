"""服装分类路由模块。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from app.core.sqlalchemy_compat import Session

from app.core.database import get_db
from app.core.deps import CurrentUser, get_current_user
from app.services.category_service import CategoryService


router = APIRouter()
service = CategoryService()


@router.post('/md/categoryTag/add', summary='新增服装分类节点。')
async def add(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """新增服装分类节点。"""
    return await service.add(db=db, request=request, current_user=current_user)


@router.post('/md/categoryTag/update', summary='更新服装分类节点。')
async def update(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """更新服装分类节点。"""
    return await service.update(db=db, request=request, current_user=current_user)


@router.post('/md/categoryTag/delete', summary='删除服装分类节点。')
async def delete(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """删除服装分类节点。"""
    return await service.delete(db=db, request=request, current_user=current_user)


@router.post('/md/categoryTag/list', summary='服装分类树。')
async def list(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """服装分类树。"""
    return await service.list(db=db, request=request, current_user=current_user)
