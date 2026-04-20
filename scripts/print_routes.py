"""打印当前 FastAPI 路由清单。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.main import app


def main() -> None:
    """输出当前应用的全部业务路由。"""
    routes = []
    for route in app.routes:
        path = getattr(route, 'path', None)
        methods = sorted(list(getattr(route, 'methods', [])))
        if not path or path in {'/openapi.json', '/docs', '/redoc'}:
            continue
        routes.append({'path': path, 'methods': methods, 'name': getattr(route, 'name', '')})
    print(json.dumps(routes, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
