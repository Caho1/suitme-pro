"""系统角色服务。"""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Any

from fastapi import Request
from fastapi.responses import StreamingResponse
try:
    from sqlalchemy import bindparam, text
except Exception:  # pragma: no cover - 仅用于依赖未安装时的导入兼容
    def text(sql: str) -> str:
        return sql

    def bindparam(name: str, expanding: bool = False) -> str:
        return name


from app.core.deps import CurrentUser
from app.core.request_utils import collect_params, get_int, read_json_body, split_to_int_list
from app.core.response import error, success, table_data, to_ajax
from app.services.base import SkeletonService
from app.services.sys_support import (
    build_excel_bytes,
    get_menu_ids_by_role,
    mapping_to_dict,
    next_table_id,
    sync_role_menus,
)


class SysRoleService(SkeletonService):
    """系统角色服务。"""

    def _serialize_role(self, row: Any) -> dict[str, Any]:
        """把角色查询结果转换成前端可用结构。"""
        data = mapping_to_dict(row)
        if 'role_id' in data:
            data['roleId'] = data.pop('role_id')
        if 'role_name' in data:
            data['roleName'] = data.pop('role_name')
        if 'role_key' in data:
            data['roleKey'] = data.pop('role_key')
        if 'role_sort' in data:
            data['roleSort'] = data.pop('role_sort')
        if 'data_scope' in data:
            data['dataScope'] = data.pop('data_scope')
        if 'menu_check_strictly' in data:
            data['menuCheckStrictly'] = data.pop('menu_check_strictly')
        if 'dept_check_strictly' in data:
            data['deptCheckStrictly'] = data.pop('dept_check_strictly')
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

    def _query_roles(self, db: Any, params: dict[str, Any], include_paging: bool = True) -> tuple[list[dict[str, Any]], int]:
        """按查询条件读取角色列表。"""
        where = ["r.del_flag = '0'"]
        query_params: dict[str, Any] = {}
        role_name = str(params.get('roleName') or '').strip()
        if role_name:
            where.append('r.role_name LIKE :role_name')
            query_params['role_name'] = f'%{role_name}%'
        role_key = str(params.get('roleKey') or '').strip()
        if role_key:
            where.append('r.role_key LIKE :role_key')
            query_params['role_key'] = f'%{role_key}%'
        status = str(params.get('status') or '').strip()
        if status != '':
            where.append('r.status = :status')
            query_params['status'] = status
        where_sql = ' AND '.join(where)
        total = int(db.execute(text(f'SELECT COUNT(1) FROM sys_role r WHERE {where_sql}'), query_params).scalar() or 0)
        limit_sql = ''
        if include_paging:
            page_num = max(1, get_int(params.get('pageNum'), 1))
            page_size = max(1, get_int(params.get('pageSize'), 10))
            query_params['offset'] = (page_num - 1) * page_size
            query_params['page_size'] = page_size
            limit_sql = ' LIMIT :offset, :page_size'
        rows = db.execute(
            text(
                f'''
                SELECT r.role_id, r.role_name, r.role_key, r.role_sort, r.data_scope,
                       r.menu_check_strictly, r.dept_check_strictly, r.status,
                       r.create_by, r.create_time, r.update_by, r.update_time,
                       r.remark, r.del_flag
                FROM sys_role r
                WHERE {where_sql}
                ORDER BY r.role_sort ASC, r.role_id ASC
                {limit_sql}
                '''
            ),
            query_params,
        ).mappings().all()
        return [self._serialize_role(row) for row in rows], total

    def _load_role(self, db: Any, role_id: int) -> dict[str, Any] | None:
        """读取单个角色详情。"""
        row = db.execute(
            text(
                '''
                SELECT role_id, role_name, role_key, role_sort, data_scope,
                       menu_check_strictly, dept_check_strictly, status,
                       create_by, create_time, update_by, update_time,
                       remark, del_flag
                FROM sys_role
                WHERE role_id = :role_id AND del_flag = '0'
                LIMIT 1
                '''
            ),
            {'role_id': role_id},
        ).mappings().first()
        if row is None:
            return None
        return self._serialize_role(row)

    def _role_name_exists(self, db: Any, role_name: str, exclude_role_id: int | None = None) -> bool:
        """校验角色名称是否重复。"""
        sql = 'SELECT 1 FROM sys_role WHERE role_name = :role_name AND del_flag = \'0\''
        params: dict[str, Any] = {'role_name': role_name}
        if exclude_role_id is not None:
            sql += ' AND role_id <> :role_id'
            params['role_id'] = exclude_role_id
        sql += ' LIMIT 1'
        return db.execute(text(sql), params).first() is not None

    def _role_key_exists(self, db: Any, role_key: str, exclude_role_id: int | None = None) -> bool:
        """校验角色权限字符是否重复。"""
        sql = 'SELECT 1 FROM sys_role WHERE role_key = :role_key AND del_flag = \'0\''
        params: dict[str, Any] = {'role_key': role_key}
        if exclude_role_id is not None:
            sql += ' AND role_id <> :role_id'
            params['role_id'] = exclude_role_id
        sql += ' LIMIT 1'
        return db.execute(text(sql), params).first() is not None

    def _query_auth_users(self, db: Any, role_id: int, params: dict[str, Any], allocated: bool) -> tuple[list[dict[str, Any]], int]:
        """查询角色已分配或未分配用户列表。"""
        where = ["u.del_flag = '0'"]
        query_params: dict[str, Any] = {'role_id': role_id}
        user_name = str(params.get('userName') or '').strip()
        if user_name:
            where.append('u.user_name LIKE :user_name')
            query_params['user_name'] = f'%{user_name}%'
        phone = str(params.get('phonenumber') or '').strip()
        if phone:
            where.append('u.phonenumber LIKE :phonenumber')
            query_params['phonenumber'] = f'%{phone}%'
        if allocated:
            where.append('EXISTS (SELECT 1 FROM sys_user_role ur WHERE ur.user_id = u.user_id AND ur.role_id = :role_id)')
        else:
            where.append('NOT EXISTS (SELECT 1 FROM sys_user_role ur WHERE ur.user_id = u.user_id AND ur.role_id = :role_id)')
        where_sql = ' AND '.join(where)
        total = int(db.execute(text(f'SELECT COUNT(1) FROM sys_user u WHERE {where_sql}'), query_params).scalar() or 0)
        page_num = max(1, get_int(params.get('pageNum'), 1))
        page_size = max(1, get_int(params.get('pageSize'), 10))
        query_params['offset'] = (page_num - 1) * page_size
        query_params['page_size'] = page_size
        rows = db.execute(
            text(
                f'''
                SELECT u.user_id, u.user_name, u.nick_name, u.email, u.phonenumber,
                       u.status, u.create_time
                FROM sys_user u
                WHERE {where_sql}
                ORDER BY u.user_id DESC
                LIMIT :offset, :page_size
                '''
            ),
            query_params,
        ).mappings().all()
        payload = []
        for row in rows:
            item = mapping_to_dict(row)
            item['userId'] = item.pop('user_id')
            item['userName'] = item.pop('user_name')
            item['nickName'] = item.pop('nick_name')
            item['createTime'] = item.pop('create_time')
            payload.append(item)
        return payload, total

    async def auth_user_allocated_list(
        self,
        db: Any,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """查询已分配给角色的用户。"""
        params = await collect_params(request) if request is not None else {}
        role_id = get_int(params.get('roleId'))
        if role_id <= 0:
            return error('缺少角色编号')
        rows, total = self._query_auth_users(db, role_id, params, allocated=True)
        return table_data(rows=rows, total=total)

    async def auth_user_unallocated_list(
        self,
        db: Any,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """查询未分配给角色的用户。"""
        params = await collect_params(request) if request is not None else {}
        role_id = get_int(params.get('roleId'))
        if role_id <= 0:
            return error('缺少角色编号')
        rows, total = self._query_auth_users(db, role_id, params, allocated=False)
        return table_data(rows=rows, total=total)

    async def auth_user_cancel(
        self,
        db: Any,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """取消单个用户的角色。"""
        payload = await read_json_body(request) if request is not None else {}
        user_id = get_int(payload.get('userId'))
        role_id = get_int(payload.get('roleId'))
        if user_id <= 0 or role_id <= 0:
            return error('参数不完整')
        db.execute(
            text('DELETE FROM sys_user_role WHERE user_id = :user_id AND role_id = :role_id'),
            {'user_id': user_id, 'role_id': role_id},
        )
        db.commit()
        return success(msg='取消授权成功')

    async def auth_user_cancel_all(
        self,
        db: Any,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """批量取消角色下的用户。"""
        payload = await read_json_body(request) if request is not None else {}
        role_id = get_int(payload.get('roleId'))
        user_ids = split_to_int_list(payload.get('userIds') or payload.get('userId'))
        if role_id <= 0 or not user_ids:
            return error('参数不完整')
        stmt = text('DELETE FROM sys_user_role WHERE role_id = :role_id AND user_id IN :user_ids').bindparams(
            bindparam('user_ids', expanding=True)
        )
        db.execute(stmt, {'role_id': role_id, 'user_ids': user_ids})
        db.commit()
        return success(msg='取消授权成功')

    async def auth_user_select_all(
        self,
        db: Any,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """批量给角色授权用户。"""
        payload = await read_json_body(request) if request is not None else {}
        role_id = get_int(payload.get('roleId'))
        user_ids = split_to_int_list(payload.get('userIds') or payload.get('userId'))
        if role_id <= 0 or not user_ids:
            return error('参数不完整')
        existing = {
            int(row['user_id'])
            for row in db.execute(
                text('SELECT user_id FROM sys_user_role WHERE role_id = :role_id'),
                {'role_id': role_id},
            ).mappings().all()
            if row.get('user_id') is not None
        }
        for user_id in user_ids:
            if user_id in existing:
                continue
            db.execute(
                text('INSERT INTO sys_user_role (user_id, role_id) VALUES (:user_id, :role_id)'),
                {'user_id': user_id, 'role_id': role_id},
            )
        db.commit()
        return success(msg='授权成功')

    async def list(
        self,
        db: Any,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """分页查询角色。"""
        params = await collect_params(request) if request is not None else {}
        rows, total = self._query_roles(db, params, include_paging=True)
        return table_data(rows=rows, total=total)

    async def get(
        self,
        db: Any,
        roleId: int,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """查询角色详情。"""
        role = self._load_role(db, roleId)
        if role is None:
            return error('角色不存在')
        menu_ids = get_menu_ids_by_role(db, roleId)
        return success(data=role, menuIds=menu_ids)

    async def add(
        self,
        db: Any,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """新增角色。"""
        payload = await read_json_body(request) if request is not None else {}
        role_name = str(payload.get('roleName') or '').strip()
        role_key = str(payload.get('roleKey') or '').strip()
        if not role_name or not role_key:
            return error('角色名称和权限字符不能为空')
        if self._role_name_exists(db, role_name):
            return error('新增角色失败，角色名称已存在')
        if self._role_key_exists(db, role_key):
            return error('新增角色失败，权限字符已存在')
        role_id = next_table_id(db, 'sys_role', 'role_id')
        operator = getattr(current_user, 'user_name', None) or 'system'
        db.execute(
            text(
                '''
                INSERT INTO sys_role (
                    role_id, role_name, role_key, role_sort, data_scope,
                    menu_check_strictly, dept_check_strictly, status,
                    remark, del_flag, create_by, create_time, update_by, update_time
                ) VALUES (
                    :role_id, :role_name, :role_key, :role_sort, :data_scope,
                    :menu_check_strictly, :dept_check_strictly, :status,
                    :remark, '0', :create_by, :create_time, :update_by, :update_time
                )
                '''
            ),
            {
                'role_id': role_id,
                'role_name': role_name,
                'role_key': role_key,
                'role_sort': get_int(payload.get('roleSort'), 1),
                'data_scope': str(payload.get('dataScope') or '1').strip() or '1',
                'menu_check_strictly': get_int(payload.get('menuCheckStrictly'), 1),
                'dept_check_strictly': get_int(payload.get('deptCheckStrictly'), 1),
                'status': str(payload.get('status') or '0').strip() or '0',
                'remark': str(payload.get('remark') or '').strip() or None,
                'create_by': operator,
                'create_time': datetime.now(),
                'update_by': operator,
                'update_time': datetime.now(),
            },
        )
        sync_role_menus(db, role_id, split_to_int_list(payload.get('menuIds') or payload.get('menuId')))
        db.commit()
        return success(msg='新增成功')

    async def update(
        self,
        db: Any,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """修改角色。"""
        payload = await read_json_body(request) if request is not None else {}
        role_id = get_int(payload.get('roleId'))
        if role_id <= 0:
            return error('缺少角色编号')
        role = self._load_role(db, role_id)
        if role is None:
            return error('角色不存在')
        role_name = str(payload.get('roleName') or '').strip()
        role_key = str(payload.get('roleKey') or '').strip()
        if self._role_name_exists(db, role_name, role_id):
            return error('修改角色失败，角色名称已存在')
        if self._role_key_exists(db, role_key, role_id):
            return error('修改角色失败，权限字符已存在')
        db.execute(
            text(
                '''
                UPDATE sys_role
                SET role_name = :role_name,
                    role_key = :role_key,
                    role_sort = :role_sort,
                    data_scope = :data_scope,
                    menu_check_strictly = :menu_check_strictly,
                    dept_check_strictly = :dept_check_strictly,
                    status = :status,
                    remark = :remark,
                    update_by = :update_by,
                    update_time = :update_time
                WHERE role_id = :role_id AND del_flag = '0'
                '''
            ),
            {
                'role_name': role_name,
                'role_key': role_key,
                'role_sort': get_int(payload.get('roleSort'), 1),
                'data_scope': str(payload.get('dataScope') or role.get('dataScope') or '1'),
                'menu_check_strictly': get_int(payload.get('menuCheckStrictly'), 1),
                'dept_check_strictly': get_int(payload.get('deptCheckStrictly'), 1),
                'status': str(payload.get('status') or role.get('status') or '0'),
                'remark': str(payload.get('remark') or '').strip() or None,
                'update_by': getattr(current_user, 'user_name', None) or 'system',
                'update_time': datetime.now(),
                'role_id': role_id,
            },
        )
        sync_role_menus(db, role_id, split_to_int_list(payload.get('menuIds') or payload.get('menuId')))
        db.commit()
        return success(msg='修改成功')

    async def change_status(
        self,
        db: Any,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """启停角色。"""
        payload = await read_json_body(request) if request is not None else {}
        role_id = get_int(payload.get('roleId'))
        status = str(payload.get('status') or '').strip()
        if role_id <= 0 or status == '':
            return error('参数不完整')
        db.execute(
            text(
                '''
                UPDATE sys_role
                SET status = :status,
                    update_by = :update_by,
                    update_time = :update_time
                WHERE role_id = :role_id AND del_flag = '0'
                '''
            ),
            {
                'status': status,
                'update_by': getattr(current_user, 'user_name', None) or 'system',
                'update_time': datetime.now(),
                'role_id': role_id,
            },
        )
        db.commit()
        return success(msg='操作成功')

    async def delete(
        self,
        db: Any,
        roleIds: str,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """批量删除角色。"""
        ids = split_to_int_list(roleIds)
        if not ids:
            return error('缺少角色编号')
        stmt_role = text(
            '''
            UPDATE sys_role
            SET del_flag = '1', update_by = :update_by, update_time = :update_time
            WHERE role_id IN :role_ids AND del_flag = '0'
            '''
        ).bindparams(bindparam('role_ids', expanding=True))
        db.execute(stmt_role, {'role_ids': ids, 'update_by': getattr(current_user, 'user_name', None), 'update_time': datetime.now()})
        stmt_user_role = text('DELETE FROM sys_user_role WHERE role_id IN :role_ids').bindparams(bindparam('role_ids', expanding=True))
        stmt_role_menu = text('DELETE FROM sys_role_menu WHERE role_id IN :role_ids').bindparams(bindparam('role_ids', expanding=True))
        db.execute(stmt_user_role, {'role_ids': ids})
        db.execute(stmt_role_menu, {'role_ids': ids})
        db.commit()
        return to_ajax(len(ids), success_msg='删除成功')

    async def export(
        self,
        db: Any,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> Any:
        """导出角色 Excel。"""
        params = await collect_params(request) if request is not None else {}
        rows, _ = self._query_roles(db, params, include_paging=False)
        content = build_excel_bytes(
            sheet_name='角色数据',
            headers=['角色编号', '角色名称', '权限字符', '显示顺序', '状态', '创建时间'],
            rows=[
                [
                    item.get('roleId'),
                    item.get('roleName'),
                    item.get('roleKey'),
                    item.get('roleSort'),
                    item.get('status'),
                    item.get('createTime'),
                ]
                for item in rows
            ],
        )
        filename = f'sys_role_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx'
        return StreamingResponse(
            BytesIO(content),
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'},
        )
