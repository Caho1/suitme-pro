"""搭配服务。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import Request
from app.core.sqlalchemy_compat import Session, select

from app.core.deps import CurrentUser
from app.core.request_utils import collect_params, get_int, read_json_body, split_to_int_list
from app.core.response import error, success, to_ajax
from app.models.matching import Matching, MatchingSku, MatchingTag
from app.models.product import Product, ProductColor
from app.services.base import SkeletonService
from app.services.biz_support import next_numeric_id, resolve_operator


class MatchingService(SkeletonService):
    """搭配服务。"""

    def _base_matching_query(self, current_user: CurrentUser | None = None) -> Any:
        """构造搭配主表查询。"""
        stmt = select(Matching).where(Matching.del_flag == '0').order_by(Matching.matching_id.desc())
        return stmt

    def _base_tag_query(self, current_user: CurrentUser | None = None) -> Any:
        """构造搭配标签查询。"""
        stmt = select(MatchingTag).where(MatchingTag.del_flag == '0').order_by(MatchingTag.matching_tag_id.desc())
        return stmt

    def _serialize_sku(self, sku: MatchingSku) -> dict[str, Any]:
        """序列化搭配 SKU。"""
        return {
            'matchingSkuId': sku.matching_sku_id,
            'matchingId': sku.matching_id,
            'productId': sku.product_id,
            'productColorId': sku.product_color_id,
            'angle': sku.angle,
            'delFlag': sku.del_flag,
        }

    def _load_skus(self, db: Session, matching_id: int) -> list[dict[str, Any]]:
        """读取搭配下的 SKU 明细。"""
        stmt = (
            select(MatchingSku)
            .where(MatchingSku.matching_id == matching_id)
            .where(MatchingSku.del_flag == '0')
            .order_by(MatchingSku.matching_sku_id.asc())
        )
        return [self._serialize_sku(item) for item in db.scalars(stmt).all()]

    def _serialize_matching(self, db: Session, matching: Matching) -> dict[str, Any]:
        """序列化搭配主表，并带上明细列表。"""
        sku_list = self._load_skus(db, matching.matching_id)
        return {
            'matchingId': matching.matching_id,
            'userId': matching.user_id,
            'name': matching.name,
            'tagId': matching.tag_id,
            'remark': matching.remark,
            'skuList': sku_list,
            'matchingSkuList': sku_list,
            'createBy': matching.create_by,
            'createTime': matching.create_time.strftime('%Y-%m-%d %H:%M:%S') if matching.create_time else None,
            'updateBy': matching.update_by,
            'updateTime': matching.update_time.strftime('%Y-%m-%d %H:%M:%S') if matching.update_time else None,
            'delFlag': matching.del_flag,
        }

    def _serialize_tag(self, tag: MatchingTag) -> dict[str, Any]:
        """序列化搭配标签。"""
        return {
            'matchingTagId': tag.matching_tag_id,
            'userId': tag.user_id,
            'name': tag.name,
            'displayFlag': tag.display_flag,
            'createBy': tag.create_by,
            'createTime': tag.create_time.strftime('%Y-%m-%d %H:%M:%S') if tag.create_time else None,
            'updateBy': tag.update_by,
            'updateTime': tag.update_time.strftime('%Y-%m-%d %H:%M:%S') if tag.update_time else None,
            'delFlag': tag.del_flag,
        }

    def _extract_sku_list(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        """从请求体里提取搭配 SKU 列表。"""
        source = payload.get('matchingSkuList') or payload.get('skuList') or payload.get('items') or []
        result: list[dict[str, Any]] = []
        if isinstance(source, list):
            for item in source:
                if isinstance(item, dict):
                    result.append(
                        {
                            'productColorId': get_int(item.get('productColorId') or item.get('colorId') or item.get('product_color_id')),
                            'productId': get_int(item.get('productId') or item.get('product_id')),
                            'angle': (item.get('angle') or '').strip() or None,
                        }
                    )
                else:
                    color_id = get_int(item)
                    if color_id > 0:
                        result.append({'productColorId': color_id, 'angle': None})
        elif payload.get('productColorIds'):
            for color_id in split_to_int_list(payload.get('productColorIds')):
                result.append({'productColorId': color_id, 'productId': 0, 'angle': None})
        return [item for item in result if item.get('productColorId')]

    def _resolve_product_id(self, db: Session, product_color_id: int, product_id: int) -> int:
        """根据颜色编号补齐单品编号，避免写入真实表的非空 product_id 失败。"""
        if product_id > 0:
            return product_id
        resolved = db.scalar(select(ProductColor.product_id).where(ProductColor.product_color_id == product_color_id))
        return int(resolved or 0)

    def _build_matching_list_query(self, params: dict[str, Any]) -> Any:
        """按 Java 原项目的 MatchingMapper.xml 构造试穿搭配查询。"""
        stmt = (
            select(
                Matching.matching_id.label('matching_id'),
                Matching.name.label('matching_name'),
                Matching.matching_tag_id.label('matching_tag_id'),
                MatchingSku.matching_sku_id.label('matching_sku_id'),
                ProductColor.product_color_id.label('product_color_id'),
                ProductColor.product_id.label('product_id'),
                ProductColor.front_image_url.label('color_front_img_url'),
                Product.scene_tag_id.label('scene_tag_id'),
                Product.style_tag_id.label('style_tag_id'),
            )
            .select_from(Matching)
            .join(MatchingSku, Matching.matching_id == MatchingSku.matching_id)
            .join(ProductColor, ProductColor.product_color_id == MatchingSku.product_color_id)
            .join(Product, Product.product_id == ProductColor.product_id)
            .where(Matching.del_flag == '0')
            .where(MatchingSku.del_flag == '0')
            .where(ProductColor.del_flag == '0')
            .where(Product.del_flag == '0')
            .order_by(Matching.matching_id.desc(), MatchingSku.matching_sku_id.asc())
        )
        matching_tag_id = get_int(params.get('matchingTagId') or params.get('tagId'))
        if matching_tag_id > 0:
            stmt = stmt.where(Matching.matching_tag_id == matching_tag_id)
        name = (params.get('name') or '').strip()
        if name:
            stmt = stmt.where(Matching.name.like(f'%{name}%'))
        return stmt

    def _serialize_matching_eo(self, row: dict[str, Any]) -> dict[str, Any]:
        """序列化 Java MatchingEO 对应的单品行。"""
        return {
            'matchingId': row['matching_id'],
            'matchingName': row['matching_name'],
            'matchingTagId': row['matching_tag_id'],
            'matchingSkuId': row['matching_sku_id'],
            'productId': row['product_id'],
            'productColorId': row['product_color_id'],
            'colorFrontImgUrl': row['color_front_img_url'],
            'sceneTagId': row['scene_tag_id'],
            'styleTagId': row['style_tag_id'],
        }

    def _group_matching_rows(self, rows: list[dict[str, Any]], params: dict[str, Any]) -> list[dict[str, Any]]:
        """把 Java MatchingEO 行聚合成 MatchingVO 列表，并执行场景/风格弱匹配。"""
        grouped: dict[int, dict[str, Any]] = {}
        scene_tag_id = get_int(params.get('sceneTagId'))
        style_tag_id = get_int(params.get('styleTagId'))

        for row in rows:
            matching_id = int(row['matching_id'])
            eo = self._serialize_matching_eo(row)
            item = grouped.setdefault(
                matching_id,
                {
                    'matchingId': matching_id,
                    'matchingName': row['matching_name'],
                    'matchingTagId': row['matching_tag_id'],
                    'matchingEOList': [],
                },
            )
            item['matchingEOList'].append(eo)

        result: list[dict[str, Any]] = []
        for item in grouped.values():
            eo_list = item['matchingEOList']
            if scene_tag_id > 0 or style_tag_id > 0:
                # Java 原逻辑是弱匹配：任一单品满足场景或风格，即整套搭配命中。
                matched = any(
                    (scene_tag_id > 0 and eo.get('sceneTagId') == scene_tag_id)
                    or (style_tag_id > 0 and eo.get('styleTagId') == style_tag_id)
                    for eo in eo_list
                )
                if not matched:
                    continue
            item['skuCount'] = len(eo_list)
            item['SkuCount'] = len(eo_list)
            result.append(item)
        return result

    def _rewrite_skus(self, db: Session, matching_id: int, sku_list: list[dict[str, Any]], operator: str) -> None:
        """重建搭配 SKU 明细。"""
        stmt = select(MatchingSku).where(MatchingSku.matching_id == matching_id).where(MatchingSku.del_flag == '0')
        for old in db.scalars(stmt).all():
            old.del_flag = '1'
            old.update_by = operator
            old.update_time = datetime.now()
        for item in sku_list:
            product_color_id = get_int(item.get('productColorId'))
            product_id = self._resolve_product_id(db, product_color_id, get_int(item.get('productId')))
            db.add(
                MatchingSku(
                    matching_sku_id=next_numeric_id(db, MatchingSku, MatchingSku.matching_sku_id),
                    matching_id=matching_id,
                    product_color_id=product_color_id,
                    product_id=product_id,
                    create_by=operator,
                    create_time=datetime.now(),
                    update_by=operator,
                    update_time=datetime.now(),
                    del_flag='0',
                )
            )
            db.flush()

    async def add_or_update(
        self,
        db: Session,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """新增或修改搭配。"""
        payload = await read_json_body(request) if request is not None else {}
        matching_id = get_int(payload.get('matchingId') or payload.get('id'))
        operator = resolve_operator(current_user)
        now = datetime.now()
        if matching_id > 0:
            matching = db.scalar(self._base_matching_query(current_user).where(Matching.matching_id == matching_id))
            if matching is None:
                return error('搭配不存在')
            matching.name = (payload.get('name') or matching.name or '').strip() or None
            matching.matching_tag_id = (
                get_int(payload.get('matchingTagId') or payload.get('tagId'), matching.matching_tag_id or 0) or 0
            )
            matching.update_by = operator
            matching.update_time = now
        else:
            matching = Matching(
                matching_id=next_numeric_id(db, Matching, Matching.matching_id),
                name=(payload.get('name') or '').strip() or '',
                matching_tag_id=get_int(payload.get('matchingTagId') or payload.get('tagId'), 0) or 0,
                create_by=operator,
                create_time=now,
                update_by=operator,
                update_time=now,
                del_flag='0',
            )
            db.add(matching)
            db.flush()
        self._rewrite_skus(db, matching.matching_id, self._extract_sku_list(payload), operator)
        db.commit()
        db.refresh(matching)
        return success(data=self._serialize_matching(db, matching))

    async def list(
        self,
        db: Session,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """查询搭配列表。"""
        params = await collect_params(request) if request is not None else {}
        stmt = self._build_matching_list_query(params)
        rows = [dict(row) for row in db.execute(stmt).mappings().all()]
        return success(data=self._group_matching_rows(rows, params))

    async def delete(
        self,
        db: Session,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """逻辑删除搭配。"""
        params = await collect_params(request) if request is not None else {}
        ids = split_to_int_list(params.get('matchingIds') or params.get('matchingId') or params.get('ids'))
        if not ids:
            return error('缺少搭配编号')
        operator = resolve_operator(current_user)
        rows = 0
        for matching in db.scalars(self._base_matching_query(current_user).where(Matching.matching_id.in_(ids))).all():
            matching.del_flag = '1'
            matching.update_by = operator
            matching.update_time = datetime.now()
            for sku in db.scalars(select(MatchingSku).where(MatchingSku.matching_id == matching.matching_id).where(MatchingSku.del_flag == '0')).all():
                sku.del_flag = '1'
                sku.update_by = operator
                sku.update_time = datetime.now()
            rows += 1
        db.commit()
        return to_ajax(rows)

    async def tag_add_or_update(
        self,
        db: Session,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """新增或修改搭配标签。"""
        payload = await read_json_body(request) if request is not None else {}
        tag_id = get_int(payload.get('matchingTagId') or payload.get('id'))
        operator = resolve_operator(current_user)
        now = datetime.now()
        if tag_id > 0:
            tag = db.scalar(self._base_tag_query(current_user).where(MatchingTag.matching_tag_id == tag_id))
            if tag is None:
                return error('搭配标签不存在')
            tag.name = (payload.get('name') or tag.name or '').strip() or None
            tag.display_flag = get_int(payload.get('displayFlag'), tag.display_flag or 0)
            tag.update_by = operator
            tag.update_time = now
        else:
            tag = MatchingTag(
                matching_tag_id=next_numeric_id(db, MatchingTag, MatchingTag.matching_tag_id),
                name=(payload.get('name') or '').strip() or '',
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

    async def tag_list(
        self,
        db: Session,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """查询搭配标签列表。"""
        params = await collect_params(request) if request is not None else {}
        stmt = self._base_tag_query(current_user)
        name = (params.get('name') or '').strip()
        if name:
            stmt = stmt.where(MatchingTag.name.like(f'%{name}%'))
        rows = [self._serialize_tag(item) for item in db.scalars(stmt).all()]
        return success(data=rows)

    async def tag_delete(
        self,
        db: Session,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """逻辑删除搭配标签。"""
        params = await collect_params(request) if request is not None else {}
        ids = split_to_int_list(params.get('matchingTagIds') or params.get('matchingTagId') or params.get('ids'))
        if not ids:
            return error('缺少搭配标签编号')
        operator = resolve_operator(current_user)
        rows = 0
        for tag in db.scalars(self._base_tag_query(current_user).where(MatchingTag.matching_tag_id.in_(ids))).all():
            tag.del_flag = '1'
            tag.update_by = operator
            tag.update_time = datetime.now()
            rows += 1
        db.commit()
        return to_ajax(rows)
