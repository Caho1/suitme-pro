"""导出真实数据库 schema 快照。

用法：

```bash
uv run python scripts/inspect_db.py
```

说明：
1. 这个脚本不会改数据库。
2. 它会读取 `.env` 中的 `DATABASE_URL`。
3. 输出结果写到 `docs/references/schema_snapshot.json`。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import create_engine, inspect

from app.core.config import get_settings


def main() -> None:
    """连接数据库并导出表结构快照。"""
    settings = get_settings()
    engine = create_engine(settings.database_url, future=True)
    inspector = inspect(engine)
    snapshot: dict[str, object] = {'tables': []}

    for table_name in sorted(inspector.get_table_names()):
        columns = []
        for column in inspector.get_columns(table_name):
            columns.append(
                {
                    'name': column.get('name'),
                    'type': str(column.get('type')),
                    'nullable': column.get('nullable'),
                    'default': str(column.get('default')),
                }
            )
        snapshot['tables'].append(
            {
                'table': table_name,
                'columns': columns,
                'primary_key': inspector.get_pk_constraint(table_name),
                'indexes': inspector.get_indexes(table_name),
            }
        )

    output = PROJECT_ROOT / 'docs/references/schema_snapshot.json'
    output.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'已输出 schema 快照：{output}')


if __name__ == '__main__':
    main()
