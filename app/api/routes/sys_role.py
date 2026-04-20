"""系统角色路由模块。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from app.core.sqlalchemy_compat import Session

from app.core.database import get_db
from app.core.deps import CurrentUser, get_current_user
from app.services.sys_role_service import SysRoleService


router = APIRouter()
service = SysRoleService()


@router.get('/system/role/authUser/allocatedList', summary='已分配用户列表。')
async def auth_user_allocated_list(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """已分配用户列表。"""
    return await service.auth_user_allocated_list(db=db, request=request, current_user=current_user)


@router.get('/system/role/authUser/unallocatedList', summary='未分配用户列表。')
async def auth_user_unallocated_list(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """未分配用户列表。"""
    return await service.auth_user_unallocated_list(db=db, request=request, current_user=current_user)


@router.put('/system/role/authUser/cancel', summary='取消单个用户角色。')
async def auth_user_cancel(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """取消单个用户角色。"""
    return await service.auth_user_cancel(db=db, request=request, current_user=current_user)


@router.put('/system/role/authUser/cancelAll', summary='批量取消用户角色。')
async def auth_user_cancel_all(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """批量取消用户角色。"""
    return await service.auth_user_cancel_all(db=db, request=request, current_user=current_user)


@router.put('/system/role/authUser/selectAll', summary='批量授权用户到角色。')
async def auth_user_select_all(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """批量授权用户到角色。"""
    return await service.auth_user_select_all(db=db, request=request, current_user=current_user)


@router.get('/system/role/list', summary='分页查询角色。')
async def list(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """分页查询角色。"""
    return await service.list(db=db, request=request, current_user=current_user)


@router.get('/system/role/{roleId}', summary='查询角色详情。')
async def get(
    roleId: int,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """查询角色详情。"""
    return await service.get(db=db, roleId=roleId, request=request, current_user=current_user)


@router.post('/system/role', summary='新增角色。')
async def add(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """新增角色。"""
    return await service.add(db=db, request=request, current_user=current_user)


@router.put('/system/role', summary='修改角色。')
async def update(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """修改角色。"""
    return await service.update(db=db, request=request, current_user=current_user)


@router.put('/system/role/changeStatus', summary='启停角色。')
async def change_status(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """启停角色。"""
    return await service.change_status(db=db, request=request, current_user=current_user)


@router.delete('/system/role/{roleIds}', summary='批量删除角色。')
async def delete(
    roleIds: str,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """批量删除角色。"""
    return await service.delete(db=db, roleIds=roleIds, request=request, current_user=current_user)


@router.post('/system/role/export', summary='导出角色 Excel。')
async def export(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """导出角色 Excel。"""
    return await service.export(db=db, request=request, current_user=current_user)
