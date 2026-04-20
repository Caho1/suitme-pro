"""空基线版本。

用法说明：
1. 如果当前直接连接已有生产 / 测试库，请执行 `alembic stamp head`。
2. 这份基线不主动创建表，只用于占位。
3. 等 ORM 完整补齐后，再创建后续真实 revision。
"""

from __future__ import annotations

# revision identifiers, used by Alembic.
revision = "20260420_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """当前基线不执行任何 DDL。"""
    pass


def downgrade() -> None:
    """当前基线没有回滚动作。"""
    pass
