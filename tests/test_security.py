from __future__ import annotations

from app.core.security import hash_password, verify_password


def test_bcrypt_password_verify_supports_admin_password() -> None:
    """确保默认测试账号密码可以正常哈希和校验。"""
    hashed_password = hash_password("admin123")

    assert verify_password("admin123", hashed_password)
    assert not verify_password("wrong-password", hashed_password)
