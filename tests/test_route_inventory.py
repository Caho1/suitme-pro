
"""路由清单测试。"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def test_route_inventory_count() -> None:
    """确保路由清单数量与文档一致。"""
    inventory = json.loads(Path('docs/route_inventory.json').read_text(encoding='utf-8'))
    assert len(inventory) == 81


def test_all_inventory_routes_exist() -> None:
    """确保文档中的每个路由都已经挂到 FastAPI。"""
    inventory = json.loads(Path('docs/route_inventory.json').read_text(encoding='utf-8'))
    actual = set()
    for route in app.routes:
        path = getattr(route, 'path', None)
        methods = set(getattr(route, 'methods', []))
        if not path:
            continue
        for method in methods:
            if method in {'HEAD', 'OPTIONS'}:
                continue
            actual.add((method, path))
    missing = [(item['method'], item['path']) for item in inventory if (item['method'], item['path']) not in actual]
    assert not missing, missing


def test_captcha_image_contract() -> None:
    """验证码端点应该返回兼容结构。"""
    client = TestClient(app)
    response = client.get('/captchaImage')
    assert response.status_code == 200
    data = response.json()
    assert data['code'] == 200
    assert data['captchaEnabled'] is False
    assert data['uuid'] == ''
    assert data['img'] == ''
