
"""服装分类树 ORM。"""

from __future__ import annotations

from app.core.sqlalchemy_compat import BigInteger, Integer, String, Mapped, mapped_column

from app.models.base import AuditMixin, Base, SoftDeleteMixin


class ClothingCategory(Base, AuditMixin, SoftDeleteMixin):
    """服装分类树。

    当前结构为最小占位，后续请以真实数据库字段为准。
    """

    __tablename__ = 'clothing_category'

    category_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    parent_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    order_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    default_flag: Mapped[int | None] = mapped_column(Integer, nullable=True)
    editable_flag: Mapped[int | None] = mapped_column(Integer, nullable=True)
