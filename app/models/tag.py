
"""标签 ORM。"""

from __future__ import annotations

from app.core.sqlalchemy_compat import BigInteger, Integer, String, Mapped, mapped_column

from app.models.base import AuditMixin, Base, SoftDeleteMixin


class Tag(Base, AuditMixin, SoftDeleteMixin):
    """标签表。

    现网 `md_tag` 只有最核心的标签字段，没有 `user_id / display_flag`。
    为了兼容旧服务层与前端响应，这里保留同名属性，但不再映射到数据库列。
    """

    __tablename__ = 'md_tag'

    tag_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    order_value: Mapped[int | None] = mapped_column(Integer, nullable=True)

    @property
    def user_id(self) -> None:
        """兼容旧响应字段；真实表当前没有 user_id。"""
        return None

    @user_id.setter
    def user_id(self, value: int | None) -> None:
        """兼容旧写法，忽略不存在的 user_id。"""
        return None

    @property
    def display_flag(self) -> int:
        """兼容旧响应字段；真实表当前没有 display_flag。"""
        return int(getattr(self, '_display_flag_cache', 1))

    @display_flag.setter
    def display_flag(self, value: int | None) -> None:
        """兼容旧写法，仅缓存响应值，不写数据库。"""
        self._display_flag_cache = 1 if value in (None, '') else int(value)
