# SuitMe Python / FastAPI 迁移工程

这个压缩包是给 **本地 Codex / Claude Code 继续开发** 用的迁移工程底座。

它已经把：

- FastAPI 应用入口
- 通用响应结构（`AjaxResult` / `TableDataInfo` / MyBatis-Plus 分页）
- JWT / BCrypt 密码哈希基础设施
- Alembic 骨架
- **81 条兼容路由**
- 路由清单与测试
- 模块化 PRD / 架构设计 / 风险说明
- 数据库 schema 导出脚本

都准备好了。

## 当前状态

这已经不是“只有路由的纯骨架”，而是一个**可启动、可继续补细节**的迁移工程。

已完成：

- 应用可以启动。
- `/swagger-ui.html` 与 `/v3/api-docs` 已就位。
- `/captchaImage` 与 `/logout` 已按兼容思路提供实现。
- `/login`、`/register`、`/getInfo` 已补上可直接连 MySQL 的基础实现。
- `/common/upload`、`/common/uploads`、`/common/download`、`/common/download/resource` 已补上本地磁盘实现。
- `/profile/**` 静态资源挂载已就位。
- AI 测试接口已补成到外部 Python 生图服务的最小透传。
- SUITME 业务主链路已经补上：顾客、搭配、搭配标签、穿搭任务、主数据、分类树、OSS。
- 系统管理核心已经补上：用户、角色、菜单、个人资料、分角色、分菜单、Excel 导出。
- 当前自带 smoke tests 通过：`5 passed`。

仍需继续补齐：

- 与真实现网库字段逐字段核对后的 ORM 完整映射。
- 某些复杂 Java 业务边角逻辑的逐行对齐。
- 新数据库最终 DDL / Alembic 正式迁移链。
- 更完整的契约快照测试与前端联调。

## 本地启动

```bash
cp .env.example .env
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 运行测试

```bash
uv run pytest -q
```

## 推荐第一步

先在你本机连真实数据库执行：

```bash
uv run python scripts/inspect_db.py
```

然后再根据导出的 `docs/references/schema_snapshot.json` 补齐 ORM 与 SQL 细节。

## 重要入口

- 文档索引：`docs/INDEX.md`
- 路由清单：`docs/route_inventory.json`
- 原始 PRD：`docs/references/01-原始PRD.md`
- 开发代理说明：`AGENTS.md`
- 本轮更新说明：`docs/notes/05-本轮更新说明.md`
