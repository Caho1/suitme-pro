
"""主数据 ORM。"""

from __future__ import annotations

from app.core.sqlalchemy_compat import BigInteger, Integer, String, Mapped, mapped_column

from app.models.base import AuditMixin, Base, SoftDeleteMixin


class Product(Base, AuditMixin, SoftDeleteMixin):
    """服装主数据。

    这里按 Java 原项目 `md_product` 的真实字段映射；旧迁移占位字段通过属性保留，
    避免服务层或前端响应里仍使用旧字段名时直接报错。
    """

    __tablename__ = 'md_product'

    product_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str | None] = mapped_column(String(30), nullable=True)
    category_tag_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    scene_tag_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    style_tag_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    material_tag_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    display_flag: Mapped[int | None] = mapped_column(Integer, nullable=True)

    @property
    def user_id(self) -> None:
        """兼容旧响应字段；真实表当前没有 user_id。"""
        return None

    @user_id.setter
    def user_id(self, value: int | None) -> None:
        """兼容旧写法，忽略不存在的 user_id。"""
        return None

    @property
    def picture_url(self) -> str | None:
        """兼容旧响应字段，默认取第一个颜色图时由服务层补齐。"""
        return None

    @picture_url.setter
    def picture_url(self, value: str | None) -> None:
        """兼容旧写法，忽略不存在的 picture_url。"""
        return None

    @property
    def remark(self) -> None:
        """兼容旧响应字段；真实表当前没有 remark。"""
        return None

    @remark.setter
    def remark(self, value: str | None) -> None:
        """兼容旧写法，忽略不存在的 remark。"""
        return None


class ProductColor(Base, AuditMixin, SoftDeleteMixin):
    """服装颜色 SKU。"""

    __tablename__ = 'md_product_color'

    product_color_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    product_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    color_name: Mapped[str | None] = mapped_column('name', String(30), nullable=True)
    front_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    side_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    back_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    @property
    def image_url(self) -> str | None:
        """兼容旧字段名，默认使用正面图片。"""
        return self.front_image_url

    @image_url.setter
    def image_url(self, value: str | None) -> None:
        """兼容旧写法，实际写入正面图片字段。"""
        self.front_image_url = value
