"""鉴权服务。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import Request
try:
    from sqlalchemy import text
    from sqlalchemy.exc import SQLAlchemyError
except Exception:  # pragma: no cover - 仅用于依赖未安装时的骨架导入
    def text(sql: str) -> str:
        return sql

    class SQLAlchemyError(Exception):
        """最小化占位数据库异常。"""


from app.core.database import session_scope
from app.core.deps import CurrentUser
from app.core.response import captcha_disabled, error, success
from app.core.security import create_access_token, hash_password, verify_password
from app.services.base import SkeletonService
from app.services.category_service import CategoryService


class AuthService(SkeletonService):
    """鉴权相关业务。

    这一版先把最关键、最常用的鉴权链路落地：
    - `/login`
    - `/register`
    - `/captchaImage`
    - `/getInfo`
    - `/logout`

    由于当前仓库是迁移中的基础工程，这里优先保证：
    1. 返回结构兼容若依；
    2. 密码校验兼容 BCrypt；
    3. 能直接连接现有 `sys_user/sys_role/sys_menu` 表工作。
    """

    def __init__(self) -> None:
        """初始化依赖服务。"""
        self.category_service = CategoryService()

    async def login(self, request: Request | None = None, **kwargs: Any) -> dict[str, Any]:
        """登录接口。

        入参兼容若依默认结构：
        - username
        - password
        - code
        - uuid

        当前按 PRD 约定不校验验证码，因此只读取用户名和密码。
        """
        if request is None:
            return error(msg='请求对象不能为空')

        body = await request.json()
        username = str(body.get('username') or body.get('userName') or '').strip()
        password = str(body.get('password') or '').strip()
        if not username or not password:
            return error(msg='用户名或密码不能为空')

        try:
            with session_scope() as db:
                user = self._load_user_for_login(db=db, username=username)
                if user is None:
                    return error(msg='登录用户不存在')
                if str(user.get('del_flag', '0')) not in {'0', 'False', 'false', ''}:
                    return error(msg='登录用户已被删除')
                if str(user.get('status', '0')) == '1':
                    return error(msg='对不起，您的账号已停用')
                hashed_password = str(user.get('password') or '')
                if not hashed_password or not verify_password(password, hashed_password):
                    return error(msg='用户名或密码错误')

                roles = self._load_role_keys(db=db, user_id=int(user['user_id']), user_name=str(user.get('user_name') or username))
                permissions = self._load_permissions(db=db, user_id=int(user['user_id']))
                token = create_access_token(
                    {
                        'userId': int(user['user_id']),
                        'userName': str(user.get('user_name') or username),
                        'roles': roles,
                        'permissions': permissions,
                    }
                )
                self._touch_login_state(db=db, user_id=int(user['user_id']), client_ip=self._client_ip(request))
                return success(msg='操作成功', token=token)
        except SQLAlchemyError as exc:
            return error(msg=f'数据库访问失败: {exc}')

    async def register(self, request: Request | None = None, **kwargs: Any) -> dict[str, Any]:
        """注册接口。

        这里优先兼容若依风格的注册体，并在成功后初始化默认服装分类树。
        当前只做最小必要校验，不额外加复杂兜底。
        """
        if request is None:
            return error(msg='请求对象不能为空')

        body = await request.json()
        username = str(body.get('username') or body.get('userName') or '').strip()
        password = str(body.get('password') or '').strip()
        nick_name = str(body.get('nickName') or username).strip()
        phone = str(body.get('phonenumber') or body.get('phoneNumber') or '').strip()
        email = str(body.get('email') or '').strip()
        if not username or not password:
            return error(msg='用户名或密码不能为空')

        try:
            with session_scope() as db:
                exists = db.execute(
                    text('SELECT user_id FROM sys_user WHERE user_name = :username LIMIT 1'),
                    {'username': username},
                ).mappings().first()
                if exists is not None:
                    return error(msg='保存用户失败，注册账号已存在')

                db.execute(
                    text(
                        '''
                        INSERT INTO sys_user (
                            user_name, nick_name, email, phonenumber, password,
                            status, del_flag, create_by, create_time, update_by, update_time
                        ) VALUES (
                            :user_name, :nick_name, :email, :phonenumber, :password,
                            '0', '0', :create_by, NOW(), :update_by, NOW()
                        )
                        '''
                    ),
                    {
                        'user_name': username,
                        'nick_name': nick_name,
                        'email': email or None,
                        'phonenumber': phone or None,
                        'password': hash_password(password),
                        'create_by': username,
                        'update_by': username,
                    },
                )
                new_user = db.execute(
                    text('SELECT user_id FROM sys_user WHERE user_name = :username LIMIT 1'),
                    {'username': username},
                ).mappings().first()
                if new_user is None:
                    return error(msg='注册失败')

                # 注册成功后，按照当前 PRD 约定初始化默认服装分类树。
                await self.category_service.init_default_categories(
                    user_id=int(new_user['user_id']),
                    operator=username,
                    db=db,
                )
                return success(msg='注册成功')
        except SQLAlchemyError as exc:
            return error(msg=f'数据库访问失败: {exc}')

    async def captcha_image(self, request: Request | None = None, **kwargs: Any) -> dict[str, Any]:
        """返回关闭验证码的兼容结构。"""
        return captcha_disabled()

    async def get_info(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """获取当前登录用户信息。"""
        if current_user is None or current_user.user_id is None:
            return error(msg='认证失败', code=401)

        try:
            with session_scope() as db:
                row = db.execute(
                    text(
                        '''
                        SELECT user_id, dept_id, user_name, nick_name, email, phonenumber,
                               sex, avatar, status, login_ip, login_date, create_by,
                               create_time, update_by, update_time, remark
                        FROM sys_user
                        WHERE user_id = :user_id
                        LIMIT 1
                        '''
                    ),
                    {'user_id': current_user.user_id},
                ).mappings().first()
                if row is None:
                    return error(msg='用户不存在', code=401)

                roles = self._load_role_keys(
                    db=db,
                    user_id=current_user.user_id,
                    user_name=str(row.get('user_name') or current_user.user_name or ''),
                )
                permissions = self._load_permissions(db=db, user_id=current_user.user_id)
                user = self._serialize_user(row)
                return success(
                    msg='操作成功',
                    user=user,
                    roles=roles,
                    permissions=permissions,
                    isDefaultModifyPwd=False,
                    isPasswordExpired=False,
                )
        except SQLAlchemyError as exc:
            return error(msg=f'数据库访问失败: {exc}')

    async def logout(
        self,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """退出登录兼容端点。

        纯 JWT 模式下没有服务端会话状态，因此直接返回成功即可。
        """
        return success(msg='退出成功')

    def _load_user_for_login(self, db: Any, username: str) -> dict[str, Any] | None:
        """按用户名读取登录用户。

        这里不依赖 ORM 字段完整性，直接使用 SQL 文本读取标准若依字段。
        """
        row = db.execute(
            text(
                '''
                SELECT user_id, user_name, password, status, del_flag
                FROM sys_user
                WHERE user_name = :username
                LIMIT 1
                '''
            ),
            {'username': username},
        ).mappings().first()
        return dict(row) if row is not None else None

    def _load_role_keys(self, db: Any, user_id: int, user_name: str) -> list[str]:
        """读取当前用户角色键列表。"""
        rows = db.execute(
            text(
                '''
                SELECT DISTINCT r.role_key
                FROM sys_role r
                JOIN sys_user_role ur ON ur.role_id = r.role_id
                WHERE ur.user_id = :user_id
                  AND r.status = '0'
                  AND r.del_flag = '0'
                ORDER BY r.role_id
                '''
            ),
            {'user_id': user_id},
        ).mappings().all()
        roles = [str(row['role_key']) for row in rows if row.get('role_key')]
        if user_name == 'admin' and 'admin' not in roles:
            roles.insert(0, 'admin')
        return roles

    def _load_permissions(self, db: Any, user_id: int) -> list[str]:
        """读取当前用户权限标识列表。"""
        rows = db.execute(
            text(
                '''
                SELECT DISTINCT m.perms
                FROM sys_menu m
                JOIN sys_role_menu rm ON rm.menu_id = m.menu_id
                JOIN sys_user_role ur ON ur.role_id = rm.role_id
                JOIN sys_role r ON r.role_id = ur.role_id
                WHERE ur.user_id = :user_id
                  AND COALESCE(m.perms, '') <> ''
                  AND m.status = '0'
                  AND r.status = '0'
                  AND r.del_flag = '0'
                ORDER BY m.menu_id
                '''
            ),
            {'user_id': user_id},
        ).mappings().all()
        return [str(row['perms']) for row in rows if row.get('perms')]

    def _touch_login_state(self, db: Any, user_id: int, client_ip: str | None) -> None:
        """更新最近登录信息。"""
        db.execute(
            text(
                '''
                UPDATE sys_user
                SET login_ip = :login_ip,
                    login_date = :login_date,
                    update_time = :login_date
                WHERE user_id = :user_id
                '''
            ),
            {
                'login_ip': client_ip,
                'login_date': datetime.now(),
                'user_id': user_id,
            },
        )

    def _serialize_user(self, row: Any) -> dict[str, Any]:
        """把数据库行转换为前端可直接消费的用户对象。"""
        data = dict(row)
        for field_name in ('login_date', 'create_time', 'update_time'):
            value = data.get(field_name)
            if hasattr(value, 'strftime'):
                data[field_name] = value.strftime('%Y-%m-%d %H:%M:%S')
        return data

    def _client_ip(self, request: Request | None) -> str | None:
        """解析客户端 IP。"""
        if request is None or request.client is None:
            return None
        return request.client.host
