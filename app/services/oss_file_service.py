"""OSS 文件服务。"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import Request
from fastapi.responses import StreamingResponse

from app.core.config import get_settings
from app.core.deps import CurrentUser
from app.core.request_utils import read_form_dict
from app.core.response import error, success
from app.models.oss_file import OssFile
from app.services.base import SkeletonService
from app.services.biz_support import next_numeric_id, resolve_operator


class OssFileService(SkeletonService):
    """阿里云 OSS 文件服务。"""

    def __init__(self) -> None:
        self.settings = get_settings()

    def _get_bucket(self) -> Any:
        """创建 OSS Bucket 对象。"""
        if not all(
            [
                self.settings.oss_endpoint,
                self.settings.oss_bucket_name,
                self.settings.oss_access_key_id,
                self.settings.oss_access_key_secret,
            ]
        ):
            raise RuntimeError('OSS 配置不完整')
        import oss2

        auth = oss2.Auth(self.settings.oss_access_key_id, self.settings.oss_access_key_secret)
        return oss2.Bucket(auth, self.settings.oss_endpoint, self.settings.oss_bucket_name)

    def _build_object_key(self, filename: str) -> str:
        """生成对象存储 key。"""
        suffix = Path(filename or '').suffix
        date_folder = datetime.now().strftime('%Y%m%d')
        return f'suitme/{date_folder}/{uuid4().hex}{suffix}'

    def _build_public_url(self, object_key: str) -> str:
        """根据对象 key 生成公开访问 URL。"""
        if self.settings.oss_public_url:
            return f"{self.settings.oss_public_url.rstrip('/')}/{object_key}"
        endpoint = (self.settings.oss_endpoint or '').replace('https://', '').replace('http://', '')
        return f'https://{self.settings.oss_bucket_name}.{endpoint}/{object_key}'

    def _serialize_record(self, record: OssFile) -> dict[str, Any]:
        """序列化 OSS 文件元数据。"""
        return {
            'fileId': record.file_id,
            'fileName': record.file_name,
            'originalName': record.original_name,
            'objectKey': record.object_key,
            'url': record.url,
            'etag': record.etag,
            'contentType': record.content_type,
            'remark': record.remark,
            'createBy': record.create_by,
            'createTime': record.create_time.strftime('%Y-%m-%d %H:%M:%S') if record.create_time else None,
            'updateBy': record.update_by,
            'updateTime': record.update_time.strftime('%Y-%m-%d %H:%M:%S') if record.update_time else None,
        }

    async def _upload_single(self, db: Any, upload_file: Any, current_user: CurrentUser | None) -> dict[str, Any]:
        """上传单个文件并写入元数据。"""
        bucket = self._get_bucket()
        object_key = self._build_object_key(upload_file.filename or '')
        content = await upload_file.read()
        result = bucket.put_object(object_key, content)
        url = self._build_public_url(object_key)
        now = datetime.now()
        operator = resolve_operator(current_user)
        record = OssFile(
            file_id=next_numeric_id(db, OssFile, OssFile.file_id),
            file_name=Path(object_key).name,
            original_name=upload_file.filename or None,
            object_key=object_key,
            url=url,
            etag=getattr(result, 'etag', None),
            content_type=getattr(upload_file, 'content_type', None),
            create_by=operator,
            create_time=now,
            update_by=operator,
            update_time=now,
        )
        db.add(record)
        db.flush()
        return self._serialize_record(record)

    async def upload(
        self,
        db: Any,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """上传单个文件到 OSS。"""
        try:
            _, files, _ = await read_form_dict(request) if request is not None else ({}, {}, [])
            upload_file = files.get('file') or next(iter(files.values()), None)
            if upload_file is None:
                return error('上传文件不能为空')
            record = await self._upload_single(db, upload_file, current_user)
            db.commit()
            return success(
                data=record,
                url=record['url'],
                fileName=record['url'],
                newFileName=record['objectKey'],
                originalFilename=record['originalName'],
            )
        except Exception as exc:
            db.rollback()
            return error(str(exc))

    async def batch_upload(
        self,
        db: Any,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """批量上传文件到 OSS。"""
        try:
            _, _, files = await read_form_dict(request) if request is not None else ({}, {}, [])
            if not files:
                return error('上传文件不能为空')
            records = []
            for upload_file in files:
                records.append(await self._upload_single(db, upload_file, current_user))
            db.commit()
            return success(
                data=records,
                urls=','.join(item['url'] for item in records if item.get('url')),
                fileNames=','.join(item['url'] for item in records if item.get('url')),
                newFileNames=','.join(item['objectKey'] for item in records if item.get('objectKey')),
                originalFilenames=','.join(item['originalName'] or '' for item in records),
            )
        except Exception as exc:
            db.rollback()
            return error(str(exc))

    async def download(
        self,
        db: Any,
        fileId: int,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> StreamingResponse | dict[str, Any]:
        """按 fileId 下载 OSS 文件。"""
        record = db.get(OssFile, fileId)
        if record is None:
            return error('文件不存在')
        try:
            bucket = self._get_bucket()
            result = bucket.get_object(record.object_key)
            filename = record.original_name or record.file_name or 'download.bin'
            media_type = record.content_type or 'application/octet-stream'
            return StreamingResponse(
                iter([result.read()]),
                media_type=media_type,
                headers={'Content-Disposition': f"attachment; filename*=UTF-8''{filename}"},
            )
        except Exception as exc:
            return error(str(exc))

    async def check_connection(
        self,
        db: Any,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """检查 OSS 连通性。"""
        try:
            bucket = self._get_bucket()
            bucket.get_bucket_info()
            return success(data=True, endpoint=self.settings.oss_endpoint, bucket=self.settings.oss_bucket_name)
        except Exception as exc:
            return error(str(exc))
