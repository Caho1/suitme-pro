"""FastAPI 依赖模块。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from fastapi import Depends, Header, HTTPException, status

from app.core.database import get_db
from app.core.security import decode_access_token


@dataclass
class CurrentUser:
    """当前登录用户的最小抽象。"""

    user_id: int | None = None
    user_name: str | None = None
    roles: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    raw_payload: dict[str, Any] = field(default_factory=dict)


def _extract_bearer_token(authorization: str | None) -> str:
    """从 Authorization 头中提取 Bearer Token。"""
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="认证失败")
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="认证失败")
    return authorization[len(prefix):].strip()


def get_current_user(authorization: str | None = Header(default=None)) -> CurrentUser:
    """解析当前登录用户。"""
    token = _extract_bearer_token(authorization)
    payload = decode_access_token(token)
    return CurrentUser(
        user_id=payload.get("userId"),
        user_name=payload.get("userName"),
        roles=list(payload.get("roles", [])),
        permissions=list(payload.get("permissions", [])),
        raw_payload=payload,
    )


def require_permission(permission: str) -> Callable[[CurrentUser], CurrentUser]:
    """创建权限校验依赖。"""

    def dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if permission not in current_user.permissions and "admin" not in current_user.roles:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="认证失败")
        return current_user

    return dependency
