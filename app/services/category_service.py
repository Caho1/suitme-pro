"""服装分类服务。"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from fastapi import Request
from app.core.sqlalchemy_compat import Session, select

from app.core.deps import CurrentUser
from app.core.request_utils import collect_params, get_int, read_json_body, split_to_int_list
from app.core.response import error, success, to_ajax, warn
from app.models.category import ClothingCategory
from app.services.base import SkeletonService
from app.services.biz_support import next_numeric_id, resolve_operator, resolve_user_id


class CategoryService(SkeletonService):
    """服装分类服务。"""

    def _base_query(self, current_user: CurrentUser | None = None) -> Any:
        """构造分类基础查询。"""
        stmt = (
            select(ClothingCategory)
            .where(ClothingCategory.del_flag == '0')
            .order_by(ClothingCategory.parent_id.asc(), ClothingCategory.order_value.asc(), ClothingCategory.category_id.asc())
        )
        if current_user is not None and current_user.user_id is not None:
            stmt = stmt.where(ClothingCategory.user_id == current_user.user_id)
        return stmt

    def _serialize_category(self, category: ClothingCategory) -> dict[str, Any]:
        """序列化分类节点。"""
        return {
            'categoryId': category.category_id,
            'userId': category.user_id,
            'parentId': category.parent_id,
            'name': category.name,
            'orderValue': category.order_value,
            'defaultFlag': category.default_flag,
            'editableFlag': category.editable_flag,
            'createBy': category.create_by,
            'createTime': category.create_time.strftime('%Y-%m-%d %H:%M:%S') if category.create_time else None,
            'updateBy': category.update_by,
            'updateTime': category.update_time.strftime('%Y-%m-%d %H:%M:%S') if category.update_time else None,
            'delFlag': category.del_flag,
        }

    def _build_tree(self, categories: list[ClothingCategory]) -> list[dict[str, Any]]:
        """把平铺分类列表组装成树。"""
        items = [self._serialize_category(item) for item in categories]
        by_id = {item['categoryId']: item for item in items}
        children_map: defaultdict[int, list[dict[str, Any]]] = defaultdict(list)
        roots: list[dict[str, Any]] = []
        for item in items:
            item.setdefault('children', [])
            parent_id = item.get('parentId') or 0
            if parent_id and parent_id in by_id:
                children_map[parent_id].append(item)
            else:
                roots.append(item)
        for parent_id, children in children_map.items():
            by_id[parent_id]['children'] = children
        return roots

    async def add(
        self,
        db: Session,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """新增服装分类节点。"""
        payload = await read_json_body(request) if request is not None else {}
        now = datetime.now()
        operator = resolve_operator(current_user)
        parent_id = get_int(payload.get('parentId'), 0)
        category = ClothingCategory(
            category_id=next_numeric_id(db, ClothingCategory, ClothingCategory.category_id),
            user_id=resolve_user_id(current_user, payload),
            parent_id=parent_id,
            name=(payload.get('name') or '').strip() or None,
            order_value=get_int(payload.get('orderValue'), 1),
            default_flag=get_int(payload.get('defaultFlag'), 0),
            editable_flag=get_int(payload.get('editableFlag'), 1),
            create_by=operator,
            create_time=now,
            update_by=operator,
            update_time=now,
            del_flag='0',
        )
        db.add(category)
        db.commit()
        return success(data=self._serialize_category(category))

    async def update(
        self,
        db: Session,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """更新服装分类节点。"""
        payload = await read_json_body(request) if request is not None else {}
        category_id = get_int(payload.get('categoryId') or payload.get('id'))
        if category_id <= 0:
            return error('缺少分类编号')
        category = db.scalar(self._base_query(current_user).where(ClothingCategory.category_id == category_id))
        if category is None:
            return error('分类不存在')
        parent_id = get_int(payload.get('parentId'), category.parent_id or 0)
        if category_id == parent_id:
            return error('上级分类不能选择自己')
        if 'name' in payload:
            category.name = (payload.get('name') or '').strip() or None
        category.parent_id = parent_id
        if 'orderValue' in payload:
            category.order_value = get_int(payload.get('orderValue'), category.order_value or 0)
        if 'defaultFlag' in payload:
            category.default_flag = get_int(payload.get('defaultFlag'), category.default_flag or 0)
        if 'editableFlag' in payload:
            category.editable_flag = get_int(payload.get('editableFlag'), category.editable_flag or 0)
        category.update_by = resolve_operator(current_user)
        category.update_time = datetime.now()
        db.commit()
        return success(data=self._serialize_category(category))

    async def delete(
        self,
        db: Session,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """删除服装分类节点。"""
        params = await collect_params(request) if request is not None else {}
        ids = split_to_int_list(params.get('categoryIds') or params.get('categoryId') or params.get('ids'))
        if not ids:
            return error('缺少分类编号')
        operator = resolve_operator(current_user)
        rows = 0
        for category_id in ids:
            child_exists = db.scalar(
                select(ClothingCategory.category_id)
                .where(ClothingCategory.parent_id == category_id)
                .where(ClothingCategory.del_flag == '0')
                .limit(1)
            )
            if child_exists:
                return warn('存在子分类,不允许删除')
            category = db.scalar(self._base_query(current_user).where(ClothingCategory.category_id == category_id))
            if category is None:
                continue
            category.del_flag = '1'
            category.update_by = operator
            category.update_time = datetime.now()
            rows += 1
        db.commit()
        return to_ajax(rows)

    async def list(
        self,
        db: Session,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """查询服装分类树。"""
        params = await collect_params(request) if request is not None else {}
        stmt = self._base_query(current_user)
        name = (params.get('name') or '').strip()
        if name:
            stmt = stmt.where(ClothingCategory.name.like(f'%{name}%'))
        rows = list(db.scalars(stmt).all())
        return success(data=self._build_tree(rows))
