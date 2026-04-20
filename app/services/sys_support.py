"""系统管理公共支持函数。"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from io import BytesIO
from typing import Any, Iterable

from openpyxl import Workbook
try:
    from sqlalchemy import text
except Exception:  # pragma: no cover - 仅用于依赖未安装时的导入兼容
    def text(sql: str) -> str:
        return sql



ADMIN_ROLE_KEY = 'admin'



def format_datetime(value: Any) -> Any:
    """把日期时间格式化成若依兼容字符串。"""
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    return value



def mapping_to_dict(row: Any) -> dict[str, Any]:
    """把 SQLAlchemy RowMapping 转换为普通字典。"""
    data = dict(row)
    for key, value in list(data.items()):
        data[key] = format_datetime(value)
    return data



def next_table_id(db: Any, table_name: str, pk_name: str) -> int:
    """读取表当前最大主键并生成下一个编号。"""
    value = db.execute(text(f'SELECT COALESCE(MAX({pk_name}), 0) + 1 AS next_id FROM {table_name}')).scalar()
    return int(value or 1)



def is_admin_user(current_user: Any | None) -> bool:
    """判断当前登录用户是否为管理员。"""
    if current_user is None:
        return False
    if getattr(current_user, 'user_name', None) == 'admin':
        return True
    return ADMIN_ROLE_KEY in list(getattr(current_user, 'roles', []) or [])



def get_role_ids_by_user(db: Any, user_id: int) -> list[int]:
    """查询用户已分配角色编号。"""
    rows = db.execute(
        text('SELECT role_id FROM sys_user_role WHERE user_id = :user_id ORDER BY role_id'),
        {'user_id': user_id},
    ).mappings().all()
    return [int(row['role_id']) for row in rows if row.get('role_id') is not None]



def get_menu_ids_by_role(db: Any, role_id: int) -> list[int]:
    """查询角色已分配菜单编号。"""
    rows = db.execute(
        text('SELECT menu_id FROM sys_role_menu WHERE role_id = :role_id ORDER BY menu_id'),
        {'role_id': role_id},
    ).mappings().all()
    return [int(row['menu_id']) for row in rows if row.get('menu_id') is not None]



def load_all_roles(db: Any) -> list[dict[str, Any]]:
    """读取全部未删除角色。"""
    rows = db.execute(
        text(
            '''
            SELECT role_id, role_name, role_key, role_sort, data_scope,
                   menu_check_strictly, dept_check_strictly, status,
                   create_by, create_time, update_by, update_time, remark, del_flag
            FROM sys_role
            WHERE del_flag = '0'
            ORDER BY role_sort ASC, role_id ASC
            '''
        )
    ).mappings().all()
    return [mapping_to_dict(row) for row in rows]



def sync_user_roles(db: Any, user_id: int, role_ids: list[int]) -> None:
    """重建用户角色关联。"""
    db.execute(text('DELETE FROM sys_user_role WHERE user_id = :user_id'), {'user_id': user_id})
    for role_id in sorted({int(item) for item in role_ids if int(item) > 0}):
        db.execute(
            text('INSERT INTO sys_user_role (user_id, role_id) VALUES (:user_id, :role_id)'),
            {'user_id': user_id, 'role_id': role_id},
        )



def sync_role_menus(db: Any, role_id: int, menu_ids: list[int]) -> None:
    """重建角色菜单关联。"""
    db.execute(text('DELETE FROM sys_role_menu WHERE role_id = :role_id'), {'role_id': role_id})
    for menu_id in sorted({int(item) for item in menu_ids if int(item) > 0}):
        db.execute(
            text('INSERT INTO sys_role_menu (role_id, menu_id) VALUES (:role_id, :menu_id)'),
            {'role_id': role_id, 'menu_id': menu_id},
        )



def build_menu_tree(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """把菜单平铺列表组装成树结构。"""
    items = [dict(item) for item in rows]
    by_id = {int(item['menuId']): item for item in items if item.get('menuId') is not None}
    child_map: defaultdict[int, list[dict[str, Any]]] = defaultdict(list)
    roots: list[dict[str, Any]] = []
    for item in items:
        item.setdefault('children', [])
        parent_id = int(item.get('parentId') or 0)
        menu_id = int(item.get('menuId') or 0)
        if parent_id and parent_id in by_id and parent_id != menu_id:
            child_map[parent_id].append(item)
        else:
            roots.append(item)
    for parent_id, children in child_map.items():
        children.sort(key=lambda x: (int(x.get('orderNum') or 0), int(x.get('menuId') or 0)))
        by_id[parent_id]['children'] = children
    roots.sort(key=lambda x: (int(x.get('orderNum') or 0), int(x.get('menuId') or 0)))
    return roots



def build_tree_select(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """把菜单列表转换为 treeselect 结构。"""
    def convert(node: dict[str, Any]) -> dict[str, Any]:
        item = {'id': node.get('menuId'), 'label': node.get('menuName')}
        children = [convert(child) for child in node.get('children', [])]
        if children:
            item['children'] = children
        return item

    return [convert(item) for item in build_menu_tree(rows)]



def build_excel_bytes(sheet_name: str, headers: list[str], rows: Iterable[Iterable[Any]]) -> bytes:
    """构造 Excel 二进制内容。"""
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = sheet_name
    sheet.append(headers)
    for row in rows:
        sheet.append(list(row))
    stream = BytesIO()
    workbook.save(stream)
    return stream.getvalue()
