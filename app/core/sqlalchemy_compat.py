"""SQLAlchemy 兼容层。"""

from __future__ import annotations

from typing import Any

try:
    from sqlalchemy import BigInteger, DateTime, Integer, String, Text, create_engine, delete, exists, func, or_, select
    from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

    SA_AVAILABLE = True
except Exception:
    SA_AVAILABLE = False

    class _DummyExpr:
        """最小可链式占位对象。"""

        def __call__(self, *args: Any, **kwargs: Any) -> '_DummyExpr':
            return self

        def __getattr__(self, name: str) -> '_DummyExpr':
            return self

        def where(self, *args: Any, **kwargs: Any) -> '_DummyExpr':
            return self

        def order_by(self, *args: Any, **kwargs: Any) -> '_DummyExpr':
            return self

        def offset(self, *args: Any, **kwargs: Any) -> '_DummyExpr':
            return self

        def limit(self, *args: Any, **kwargs: Any) -> '_DummyExpr':
            return self

        def join(self, *args: Any, **kwargs: Any) -> '_DummyExpr':
            return self

        def select_from(self, *args: Any, **kwargs: Any) -> '_DummyExpr':
            return self

        def subquery(self, *args: Any, **kwargs: Any) -> '_DummyExpr':
            return self

        def in_(self, *args: Any, **kwargs: Any) -> '_DummyExpr':
            return self

        def not_in(self, *args: Any, **kwargs: Any) -> '_DummyExpr':
            return self

        def like(self, *args: Any, **kwargs: Any) -> '_DummyExpr':
            return self

        def is_not(self, *args: Any, **kwargs: Any) -> '_DummyExpr':
            return self

        def asc(self) -> '_DummyExpr':
            return self

        def desc(self) -> '_DummyExpr':
            return self

    def select(*args: Any, **kwargs: Any) -> _DummyExpr:
        return _DummyExpr()

    def delete(*args: Any, **kwargs: Any) -> _DummyExpr:
        return _DummyExpr()

    def exists(*args: Any, **kwargs: Any) -> _DummyExpr:
        return _DummyExpr()

    def or_(*args: Any, **kwargs: Any) -> _DummyExpr:
        return _DummyExpr()

    class _Func(_DummyExpr):
        pass

    func = _Func()

    class BigInteger:
        pass

    class DateTime:
        pass

    class Integer:
        pass

    class String:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

    class Text:
        pass

    class Session:
        """占位 Session。"""

        def close(self) -> None:
            return None

        def scalar(self, *args: Any, **kwargs: Any) -> Any:
            raise RuntimeError('当前环境未安装 SQLAlchemy，无法执行数据库查询。')

        def scalars(self, *args: Any, **kwargs: Any) -> Any:
            raise RuntimeError('当前环境未安装 SQLAlchemy，无法执行数据库查询。')

        def execute(self, *args: Any, **kwargs: Any) -> Any:
            raise RuntimeError('当前环境未安装 SQLAlchemy，无法执行数据库查询。')

        def add(self, *args: Any, **kwargs: Any) -> None:
            raise RuntimeError('当前环境未安装 SQLAlchemy，无法执行数据库写入。')

        def commit(self) -> None:
            raise RuntimeError('当前环境未安装 SQLAlchemy，无法执行数据库写入。')

        def flush(self) -> None:
            raise RuntimeError('当前环境未安装 SQLAlchemy，无法执行数据库写入。')

        def refresh(self, *args: Any, **kwargs: Any) -> None:
            raise RuntimeError('当前环境未安装 SQLAlchemy，无法执行数据库刷新。')

        def rollback(self) -> None:
            raise RuntimeError('当前环境未安装 SQLAlchemy，无法执行数据库回滚。')

        def get(self, *args: Any, **kwargs: Any) -> Any:
            raise RuntimeError('当前环境未安装 SQLAlchemy，无法执行数据库查询。')

    class _SessionFactory:
        def __call__(self, *args: Any, **kwargs: Any) -> Session:
            return Session()

    def sessionmaker(*args: Any, **kwargs: Any) -> _SessionFactory:
        return _SessionFactory()

    def create_engine(*args: Any, **kwargs: Any) -> object:
        return object()

    class DeclarativeBase:
        pass

    class Mapped:
        def __class_getitem__(cls, item: Any) -> Any:
            return Any

    def mapped_column(*args: Any, **kwargs: Any) -> Any:
        return None
