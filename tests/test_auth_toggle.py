from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.core.config import get_settings
from app.core.deps import get_current_user, require_permission


def test_get_current_user_skips_jwt_when_auth_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """关闭 JWT 校验时，业务依赖应返回系统用户。"""
    monkeypatch.setenv("JWT_AUTH_ENABLED", "false")
    get_settings.cache_clear()

    current_user = get_current_user(None)

    assert current_user.user_name == "system"
    assert "admin" in current_user.roles
    assert "*" in current_user.permissions


def test_get_current_user_requires_token_when_auth_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """开启 JWT 校验时，缺少 Bearer Token 应继续返回认证失败。"""
    monkeypatch.setenv("JWT_AUTH_ENABLED", "true")
    get_settings.cache_clear()

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(None)

    assert exc_info.value.status_code == 401


def test_permission_dependency_allows_disabled_auth_user(monkeypatch: pytest.MonkeyPatch) -> None:
    """关闭 JWT 校验时，权限依赖不应拦截业务接口。"""
    monkeypatch.setenv("JWT_AUTH_ENABLED", "false")
    get_settings.cache_clear()
    current_user = get_current_user(None)

    assert require_permission("system:user:list")(current_user) is current_user
