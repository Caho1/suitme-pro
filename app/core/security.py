"""安全相关工具。

这里负责：
1. JWT 签发与解析
2. 密码哈希与校验

说明：
- 正常运行建议安装 `python-jose` 与 `passlib[bcrypt]`。
- 为了方便只做骨架导入与文档测试，这里对“依赖尚未安装”的情况做了最小兜底。
- 真实开发与上线时请务必安装正式依赖，不要依赖 fallback 实现。
"""

from __future__ import annotations

import base64
import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import get_settings

try:
    from jose import JWTError, jwt
except Exception:  # pragma: no cover - 仅用于依赖未安装时的骨架导入
    jwt = None  # type: ignore[assignment]

    class JWTError(Exception):
        """最小化占位异常。"""

try:
    from passlib.context import CryptContext
except Exception:  # pragma: no cover - 仅用于依赖未安装时的骨架导入
    CryptContext = None  # type: ignore[assignment]


settings = get_settings()

if CryptContext is not None:
    pwd_context = CryptContext(
        schemes=["bcrypt"],
        deprecated="auto",
        bcrypt__rounds=10,
    )
else:  # pragma: no cover - 仅用于依赖未安装时的骨架导入
    pwd_context = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验明文密码和哈希密码是否匹配。"""
    if pwd_context is not None:
        return pwd_context.verify(plain_password, hashed_password)
    return hash_password(plain_password) == hashed_password


def hash_password(password: str) -> str:
    """生成密码哈希。"""
    if pwd_context is not None:
        return pwd_context.hash(password)
    return hashlib.sha256(f"suitme-fallback::{password}".encode("utf-8")).hexdigest()


def create_access_token(data: dict[str, Any], expires_delta_minutes: int | None = None) -> str:
    """创建访问令牌。"""
    to_encode = data.copy()
    expire_minutes = expires_delta_minutes or settings.jwt_expire_minutes
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    to_encode.update({"exp": expire.isoformat(), "iat": datetime.now(timezone.utc).isoformat()})
    if jwt is not None:
        return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    payload = json.dumps(to_encode, ensure_ascii=False).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("utf-8")


def decode_access_token(token: str) -> dict[str, Any]:
    """解析访问令牌。"""
    if jwt is not None:
        try:
            return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        except JWTError as exc:
            raise ValueError("无效或过期的令牌") from exc
    try:
        payload = base64.urlsafe_b64decode(token.encode("utf-8")).decode("utf-8")
        return json.loads(payload)
    except Exception as exc:  # pragma: no cover - 骨架 fallback
        raise ValueError("无效或过期的令牌") from exc
