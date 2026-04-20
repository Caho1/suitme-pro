"""标签服务。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import Request
from app.core.sqlalchemy_compat import Session, select

from app.core.deps import CurrentUser
from app.core.request_utils import collect_params, get_int, read_json_body, split_to_int_list
from app.core.response import error, success, to_ajax
from app.models.tag import Tag
from app.services.base import SkeletonService
from app.services.biz_support import ensure_list, next_numeric_id, resolve_operator, resolve_user_id


class TagService(SkeletonService):
    """标签服务。"""

    def _base_query(self, current_user: CurrentUser | None = None) -> Any:
        """构造标签基础查询。"""
        stmt = select(Tag).where(Tag.del_flag == '0').order_by(Tag.order_value.asc(), Tag.tag_id.asc())
        if current_user is not None and current_user.user_id is not None:
            stmt = stmt.where(Tag.user_id == current_user.user_id)
        return stmt

    def _serialize_tag(self, tag: Tag) -> dict[str, Any]:
        """序列化标签。"""
        return {
            'tagId': tag.tag_id,
            'userId': tag.user_id,
            'name': tag.name,
            'type': tag.type,
            'orderValue': tag.order_value,
            'displayFlag': tag.display_flag,
            'createBy': tag.create_by,
            'createTime': tag.create_time.strftime('%Y-%m-%d %H:%M:%S') if tag.create_time else None,
            'updateBy': tag.update_by,
            'updateTime': tag.update_time.strftime('%Y-%m-%d %H:%M:%S') if tag.update_time else None,
            'delFlag': tag.del_flag,
        }

    async def add(
        self,
        db: Session,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """新增标签。"""
        payload = await read_json_body(request) if request is not None else {}
        now = datetime.now()
        operator = resolve_operator(current_user)
        max_order = db.scalar(select(Tag.order_value).where(Tag.del_flag == '0').order_by(Tag.order_value.desc()).limit(1))
        tag = Tag(
            tag_id=next_numeric_id(db, Tag, Tag.tag_id),
            user_id=resolve_user_id(current_user, payload),
            name=(payload.get('name') or '').strip() or None,
            type=(payload.get('type') or '').strip() or None,
            order_value=get_int(payload.get('orderValue'), get_int(max_order, 0) + 1),
            display_flag=get_int(payload.get('displayFlag'), 1),
            create_by=operator,
            create_time=now,
            update_by=operator,
            update_time=now,
            del_flag='0',
        )
        db.add(tag)
        db.commit()
        return success(data=self._serialize_tag(tag))

    async def delete(
        self,
        db: Session,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """逻辑删除标签。"""
        params = await collect_params(request) if request is not None else {}
        ids = split_to_int_list(params.get('tagIds') or params.get('tagId') or params.get('ids'))
        if not ids:
            return error('缺少标签编号')
        operator = resolve_operator(current_user)
        rows = 0
        for tag in db.scalars(self._base_query(current_user).where(Tag.tag_id.in_(ids))).all():
            tag.del_flag = '1'
            tag.update_by = operator
            tag.update_time = datetime.now()
            rows += 1
        db.commit()
        return to_ajax(rows)

    async def update(
        self,
        db: Session,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """更新标签。"""
        payload = await read_json_body(request) if request is not None else {}
        tag_id = get_int(payload.get('tagId') or payload.get('id'))
        if tag_id <= 0:
            return error('缺少标签编号')
        tag = db.scalar(self._base_query(current_user).where(Tag.tag_id == tag_id))
        if tag is None:
            return error('标签不存在')
        if 'name' in payload:
            tag.name = (payload.get('name') or '').strip() or None
        if 'type' in payload:
            tag.type = (payload.get('type') or '').strip() or None
        if 'orderValue' in payload:
            tag.order_value = get_int(payload.get('orderValue'), tag.order_value or 0)
        if 'displayFlag' in payload:
            tag.display_flag = get_int(payload.get('displayFlag'), tag.display_flag or 0)
        tag.update_by = resolve_operator(current_user)
        tag.update_time = datetime.now()
        db.commit()
        return success(data=self._serialize_tag(tag))

    async def list(
        self,
        db: Session,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """标签列表。"""
        params = dict(request.query_params) if request is not None else {}
        stmt = self._base_query(current_user)
        tag_type = (params.get('type') or '').strip()
        name = (params.get('name') or '').strip()
        if tag_type:
            stmt = stmt.where(Tag.type == tag_type)
        if name:
            stmt = stmt.where(Tag.name.like(f'%{name}%'))
        rows = [self._serialize_tag(item) for item in db.scalars(stmt).all()]
        return success(data=rows)

    async def update_orders(
        self,
        db: Session,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """批量调整标签顺序。"""
        payload = await read_json_body(request) if request is not None else {}
        raw_items = payload if isinstance(payload, list) else payload.get('items') or payload.get('list') or payload.get('tags')
        rows = 0
        operator = resolve_operator(current_user)
        if isinstance(raw_items, list) and raw_items:
            for index, item in enumerate(raw_items, start=1):
                if not isinstance(item, dict):
                    continue
                tag_id = get_int(item.get('tagId') or item.get('id'))
                tag = db.scalar(self._base_query(current_user).where(Tag.tag_id == tag_id))
                if tag is None:
                    continue
                tag.order_value = get_int(item.get('orderValue'), index)
                tag.update_by = operator
                tag.update_time = datetime.now()
                rows += 1
        else:
            ids = split_to_int_list(payload.get('tagIds') if isinstance(payload, dict) else None)
            if not ids:
                ids = [get_int(item) for item in ensure_list(payload) if get_int(item) > 0]
            for index, tag_id in enumerate(ids, start=1):
                tag = db.scalar(self._base_query(current_user).where(Tag.tag_id == tag_id))
                if tag is None:
                    continue
                tag.order_value = index
                tag.update_by = operator
                tag.update_time = datetime.now()
                rows += 1
        db.commit()
        return to_ajax(rows)
