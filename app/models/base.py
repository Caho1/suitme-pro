
"""ORM 基础模型。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


class AuditMixin:
    """审计字段混入。

    注意：这里只放通用字段，不代表已经完整覆盖了现网所有列。
    真正迁移前仍要用 `scripts/inspect_db.py` 对真实数据库做快照。
    """

    create_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    create_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, server_default=func.now())
    update_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    update_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, onupdate=func.now())


class SoftDeleteMixin:
    """软删除字段混入。"""

    del_flag: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
