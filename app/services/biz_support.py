"""业务模块共享辅助函数。"""

from __future__ import annotations

import json
from math import ceil
from typing import Any
from uuid import uuid4

from app.core.sqlalchemy_compat import Session, func, select


AI_STATUS_SUBMITTED = 'submitted'
AI_STATUS_PROCESSING = 'processing'
AI_STATUS_COMPLETED = 'completed'
AI_STATUS_FAILED = 'failed'
AI_STATUS_NONE = 'none'


def pick_first(data: dict[str, Any] | None, *keys: str, default: Any = None) -> Any:
    """按顺序返回字典中的第一个非空值。"""
    if not isinstance(data, dict):
        return default
    for key in keys:
        value = data.get(key)
        if value not in (None, ''):
            return value
    return default


def json_dumps_if_needed(value: Any) -> str | None:
    """把字典或列表转成 JSON 字符串；普通字符串原样返回。"""
    if value in (None, ''):
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def json_loads_if_possible(value: Any) -> Any:
    """尽量把 JSON 字符串还原为 Python 对象。"""
    if value in (None, ''):
        return None
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except Exception:
        return value


def next_numeric_id(db: Session, model: type[Any], column: Any, start: int = 1) -> int:
    """计算某张表的下一个数值主键。

    说明：
    1. 这是为了兼容当前占位模型里还没有全部补齐自增策略的场景。
    2. 真实接入现网 MySQL 后，如果表本身已经是 AUTO_INCREMENT，也可以继续保留这层逻辑。
    """
    current = db.scalar(select(func.max(column)))
    if current in (None, ''):
        return start
    try:
        return int(current) + 1
    except Exception:
        return start


def resolve_user_id(current_user: Any | None, payload: dict[str, Any] | None = None, *keys: str) -> int | None:
    """优先从当前登录用户获取 userId，没有时再从请求体取。"""
    if current_user is not None and getattr(current_user, 'user_id', None) is not None:
        return int(current_user.user_id)
    payload = payload or {}
    for key in keys or ('userId', 'user_id'):
        value = payload.get(key)
        if value not in (None, ''):
            try:
                return int(value)
            except Exception:
                continue
    return None


def resolve_operator(current_user: Any | None, default: str = 'system') -> str:
    """返回审计字段中的操作人。"""
    if current_user is not None and getattr(current_user, 'user_name', None):
        return str(current_user.user_name)
    return default


def normalize_ai_status(value: Any) -> str:
    """把外部 AI 返回的状态值规范成项目内部的几个固定值。"""
    text = str(value or '').strip().lower()
    if text in {'submitted', 'queued', 'pending'}:
        return AI_STATUS_SUBMITTED
    if text in {'processing', 'running', 'in_progress'}:
        return AI_STATUS_PROCESSING
    if text in {'completed', 'success', 'succeeded', 'done', 'finished'}:
        return AI_STATUS_COMPLETED
    if text in {'failed', 'error', 'aborted', 'cancelled'}:
        return AI_STATUS_FAILED
    return AI_STATUS_NONE


def extract_ai_submission(response: dict[str, Any] | None) -> dict[str, Any]:
    """从外部 AI 接口响应中提取任务编号、图片地址与状态。"""
    response = response or {}
    data = response.get('data') if isinstance(response.get('data'), dict) else response
    task_id = pick_first(data, 'taskId', 'task_id', 'id')
    image_url = pick_first(data, 'imageUrl', 'imgUrl', 'url', 'image', 'resultUrl')
    status = normalize_ai_status(pick_first(data, 'taskStatus', 'status', default=''))
    if status == AI_STATUS_NONE:
        if image_url:
            status = AI_STATUS_COMPLETED
        elif task_id:
            status = AI_STATUS_SUBMITTED
    return {
        'task_id': str(task_id) if task_id not in (None, '') else None,
        'image_url': image_url,
        'status': status,
        'raw': response,
    }


def build_mp_page_payload(records: list[Any], total: int, page_num: int, page_size: int) -> dict[str, Any]:
    """构造 MyBatis-Plus 风格分页 data。"""
    pages = ceil(total / page_size) if page_size else 0
    return {
        'records': records,
        'total': total,
        'size': page_size,
        'current': page_num,
        'pages': pages,
    }


def ensure_list(value: Any) -> list[Any]:
    """把任意输入尽量转成列表。"""
    if value in (None, ''):
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple | set):
        return list(value)
    return [value]


def make_task_id(prefix: str = 'task') -> str:
    """生成一个字符串任务编号。"""
    return f'{prefix}_{uuid4().hex}'
