"""系统菜单路由模块。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from app.core.sqlalchemy_compat import Session

from app.core.database import get_db
from app.core.deps import CurrentUser, get_current_user
from app.services.sys_menu_service import SysMenuService


router = APIRouter()
service = SysMenuService()


@router.get('/system/menu/list', summary='查询菜单列表。')
async def list(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """查询菜单列表。"""
    return await service.list(db=db, request=request, current_user=current_user)


@router.get('/system/menu/treeselect', summary='菜单树下拉。')
async def treeselect(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """菜单树下拉。"""
    return await service.treeselect(db=db, request=request, current_user=current_user)


@router.get('/system/menu/roleMenuTreeselect/{roleId}', summary='角色菜单树。')
async def role_menu_treeselect(
    roleId: int,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """角色菜单树。"""
    return await service.role_menu_treeselect(db=db, roleId=roleId, request=request, current_user=current_user)


@router.get('/system/menu/{menuId}', summary='查询菜单详情。')
async def get(
    menuId: int,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """查询菜单详情。"""
    return await service.get(db=db, menuId=menuId, request=request, current_user=current_user)


@router.post('/system/menu', summary='新增菜单。')
async def add(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """新增菜单。"""
    return await service.add(db=db, request=request, current_user=current_user)


@router.put('/system/menu', summary='修改菜单。')
async def update(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """修改菜单。"""
    return await service.update(db=db, request=request, current_user=current_user)


@router.delete('/system/menu/{menuId}', summary='删除菜单。')
async def delete(
    menuId: int,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """删除菜单。"""
    return await service.delete(db=db, menuId=menuId, request=request, current_user=current_user)
