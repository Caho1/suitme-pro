"""系统用户路由模块。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from app.core.sqlalchemy_compat import Session

from app.core.database import get_db
from app.core.deps import CurrentUser, get_current_user
from app.services.sys_user_service import SysUserService


router = APIRouter()
service = SysUserService()


@router.get('/system/user/profile', summary='获取个人资料。')
async def profile_get(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """获取个人资料。"""
    return await service.profile_get(db=db, request=request, current_user=current_user)


@router.put('/system/user/profile', summary='更新个人资料。')
async def profile_update(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """更新个人资料。"""
    return await service.profile_update(db=db, request=request, current_user=current_user)


@router.put('/system/user/profile/updatePwd', summary='修改个人密码。')
async def profile_update_pwd(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """修改个人密码。"""
    return await service.profile_update_pwd(db=db, request=request, current_user=current_user)


@router.post('/system/user/profile/avatar', summary='上传个人头像。')
async def profile_avatar(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """上传个人头像。"""
    return await service.profile_avatar(db=db, request=request, current_user=current_user)


@router.get('/system/user/list', summary='分页查询用户。')
async def list(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """分页查询用户。"""
    return await service.list(db=db, request=request, current_user=current_user)


@router.get('/system/user/{userId}', summary='查询用户详情。')
async def get(
    userId: int,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """查询用户详情。"""
    return await service.get(db=db, userId=userId, request=request, current_user=current_user)


@router.post('/system/user', summary='新增用户。')
async def add(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """新增用户。"""
    return await service.add(db=db, request=request, current_user=current_user)


@router.put('/system/user', summary='修改用户。')
async def update(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """修改用户。"""
    return await service.update(db=db, request=request, current_user=current_user)


@router.delete('/system/user/{userIds}', summary='批量删除用户。')
async def delete(
    userIds: str,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """批量删除用户。"""
    return await service.delete(db=db, userIds=userIds, request=request, current_user=current_user)


@router.put('/system/user/changeStatus', summary='启停用户。')
async def change_status(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """启停用户。"""
    return await service.change_status(db=db, request=request, current_user=current_user)


@router.put('/system/user/resetPwd', summary='重置密码。')
async def reset_pwd(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """重置密码。"""
    return await service.reset_pwd(db=db, request=request, current_user=current_user)


@router.get('/system/user/authRole/{userId}', summary='查询用户可分配角色。')
async def auth_role_get(
    userId: int,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """查询用户可分配角色。"""
    return await service.auth_role_get(db=db, userId=userId, request=request, current_user=current_user)


@router.put('/system/user/authRole', summary='批量给用户授权角色。')
async def auth_role_update(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """批量给用户授权角色。"""
    return await service.auth_role_update(db=db, request=request, current_user=current_user)


@router.post('/system/user/export', summary='导出用户 Excel。')
async def export(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """导出用户 Excel。"""
    return await service.export(db=db, request=request, current_user=current_user)
