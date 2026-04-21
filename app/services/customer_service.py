"""顾客服务。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import Request
from app.core.sqlalchemy_compat import Session, func, select

from app.core.deps import CurrentUser
from app.core.request_utils import collect_params, get_int, read_json_body, split_to_int_list
from app.core.response import error, mp_page, success, to_ajax
from app.models.customer import Customer
from app.services.ai_client import AiClient
from app.services.base import SkeletonService
from app.services.biz_support import AI_STATUS_COMPLETED, build_mp_page_payload, extract_ai_submission, json_loads_if_possible, next_numeric_id, resolve_operator, resolve_user_id


class CustomerService(SkeletonService):
    """顾客服务。

    说明：
    1. 这里先按当前已知字段做最小可用迁移。
    2. 真实现网字段如果比当前更多，后续只需要补 ORM 与字段映射即可。
    """

    def __init__(self) -> None:
        self.ai_client = AiClient()

    def _base_query(self, current_user: CurrentUser | None = None) -> Any:
        """构造顾客基础查询。"""
        stmt = select(Customer).where(Customer.del_flag == '0').order_by(Customer.customer_id.desc())
        return stmt

    def _serialize_customer(self, customer: Customer) -> dict[str, Any]:
        """把顾客 ORM 转成前端可直接消费的结构。"""
        data = {
            'customerId': customer.customer_id,
            'name': customer.name,
            'pictureUrl': customer.picture_url,
            'digitalTaskId': customer.digital_task_id,
            'digitalImgUrl': customer.digital_img_url,
            'bodyProfileJson': customer.body_profile_json,
            'bodyProfile': json_loads_if_possible(customer.body_profile_json),
            'createBy': customer.create_by,
            'createTime': customer.create_time.strftime('%Y-%m-%d %H:%M:%S') if customer.create_time else None,
            'updateBy': customer.update_by,
            'updateTime': customer.update_time.strftime('%Y-%m-%d %H:%M:%S') if customer.update_time else None,
            'delFlag': customer.del_flag,
        }
        return {key: value for key, value in data.items() if value is not None}

    def _get_customer_id(self, params: dict[str, Any]) -> int:
        """从请求参数中提取 customerId。"""
        return get_int(params.get('customerId') or params.get('id'))

    async def add(
        self,
        db: Session,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """新增顾客并立即调用 AI 数字形象接口。"""
        payload = await read_json_body(request) if request is not None else {}
        operator = resolve_operator(current_user)
        now = datetime.now()
        customer = Customer(
            customer_id=next_numeric_id(db, Customer, Customer.customer_id),
            name=(payload.get('name') or payload.get('customerName') or '').strip() or None,
            picture_url=(payload.get('pictureUrl') or payload.get('picture') or '').strip() or None,
            create_by=operator,
            create_time=now,
            update_by=operator,
            update_time=now,
            del_flag='0',
        )
        db.add(customer)
        db.flush()

        ai_payload = {
            'userId': resolve_user_id(current_user, payload),
            'pictureUrl': customer.picture_url,
            'bodyProfile': payload.get('bodyProfile') or payload.get('bodyProfileJson'),
            'size': payload.get('size'),
        }
        try:
            ai_response = await self.ai_client.generate_digital_image(ai_payload)
            submission = extract_ai_submission(ai_response)
            customer.digital_task_id = submission['task_id']
            customer.digital_img_url = submission['image_url']
            customer.update_by = operator
            customer.update_time = datetime.now()
            db.commit()
            db.refresh(customer)
            result = self._serialize_customer(customer)
            if submission['status']:
                result['taskStatus'] = submission['status']
            return success(data=result)
        except Exception as exc:
            db.rollback()
            return error(f'调用 AI 数字形象接口失败: {exc}')

    async def get(
        self,
        db: Session,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """查询顾客详情。"""
        params = dict(request.query_params) if request is not None else {}
        customer_id = self._get_customer_id(params)
        if customer_id <= 0:
            return error('缺少顾客编号')
        stmt = self._base_query(current_user).where(Customer.customer_id == customer_id)
        customer = db.scalar(stmt)
        if customer is None:
            return error('顾客不存在')
        return success(data=self._serialize_customer(customer))

    async def get_digital_img(
        self,
        db: Session,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """查询顾客数字形象，如有任务编号则主动轮询外部任务。"""
        params = dict(request.query_params) if request is not None else {}
        customer_id = self._get_customer_id(params)
        if customer_id <= 0:
            return error('缺少顾客编号')
        stmt = self._base_query(current_user).where(Customer.customer_id == customer_id)
        customer = db.scalar(stmt)
        if customer is None:
            return error('顾客不存在')

        task_status = None
        if customer.digital_img_url:
            task_status = AI_STATUS_COMPLETED
        elif customer.digital_task_id:
            response = await self.ai_client.get_task_status(customer.digital_task_id)
            submission = extract_ai_submission(response)
            task_status = submission['status']
            if submission['image_url']:
                customer.digital_img_url = submission['image_url']
                customer.update_by = resolve_operator(current_user)
                customer.update_time = datetime.now()
                db.commit()
        payload = self._serialize_customer(customer)
        if task_status:
            payload['taskStatus'] = task_status
        return success(data=payload)

    async def page(
        self,
        db: Session,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """按 MyBatis-Plus 风格分页查询顾客。"""
        params = await collect_params(request) if request is not None else {}
        page_num = max(1, get_int(params.get('pageNum') or params.get('current'), 1))
        page_size = max(1, get_int(params.get('pageSize') or params.get('size'), 10))
        stmt = self._base_query(current_user)
        name = (params.get('name') or params.get('customerName') or '').strip()
        if name:
            stmt = stmt.where(Customer.name.like(f'%{name}%'))
        total = int(db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0)
        records = list(db.scalars(stmt.offset((page_num - 1) * page_size).limit(page_size)).all())
        return mp_page(
            records=[self._serialize_customer(item) for item in records],
            total=total,
            size=page_size,
            current=page_num,
            pages=build_mp_page_payload([], total, page_num, page_size)['pages'],
        )

    async def delete(
        self,
        db: Session,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """逻辑删除顾客。"""
        params = await collect_params(request) if request is not None else {}
        ids = split_to_int_list(params.get('customerIds') or params.get('customerId') or params.get('ids'))
        if not ids:
            return error('缺少顾客编号')
        operator = resolve_operator(current_user)
        stmt = self._base_query(current_user).where(Customer.customer_id.in_(ids))
        rows = 0
        for customer in db.scalars(stmt).all():
            customer.del_flag = '1'
            customer.update_by = operator
            customer.update_time = datetime.now()
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
        """局部更新顾客。"""
        payload = await read_json_body(request) if request is not None else {}
        customer_id = self._get_customer_id(payload)
        if customer_id <= 0:
            return error('缺少顾客编号')
        stmt = self._base_query(current_user).where(Customer.customer_id == customer_id)
        customer = db.scalar(stmt)
        if customer is None:
            return error('顾客不存在')
        if 'name' in payload or 'customerName' in payload:
            customer.name = (payload.get('name') or payload.get('customerName') or '').strip() or None
        if 'pictureUrl' in payload or 'picture' in payload:
            customer.picture_url = (payload.get('pictureUrl') or payload.get('picture') or '').strip() or None
        if 'digitalTaskId' in payload:
            customer.digital_task_id = (payload.get('digitalTaskId') or '').strip() or None
        if 'digitalImgUrl' in payload:
            customer.digital_img_url = (payload.get('digitalImgUrl') or '').strip() or None
        customer.update_by = resolve_operator(current_user)
        customer.update_time = datetime.now()
        db.commit()
        db.refresh(customer)
        return success(data=self._serialize_customer(customer))
