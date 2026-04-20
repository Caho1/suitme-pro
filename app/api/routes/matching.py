"""搭配路由模块。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from app.core.sqlalchemy_compat import Session

from app.core.database import get_db
from app.core.deps import CurrentUser, get_current_user
from app.services.matching_service import MatchingService


router = APIRouter()
service = MatchingService()


@router.post('/matching/addOrUpdate', summary='新增或修改搭配。')
async def add_or_update(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """新增或修改搭配。"""
    return await service.add_or_update(db=db, request=request, current_user=current_user)


@router.post('/matching/list', summary='查询搭配列表。')
async def list(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """查询搭配列表。"""
    return await service.list(db=db, request=request, current_user=current_user)


@router.post('/matching/delete', summary='删除搭配。')
async def delete(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """删除搭配。"""
    return await service.delete(db=db, request=request, current_user=current_user)


@router.post('/matching/tag/addOrUpdate', summary='新增或修改搭配标签。')
async def tag_add_or_update(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """新增或修改搭配标签。"""
    return await service.tag_add_or_update(db=db, request=request, current_user=current_user)


@router.post('/matching/tag/list', summary='查询搭配标签列表。')
async def tag_list(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """查询搭配标签列表。"""
    return await service.tag_list(db=db, request=request, current_user=current_user)


@router.post('/matching/tag/delete', summary='删除搭配标签。')
async def tag_delete(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """删除搭配标签。"""
    return await service.tag_delete(db=db, request=request, current_user=current_user)
