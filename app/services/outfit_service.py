"""穿搭任务服务。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx
from fastapi import Request
from app.core.sqlalchemy_compat import Session, func, select

from app.core.deps import CurrentUser
from app.core.request_utils import collect_params, get_int, read_json_body, split_to_int_list
from app.core.response import error, mp_page, success
from app.models.ai import AiJoin, AiOutfit, AiTask
from app.models.customer import Customer
from app.models.product import ProductColor
from app.services.ai_client import AiClient
from app.services.base import SkeletonService
from app.services.biz_support import (
    AI_STATUS_COMPLETED,
    AI_STATUS_FAILED,
    AI_STATUS_NONE,
    AI_STATUS_PROCESSING,
    AI_STATUS_SUBMITTED,
    build_mp_page_payload,
    ensure_list,
    extract_ai_submission,
    make_task_id,
    next_numeric_id,
    normalize_ai_status,
    pick_first,
    resolve_ai_user_id,
    resolve_operator,
)


ANGLE_IMAGE_ATTRS = {
    'front': 'front_image_url',
    'side': 'side_image_url',
    'back': 'back_image_url',
}

ANGLE_CN_MAP = {
    'front': '正面',
    'side': '侧面',
    'back': '背面',
}

STATUS_CN_MAP = {
    AI_STATUS_NONE: '未提交',
    AI_STATUS_SUBMITTED: '已提交',
    AI_STATUS_PROCESSING: '进行中',
    AI_STATUS_COMPLETED: '已完成',
    AI_STATUS_FAILED: '已失败',
}

VALID_OUTFIT_SIZES = {'1:1', '2:3', '3:2', '3:4', '4:3', '4:5', '5:4', '9:16', '16:9', '21:9'}
DEFAULT_OUTFIT_SIZE = '9:16'


class OutfitService(SkeletonService):
    """穿搭任务服务。"""

    def __init__(self) -> None:
        self.ai_client = AiClient()

    def _base_join_query(self, current_user: CurrentUser | None = None) -> Any:
        """构造穿搭批次基础查询。"""
        stmt = select(AiJoin).where(AiJoin.del_flag == '0').order_by(AiJoin.join_id.desc())
        if current_user is not None and current_user.user_name not in (None, '', 'system'):
            stmt = stmt.where(AiJoin.create_by == current_user.user_name)
        return stmt

    def _base_task_query(self, current_user: CurrentUser | None = None) -> Any:
        """构造穿搭任务基础查询。"""
        stmt = select(AiTask).where(AiTask.del_flag == '0').order_by(AiTask.create_time.desc(), AiTask.task_id.desc())
        if current_user is not None and current_user.user_name not in (None, '', 'system'):
            stmt = stmt.where(AiTask.create_by == current_user.user_name)
        return stmt

    def _status_cn(self, status: str | None) -> str:
        """返回任务状态中文。"""
        return STATUS_CN_MAP.get(normalize_ai_status(status), '')

    def _angle_cn(self, angle: str | None) -> str:
        """返回角度中文。"""
        return ANGLE_CN_MAP.get(str(angle or '').strip().lower(), '')

    def _normalize_outfit_size(self, value: Any) -> str:
        """把旧输入里的尺寸值规范成模型服务可接受的比例。"""
        text = str(value or '').strip()
        if text in VALID_OUTFIT_SIZES:
            return text
        if text.lower() in {'1k', '2k'}:
            return DEFAULT_OUTFIT_SIZE
        return DEFAULT_OUTFIT_SIZE

    def _serialize_task(self, task: AiTask) -> dict[str, Any]:
        """序列化任务记录。"""
        status = normalize_ai_status(task.task_status)
        return {
            'taskId': task.task_id,
            'joinId': task.join_id,
            'customerId': task.customer_id,
            'angle': task.angle,
            'angleCN': self._angle_cn(task.angle),
            'status': status,
            'taskStatus': status,
            'statusCN': self._status_cn(status),
            'imageUrl': task.image_url,
            'size': task.size,
            'createBy': task.create_by,
            'createTime': task.create_time.strftime('%Y-%m-%d %H:%M:%S') if task.create_time else None,
            'updateBy': task.update_by,
            'updateTime': task.update_time.strftime('%Y-%m-%d %H:%M:%S') if task.update_time else None,
            'delFlag': task.del_flag,
        }

    def _serialize_task_page_item(self, task: AiTask) -> dict[str, Any]:
        """序列化任务分页项，兼容 Java `AiTaskVO`。"""
        payload = self._serialize_task(task)
        payload['url'] = task.image_url
        return payload

    def _task_progress(self, status: str | None) -> int:
        """把任务状态折算成前端旧列表页需要的进度值。"""
        normalized = normalize_ai_status(status)
        if normalized == AI_STATUS_COMPLETED:
            return 100
        if normalized == AI_STATUS_PROCESSING:
            return 50
        if normalized == AI_STATUS_FAILED:
            return 0
        if normalized == AI_STATUS_SUBMITTED:
            return 10
        return 0

    def _serialize_legacy_task_page_item(self, task: AiTask) -> dict[str, Any]:
        """序列化旧版 `/tasks/outfit/users/*` 所需的蛇形字段。"""
        status = normalize_ai_status(task.task_status)
        completed_at = None
        if status in {AI_STATUS_COMPLETED, AI_STATUS_FAILED} and task.update_time is not None:
            completed_at = task.update_time.strftime('%Y-%m-%d %H:%M:%S')
        return {
            'task_id': task.task_id,
            'status': status,
            'progress': self._task_progress(status),
            'angle': task.angle,
            'created_at': task.create_time.strftime('%Y-%m-%d %H:%M:%S') if task.create_time else None,
            'completed_at': completed_at,
            'image_url': task.image_url,
            'error_message': None,
        }

    def _serialize_outfit(self, outfit: AiOutfit) -> dict[str, Any]:
        """序列化穿搭明细记录。"""
        return {
            'outfitId': outfit.outfit_id,
            'joinId': outfit.join_id,
            'customerId': outfit.customer_id,
            'productId': outfit.product_id,
            'productColorId': outfit.product_color_id,
            'createBy': outfit.create_by,
            'createTime': outfit.create_time.strftime('%Y-%m-%d %H:%M:%S') if outfit.create_time else None,
            'updateBy': outfit.update_by,
            'updateTime': outfit.update_time.strftime('%Y-%m-%d %H:%M:%S') if outfit.update_time else None,
            'delFlag': outfit.del_flag,
        }

    def _serialize_product_color(self, color: ProductColor) -> dict[str, Any]:
        """序列化颜色 SKU，兼容前端结果页。"""
        return {
            'productColorId': color.product_color_id,
            'productId': color.product_id,
            'colorName': color.color_name,
            'name': color.color_name,
            'imageUrl': color.image_url,
            'frontImageUrl': color.front_image_url,
            'sideImageUrl': color.side_image_url,
            'backImageUrl': color.back_image_url,
            'createBy': color.create_by,
            'createTime': color.create_time.strftime('%Y-%m-%d %H:%M:%S') if color.create_time else None,
            'updateBy': color.update_by,
            'updateTime': color.update_time.strftime('%Y-%m-%d %H:%M:%S') if color.update_time else None,
            'delFlag': color.del_flag,
        }

    def _load_tasks(self, db: Session, join_id: int) -> list[AiTask]:
        """读取批次下的全部任务。"""
        stmt = (
            select(AiTask)
            .where(AiTask.join_id == join_id)
            .where(AiTask.del_flag == '0')
            .order_by(AiTask.create_time.asc(), AiTask.task_id.asc())
        )
        return list(db.scalars(stmt).all())

    def _load_outfits(self, db: Session, join_id: int) -> list[AiOutfit]:
        """读取批次下的全部搭配明细。"""
        stmt = (
            select(AiOutfit)
            .where(AiOutfit.join_id == join_id)
            .where(AiOutfit.del_flag == '0')
            .order_by(AiOutfit.outfit_id.asc())
        )
        return list(db.scalars(stmt).all())

    def _load_product_colors_by_ids(self, db: Session, product_color_ids: list[int]) -> dict[int, ProductColor]:
        """按编号批量读取颜色 SKU。"""
        if not product_color_ids:
            return {}
        stmt = (
            select(ProductColor)
            .where(ProductColor.del_flag == '0')
            .where(ProductColor.product_color_id.in_(product_color_ids))
            .order_by(ProductColor.product_color_id.asc())
        )
        return {int(item.product_color_id): item for item in db.scalars(stmt).all()}

    def _compute_join_status(self, tasks: list[AiTask]) -> str:
        """根据子任务状态汇总批次状态。"""
        statuses = {normalize_ai_status(task.task_status) for task in tasks if task.del_flag == '0'}
        if not statuses:
            return AI_STATUS_NONE
        if statuses == {AI_STATUS_COMPLETED}:
            return AI_STATUS_COMPLETED
        if AI_STATUS_FAILED in statuses and statuses <= {AI_STATUS_FAILED}:
            return AI_STATUS_FAILED
        if AI_STATUS_PROCESSING in statuses:
            return AI_STATUS_PROCESSING
        if AI_STATUS_SUBMITTED in statuses:
            return AI_STATUS_SUBMITTED
        if AI_STATUS_COMPLETED in statuses and AI_STATUS_FAILED in statuses:
            return AI_STATUS_PROCESSING
        return next(iter(statuses), AI_STATUS_NONE) or AI_STATUS_NONE

    def _sync_join_status(self, db: Session, join: AiJoin, operator: str) -> str:
        """根据子任务状态更新批次审计时间。"""
        status = self._compute_join_status(self._load_tasks(db, join.join_id))
        join.update_by = operator
        join.update_time = datetime.now()
        return status

    def _serialize_join(self, db: Session, join: AiJoin) -> dict[str, Any]:
        """序列化批次详情。"""
        tasks = self._load_tasks(db, join.join_id)
        outfits = self._load_outfits(db, join.join_id)
        task_dicts = [self._serialize_task(item) for item in tasks]
        image_list = [item['imageUrl'] for item in task_dicts if item.get('imageUrl')]
        return {
            'joinId': join.join_id,
            'customerId': join.customer_id,
            'matchingId': join.matching_id,
            'status': self._compute_join_status(tasks),
            'statusCN': self._status_cn(self._compute_join_status(tasks)),
            'tasks': task_dicts,
            'outfits': [self._serialize_outfit(item) for item in outfits],
            'outfitImages': image_list,
            'createBy': join.create_by,
            'createTime': join.create_time.strftime('%Y-%m-%d %H:%M:%S') if join.create_time else None,
            'updateBy': join.update_by,
            'updateTime': join.update_time.strftime('%Y-%m-%d %H:%M:%S') if join.update_time else None,
            'delFlag': join.del_flag,
        }

    def _serialize_outfit_vo(self, db: Session, join: AiJoin) -> dict[str, Any]:
        """按 Java `OutfitVO` 形状聚合结果。"""
        tasks = self._load_tasks(db, join.join_id)
        vo = {
            'joinId': join.join_id,
            'frontImgUrl': None,
            'sideImgUrl': None,
            'backImgUrl': None,
            'frontImgStatus': AI_STATUS_NONE,
            'sideImgStatus': AI_STATUS_NONE,
            'backImgStatus': AI_STATUS_NONE,
            'productColorList': [],
        }
        for task in tasks:
            angle = str(task.angle or '').strip().lower()
            if angle not in ANGLE_IMAGE_ATTRS:
                continue
            status = normalize_ai_status(task.task_status)
            vo[f'{angle}ImgStatus'] = status
            if task.image_url:
                vo[f'{angle}ImgUrl'] = task.image_url

        outfits = self._load_outfits(db, join.join_id)
        product_color_ids = [int(item.product_color_id) for item in outfits if item.product_color_id]
        product_color_map = self._load_product_colors_by_ids(db, product_color_ids)
        vo['productColorList'] = [
            self._serialize_product_color(product_color_map[color_id])
            for color_id in product_color_ids
            if color_id in product_color_map
        ]
        return vo

    def _load_customer(self, db: Session, customer_id: int) -> Customer | None:
        """读取顾客信息。"""
        if customer_id <= 0:
            return None
        stmt = select(Customer).where(Customer.customer_id == customer_id).where(Customer.del_flag == '0')
        return db.scalar(stmt)

    def _extract_product_color_ids(self, value: Any) -> list[int]:
        """从任意嵌套输入里提取颜色 SKU 编号。"""
        ids: list[int] = []

        def append_id(raw: Any) -> None:
            parsed = get_int(raw)
            if parsed > 0:
                ids.append(parsed)

        def walk(item: Any) -> None:
            if item in (None, ''):
                return
            if isinstance(item, list | tuple | set):
                for sub_item in item:
                    walk(sub_item)
                return
            if isinstance(item, dict):
                nested = item.get('matchingEOList') or item.get('productColorList') or item.get('matchingList') or item.get('skuList')
                if isinstance(nested, list):
                    walk(nested)
                raw_ids = item.get('productColorIds') or item.get('ids')
                if raw_ids not in (None, ''):
                    ids.extend(split_to_int_list(raw_ids))
                append_id(item.get('productColorId') or item.get('colorId'))
                return
            append_id(item)

        walk(value)

        deduped: list[int] = []
        seen: set[int] = set()
        for color_id in ids:
            if color_id in seen:
                continue
            seen.add(color_id)
            deduped.append(color_id)
        return deduped

    def _resolve_matching_colors(self, db: Session, value: Any) -> list[ProductColor]:
        """把前端传来的搭配项转成颜色 SKU 实体列表。"""
        color_ids = self._extract_product_color_ids(value)
        if not color_ids:
            return []
        color_map = self._load_product_colors_by_ids(db, color_ids)
        return [color_map[color_id] for color_id in color_ids if color_id in color_map]

    def _resolve_matching_groups(self, db: Session, payload: dict[str, Any]) -> list[list[ProductColor]]:
        """解析本次要生图的多套搭配。"""
        raw_matching_list = payload.get('matchingList')
        groups: list[list[ProductColor]] = []
        if isinstance(raw_matching_list, list) and raw_matching_list:
            for item in raw_matching_list:
                colors = self._resolve_matching_colors(db, item)
                if colors:
                    groups.append(colors)
            if groups:
                return groups

        colors = self._resolve_matching_colors(db, payload)
        return [colors] if colors else []

    def _resolve_requested_angles(self, payload: dict[str, Any], *, default_all_angles: bool) -> list[str]:
        """解析本次需要生成的角度列表。"""
        raw_angles: list[Any] = []
        if payload.get('angles'):
            raw_angles = ensure_list(payload.get('angles'))
        elif payload.get('angle') not in (None, ''):
            raw_angles = [payload.get('angle')]

        resolved: list[str] = []
        seen: set[str] = set()
        for item in raw_angles:
            angle = str(item or '').strip().lower()
            if angle not in ANGLE_IMAGE_ATTRS or angle in seen:
                continue
            seen.add(angle)
            resolved.append(angle)

        if resolved:
            return resolved
        return ['front', 'side', 'back'] if default_all_angles else ['front']

    def _collect_angle_urls(self, colors: list[ProductColor], angle: str) -> list[str]:
        """按角度聚合商品图 URL；缺任意一张则整角度跳过。"""
        image_attr = ANGLE_IMAGE_ATTRS[angle]
        urls: list[str] = []
        for color in colors:
            image_url = getattr(color, image_attr, None)
            if not image_url:
                return []
            urls.append(str(image_url))
        return urls

    def _build_remote_payload(
        self,
        payload: dict[str, Any],
        current_user: CurrentUser | None,
        customer: Customer | None,
        *,
        angle: str,
        outfit_images: list[str],
    ) -> dict[str, Any]:
        """构造调用模型服务的请求体。"""
        customer_id = customer.customer_id if customer is not None else get_int(payload.get('customerId'), 0) or None
        remote_payload = {
            'userId': resolve_ai_user_id(current_user, payload, customer_id),
            'taskId': (
                (customer.digital_task_id if customer is not None else None)
                or pick_first(payload, 'bodyTaskId', 'baseModelTaskId', 'digitalTaskId', 'taskId')
            ),
            'angle': angle,
            'outfitImages': outfit_images,
            'size': self._normalize_outfit_size(payload.get('size')),
        }
        base_model_image_url = (
            (customer.digital_img_url if customer is not None else None)
            or pick_first(payload, 'baseModelImageUrl', 'digitalImgUrl', 'baseModelImage', 'imageUrl')
        )
        if base_model_image_url:
            remote_payload['baseModelImageUrl'] = base_model_image_url
        return remote_payload

    def _mark_task_failed(self, task: AiTask, operator: str) -> None:
        """把远端已失效的任务在本地标记为失败。"""
        task.task_status = AI_STATUS_FAILED
        task.update_by = operator
        task.update_time = datetime.now()

    async def _refresh_task(self, db: Session, task: AiTask, operator: str) -> None:
        """主动刷新单个任务状态。"""
        try:
            response = await self.ai_client.get_task_status(task.task_id)
        except httpx.HTTPStatusError as exc:
            if exc.response is None or exc.response.status_code != 404:
                raise
            self._mark_task_failed(task, operator)
            return

        parsed = extract_ai_submission(response)
        task.task_status = parsed['status'] or task.task_status
        if parsed['image_url']:
            task.image_url = parsed['image_url']
        task.update_by = operator
        task.update_time = datetime.now()

        outfit = (
            db.scalar(select(AiOutfit).where(AiOutfit.join_id == task.join_id).where(AiOutfit.del_flag == '0').limit(1))
        )
        if outfit is not None:
            outfit.update_by = operator
            outfit.update_time = datetime.now()

    async def generate_outfit_img(
        self,
        db: Session,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """创建穿搭生图任务。"""
        payload = await read_json_body(request) if request is not None else {}
        operator = resolve_operator(current_user)
        now = datetime.now()
        customer_id = get_int(payload.get('customerId'), 0)

        if customer_id <= 0:
            return error('请选择用户')

        customer = self._load_customer(db, customer_id)

        if customer_id > 0 and customer is None:
            return error('顾客不存在')

        preview_payload = self._build_remote_payload(payload, current_user, customer, angle='front', outfit_images=[])
        if not preview_payload.get('taskId') and not preview_payload.get('baseModelImageUrl'):
            return error('请先生成顾客数字形象')

        matching_groups = self._resolve_matching_groups(db, payload)
        fallback_images = [
            str(item).strip()
            for item in ensure_list(payload.get('outfitImages') or payload.get('images') or payload.get('urls'))
            if str(item).strip()
        ]
        if not matching_groups and not fallback_images:
            return error('请选择至少1个单品')
        if not matching_groups:
            matching_groups = [[]]

        created_joins: list[AiJoin] = []

        try:
            for colors in matching_groups:
                join = AiJoin(
                    join_id=next_numeric_id(db, AiJoin, AiJoin.join_id),
                    customer_id=customer_id or None,
                    create_by=operator,
                    create_time=now,
                    update_by=operator,
                    update_time=now,
                    del_flag='0',
                )
                db.add(join)
                db.flush()

                for color in colors:
                    db.add(
                        AiOutfit(
                            outfit_id=next_numeric_id(db, AiOutfit, AiOutfit.outfit_id),
                            join_id=join.join_id,
                            customer_id=join.customer_id,
                            product_id=color.product_id,
                            product_color_id=color.product_color_id,
                            create_by=operator,
                            create_time=now,
                            update_by=operator,
                            update_time=now,
                            del_flag='0',
                        )
                    )
                    db.flush()

                for angle in self._resolve_requested_angles(payload, default_all_angles=bool(colors)):
                    outfit_images = self._collect_angle_urls(colors, angle) if colors else fallback_images
                    if not outfit_images:
                        continue

                    remote_payload = self._build_remote_payload(
                        payload,
                        current_user,
                        customer,
                        angle=angle,
                        outfit_images=outfit_images,
                    )
                    remote_response = await self.ai_client.generate_outfit_image(remote_payload)
                    parsed = extract_ai_submission(remote_response)

                    db.add(
                        AiTask(
                            task_id=parsed['task_id'] or make_task_id('outfit'),
                            join_id=join.join_id,
                            customer_id=join.customer_id,
                            angle=angle,
                            task_status=parsed['status'] or AI_STATUS_SUBMITTED,
                            image_url=parsed['image_url'],
                            size=self._normalize_outfit_size(payload.get('size')),
                            create_by=operator,
                            create_time=now,
                            update_by=operator,
                            update_time=now,
                            del_flag='0',
                        )
                    )
                    db.flush()

                self._sync_join_status(db, join, operator)
                created_joins.append(join)

            db.commit()
            for join in created_joins:
                db.refresh(join)
            return success(data=[self._serialize_join(db, join) for join in created_joins])
        except Exception as exc:
            db.rollback()
            return error(f'调用 AI 穿搭生图接口失败: {exc}')

    async def get_outfit_img(
        self,
        db: Session,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """按 Java `OutfitVO` 形状聚合穿搭结果。"""
        payload = await read_json_body(request) if request is not None else {}
        operator = resolve_operator(current_user)

        join_ids: list[int] = []
        ai_join_list = payload.get('aiJoinList')
        if isinstance(ai_join_list, list):
            for item in ai_join_list:
                join_id = get_int(item.get('joinId') if isinstance(item, dict) else item)
                if join_id > 0:
                    join_ids.append(join_id)
        else:
            join_id = get_int(payload.get('joinId'))
            if join_id > 0:
                join_ids.append(join_id)
            else:
                task_id = payload.get('taskId')
                if task_id:
                    task = db.get(AiTask, str(task_id))
                    if task is not None and task.del_flag == '0':
                        join_ids.append(int(task.join_id))
                else:
                    customer_id = get_int(payload.get('customerId'))
                    if customer_id > 0:
                        stmt = self._base_join_query(current_user).where(AiJoin.customer_id == customer_id)
                        join_ids.extend(int(item.join_id) for item in db.scalars(stmt).all())

        if not join_ids:
            return error('穿搭任务不存在')

        vo_list: list[dict[str, Any]] = []
        for join_id in join_ids:
            join = db.scalar(self._base_join_query(current_user).where(AiJoin.join_id == join_id))
            if join is None:
                continue
            for task in self._load_tasks(db, join.join_id):
                if normalize_ai_status(task.task_status) in {AI_STATUS_COMPLETED, AI_STATUS_FAILED}:
                    continue
                await self._refresh_task(db, task, operator)
            self._sync_join_status(db, join, operator)
            vo_list.append(self._serialize_outfit_vo(db, join))

        db.commit()
        return success(data=vo_list)

    async def get_task_status(
        self,
        db: Session,
        taskId: str,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """透传外部任务查询，并顺手回写本地状态。"""
        try:
            response = await self.ai_client.get_task_status(taskId)
        except httpx.HTTPStatusError as exc:
            if exc.response is None or exc.response.status_code != 404:
                raise
            task = db.get(AiTask, str(taskId))
            if task is not None and task.del_flag == '0':
                self._mark_task_failed(task, resolve_operator(current_user))
                join = db.get(AiJoin, task.join_id)
                if join is not None and join.del_flag == '0':
                    self._sync_join_status(db, join, resolve_operator(current_user))
                db.commit()
            return success(
                data={
                    'taskId': taskId,
                    'status': AI_STATUS_FAILED,
                    'taskStatus': AI_STATUS_FAILED,
                    'image': None,
                    'imageUrl': None,
                    'resultUrl': None,
                    'errorMessage': '远端任务不存在或已失效',
                }
            )

        task = db.get(AiTask, str(taskId))
        if task is not None and task.del_flag == '0':
            parsed = extract_ai_submission(response)
            task.task_status = parsed['status'] or task.task_status
            if parsed['image_url']:
                task.image_url = parsed['image_url']
            task.update_by = resolve_operator(current_user)
            task.update_time = datetime.now()
            join = db.get(AiJoin, task.join_id)
            if join is not None and join.del_flag == '0':
                self._sync_join_status(db, join, resolve_operator(current_user))
            outfit = (
                db.scalar(select(AiOutfit).where(AiOutfit.join_id == task.join_id).where(AiOutfit.del_flag == '0').limit(1))
            )
            if outfit is not None:
                outfit.update_by = resolve_operator(current_user)
                outfit.update_time = datetime.now()
            db.commit()
        return response

    async def task_page(
        self,
        db: Session,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """按 Java `AiTaskVO` 形状分页查询穿搭任务。"""
        params = await collect_params(request) if request is not None else {}
        page_num = max(1, get_int(params.get('pageNum') or params.get('current'), 1))
        page_size = max(1, get_int(params.get('pageSize') or params.get('size'), 10))
        stmt = self._base_task_query(current_user)
        customer_id = get_int(params.get('customerId'))
        if customer_id > 0:
            stmt = stmt.where(AiTask.customer_id == customer_id)
        status = str(params.get('status') or '').strip().lower()
        if status:
            stmt = stmt.where(AiTask.task_status == status)
        total = int(db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0)
        rows = list(db.scalars(stmt.offset((page_num - 1) * page_size).limit(page_size)).all())
        return mp_page(
            records=[self._serialize_task_page_item(item) for item in rows],
            total=total,
            size=page_size,
            current=page_num,
            pages=build_mp_page_payload([], total, page_num, page_size)['pages'],
        )

    async def legacy_task_page(
        self,
        db: Session,
        user_id: str,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """兼容前端旧版 `/tasks/outfit/users/{userId|all}` 任务列表。"""
        params = await collect_params(request) if request is not None else {}
        page_num = max(1, get_int(params.get('pageNum') or params.get('current'), 1))
        page_size = max(1, get_int(params.get('pageSize') or params.get('size'), 10))

        stmt = self._base_task_query(current_user)
        customer_id = get_int(user_id)
        if customer_id > 0:
            stmt = stmt.where(AiTask.customer_id == customer_id)

        total = int(db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0)
        rows = list(db.scalars(stmt.offset((page_num - 1) * page_size).limit(page_size)).all())

        return mp_page(
            records=[self._serialize_legacy_task_page_item(item) for item in rows],
            total=total,
            size=page_size,
            current=page_num,
            pages=build_mp_page_payload([], total, page_num, page_size)['pages'],
        )
