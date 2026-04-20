# 开发代理说明（给 Codex / Claude Code）

你现在接手的是 SuitMe Java 后端迁移到 FastAPI 的项目，请严格遵守以下约束：

## 一、契约约束

1. **不要修改任何既有接口的路径、HTTP 方法、请求体字段名、响应体字段名。**
2. 对前端暴露的接口默认使用 `camelCase` 字段名。
3. `AjaxResult` 必须保持松散结构，允许随接口动态追加 key。
4. 分页接口要区分：
   - `TableDataInfo`：`{{code,msg,total,rows}}`
   - MyBatis-Plus 风格：`{{code,msg,data:{{records,total,size,current,pages}}}}`
5. 时间格式统一为 `yyyy-MM-dd HH:mm:ss`。
6. 除明确确认不需要的接口外，不要擅自删接口。
7. `/logout` 建议保留兼容端点，纯 JWT 模式下直接返回成功即可。

## 二、实现风格

1. 逻辑尽量简单，不要加过多兜底。
2. 所有重要类、方法、函数必须写中文注释。
3. 优先拆成：
   - api（协议层）
   - services（业务层）
   - models（ORM）
   - core（基础设施）
4. 优先使用同步 SQLAlchemy，会比 async 版本更贴近原 Java 项目，排查更容易。
5. 不要把敏感配置写回仓库，统一放 `.env`。

## 三、数据库规则

1. 先以 **现网 MySQL 5.7** 为兼容源。
2. 在真实库 schema 未完整导出前，不要做 destructive 的 Alembic autogenerate。
3. `create_by / update_by` 保持写 `sys_user.user_name` 字符串。
4. 软删除默认沿用 `del_flag`。

## 四、优先级

1. 鉴权 + 公共响应
2. 用户 / 角色 / 菜单
3. SUITME 主业务
4. 文件 / OSS
5. 契约测试
6. 新数据库迁移

## 五、外部集成

- AI 数字形象：`POST {{baseUrl}}/models/default`
- AI 穿搭生图：`POST {{baseUrl}}/models/outfit`
- AI 任务查询：`GET {{baseUrl}}/tasks/{{taskId}}`

Bearer Token、超时、JSON 字段名都要保持兼容。
