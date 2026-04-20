"""OSS 文件路由模块。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from app.core.sqlalchemy_compat import Session

from app.core.database import get_db
from app.core.deps import CurrentUser, get_current_user
from app.services.oss_file_service import OssFileService


router = APIRouter()
service = OssFileService()


@router.post('/oss/file/upload', summary='上传单个文件到 OSS。')
async def upload(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """上传单个文件到 OSS。"""
    return await service.upload(db=db, request=request, current_user=current_user)


@router.post('/oss/file/batchUpload', summary='批量上传文件到 OSS。')
async def batch_upload(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """批量上传文件到 OSS。"""
    return await service.batch_upload(db=db, request=request, current_user=current_user)


@router.get('/oss/file/download/{fileId}', summary='按 fileId 下载 OSS 文件。')
async def download(
    fileId: int,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """按 fileId 下载 OSS 文件。"""
    return await service.download(db=db, fileId=fileId, request=request, current_user=current_user)


@router.get('/oss/file/checkConnection', summary='检查 OSS 连通性。')
async def check_connection(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """检查 OSS 连通性。"""
    return await service.check_connection(db=db, request=request, current_user=current_user)
