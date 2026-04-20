
# SuitMe Python / FastAPI 迁移骨架

这个压缩包是给 **本地 Codex / Claude Code 继续开发** 用的基础工程。

它已经把：

- FastAPI 应用入口
- 通用响应结构
- JWT / 密码哈希基础设施
- Alembic 骨架
- **81 条兼容路由骨架**
- 路由清单
- 模块化 PRD
- 架构设计
- 风险说明
- 数据库 schema 导出脚本

先全部准备好了。

## 当前状态

这是一个**可继续开发的基础框架**，不是完整迁移成品。

已完成：

- 应用可以启动。
- `/swagger-ui.html` 与 `/v3/api-docs` 已就位。
- `/captchaImage` 和 `/logout` 已按兼容思路提供最小实现。
- 其余接口已建立路由与服务层骨架，便于继续补业务。

未完成：

- 所有 Java 业务逻辑的完整迁移。
- 真实数据库全量 ORM 对齐。
- 新数据库最终 DDL。
- 完整契约测试快照。

## 本地启动

```bash
cp .env.example .env
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 推荐第一步

先在你本机连真实数据库执行：

```bash
uv run python scripts/inspect_db.py
```

然后再根据导出的 `docs/references/schema_snapshot.json` 补齐 ORM。

## 重要入口

- 文档索引：`docs/INDEX.md`
- 路由清单：`docs/route_inventory.json`
- 原始 PRD：`docs/references/01-原始PRD.md`
- 开发代理说明：`AGENTS.md`
