"""通用文件服务。"""

from __future__ import annotations

import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from fastapi import Request, UploadFile
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from app.core.config import get_settings
from app.core.deps import CurrentUser
from app.core.response import error, success
from app.services.base import SkeletonService


class CommonService(SkeletonService):
    """本地上传与下载服务。"""

    def __init__(self) -> None:
        """读取全局配置。"""
        self.settings = get_settings()

    async def download(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> Any:
        """通用下载接口。

        兼容若依默认参数：
        - fileName
        - delete
        """
        if request is None:
            return error(msg='请求对象不能为空')
        file_name = str(request.query_params.get('fileName') or '').strip()
        delete_after_download = str(request.query_params.get('delete') or 'false').lower() == 'true'
        if not file_name:
            return error(msg='fileName 不能为空')
        if not self._is_safe_relative_path(file_name):
            return error(msg=f'文件名称({file_name})非法，不允许下载。')

        candidate = (self.settings.upload_profile_path / 'download' / file_name).resolve()
        if not candidate.exists() or not candidate.is_file():
            return error(msg='下载文件不存在')

        download_name = self._build_download_name(file_name)
        background = BackgroundTask(self._safe_delete_file, candidate) if delete_after_download else None
        return FileResponse(
            path=candidate,
            filename=download_name,
            media_type='application/octet-stream',
            background=background,
        )

    async def upload(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """本地单文件上传接口。"""
        if request is None:
            return error(msg='请求对象不能为空')

        form = await request.form()
        file = form.get('file')
        if not isinstance(file, UploadFile):
            return error(msg='缺少上传文件 file')

        result = await self._save_single_file(file=file)
        return success(**result)

    async def uploads(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """本地多文件上传接口。"""
        if request is None:
            return error(msg='请求对象不能为空')

        form = await request.form()
        files = []
        if hasattr(form, 'getlist'):
            files = [item for item in form.getlist('files') if isinstance(item, UploadFile)]
        if not files:
            files = [value for _, value in form.multi_items() if isinstance(value, UploadFile)]
        if not files:
            return error(msg='缺少上传文件 files')

        urls: list[str] = []
        file_names: list[str] = []
        new_file_names: list[str] = []
        original_filenames: list[str] = []
        for file in files:
            item = await self._save_single_file(file=file)
            urls.append(str(item['url']))
            file_names.append(str(item['fileName']))
            new_file_names.append(str(item['newFileName']))
            original_filenames.append(str(item['originalFilename']))

        return success(
            urls=','.join(urls),
            fileNames=','.join(file_names),
            newFileNames=','.join(new_file_names),
            originalFilenames=','.join(original_filenames),
        )

    async def download_resource(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> Any:
        """下载本地资源文件。"""
        if request is None:
            return error(msg='请求对象不能为空')

        resource = str(request.query_params.get('resource') or '').strip()
        if not resource:
            return error(msg='resource 不能为空')
        if not self._is_safe_resource(resource):
            return error(msg=f'资源文件({resource})非法，不允许下载。')

        relative_path = resource
        if relative_path.startswith(self.settings.upload_base_uri):
            relative_path = relative_path[len(self.settings.upload_base_uri):]
        relative_path = relative_path.lstrip('/\\')
        target = (self.settings.upload_profile_path / relative_path).resolve()
        if not target.exists() or not target.is_file():
            return error(msg='资源文件不存在')

        return FileResponse(
            path=target,
            filename=target.name,
            media_type='application/octet-stream',
        )

    async def _save_single_file(self, file: UploadFile) -> dict[str, str]:
        """把单个上传文件保存到本地磁盘，并返回若依兼容结构。"""
        original_name = file.filename or 'file'
        safe_original_name = self._sanitize_filename(original_name)
        base_name, dot, ext = safe_original_name.rpartition('.')
        if not base_name:
            base_name = safe_original_name
            ext = ''
        date_path = datetime.now().strftime('%Y/%m/%d')
        suffix = str(int(time.time() * 1000))
        new_file_name = f'{base_name}_{suffix}' + (f'.{ext}' if ext else '')
        relative_path = Path('upload') / date_path / new_file_name
        absolute_path = self.settings.upload_profile_path / relative_path
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        content = await file.read()
        absolute_path.write_bytes(content)

        file_name = f"{self.settings.upload_base_uri.rstrip('/')}/{relative_path.as_posix()}"
        return {
            'url': file_name,
            'fileName': file_name,
            'newFileName': new_file_name,
            'originalFilename': original_name,
        }

    def _build_download_name(self, file_name: str) -> str:
        """构造若依风格的下载文件名。"""
        base_name = Path(file_name).name
        if '_' in base_name:
            base_name = base_name.split('_', 1)[1]
        return f"{int(time.time() * 1000)}{base_name}"

    def _is_safe_relative_path(self, value: str) -> bool:
        """校验相对路径，防止目录穿越。"""
        if not value or '..' in value or value.startswith(('/', '\\')):
            return False
        return True

    def _is_safe_resource(self, value: str) -> bool:
        """校验资源路径。"""
        decoded = unquote(value)
        if '..' in decoded:
            return False
        return decoded.startswith(self.settings.upload_base_uri) or not decoded.startswith(('http://', 'https://'))

    def _sanitize_filename(self, value: str) -> str:
        """清理文件名中的危险字符。"""
        value = value.replace('\\', '_').replace('/', '_').strip()
        value = re.sub(r'[^0-9A-Za-z\u4e00-\u9fa5._-]+', '_', value)
        return value or 'file'

    def _safe_delete_file(self, path: Path) -> None:
        """后台安全删除文件。"""
        try:
            if path.exists() and path.is_file():
                os.remove(path)
        except OSError:
            return
