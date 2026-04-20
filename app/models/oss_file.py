
"""OSS 文件元数据 ORM。"""

from __future__ import annotations

from app.core.sqlalchemy_compat import BigInteger, String, Text, Mapped, mapped_column

from app.models.base import AuditMixin, Base


class OssFile(Base, AuditMixin):
    """OSS 文件元数据表。"""

    __tablename__ = 'oss_file'

    file_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    original_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    object_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    etag: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
