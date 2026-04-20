
"""OpenAPI 路径测试。"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_swagger_url() -> None:
    """Swagger UI 地址应保持兼容。"""
    client = TestClient(app)
    response = client.get('/swagger-ui.html')
    assert response.status_code == 200


def test_openapi_json_url() -> None:
    """OpenAPI JSON 地址应保持兼容。"""
    client = TestClient(app)
    response = client.get('/v3/api-docs')
    assert response.status_code == 200
