
"""搭配相关 ORM 占位文件。"""

from __future__ import annotations

from sqlalchemy import BigInteger, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AuditMixin, Base, SoftDeleteMixin


class Matching(Base, AuditMixin, SoftDeleteMixin):
    """搭配主表占位模型。"""

    __tablename__ = 't_matching'

    matching_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tag_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)


class MatchingSku(Base, AuditMixin, SoftDeleteMixin):
    """搭配 SKU 明细占位模型。"""

    __tablename__ = 't_matching_sku'

    matching_sku_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    matching_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    product_color_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    angle: Mapped[str | None] = mapped_column(String(20), nullable=True)


class MatchingTag(Base, AuditMixin, SoftDeleteMixin):
    """搭配标签占位模型。"""

    __tablename__ = 't_matching_tag'

    matching_tag_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    display_flag: Mapped[int | None] = mapped_column(Integer, nullable=True)
