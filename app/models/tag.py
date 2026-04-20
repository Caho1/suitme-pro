
"""标签 ORM。"""

from __future__ import annotations

from app.core.sqlalchemy_compat import BigInteger, Integer, String, Mapped, mapped_column

from app.models.base import AuditMixin, Base, SoftDeleteMixin


class Tag(Base, AuditMixin, SoftDeleteMixin):
    """标签表。"""

    __tablename__ = 'md_tag'

    tag_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    order_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    display_flag: Mapped[int | None] = mapped_column(Integer, nullable=True)
