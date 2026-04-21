"""穿搭任务服务。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import Request
from app.core.sqlalchemy_compat import Session, func, select

from app.core.deps import CurrentUser
from app.core.request_utils import collect_params, get_int, read_json_body
from app.core.response import error, mp_page, success
from app.models.ai import AiJoin, AiOutfit, AiTask
from app.models.customer import Customer
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
    resolve_operator,
    resolve_user_id,
)


class OutfitService(SkeletonService):
    """穿搭任务服务。"""

    def __init__(self) -> None:
        self.ai_client = AiClient()

    def _base_join_query(self, current_user: CurrentUser | None = None) -> Any:
        """构造穿搭批次基础查询。"""
        stmt = select(AiJoin).where(AiJoin.del_flag == '0').order_by(AiJoin.join_id.desc())
        return stmt

    def _serialize_task(self, task: AiTask) -> dict[str, Any]:
        """序列化任务记录。"""
        return {
            'taskId': task.task_id,
            'joinId': task.join_id,
            'angle': task.angle,
            'taskStatus': task.task_status,
            'imageUrl': task.image_url,
            'createBy': task.create_by,
            'createTime': task.create_time.strftime('%Y-%m-%d %H:%M:%S') if task.create_time else None,
            'updateBy': task.update_by,
            'updateTime': task.update_time.strftime('%Y-%m-%d %H:%M:%S') if task.update_time else None,
            'delFlag': task.del_flag,
        }

    def _serialize_outfit(self, outfit: AiOutfit) -> dict[str, Any]:
        """序列化穿搭角度记录。"""
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

    def _load_tasks(self, db: Session, join_id: int) -> list[AiTask]:
        """读取批次下的全部任务。"""
        stmt = select(AiTask).where(AiTask.join_id == join_id).where(AiTask.del_flag == '0').order_by(AiTask.create_time.asc(), AiTask.task_id.asc())
        return list(db.scalars(stmt).all())

    def _load_outfits(self, db: Session, join_id: int) -> list[AiOutfit]:
        """读取批次下的全部角度记录。"""
        stmt = select(AiOutfit).where(AiOutfit.join_id == join_id).where(AiOutfit.del_flag == '0').order_by(AiOutfit.outfit_id.asc())
        return list(db.scalars(stmt).all())

    def _compute_join_status(self, tasks: list[AiTask]) -> str:
        """根据子任务状态计算批次状态，不写数据库。"""
        statuses = {normalize_ai_status(task.task_status) for task in tasks if task.del_flag == '0'}
        if not statuses:
            return AI_STATUS_NONE
        elif statuses == {AI_STATUS_COMPLETED}:
            return AI_STATUS_COMPLETED
        elif AI_STATUS_FAILED in statuses and AI_STATUS_COMPLETED not in statuses and AI_STATUS_PROCESSING not in statuses and AI_STATUS_SUBMITTED not in statuses:
            return AI_STATUS_FAILED
        elif AI_STATUS_PROCESSING in statuses:
            return AI_STATUS_PROCESSING
        elif AI_STATUS_SUBMITTED in statuses:
            return AI_STATUS_SUBMITTED
        elif AI_STATUS_COMPLETED in statuses and AI_STATUS_FAILED in statuses:
            return AI_STATUS_PROCESSING
        return next(iter(statuses), AI_STATUS_NONE) or AI_STATUS_NONE

    def _sync_join_status(self, db: Session, join: AiJoin, operator: str) -> str:
        """根据子任务状态汇总批次状态，只更新审计时间。"""
        tasks = self._load_tasks(db, join.join_id)
        status = self._compute_join_status(tasks)
        join.update_by = operator
        join.update_time = datetime.now()
        return status

    def _serialize_join(self, db: Session, join: AiJoin) -> dict[str, Any]:
        """序列化穿搭批次，并带上任务与图片聚合结果。"""
        tasks = self._load_tasks(db, join.join_id)
        outfits = self._load_outfits(db, join.join_id)
        task_dicts = [self._serialize_task(item) for item in tasks]
        image_list = [item['imageUrl'] for item in task_dicts if item.get('imageUrl')]
        return {
            'joinId': join.join_id,
            'customerId': join.customer_id,
            'matchingId': join.matching_id,
            'status': self._compute_join_status(tasks),
            'tasks': task_dicts,
            'outfits': [self._serialize_outfit(item) for item in outfits],
            'outfitImages': image_list,
            'createBy': join.create_by,
            'createTime': join.create_time.strftime('%Y-%m-%d %H:%M:%S') if join.create_time else None,
            'updateBy': join.update_by,
            'updateTime': join.update_time.strftime('%Y-%m-%d %H:%M:%S') if join.update_time else None,
            'delFlag': join.del_flag,
        }

    def _resolve_angles(self, payload: dict[str, Any]) -> list[str]:
        """解析本次需要生成的角度列表。"""
        angles = []
        if payload.get('angles'):
            angles = [str(item).strip() for item in ensure_list(payload.get('angles')) if str(item).strip()]
        elif payload.get('angle'):
            angles = [str(payload.get('angle')).strip()]
        return angles or ['front']

    def _build_remote_payload(self, payload: dict[str, Any], current_user: CurrentUser | None, task_id: str, angle: str) -> dict[str, Any]:
        """构造外部 AI 穿搭生图请求体。"""
        return {
            'userId': resolve_user_id(current_user, payload),
            'taskId': task_id,
            'angle': angle,
            'outfitImages': payload.get('outfitImages') or payload.get('images') or [],
            'size': payload.get('size'),
        }

    async def _refresh_task(self, db: Session, task: AiTask, operator: str) -> None:
        """主动刷新单个任务状态。"""
        response = await self.ai_client.get_task_status(task.task_id)
        parsed = extract_ai_submission(response)
        task.task_status = parsed['status'] or task.task_status
        if parsed['image_url']:
            task.image_url = parsed['image_url']
        task.update_by = operator
        task.update_time = datetime.now()
        outfit = db.scalar(
            select(AiOutfit)
            .where(AiOutfit.join_id == task.join_id)
            .where(AiOutfit.del_flag == '0')
            .limit(1)
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
        join = AiJoin(
            join_id=next_numeric_id(db, AiJoin, AiJoin.join_id),
            customer_id=get_int(payload.get('customerId'), 0) or None,
            create_by=operator,
            create_time=now,
            update_by=operator,
            update_time=now,
            del_flag='0',
        )
        db.add(join)
        db.flush()

        try:
            for angle in self._resolve_angles(payload):
                local_task_id = make_task_id('outfit')
                remote_payload = self._build_remote_payload(payload, current_user, local_task_id, angle)
                remote_response = await self.ai_client.generate_outfit_image(remote_payload)
                parsed = extract_ai_submission(remote_response)
                task_id = parsed['task_id'] or local_task_id
                task_status = parsed['status'] or AI_STATUS_SUBMITTED
                db.add(
                    AiOutfit(
                        outfit_id=next_numeric_id(db, AiOutfit, AiOutfit.outfit_id),
                        join_id=join.join_id,
                        customer_id=join.customer_id,
                        product_id=get_int(payload.get('productId'), 0) or None,
                        product_color_id=get_int(payload.get('productColorId'), 0) or None,
                        create_by=operator,
                        create_time=now,
                        update_by=operator,
                        update_time=now,
                        del_flag='0',
                    )
                )
                db.flush()
                db.add(
                    AiTask(
                        task_id=task_id,
                        join_id=join.join_id,
                        customer_id=join.customer_id,
                        angle=angle,
                        task_status=task_status,
                        image_url=parsed['image_url'],
                        size=str(payload.get('size') or '1K'),
                        create_by=operator,
                        create_time=now,
                        update_by=operator,
                        update_time=now,
                        del_flag='0',
                    )
                )
                db.flush()
            self._sync_join_status(db, join, operator)
            db.commit()
            db.refresh(join)
            return success(data=self._serialize_join(db, join))
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
        """聚合获取穿搭图，并在必要时刷新未完成任务状态。"""
        payload = await read_json_body(request) if request is not None else {}
        join_id = get_int(payload.get('joinId'))
        task_id = payload.get('taskId')
        operator = resolve_operator(current_user)

        join: AiJoin | None = None
        if join_id > 0:
            join = db.scalar(self._base_join_query(current_user).where(AiJoin.join_id == join_id))
        elif task_id:
            task = db.get(AiTask, str(task_id))
            if task is not None and task.del_flag == '0':
                join = db.scalar(self._base_join_query(current_user).where(AiJoin.join_id == task.join_id))
        else:
            customer_id = get_int(payload.get('customerId'))
            stmt = self._base_join_query(current_user)
            if customer_id > 0:
                stmt = stmt.where(AiJoin.customer_id == customer_id)
            join = db.scalar(stmt.limit(1))

        if join is None:
            return error('穿搭任务不存在')

        for task in self._load_tasks(db, join.join_id):
            if normalize_ai_status(task.task_status) in {AI_STATUS_COMPLETED, AI_STATUS_FAILED}:
                continue
            await self._refresh_task(db, task, operator)
        self._sync_join_status(db, join, operator)
        db.commit()
        return success(data=self._serialize_join(db, join))

    async def get_task_status(
        self,
        db: Session,
        taskId: str,
        request: Request | None = None,
        current_user: CurrentUser | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """透传外部任务查询，并顺手回写本地状态。"""
        response = await self.ai_client.get_task_status(taskId)
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
            outfit = db.scalar(
                select(AiOutfit)
                .where(AiOutfit.join_id == task.join_id)
                .where(AiOutfit.del_flag == '0')
                .limit(1)
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
        """按 MyBatis-Plus 风格分页查询穿搭任务。"""
        params = await collect_params(request) if request is not None else {}
        page_num = max(1, get_int(params.get('pageNum') or params.get('current'), 1))
        page_size = max(1, get_int(params.get('pageSize') or params.get('size'), 10))
        stmt = self._base_join_query(current_user)
        customer_id = get_int(params.get('customerId'))
        if customer_id > 0:
            stmt = stmt.where(AiJoin.customer_id == customer_id)
        status = (params.get('status') or '').strip().lower()
        if status:
            stmt = stmt.join(AiTask, AiTask.join_id == AiJoin.join_id).where(AiTask.task_status == status)
        total = int(db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0)
        rows = list(db.scalars(stmt.offset((page_num - 1) * page_size).limit(page_size)).all())
        return mp_page(
            records=[self._serialize_join(db, item) for item in rows],
            total=total,
            size=page_size,
            current=page_num,
            pages=build_mp_page_payload([], total, page_num, page_size)['pages'],
        )
