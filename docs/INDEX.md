
# 文档索引

这个目录是给你本地继续接着写代码用的。

## 一、需求文档（PRD 拆分）

- `prd/00-总览.md`
- `prd/01-范围与保留接口.md`
- `prd/02-接口兼容策略.md`
- `prd/03-鉴权与安全.md`
- `prd/04-业务模块拆分.md`
- `prd/05-系统管理拆分.md`
- `prd/06-外部集成.md`
- `prd/07-数据库与迁移.md`
- `prd/08-测试与切换.md`

## 二、架构设计

- `architecture/01-总体架构.md`
- `architecture/02-目录与分层.md`
- `architecture/03-请求链路与契约测试.md`

## 三、注意事项

- `notes/01-PRD修订建议.md`
- `notes/02-仓库风险与注意事项.md`
- `notes/03-开发顺序建议.md`
- `notes/04-凭证与仓库操作说明.md`
- `notes/05-本轮更新说明.md`

## 四、引用资料

- `references/01-原始PRD.md`
- `references/02-仓库识别摘要.md`
- `references/schema_snapshot.json`（运行 `scripts/inspect_db.py` 后生成）
- `route_inventory.json`
- `route_inventory.md`

## 五、当前骨架统计

- 兼容路由：**81 条**
- 建议保留 `/logout` 兼容端点：**已纳入骨架**
- OpenAPI 文档地址：`/swagger-ui.html`
- OpenAPI JSON 地址：`/v3/api-docs`
