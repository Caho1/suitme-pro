
"""搭配相关 ORM。"""

from __future__ import annotations

from app.core.sqlalchemy_compat import BigInteger, Integer, String, Mapped, mapped_column

from app.models.base import AuditMixin, Base, SoftDeleteMixin


class Matching(Base, AuditMixin, SoftDeleteMixin):
    """搭配主表。

    线上真实表当前没有 user_id、tag_id、remark 字段；服务层保留兼容响应字段，
    但 ORM 只映射真实存在的列，避免查询时选到不存在的字段。
    """

    __tablename__ = 't_matching'

    matching_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str | None] = mapped_column(String(30), nullable=True)
    matching_tag_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    @property
    def user_id(self) -> None:
        """兼容旧响应字段；真实表当前没有 user_id。"""
        return None

    @property
    def tag_id(self) -> int | None:
        """兼容旧字段名，把 tag_id 映射到真实的 matching_tag_id。"""
        return self.matching_tag_id

    @tag_id.setter
    def tag_id(self, value: int | None) -> None:
        """兼容旧写法，实际写入 matching_tag_id。"""
        self.matching_tag_id = value

    @property
    def remark(self) -> None:
        """兼容旧响应字段；真实表当前没有 remark。"""
        return None


class MatchingSku(Base, AuditMixin, SoftDeleteMixin):
    """搭配 SKU 明细。"""

    __tablename__ = 't_matching_sku'

    matching_sku_id: Mapped[int] = mapped_column('id', BigInteger, primary_key=True)
    matching_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    product_color_id: Mapped[int | None] = mapped_column('color_id', BigInteger, nullable=True)
    product_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    @property
    def angle(self) -> None:
        """兼容旧响应字段；真实表当前没有 angle。"""
        return None


class MatchingTag(Base, AuditMixin, SoftDeleteMixin):
    """搭配标签。"""

    __tablename__ = 't_matching_tag'

    matching_tag_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str | None] = mapped_column(String(30), nullable=True)
    display_flag: Mapped[int | None] = mapped_column(Integer, nullable=True)

    @property
    def user_id(self) -> None:
        """兼容旧响应字段；真实表当前没有 user_id。"""
        return None
