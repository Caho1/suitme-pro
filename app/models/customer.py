
"""顾客 ORM。"""

from __future__ import annotations

from app.core.sqlalchemy_compat import BigInteger, String, Mapped, mapped_column

from app.models.base import AuditMixin, Base, SoftDeleteMixin


class Customer(Base, AuditMixin, SoftDeleteMixin):
    """顾客表。

    注意：这里只放当前已明确的核心字段，后续要再根据真实表结构补齐。
    """

    __tablename__ = 't_customer'

    customer_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    picture_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    digital_task_id: Mapped[str | None] = mapped_column('task_id', String(100), nullable=True)
    digital_img_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    @property
    def user_id(self) -> None:
        """兼容旧服务层字段；真实表当前没有 user_id。"""
        return None

    @property
    def body_profile_json(self) -> None:
        """兼容旧服务层字段；真实表当前没有 body_profile_json。"""
        return None
