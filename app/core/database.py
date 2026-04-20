"""数据库连接模块。"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from app.core.config import get_settings
from app.core.sqlalchemy_compat import Session, create_engine, sessionmaker


settings = get_settings()

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


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """提供一个可复用的数据库会话上下文。

    这个工具主要给脚本、离线任务或单元测试使用；
    FastAPI 路由里仍然优先走 `get_db` 依赖。
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db() -> Generator[Session, None, None]:
    """提供数据库会话依赖。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
