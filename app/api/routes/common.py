"""通用文件路由模块。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from app.core.deps import CurrentUser, get_current_user
from app.services.common_service import CommonService


router = APIRouter()
service = CommonService()


@router.get('/common/download', summary='通用下载接口。')
async def download(request: Request, current_user: CurrentUser = Depends(get_current_user)) -> Any:
    """通用下载接口。"""
    return await service.download(request=request, current_user=current_user)


@router.post('/common/upload', summary='本地磁盘上传接口。')
async def upload(request: Request, current_user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    """本地单文件上传接口。"""
    return await service.upload(request=request, current_user=current_user)


@router.post('/common/uploads', summary='本地多文件上传接口。')
async def uploads(request: Request, current_user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    """本地多文件上传接口。"""
    return await service.uploads(request=request, current_user=current_user)


@router.get('/common/download/resource', summary='下载本地资源文件。')
async def download_resource(request: Request, current_user: CurrentUser = Depends(get_current_user)) -> Any:
    """下载本地资源文件。"""
    return await service.download_resource(request=request, current_user=current_user)
