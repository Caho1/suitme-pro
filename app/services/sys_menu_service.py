"""系统菜单服务。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import Request
try:
    from sqlalchemy import bindparam, text
except Exception:  # pragma: no cover - 仅用于依赖未安装时的导入兼容
    def text(sql: str) -> str:
        return sql

    def bindparam(name: str, expanding: bool = False) -> str:
        return name


from app.core.deps import CurrentUser
from app.core.request_utils import collect_params, get_int, read_json_body
from app.core.response import error, success, to_ajax, warn
from app.services.base import SkeletonService
from app.services.sys_support import build_menu_tree, build_tree_select, get_menu_ids_by_role, mapping_to_dict, next_table_id


class SysMenuService(SkeletonService):
    """系统菜单服务。"""

    def _serialize_menu(self, row: Any) -> dict[str, Any]:
        """把菜单查询结果转换为前端结构。"""
        data = mapping_to_dict(row)
        rename_map = {
            'menu_id': 'menuId',
            'menu_name': 'menuName',
            'parent_id': 'parentId',
            'order_num': 'orderNum',
            'route_name': 'routeName',
            'is_frame': 'isFrame',
            'is_cache': 'isCache',
            'menu_type': 'menuType',
            'create_by': 'createBy',
            'create_time': 'createTime',
            'update_by': 'updateBy',
            'update_time': 'updateTime',
            'del_flag': 'delFlag',
        }
        for old, new in rename_map.items():
            if old in data:
                data[new] = data.pop(old)
        return data

    def _query_menus(self, db: Any, params: dict[str, Any]) -> list[dict[str, Any]]:
        """读取菜单列表。"""
        where = ["del_flag = '0'"]
        query_params: dict[str, Any] = {}
        menu_name = str(params.get('menuName') or '').strip()
        if menu_name:
            where.append('menu_name LIKE :menu_name')
            query_params['menu_name'] = f'%{menu_name}%'
        status = str(params.get('status') or '').strip()
        if status != '':
            where.append('status = :status')
            query_params['status'] = status
        where_sql = ' AND '.join(where)
        rows = db.execute(
            text(
                f'''
                SELECT menu_id, menu_name, parent_id, order_num, path, component, query,
                       route_name, is_frame, is_cache, menu_type, visible, status,
                       perms, icon, remark, create_by, create_time, update_by, update_time, del_flag
                FROM sys_menu
                WHERE {where_sql}
                ORDER BY parent_id ASC, order_num ASC, menu_id ASC
                '''
            ),
            query_params,
        ).mappings().all()
        return [self._serialize_menu(row) for row in rows]

    def _load_menu(self, db: Any, menu_id: int) -> dict[str, Any] | None:
        """读取单个菜单详情。"""
        row = db.execute(
            text(
                '''
                SELECT menu_id, menu_name, parent_id, order_num, path, component, query,
                       route_name, is_frame, is_cache, menu_type, visible, status,
                       perms, icon, remark, create_by, create_time, update_by, update_time, del_flag
                FROM sys_menu
                WHERE menu_id = :menu_id AND del_flag = '0'
                LIMIT 1
                '''
            ),
            {'menu_id': menu_id},
        ).mappings().first()
        if row is None:
            return None
        return self._serialize_menu(row)

    def _menu_name_exists(self, db: Any, parent_id: int, menu_name: str, exclude_menu_id: int | None = None) -> bool:
        """校验同级菜单名称是否重复。"""
        sql = 'SELECT 1 FROM sys_menu WHERE parent_id = :parent_id AND menu_name = :menu_name AND del_flag = \'0\''
        params: dict[str, Any] = {'parent_id': parent_id, 'menu_name': menu_name}
        if exclude_menu_id is not None:
            sql += ' AND menu_id <> :menu_id'
            params['menu_id'] = exclude_menu_id
        sql += ' LIMIT 1'
        return db.execute(text(sql), params).first() is not None

    async def list(
        self,
        db: Any,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """查询菜单列表。"""
        params = await collect_params(request) if request is not None else {}
        rows = self._query_menus(db, params)
        return success(data=build_menu_tree(rows))

    async def treeselect(
        self,
        db: Any,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """菜单树下拉。"""
        params = await collect_params(request) if request is not None else {}
        rows = self._query_menus(db, params)
        return success(data=build_tree_select(rows))

    async def role_menu_treeselect(
        self,
        db: Any,
        roleId: int,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """查询角色菜单树。"""
        rows = self._query_menus(db, {})
        checked_keys = get_menu_ids_by_role(db, roleId)
        return success(menus=build_tree_select(rows), checkedKeys=checked_keys)

    async def get(
        self,
        db: Any,
        menuId: int,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """查询菜单详情。"""
        menu = self._load_menu(db, menuId)
        if menu is None:
            return error('菜单不存在')
        return success(data=menu)

    async def add(
        self,
        db: Any,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """新增菜单。"""
        payload = await read_json_body(request) if request is not None else {}
        menu_name = str(payload.get('menuName') or '').strip()
        parent_id = get_int(payload.get('parentId'), 0)
        if not menu_name:
            return error('菜单名称不能为空')
        if self._menu_name_exists(db, parent_id, menu_name):
            return error('新增菜单失败，菜单名称已存在')
        menu_id = next_table_id(db, 'sys_menu', 'menu_id')
        operator = getattr(current_user, 'user_name', None) or 'system'
        db.execute(
            text(
                '''
                INSERT INTO sys_menu (
                    menu_id, menu_name, parent_id, order_num, path, component, query,
                    route_name, is_frame, is_cache, menu_type, visible, status,
                    perms, icon, remark, del_flag, create_by, create_time, update_by, update_time
                ) VALUES (
                    :menu_id, :menu_name, :parent_id, :order_num, :path, :component, :query,
                    :route_name, :is_frame, :is_cache, :menu_type, :visible, :status,
                    :perms, :icon, :remark, '0', :create_by, :create_time, :update_by, :update_time
                )
                '''
            ),
            {
                'menu_id': menu_id,
                'menu_name': menu_name,
                'parent_id': parent_id,
                'order_num': get_int(payload.get('orderNum'), 1),
                'path': str(payload.get('path') or '').strip() or None,
                'component': str(payload.get('component') or '').strip() or None,
                'query': str(payload.get('query') or '').strip() or None,
                'route_name': str(payload.get('routeName') or '').strip() or None,
                'is_frame': get_int(payload.get('isFrame'), 1),
                'is_cache': get_int(payload.get('isCache'), 0),
                'menu_type': str(payload.get('menuType') or 'M').strip() or 'M',
                'visible': str(payload.get('visible') or '0').strip() or '0',
                'status': str(payload.get('status') or '0').strip() or '0',
                'perms': str(payload.get('perms') or '').strip() or None,
                'icon': str(payload.get('icon') or '').strip() or None,
                'remark': str(payload.get('remark') or '').strip() or None,
                'create_by': operator,
                'create_time': datetime.now(),
                'update_by': operator,
                'update_time': datetime.now(),
            },
        )
        db.commit()
        return success(msg='新增成功')

    async def update(
        self,
        db: Any,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """修改菜单。"""
        payload = await read_json_body(request) if request is not None else {}
        menu_id = get_int(payload.get('menuId'))
        if menu_id <= 0:
            return error('缺少菜单编号')
        menu = self._load_menu(db, menu_id)
        if menu is None:
            return error('菜单不存在')
        parent_id = get_int(payload.get('parentId'), int(menu.get('parentId') or 0))
        if menu_id == parent_id:
            return error('上级菜单不能选择自己')
        menu_name = str(payload.get('menuName') or '').strip()
        if self._menu_name_exists(db, parent_id, menu_name, menu_id):
            return error('修改菜单失败，菜单名称已存在')
        db.execute(
            text(
                '''
                UPDATE sys_menu
                SET menu_name = :menu_name,
                    parent_id = :parent_id,
                    order_num = :order_num,
                    path = :path,
                    component = :component,
                    query = :query,
                    route_name = :route_name,
                    is_frame = :is_frame,
                    is_cache = :is_cache,
                    menu_type = :menu_type,
                    visible = :visible,
                    status = :status,
                    perms = :perms,
                    icon = :icon,
                    remark = :remark,
                    update_by = :update_by,
                    update_time = :update_time
                WHERE menu_id = :menu_id AND del_flag = '0'
                '''
            ),
            {
                'menu_name': menu_name,
                'parent_id': parent_id,
                'order_num': get_int(payload.get('orderNum'), int(menu.get('orderNum') or 1)),
                'path': str(payload.get('path') or '').strip() or None,
                'component': str(payload.get('component') or '').strip() or None,
                'query': str(payload.get('query') or '').strip() or None,
                'route_name': str(payload.get('routeName') or '').strip() or None,
                'is_frame': get_int(payload.get('isFrame'), int(menu.get('isFrame') or 1)),
                'is_cache': get_int(payload.get('isCache'), int(menu.get('isCache') or 0)),
                'menu_type': str(payload.get('menuType') or menu.get('menuType') or 'M'),
                'visible': str(payload.get('visible') or menu.get('visible') or '0'),
                'status': str(payload.get('status') or menu.get('status') or '0'),
                'perms': str(payload.get('perms') or '').strip() or None,
                'icon': str(payload.get('icon') or '').strip() or None,
                'remark': str(payload.get('remark') or '').strip() or None,
                'update_by': getattr(current_user, 'user_name', None) or 'system',
                'update_time': datetime.now(),
                'menu_id': menu_id,
            },
        )
        db.commit()
        return success(msg='修改成功')

    async def delete(
        self,
        db: Any,
        menuId: int,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """删除菜单。"""
        child_exists = db.execute(
            text('SELECT 1 FROM sys_menu WHERE parent_id = :menu_id AND del_flag = \'0\' LIMIT 1'),
            {'menu_id': menuId},
        ).first()
        if child_exists is not None:
            return warn('存在子菜单,不允许删除')
        role_ref = db.execute(
            text('SELECT 1 FROM sys_role_menu WHERE menu_id = :menu_id LIMIT 1'),
            {'menu_id': menuId},
        ).first()
        if role_ref is not None:
            return warn('菜单已分配,不允许删除')
        db.execute(
            text(
                '''
                UPDATE sys_menu
                SET del_flag = '1', update_by = :update_by, update_time = :update_time
                WHERE menu_id = :menu_id AND del_flag = '0'
                '''
            ),
            {'menu_id': menuId, 'update_by': getattr(current_user, 'user_name', None), 'update_time': datetime.now()},
        )
        db.commit()
        return to_ajax(1, success_msg='删除成功')
