"""路由模块。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from app.core.deps import CurrentUser, get_current_user
from app.services.auth_service import AuthService


router = APIRouter()
service = AuthService()

@router.post("/login", summary="登录；返回 {code,msg,token}。")
async def login(request: Request) -> dict[str, Any]:
    """登录；返回 {code,msg,token}。"""
    return await service.login(request=request)


@router.post("/register", summary="注册；成功后初始化默认服装分类。")
async def register(request: Request) -> dict[str, Any]:
    """注册；成功后初始化默认服装分类。"""
    return await service.register(request=request)


@router.get("/captchaImage", summary="兼容端点；当前规划固定返回 captchaEnabled=false。")
async def captcha_image(request: Request) -> dict[str, Any]:
    """兼容端点；当前规划固定返回 captchaEnabled=false。"""
    return await service.captcha_image(request=request)


@router.get("/getInfo", summary="返回 user/roles/permissions 等。")
async def get_info(request: Request, current_user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    """返回 user/roles/permissions 等。"""
    return await service.get_info(request=request, current_user=current_user)


@router.post("/logout", summary="建议保留兼容端点；纯 JWT 模式下可直接返回成功。")
async def logout(request: Request, current_user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    """建议保留兼容端点；纯 JWT 模式下可直接返回成功。"""
    return await service.logout(request=request, current_user=current_user)
