"""系统管理相关 ORM。"""

from __future__ import annotations

from datetime import datetime

from app.core.sqlalchemy_compat import BigInteger, DateTime, Integer, String, Mapped, mapped_column

from app.models.base import AuditMixin, Base, SoftDeleteMixin


class SysUser(Base, AuditMixin, SoftDeleteMixin):
    """系统用户表。"""

    __tablename__ = 'sys_user'

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    dept_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    user_name: Mapped[str] = mapped_column(String(30), nullable=False)
    nick_name: Mapped[str | None] = mapped_column(String(30), nullable=True)
    user_type: Mapped[str | None] = mapped_column(String(2), nullable=True)
    email: Mapped[str | None] = mapped_column(String(50), nullable=True)
    phonenumber: Mapped[str | None] = mapped_column(String(11), nullable=True)
    sex: Mapped[str | None] = mapped_column(String(1), nullable=True)
    avatar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str | None] = mapped_column(String(1), nullable=True, default='0')
    login_ip: Mapped[str | None] = mapped_column(String(128), nullable=True)
    login_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    pwd_update_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    remark: Mapped[str | None] = mapped_column(String(500), nullable=True)


class SysRole(Base, AuditMixin, SoftDeleteMixin):
    """系统角色表。"""

    __tablename__ = 'sys_role'

    role_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    role_name: Mapped[str] = mapped_column(String(30), nullable=False)
    role_key: Mapped[str] = mapped_column(String(100), nullable=False)
    role_sort: Mapped[int | None] = mapped_column(Integer, nullable=True)
    data_scope: Mapped[str | None] = mapped_column(String(1), nullable=True)
    menu_check_strictly: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dept_check_strictly: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str | None] = mapped_column(String(1), nullable=True, default='0')
    remark: Mapped[str | None] = mapped_column(String(500), nullable=True)


class SysMenu(Base, AuditMixin, SoftDeleteMixin):
    """系统菜单表。"""

    __tablename__ = 'sys_menu'

    menu_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    menu_name: Mapped[str] = mapped_column(String(50), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    order_num: Mapped[int | None] = mapped_column(Integer, nullable=True)
    path: Mapped[str | None] = mapped_column(String(200), nullable=True)
    component: Mapped[str | None] = mapped_column(String(255), nullable=True)
    query: Mapped[str | None] = mapped_column(String(255), nullable=True)
    route_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_frame: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_cache: Mapped[int | None] = mapped_column(Integer, nullable=True)
    menu_type: Mapped[str | None] = mapped_column(String(1), nullable=True)
    visible: Mapped[str | None] = mapped_column(String(1), nullable=True)
    status: Mapped[str | None] = mapped_column(String(1), nullable=True)
    perms: Mapped[str | None] = mapped_column(String(100), nullable=True)
    icon: Mapped[str | None] = mapped_column(String(100), nullable=True)
    remark: Mapped[str | None] = mapped_column(String(500), nullable=True)


class SysUserRole(Base):
    """用户角色关联表。"""

    __tablename__ = 'sys_user_role'

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    role_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)


class SysRoleMenu(Base):
    """角色菜单关联表。"""

    __tablename__ = 'sys_role_menu'

    role_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    menu_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
