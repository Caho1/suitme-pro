"""数据库连接模块。

说明：
1. 正常运行时应安装 SQLAlchemy 并使用真实数据库连接。
2. 为了让“只看骨架、不连数据库”的本地检查也能导入应用，这里做了最小的可导入兜底。
3. 一旦进入真实开发或联调，请先安装依赖，不要依赖这个兜底。
"""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

from app.core.config import get_settings

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session, sessionmaker
except Exception:  # pragma: no cover - 仅用于依赖未安装时的骨架导入
    create_engine = None  # type: ignore[assignment]
    Session = Any  # type: ignore[misc,assignment]
    sessionmaker = None  # type: ignore[assignment]


settings = get_settings()

if create_engine is not None and sessionmaker is not None:
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        future=True,
    )

    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        class_=Session,
    )
else:  # pragma: no cover - 仅用于依赖未安装时的骨架导入
    engine = None
    SessionLocal = None


def get_db() -> Generator[Session, None, None]:
    """提供数据库会话依赖。"""
    if SessionLocal is None:
        raise RuntimeError("当前环境未安装 SQLAlchemy，请先执行依赖安装后再连接数据库。")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
