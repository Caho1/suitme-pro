"""请求解析工具。"""

from __future__ import annotations

from typing import Any
from urllib.parse import unquote

from fastapi import Request, UploadFile


async def read_json_body(request: Request) -> dict[str, Any]:
    """读取 JSON 请求体；空体时返回空字典。"""
    body = await request.body()
    if not body:
        return {}
    try:
        data = await request.json()
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


async def read_form_dict(request: Request) -> tuple[dict[str, Any], dict[str, UploadFile], list[UploadFile]]:
    """读取表单参数与文件。"""
    form = await request.form()
    data: dict[str, Any] = {}
    files: dict[str, UploadFile] = {}
    file_list: list[UploadFile] = []
    for key, value in form.multi_items():
        if isinstance(value, UploadFile):
            files[key] = value
            file_list.append(value)
        else:
            data[key] = value
    return data, files, file_list


async def collect_params(request: Request) -> dict[str, Any]:
    """合并 query、json、form 参数。"""
    params: dict[str, Any] = dict(request.query_params)
    content_type = (request.headers.get('content-type') or '').lower()
    if 'application/json' in content_type:
        params.update(await read_json_body(request))
    elif 'multipart/form-data' in content_type or 'application/x-www-form-urlencoded' in content_type:
        data, _, _ = await read_form_dict(request)
        params.update(data)
    return params


def get_int(value: Any, default: int = 0) -> int:
    """把任意输入尽量转换为整数。"""
    if value is None or value == '':
        return default
    try:
        return int(value)
    except Exception:
        return default


def split_to_int_list(value: Any) -> list[int]:
    """把逗号串、数组等输入转换为整数列表。"""
    if value is None or value == '':
        return []
    if isinstance(value, list | tuple | set):
        items = list(value)
    else:
        items = [item.strip() for item in str(value).split(',') if item.strip()]
    result: list[int] = []
    for item in items:
        try:
            result.append(int(item))
        except Exception:
            continue
    return result


def safe_resource_path(resource: str) -> str:
    """清洗资源路径，避免简单的路径穿越。"""
    resource = unquote(resource or '').strip()
    resource = resource.replace('\\', '/')
    while '//' in resource:
        resource = resource.replace('//', '/')
    return resource
