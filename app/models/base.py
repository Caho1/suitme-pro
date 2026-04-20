"""ORM 基础模型。"""

from __future__ import annotations

from datetime import datetime

from app.core.sqlalchemy_compat import DateTime, String, func, DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


class AuditMixin:
    """审计字段混入。"""

    create_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    create_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, server_default=func.now())
    update_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    update_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, onupdate=func.now())


class SoftDeleteMixin:
    """软删除字段混入。"""

    del_flag: Mapped[str] = mapped_column(String(1), default='0', nullable=False)
