from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

import httpx
import pytest

from app.core.deps import CurrentUser
from app.core.sqlalchemy_compat import Session, create_engine, select, sessionmaker
from app.models.ai import AiJoin, AiOutfit, AiTask
from app.models.base import Base
from app.models.customer import Customer
from app.models.product import ProductColor
from app.services.customer_service import CustomerService
from app.services.outfit_service import OutfitService


@pytest.fixture
def db_session():
    """创建隔离的同步 SQLite 会话。"""
    engine = create_engine('sqlite:///:memory:', future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        class_=Session,
    )
    db = factory()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


@pytest.mark.asyncio
async def test_customer_add_falls_back_to_customer_id_for_ai_user_id(db_session, monkeypatch) -> None:
    """关闭 JWT 时，创建顾客也要给模型服务一个稳定 userId。"""
    service = CustomerService()
    captured: dict[str, object] = {}

    async def fake_read_json_body(request) -> dict[str, object]:  # noqa: ANN001
        return {
            'name': '测试顾客',
            'pictureUrl': 'https://example.com/source.png',
            'bodyProfile': {'gender': '男'},
            'size': '4:3',
        }

    async def fake_generate_digital_image(payload: dict[str, object]) -> dict[str, object]:
        captured.update(payload)
        return {'data': {'taskId': 'model-task-1', 'status': 'submitted'}}

    monkeypatch.setattr('app.services.customer_service.read_json_body', fake_read_json_body)
    monkeypatch.setattr(service.ai_client, 'generate_digital_image', fake_generate_digital_image)

    response = await service.add(
        db=db_session,
        request=object(),
        current_user=CurrentUser(user_name='system'),
    )

    assert response['code'] == 200
    assert response['data']['customerId'] == 1
    assert response['data']['digitalTaskId'] == 'model-task-1'
    assert captured['userId'] == '1'


@pytest.mark.asyncio
async def test_customer_get_digital_img_handles_missing_remote_task(db_session, monkeypatch) -> None:
    """历史 taskId 已失效时，不应再把页面打成 500。"""
    now = datetime.now()
    db_session.add(
        Customer(
            customer_id=63,
            name='debug-star-test',
            picture_url='https://example.com/customer.png',
            digital_task_id='legacy-missing-task',
            create_by='system',
            create_time=now,
            update_by='system',
            update_time=now,
            del_flag='0',
        )
    )
    db_session.commit()

    service = CustomerService()

    async def fake_get_task_status(task_id: str) -> dict[str, object]:
        request = httpx.Request('GET', f'http://unit.test/tasks/{task_id}')
        response = httpx.Response(404, request=request)
        raise httpx.HTTPStatusError('not found', request=request, response=response)

    monkeypatch.setattr(service.ai_client, 'get_task_status', fake_get_task_status)

    response = await service.get_digital_img(
        db=db_session,
        request=SimpleNamespace(query_params={'customerId': '63'}),
        current_user=CurrentUser(user_name='system'),
    )

    assert response['code'] == 200
    assert response['data']['customerId'] == 63
    assert response['data']['taskStatus'] == 'failed'
    assert response['data']['taskErrorMsg'] == '远端数字形象任务不存在或已失效'


def _build_product_color(
    *,
    product_color_id: int,
    product_id: int,
    name: str,
    front: str,
    side: str,
    back: str,
) -> ProductColor:
    """创建测试用颜色 SKU。"""
    now = datetime.now()
    return ProductColor(
        product_color_id=product_color_id,
        product_id=product_id,
        color_name=name,
        front_image_url=front,
        side_image_url=side,
        back_image_url=back,
        create_by='system',
        create_time=now,
        update_by='system',
        update_time=now,
        del_flag='0',
    )


@pytest.mark.asyncio
async def test_generate_outfit_img_uses_matching_list_and_customer_task(db_session, monkeypatch) -> None:
    """穿搭生成要兼容 Java 的 `matchingList + customer.taskId` 语义。"""
    now = datetime.now()
    db_session.add(
        Customer(
            customer_id=42,
            name='liu',
            picture_url='https://example.com/customer.png',
            digital_task_id='body-task-42',
            digital_img_url='https://example.com/body-result.png',
            create_by='system',
            create_time=now,
            update_by='system',
            update_time=now,
            del_flag='0',
        )
    )
    db_session.add_all(
        [
            _build_product_color(
                product_color_id=101,
                product_id=201,
                name='上衣',
                front='https://img.test/top-front.png',
                side='https://img.test/top-side.png',
                back='https://img.test/top-back.png',
            ),
            _build_product_color(
                product_color_id=102,
                product_id=202,
                name='裤子',
                front='https://img.test/pants-front.png',
                side='https://img.test/pants-side.png',
                back='https://img.test/pants-back.png',
            ),
        ]
    )
    db_session.commit()

    service = OutfitService()
    captured_payloads: list[dict[str, object]] = []

    async def fake_read_json_body(request) -> dict[str, object]:  # noqa: ANN001
        return {
            'customerId': 42,
            'matchingList': [
                [
                    {'productColorId': 101, 'productId': 201},
                    {'productColorId': 102, 'productId': 202},
                ]
            ],
        }

    async def fake_generate_outfit_image(payload: dict[str, object]) -> dict[str, object]:
        captured_payloads.append(payload)
        angle = str(payload['angle'])
        return {'data': {'taskId': f'remote-{angle}', 'status': 'submitted'}}

    monkeypatch.setattr('app.services.outfit_service.read_json_body', fake_read_json_body)
    monkeypatch.setattr(service.ai_client, 'generate_outfit_image', fake_generate_outfit_image)

    response = await service.generate_outfit_img(
        db=db_session,
        request=object(),
        current_user=CurrentUser(user_name='system'),
    )

    assert response['code'] == 200
    assert len(response['data']) == 1
    assert [payload['angle'] for payload in captured_payloads] == ['front', 'side', 'back']
    assert all(payload['userId'] == '42' for payload in captured_payloads)
    assert all(payload['taskId'] == 'body-task-42' for payload in captured_payloads)
    assert all(payload['baseModelImageUrl'] == 'https://example.com/body-result.png' for payload in captured_payloads)
    assert all(payload['size'] == '9:16' for payload in captured_payloads)
    assert captured_payloads[0]['outfitImages'] == [
        'https://img.test/top-front.png',
        'https://img.test/pants-front.png',
    ]

    tasks = list(db_session.scalars(select(AiTask)).all())
    assert len(tasks) == 3


