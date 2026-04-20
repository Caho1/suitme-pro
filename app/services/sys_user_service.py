"""系统用户服务。"""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Any

from fastapi import Request
from fastapi.responses import StreamingResponse
try:
    from sqlalchemy import text
except Exception:  # pragma: no cover - 仅用于依赖未安装时的导入兼容
    def text(sql: str) -> str:
        return sql


from app.core.deps import CurrentUser
from app.core.request_utils import collect_params, get_int, read_json_body, split_to_int_list
from app.core.response import error, success, table_data, to_ajax
from app.core.security import hash_password, verify_password
from app.services.base import SkeletonService
from app.services.common_service import CommonService
from app.services.sys_support import (
    build_excel_bytes,
    get_role_ids_by_user,
    is_admin_user,
    load_all_roles,
    mapping_to_dict,
    next_table_id,
    sync_user_roles,
)


class SysUserService(SkeletonService):
    """系统用户服务。

    这一版优先完成若依最常用的用户管理能力：
    - 用户列表、详情、新增、修改、删除
    - 启停、重置密码
    - 个人资料、修改密码、头像上传
    - 分配角色、导出 Excel
    """

    def __init__(self) -> None:
        """初始化依赖服务。"""
        self.common_service = CommonService()

    def _serialize_user(self, row: Any) -> dict[str, Any]:
        """把用户查询结果转换成前端可直接消费的结构。"""
        data = mapping_to_dict(row)
        if 'user_id' in data:
            data['userId'] = data.pop('user_id')
        if 'dept_id' in data:
            data['deptId'] = data.pop('dept_id')
        if 'user_name' in data:
            data['userName'] = data.pop('user_name')
        if 'nick_name' in data:
            data['nickName'] = data.pop('nick_name')
        if 'user_type' in data:
            data['userType'] = data.pop('user_type')
        if 'phoneNumber' not in data and 'phonenumber' in data:
            data['phonenumber'] = data.get('phonenumber')
        if 'login_ip' in data:
            data['loginIp'] = data.pop('login_ip')
        if 'login_date' in data:
            data['loginDate'] = data.pop('login_date')
        if 'pwd_update_date' in data:
            data['pwdUpdateDate'] = data.pop('pwd_update_date')
        if 'create_by' in data:
            data['createBy'] = data.pop('create_by')
        if 'create_time' in data:
            data['createTime'] = data.pop('create_time')
        if 'update_by' in data:
            data['updateBy'] = data.pop('update_by')
        if 'update_time' in data:
            data['updateTime'] = data.pop('update_time')
        if 'del_flag' in data:
            data['delFlag'] = data.pop('del_flag')
        return data

    def _query_user_list(self, db: Any, params: dict[str, Any], include_paging: bool = True) -> tuple[list[dict[str, Any]], int]:
        """按若依查询参数读取用户列表。"""
        where = ["u.del_flag = '0'"]
        query_params: dict[str, Any] = {}
        user_name = str(params.get('userName') or '').strip()
        if user_name:
            where.append('u.user_name LIKE :user_name')
            query_params['user_name'] = f'%{user_name}%'
        phone = str(params.get('phonenumber') or '').strip()
        if phone:
            where.append('u.phonenumber LIKE :phonenumber')
            query_params['phonenumber'] = f'%{phone}%'
        status = str(params.get('status') or '').strip()
        if status != '':
            where.append('u.status = :status')
            query_params['status'] = status
        begin_time = str(params.get('beginTime') or '').strip()
        if begin_time:
            where.append('u.create_time >= :begin_time')
            query_params['begin_time'] = begin_time
        end_time = str(params.get('endTime') or '').strip()
        if end_time:
            where.append('u.create_time <= :end_time')
            query_params['end_time'] = end_time

        where_sql = ' AND '.join(where)
        total = int(
            db.execute(text(f'SELECT COUNT(1) FROM sys_user u WHERE {where_sql}'), query_params).scalar() or 0
        )

        limit_sql = ''
        if include_paging:
            page_num = max(1, get_int(params.get('pageNum'), 1))
            page_size = max(1, get_int(params.get('pageSize'), 10))
            offset = (page_num - 1) * page_size
            limit_sql = ' LIMIT :offset, :page_size'
            query_params['offset'] = offset
            query_params['page_size'] = page_size

        rows = db.execute(
            text(
                f'''
                SELECT u.user_id, u.dept_id, u.user_name, u.nick_name, u.user_type,
                       u.email, u.phonenumber, u.sex, u.avatar, u.status,
                       u.login_ip, u.login_date, u.create_by, u.create_time,
                       u.update_by, u.update_time, u.remark, u.del_flag
                FROM sys_user u
                WHERE {where_sql}
                ORDER BY u.user_id DESC
                {limit_sql}
                '''
            ),
            query_params,
        ).mappings().all()
        return [self._serialize_user(row) for row in rows], total

    def _load_user_detail(self, db: Any, user_id: int) -> dict[str, Any] | None:
        """读取单个用户详情。"""
        row = db.execute(
            text(
                '''
                SELECT u.user_id, u.dept_id, u.user_name, u.nick_name, u.user_type,
                       u.email, u.phonenumber, u.sex, u.avatar, u.password,
                       u.status, u.login_ip, u.login_date, u.pwd_update_date,
                       u.create_by, u.create_time, u.update_by, u.update_time,
                       u.remark, u.del_flag
                FROM sys_user u
                WHERE u.user_id = :user_id AND u.del_flag = '0'
                LIMIT 1
                '''
            ),
            {'user_id': user_id},
        ).mappings().first()
        if row is None:
            return None
        return self._serialize_user(row)

    def _username_exists(self, db: Any, user_name: str, exclude_user_id: int | None = None) -> bool:
        """校验用户名是否已存在。"""
        sql = 'SELECT 1 FROM sys_user WHERE user_name = :user_name AND del_flag = \'0\''
        params: dict[str, Any] = {'user_name': user_name}
        if exclude_user_id is not None:
            sql += ' AND user_id <> :user_id'
            params['user_id'] = exclude_user_id
        sql += ' LIMIT 1'
        return db.execute(text(sql), params).first() is not None

    def _phone_exists(self, db: Any, phone: str, exclude_user_id: int | None = None) -> bool:
        """校验手机号是否已存在。"""
        if not phone:
            return False
        sql = 'SELECT 1 FROM sys_user WHERE phonenumber = :phone AND del_flag = \'0\''
        params: dict[str, Any] = {'phone': phone}
        if exclude_user_id is not None:
            sql += ' AND user_id <> :user_id'
            params['user_id'] = exclude_user_id
        sql += ' LIMIT 1'
        return db.execute(text(sql), params).first() is not None

    def _email_exists(self, db: Any, email: str, exclude_user_id: int | None = None) -> bool:
        """校验邮箱是否已存在。"""
        if not email:
            return False
        sql = 'SELECT 1 FROM sys_user WHERE email = :email AND del_flag = \'0\''
        params: dict[str, Any] = {'email': email}
        if exclude_user_id is not None:
            sql += ' AND user_id <> :user_id'
            params['user_id'] = exclude_user_id
        sql += ' LIMIT 1'
        return db.execute(text(sql), params).first() is not None

    async def profile_get(
        self,
        db: Any,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """获取当前登录用户个人资料。"""
        if current_user is None or current_user.user_id is None:
            return error(msg='认证失败', code=401)
        user = self._load_user_detail(db, current_user.user_id)
        if user is None:
            return error('用户不存在')
        role_rows = db.execute(
            text(
                '''
                SELECT r.role_name
                FROM sys_role r
                JOIN sys_user_role ur ON ur.role_id = r.role_id
                WHERE ur.user_id = :user_id AND r.del_flag = '0'
                ORDER BY r.role_sort ASC, r.role_id ASC
                '''
            ),
            {'user_id': current_user.user_id},
        ).mappings().all()
        role_group = ','.join(str(row['role_name']) for row in role_rows if row.get('role_name'))
        return success(data=user, roleGroup=role_group, postGroup='')

    async def profile_update(
        self,
        db: Any,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """修改当前登录用户个人资料。"""
        if current_user is None or current_user.user_id is None:
            return error(msg='认证失败', code=401)
        payload = await read_json_body(request) if request is not None else {}
        email = str(payload.get('email') or '').strip()
        phone = str(payload.get('phonenumber') or '').strip()
        if email and self._email_exists(db, email, current_user.user_id):
            return error('修改用户失败，邮箱账号已存在')
        if phone and self._phone_exists(db, phone, current_user.user_id):
            return error('修改用户失败，手机号码已存在')
        db.execute(
            text(
                '''
                UPDATE sys_user
                SET nick_name = :nick_name,
                    email = :email,
                    phonenumber = :phonenumber,
                    sex = :sex,
                    remark = :remark,
                    update_by = :update_by,
                    update_time = :update_time
                WHERE user_id = :user_id AND del_flag = '0'
                '''
            ),
            {
                'nick_name': str(payload.get('nickName') or '').strip() or None,
                'email': email or None,
                'phonenumber': phone or None,
                'sex': str(payload.get('sex') or '').strip() or None,
                'remark': str(payload.get('remark') or '').strip() or None,
                'update_by': current_user.user_name,
                'update_time': datetime.now(),
                'user_id': current_user.user_id,
            },
        )
        db.commit()
        return success(msg='修改成功')

    async def profile_update_pwd(
        self,
        db: Any,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """修改当前登录用户密码。"""
        if current_user is None or current_user.user_id is None:
            return error(msg='认证失败', code=401)
        payload = await read_json_body(request) if request is not None else {}
        old_password = str(payload.get('oldPassword') or payload.get('oldPwd') or '').strip()
        new_password = str(payload.get('newPassword') or payload.get('password') or '').strip()
        if not old_password or not new_password:
            return error('密码不能为空')
        row = db.execute(
            text('SELECT password FROM sys_user WHERE user_id = :user_id AND del_flag = \'0\' LIMIT 1'),
            {'user_id': current_user.user_id},
        ).mappings().first()
        if row is None or not row.get('password'):
            return error('用户不存在')
        if not verify_password(old_password, str(row['password'])):
            return error('修改密码失败，旧密码错误')
        db.execute(
            text(
                '''
                UPDATE sys_user
                SET password = :password,
                    pwd_update_date = :pwd_update_date,
                    update_by = :update_by,
                    update_time = :update_time
                WHERE user_id = :user_id
                '''
            ),
            {
                'password': hash_password(new_password),
                'pwd_update_date': datetime.now(),
                'update_by': current_user.user_name,
                'update_time': datetime.now(),
                'user_id': current_user.user_id,
            },
        )
        db.commit()
        return success(msg='修改成功')

    async def profile_avatar(
        self,
        db: Any,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """上传当前登录用户头像。"""
        if current_user is None or current_user.user_id is None:
            return error(msg='认证失败', code=401)
        if request is None:
            return error('请求对象不能为空')
        form = await request.form()
        file = form.get('avatarfile') or form.get('file')
        if file is None:
            return error('缺少头像文件')
        result = await self.common_service._save_single_file(file)  # noqa: SLF001 - 迁移期复用公共上传逻辑
        db.execute(
            text(
                '''
                UPDATE sys_user
                SET avatar = :avatar,
                    update_by = :update_by,
                    update_time = :update_time
                WHERE user_id = :user_id AND del_flag = '0'
                '''
            ),
            {
                'avatar': result['url'],
                'update_by': current_user.user_name,
                'update_time': datetime.now(),
                'user_id': current_user.user_id,
            },
        )
        db.commit()
        return success(msg='上传成功', imgUrl=result['url'])

    async def list(
        self,
        db: Any,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """分页查询用户。"""
        params = await collect_params(request) if request is not None else {}
        rows, total = self._query_user_list(db, params, include_paging=True)
        return table_data(rows=rows, total=total)

    async def get(
        self,
        db: Any,
        userId: int,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """查询用户详情，附带角色与岗位兼容字段。"""
        user = self._load_user_detail(db, userId)
        if user is None:
            return error('用户不存在')
        role_ids = get_role_ids_by_user(db, userId)
        roles = load_all_roles(db)
        for role in roles:
            role['flag'] = int(role.get('roleId') or role.get('role_id') or 0) in role_ids
        return success(data=user, roleIds=role_ids, postIds=[], roles=roles, posts=[])

    async def add(
        self,
        db: Any,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """新增用户。"""
        payload = await read_json_body(request) if request is not None else {}
        user_name = str(payload.get('userName') or payload.get('username') or '').strip()
        if not user_name:
            return error('用户名不能为空')
        if self._username_exists(db, user_name):
            return error('新增用户失败，登录账号已存在')
        phone = str(payload.get('phonenumber') or '').strip()
        if self._phone_exists(db, phone):
            return error('新增用户失败，手机号码已存在')
        email = str(payload.get('email') or '').strip()
        if self._email_exists(db, email):
            return error('新增用户失败，邮箱账号已存在')
        user_id = next_table_id(db, 'sys_user', 'user_id')
        operator = getattr(current_user, 'user_name', None) or user_name
        password = str(payload.get('password') or '123456').strip()
        db.execute(
            text(
                '''
                INSERT INTO sys_user (
                    user_id, dept_id, user_name, nick_name, user_type, email, phonenumber,
                    sex, avatar, password, status, del_flag, remark,
                    create_by, create_time, update_by, update_time, pwd_update_date
                ) VALUES (
                    :user_id, :dept_id, :user_name, :nick_name, :user_type, :email, :phonenumber,
                    :sex, :avatar, :password, :status, '0', :remark,
                    :create_by, :create_time, :update_by, :update_time, :pwd_update_date
                )
                '''
            ),
            {
                'user_id': user_id,
                'dept_id': get_int(payload.get('deptId')) or None,
                'user_name': user_name,
                'nick_name': str(payload.get('nickName') or user_name).strip(),
                'user_type': str(payload.get('userType') or '00').strip(),
                'email': email or None,
                'phonenumber': phone or None,
                'sex': str(payload.get('sex') or '').strip() or None,
                'avatar': str(payload.get('avatar') or '').strip() or None,
                'password': hash_password(password),
                'status': str(payload.get('status') or '0').strip() or '0',
                'remark': str(payload.get('remark') or '').strip() or None,
                'create_by': operator,
                'create_time': datetime.now(),
                'update_by': operator,
                'update_time': datetime.now(),
                'pwd_update_date': datetime.now(),
            },
        )
        role_ids = split_to_int_list(payload.get('roleIds') or payload.get('roleId'))
        sync_user_roles(db, user_id, role_ids)
        db.commit()
        return success(msg='新增成功')

    async def update(
        self,
        db: Any,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """修改用户。"""
        payload = await read_json_body(request) if request is not None else {}
        user_id = get_int(payload.get('userId'))
        if user_id <= 0:
            return error('缺少用户编号')
        if current_user is not None and current_user.user_id == user_id and str(payload.get('status') or '0') == '1':
            return error('当前用户不能停用自己')
        user = self._load_user_detail(db, user_id)
        if user is None:
            return error('用户不存在')
        user_name = str(payload.get('userName') or user.get('userName') or '').strip()
        if self._username_exists(db, user_name, user_id):
            return error('修改用户失败，登录账号已存在')
        phone = str(payload.get('phonenumber') or '').strip()
        if self._phone_exists(db, phone, user_id):
            return error('修改用户失败，手机号码已存在')
        email = str(payload.get('email') or '').strip()
        if self._email_exists(db, email, user_id):
            return error('修改用户失败，邮箱账号已存在')
        db.execute(
            text(
                '''
                UPDATE sys_user
                SET dept_id = :dept_id,
                    user_name = :user_name,
                    nick_name = :nick_name,
                    user_type = :user_type,
                    email = :email,
                    phonenumber = :phonenumber,
                    sex = :sex,
                    avatar = :avatar,
                    status = :status,
                    remark = :remark,
                    update_by = :update_by,
                    update_time = :update_time
                WHERE user_id = :user_id AND del_flag = '0'
                '''
            ),
            {
                'dept_id': get_int(payload.get('deptId')) or None,
                'user_name': user_name,
                'nick_name': str(payload.get('nickName') or '').strip() or None,
                'user_type': str(payload.get('userType') or '00').strip() or '00',
                'email': email or None,
                'phonenumber': phone or None,
                'sex': str(payload.get('sex') or '').strip() or None,
                'avatar': str(payload.get('avatar') or '').strip() or None,
                'status': str(payload.get('status') or '0').strip() or '0',
                'remark': str(payload.get('remark') or '').strip() or None,
                'update_by': getattr(current_user, 'user_name', None) or user_name,
                'update_time': datetime.now(),
                'user_id': user_id,
            },
        )
        role_ids = split_to_int_list(payload.get('roleIds') or payload.get('roleId'))
        sync_user_roles(db, user_id, role_ids)
        db.commit()
        return success(msg='修改成功')

    async def delete(
        self,
        db: Any,
        userIds: str,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """批量逻辑删除用户。"""
        ids = split_to_int_list(userIds)
        if not ids:
            return error('缺少用户编号')
        if current_user is not None and current_user.user_id in ids:
            return error('当前用户不能删除自己')
        db.execute(
            text(
                '''
                UPDATE sys_user
                SET del_flag = '1',
                    update_by = :update_by,
                    update_time = :update_time
                WHERE user_id IN :user_ids AND del_flag = '0'
                '''
            ).bindparams(user_ids=tuple(ids)),
            {'update_by': getattr(current_user, 'user_name', None), 'update_time': datetime.now()},
        )
        db.execute(text('DELETE FROM sys_user_role WHERE user_id IN :user_ids').bindparams(user_ids=tuple(ids)))
        db.commit()
        return to_ajax(len(ids), success_msg='删除成功')

    async def change_status(
        self,
        db: Any,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """启停用户。"""
        payload = await read_json_body(request) if request is not None else {}
        user_id = get_int(payload.get('userId'))
        status = str(payload.get('status') or '').strip()
        if user_id <= 0 or status == '':
            return error('参数不完整')
        if current_user is not None and current_user.user_id == user_id and status == '1':
            return error('当前用户不能停用自己')
        db.execute(
            text(
                '''
                UPDATE sys_user
                SET status = :status,
                    update_by = :update_by,
                    update_time = :update_time
                WHERE user_id = :user_id AND del_flag = '0'
                '''
            ),
            {
                'status': status,
                'update_by': getattr(current_user, 'user_name', None),
                'update_time': datetime.now(),
                'user_id': user_id,
            },
        )
        db.commit()
        return success(msg='操作成功')

    async def reset_pwd(
        self,
        db: Any,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """重置用户密码。"""
        payload = await read_json_body(request) if request is not None else {}
        user_id = get_int(payload.get('userId'))
        password = str(payload.get('password') or payload.get('newPassword') or '').strip()
        if user_id <= 0 or not password:
            return error('参数不完整')
        db.execute(
            text(
                '''
                UPDATE sys_user
                SET password = :password,
                    pwd_update_date = :pwd_update_date,
                    update_by = :update_by,
                    update_time = :update_time
                WHERE user_id = :user_id AND del_flag = '0'
                '''
            ),
            {
                'password': hash_password(password),
                'pwd_update_date': datetime.now(),
                'update_by': getattr(current_user, 'user_name', None),
                'update_time': datetime.now(),
                'user_id': user_id,
            },
        )
        db.commit()
        return success(msg='修改成功')

    async def auth_role_get(
        self,
        db: Any,
        userId: int,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """查询用户可分配角色。"""
        user = self._load_user_detail(db, userId)
        if user is None:
            return error('用户不存在')
        role_ids = get_role_ids_by_user(db, userId)
        roles = load_all_roles(db)
        for role in roles:
            role['flag'] = int(role.get('roleId') or role.get('role_id') or 0) in role_ids
        return success(user=user, roles=roles)

    async def auth_role_update(
        self,
        db: Any,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """批量给用户授权角色。"""
        payload = await read_json_body(request) if request is not None else {}
        user_id = get_int(payload.get('userId'))
        if user_id <= 0:
            return error('缺少用户编号')
        role_ids = split_to_int_list(payload.get('roleIds') or payload.get('roleId'))
        sync_user_roles(db, user_id, role_ids)
        db.commit()
        return success(msg='授权成功')

    async def export(
        self,
        db: Any,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> Any:
        """导出用户 Excel。"""
        params = await collect_params(request) if request is not None else {}
        rows, _ = self._query_user_list(db, params, include_paging=False)
        content = build_excel_bytes(
            sheet_name='用户数据',
            headers=['用户编号', '登录名称', '用户名称', '邮箱', '手机', '状态', '创建时间'],
            rows=[
                [
                    item.get('userId'),
                    item.get('userName'),
                    item.get('nickName'),
                    item.get('email'),
                    item.get('phonenumber'),
                    item.get('status'),
                    item.get('createTime'),
                ]
                for item in rows
            ],
        )
        filename = f'sys_user_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx'
        return StreamingResponse(
            BytesIO(content),
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'},
        )
