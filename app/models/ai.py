
"""AI 任务相关 ORM 占位文件。"""

from __future__ import annotations

from app.core.sqlalchemy_compat import BigInteger, Integer, String, Mapped, mapped_column

from app.models.base import AuditMixin, Base, SoftDeleteMixin


class AiJoin(Base, AuditMixin, SoftDeleteMixin):
    """生图批次关联表占位模型。"""

    __tablename__ = 'ai_join'

    join_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    customer_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    matching_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str | None] = mapped_column(String(32), nullable=True)


class AiOutfit(Base, AuditMixin, SoftDeleteMixin):
    """生图搭配明细表占位模型。"""

    __tablename__ = 'ai_outfit'

    outfit_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    join_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    angle: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str | None] = mapped_column(String(32), nullable=True)


class AiTask(Base, AuditMixin, SoftDeleteMixin):
    """生图任务表占位模型。"""

    __tablename__ = 'ai_task'

    task_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    join_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    angle: Mapped[str | None] = mapped_column(String(20), nullable=True)
    task_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
