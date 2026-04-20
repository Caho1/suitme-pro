"""主数据路由模块。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from app.core.sqlalchemy_compat import Session

from app.core.database import get_db
from app.core.deps import CurrentUser, get_current_user
from app.services.product_service import ProductService


router = APIRouter()
service = ProductService()


@router.post('/md/product/add', summary='新增单品。')
async def add(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """新增单品。"""
    return await service.add(db=db, request=request, current_user=current_user)


@router.post('/md/product/update', summary='更新单品。')
async def update(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """更新单品。"""
    return await service.update(db=db, request=request, current_user=current_user)


@router.post('/md/product/delete', summary='删除单品。')
async def delete(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """删除单品。"""
    return await service.delete(db=db, request=request, current_user=current_user)


@router.post('/md/product/updateDisplayFlag', summary='更新单品展示开关。')
async def update_display_flag(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """更新单品展示开关。"""
    return await service.update_display_flag(db=db, request=request, current_user=current_user)


@router.post('/md/product/page', summary='单品分页。')
async def page(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """单品分页。"""
    return await service.page(db=db, request=request, current_user=current_user)


@router.post('/md/productColor/add', summary='新增颜色 SKU。')
async def product_color_add(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """新增颜色 SKU。"""
    return await service.product_color_add(db=db, request=request, current_user=current_user)


@router.post('/md/productColor/delete', summary='删除颜色 SKU。')
async def product_color_delete(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """删除颜色 SKU。"""
    return await service.product_color_delete(db=db, request=request, current_user=current_user)
