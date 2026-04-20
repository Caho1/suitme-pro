"""主数据服务。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import Request
from app.core.sqlalchemy_compat import Session, func, select

from app.core.deps import CurrentUser
from app.core.request_utils import collect_params, get_int, read_json_body, split_to_int_list
from app.core.response import error, mp_page, success, to_ajax
from app.models.product import Product, ProductColor
from app.services.base import SkeletonService
from app.services.biz_support import build_mp_page_payload, next_numeric_id, resolve_operator, resolve_user_id


class ProductService(SkeletonService):
    """主数据服务。"""

    def _base_product_query(self, current_user: CurrentUser | None = None) -> Any:
        """构造单品基础查询。"""
        stmt = select(Product).where(Product.del_flag == '0').order_by(Product.product_id.desc())
        if current_user is not None and current_user.user_id is not None:
            stmt = stmt.where(Product.user_id == current_user.user_id)
        return stmt

    def _base_color_query(self) -> Any:
        """构造颜色 SKU 基础查询。"""
        return select(ProductColor).where(ProductColor.del_flag == '0').order_by(ProductColor.product_color_id.asc())

    def _serialize_color(self, color: ProductColor) -> dict[str, Any]:
        """序列化颜色 SKU。"""
        return {
            'productColorId': color.product_color_id,
            'productId': color.product_id,
            'colorName': color.color_name,
            'imageUrl': color.image_url,
            'createBy': color.create_by,
            'createTime': color.create_time.strftime('%Y-%m-%d %H:%M:%S') if color.create_time else None,
            'updateBy': color.update_by,
            'updateTime': color.update_time.strftime('%Y-%m-%d %H:%M:%S') if color.update_time else None,
            'delFlag': color.del_flag,
        }

    def _load_colors(self, db: Session, product_id: int) -> list[dict[str, Any]]:
        """查询单品下的颜色列表。"""
        stmt = self._base_color_query().where(ProductColor.product_id == product_id)
        return [self._serialize_color(item) for item in db.scalars(stmt).all()]

    def _serialize_product(self, db: Session, product: Product) -> dict[str, Any]:
        """序列化单品。"""
        colors = self._load_colors(db, product.product_id)
        return {
            'productId': product.product_id,
            'userId': product.user_id,
            'name': product.name,
            'pictureUrl': product.picture_url,
            'displayFlag': product.display_flag,
            'remark': product.remark,
            'productColorList': colors,
            'createBy': product.create_by,
            'createTime': product.create_time.strftime('%Y-%m-%d %H:%M:%S') if product.create_time else None,
            'updateBy': product.update_by,
            'updateTime': product.update_time.strftime('%Y-%m-%d %H:%M:%S') if product.update_time else None,
            'delFlag': product.del_flag,
        }

    async def add(
        self,
        db: Session,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """新增单品。"""
        payload = await read_json_body(request) if request is not None else {}
        now = datetime.now()
        operator = resolve_operator(current_user)
        product = Product(
            product_id=next_numeric_id(db, Product, Product.product_id),
            user_id=resolve_user_id(current_user, payload),
            name=(payload.get('name') or '').strip() or None,
            picture_url=(payload.get('pictureUrl') or '').strip() or None,
            display_flag=get_int(payload.get('displayFlag'), 1),
            remark=(payload.get('remark') or '').strip() or None,
            create_by=operator,
            create_time=now,
            update_by=operator,
            update_time=now,
            del_flag='0',
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        return success(data=self._serialize_product(db, product))

    async def update(
        self,
        db: Session,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """更新单品。"""
        payload = await read_json_body(request) if request is not None else {}
        product_id = get_int(payload.get('productId') or payload.get('id'))
        if product_id <= 0:
            return error('缺少单品编号')
        product = db.scalar(self._base_product_query(current_user).where(Product.product_id == product_id))
        if product is None:
            return error('单品不存在')
        if 'name' in payload:
            product.name = (payload.get('name') or '').strip() or None
        if 'pictureUrl' in payload:
            product.picture_url = (payload.get('pictureUrl') or '').strip() or None
        if 'displayFlag' in payload:
            product.display_flag = get_int(payload.get('displayFlag'), product.display_flag or 0)
        if 'remark' in payload:
            product.remark = (payload.get('remark') or '').strip() or None
        product.update_by = resolve_operator(current_user)
        product.update_time = datetime.now()
        db.commit()
        db.refresh(product)
        return success(data=self._serialize_product(db, product))

    async def delete(
        self,
        db: Session,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """逻辑删除单品。"""
        params = await collect_params(request) if request is not None else {}
        ids = split_to_int_list(params.get('productIds') or params.get('productId') or params.get('ids'))
        if not ids:
            return error('缺少单品编号')
        operator = resolve_operator(current_user)
        rows = 0
        for product in db.scalars(self._base_product_query(current_user).where(Product.product_id.in_(ids))).all():
            product.del_flag = '1'
            product.update_by = operator
            product.update_time = datetime.now()
            for color in db.scalars(self._base_color_query().where(ProductColor.product_id == product.product_id)).all():
                color.del_flag = '1'
                color.update_by = operator
                color.update_time = datetime.now()
            rows += 1
        db.commit()
        return to_ajax(rows)

    async def update_display_flag(
        self,
        db: Session,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """更新单品展示开关。"""
        payload = await read_json_body(request) if request is not None else {}
        product_id = get_int(payload.get('productId') or payload.get('id'))
        if product_id <= 0:
            return error('缺少单品编号')
        product = db.scalar(self._base_product_query(current_user).where(Product.product_id == product_id))
        if product is None:
            return error('单品不存在')
        product.display_flag = get_int(payload.get('displayFlag'), product.display_flag or 0)
        product.update_by = resolve_operator(current_user)
        product.update_time = datetime.now()
        db.commit()
        return success(data=self._serialize_product(db, product))

    async def page(
        self,
        db: Session,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """按 MyBatis-Plus 风格分页查询单品。"""
        params = await collect_params(request) if request is not None else {}
        page_num = max(1, get_int(params.get('pageNum') or params.get('current'), 1))
        page_size = max(1, get_int(params.get('pageSize') or params.get('size'), 10))
        stmt = self._base_product_query(current_user)
        name = (params.get('name') or '').strip()
        if name:
            stmt = stmt.where(Product.name.like(f'%{name}%'))
        display_flag = params.get('displayFlag')
        if display_flag not in (None, ''):
            stmt = stmt.where(Product.display_flag == get_int(display_flag))
        total = int(db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0)
        rows = list(db.scalars(stmt.offset((page_num - 1) * page_size).limit(page_size)).all())
        return mp_page(
            records=[self._serialize_product(db, item) for item in rows],
            total=total,
            size=page_size,
            current=page_num,
            pages=build_mp_page_payload([], total, page_num, page_size)['pages'],
        )

    async def product_color_add(
        self,
        db: Session,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """新增颜色 SKU。"""
        payload = await read_json_body(request) if request is not None else {}
        product_id = get_int(payload.get('productId'))
        if product_id <= 0:
            return error('缺少单品编号')
        product = db.scalar(self._base_product_query(current_user).where(Product.product_id == product_id))
        if product is None:
            return error('单品不存在')
        now = datetime.now()
        operator = resolve_operator(current_user)
        color = ProductColor(
            product_color_id=next_numeric_id(db, ProductColor, ProductColor.product_color_id),
            product_id=product_id,
            color_name=(payload.get('colorName') or '').strip() or None,
            image_url=(payload.get('imageUrl') or '').strip() or None,
            create_by=operator,
            create_time=now,
            update_by=operator,
            update_time=now,
            del_flag='0',
        )
        db.add(color)
        db.commit()
        return success(data=self._serialize_color(color))

    async def product_color_delete(
        self,
        db: Session,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """逻辑删除颜色 SKU。"""
        params = await collect_params(request) if request is not None else {}
        ids = split_to_int_list(params.get('productColorIds') or params.get('productColorId') or params.get('ids'))
        if not ids:
            return error('缺少颜色编号')
        operator = resolve_operator(current_user)
        rows = 0
        for color in db.scalars(self._base_color_query().where(ProductColor.product_color_id.in_(ids))).all():
            color.del_flag = '1'
            color.update_by = operator
            color.update_time = datetime.now()
            rows += 1
        db.commit()
        return to_ajax(rows)
