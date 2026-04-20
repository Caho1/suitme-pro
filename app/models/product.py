
"""主数据 ORM。"""

from __future__ import annotations

from sqlalchemy import BigInteger, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AuditMixin, Base, SoftDeleteMixin


class Product(Base, AuditMixin, SoftDeleteMixin):
    """服装主数据。"""

    __tablename__ = 'md_product'

    product_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    picture_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    display_flag: Mapped[int | None] = mapped_column(Integer, nullable=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)


class ProductColor(Base, AuditMixin, SoftDeleteMixin):
    """服装颜色 SKU。"""

    __tablename__ = 'md_product_color'

    product_color_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    product_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    color_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