@pytest.mark.asyncio
async def test_get_outfit_img_returns_java_outfit_vo_shape(db_session, monkeypatch) -> None:
    """查询结果要返回 front/side/back 三面图片和商品列表。"""
    now = datetime.now()
    db_session.add_all(
        [
            _build_product_color(
                product_color_id=301,
                product_id=401,
                name='西装',
                front='https://img.test/suit-front.png',
                side='https://img.test/suit-side.png',
                back='https://img.test/suit-back.png',
            ),
            _build_product_color(
                product_color_id=302,
                product_id=402,
                name='裤子',
                front='https://img.test/trousers-front.png',
                side='https://img.test/trousers-side.png',
                back='https://img.test/trousers-back.png',
            ),
            AiJoin(
                join_id=1,
                customer_id=42,
                create_by='system',
                create_time=now,
                update_by='system',
                update_time=now,
                del_flag='0',
            ),
            AiOutfit(
                outfit_id=1,
                join_id=1,
                customer_id=42,
                product_id=401,
                product_color_id=301,
                create_by='system',
                create_time=now,
                update_by='system',
                update_time=now,
                del_flag='0',
            ),
            AiOutfit(
                outfit_id=2,
                join_id=1,
                customer_id=42,
                product_id=402,
                product_color_id=302,
                create_by='system',
                create_time=now,
                update_by='system',
                update_time=now,
                del_flag='0',
            ),
            AiTask(
                task_id='task-front',
                join_id=1,
                customer_id=42,
                angle='front',
                task_status='completed',
                image_url='https://cdn.test/front.png',
                size='9:16',
                create_by='system',
                create_time=now,
                update_by='system',
                update_time=now,
                del_flag='0',
            ),
            AiTask(
                task_id='task-back',
                join_id=1,
                customer_id=42,
                angle='back',
                task_status='submitted',
                image_url=None,
                size='9:16',
                create_by='system',
                create_time=now,
                update_by='system',
                update_time=now,
                del_flag='0',
            ),
        ]
    )
    db_session.commit()

    service = OutfitService()

    async def fake_read_json_body(request) -> dict[str, object]:  # noqa: ANN001
        return {'aiJoinList': [{'joinId': 1}]}

    async def fake_get_task_status(task_id: str) -> dict[str, object]:
        return {'data': {'taskId': task_id, 'status': 'completed', 'imageUrl': 'https://cdn.test/back.png'}}

    monkeypatch.setattr('app.services.outfit_service.read_json_body', fake_read_json_body)
    monkeypatch.setattr(service.ai_client, 'get_task_status', fake_get_task_status)

    response = await service.get_outfit_img(
        db=db_session,
        request=object(),
        current_user=CurrentUser(user_name='system'),
    )

    assert response['code'] == 200
    payload = response['data'][0]
    assert payload['frontImgStatus'] == 'completed'
    assert payload['frontImgUrl'] == 'https://cdn.test/front.png'
    assert payload['backImgStatus'] == 'completed'
    assert payload['backImgUrl'] == 'https://cdn.test/back.png'
    assert len(payload['productColorList']) == 2


@pytest.mark.asyncio
async def test_task_page_returns_flat_task_rows_with_cn_fields(db_session, monkeypatch) -> None:
    """穿搭任务分页要兼容 Java 的扁平任务列表。"""
    now = datetime.now()
    db_session.add(
        AiTask(
            task_id='task-front',
            join_id=1,
            customer_id=42,
            angle='front',
            task_status='completed',
            image_url='https://cdn.test/front.png',
            size='9:16',
            create_by='system',
            create_time=now,
            update_by='system',
            update_time=now,
            del_flag='0',
        )
    )
    db_session.commit()

    service = OutfitService()

    async def fake_collect_params(request) -> dict[str, object]:  # noqa: ANN001
        return {'pageNum': 1, 'pageSize': 10}

    monkeypatch.setattr('app.services.outfit_service.collect_params', fake_collect_params)

    response = await service.task_page(
        db=db_session,
        request=object(),
        current_user=CurrentUser(user_name='system'),
    )

    assert response['code'] == 200
    record = response['data']['records'][0]
    assert record['taskId'] == 'task-front'
    assert record['status'] == 'completed'
    assert record['statusCN'] == '已完成'
    assert record['angleCN'] == '正面'
