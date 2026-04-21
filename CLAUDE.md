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

## 六、本地修改到服务器发布链路

后续 Agent 接手时，涉及代码或依赖变更必须走这条链路：

1. **只在本地仓库修改代码**
   - `suitme-model` 本地路径：`/Users/jiahao/Desktop/PythonProject/suitme-model`
   - `suitme-pro` 本地路径：`/Users/jiahao/Desktop/PythonProject/suitme-pro`
   - 不要直接在服务器 `/data/suitme/suitme-*` 里改代码；服务器只用于拉取、安装依赖、重启和验证。

2. **本地验证后提交并推送 GitHub**
   - `suitme-model` 远端：`https://github.com/Caho1/suitme-model.git`
   - `suitme-pro` 远端：`https://github.com/Caho1/suitme-pro.git`
   - 常规命令：
     ```bash
     git status --short
     git add <changed-files>
     git commit -m "<message>"
     git push origin main
     ```

3. **服务器拉取最新代码**
   - 服务器：`root@43.139.129.10`
   - SSH 密钥路径：`/Users/jiahao/Downloads/suitme.pem`
   - 服务器项目目录：
     - `/data/suitme/suitme-model`
     - `/data/suitme/suitme-pro`
   - 拉取示例：
     ```bash
     ssh -i /Users/jiahao/Downloads/suitme.pem root@43.139.129.10
     cd /data/suitme/suitme-model
     git pull --ff-only origin main
     uv sync

     cd /data/suitme/suitme-pro
     git pull --ff-only origin main
     uv sync
     ```

4. **端口和服务关系**
   - `suitme-model` 监听 `9001`，`.env` 里应保持：`SERVICE_PORT=9001`
   - `suitme-pro` 监听 `9000`，`.env` 里应保持：
     - `APP_PORT=9000`
     - `SUITME_AI_BASE_URL=http://127.0.0.1:9001`
   - `suitme-pro` 调用 `suitme-model`，所以改动 model 后通常要先重启 `suitme-model`，再重启 `suitme-pro`。

5. **systemd 管理命令**
   - 服务名：
     - `suitme-model.service`
     - `suitme-pro.service`
   - 常用命令：
     ```bash
     systemctl status suitme-model suitme-pro
     systemctl restart suitme-model
     systemctl restart suitme-pro
     systemctl restart suitme-model suitme-pro
     ```

6. **日志路径**
   - `suitme-model` 日志：`/data/log/suitme-model.log`
   - `suitme-pro` 日志：`/data/log/suitme-pro.log`
   - 查看日志：
     ```bash
     tail -f /data/log/suitme-model.log
     tail -f /data/log/suitme-pro.log
     ```

7. **发布后验证**
   - 服务健康检查：
     ```bash
     curl -sS http://127.0.0.1:9001/health
     curl -sS http://127.0.0.1:9000/
     ```
   - 验证 `suitme-pro -> suitme-model` 调用链：
     ```bash
     curl -sS -i http://127.0.0.1:9000/api/test/getTaskStatus/connectivity-probe
     ```
     这个测试 taskId 不存在时返回业务 404/错误包装是正常的；只要 `suitme-model` 日志出现
     `GET /tasks/connectivity-probe`，说明调用 URL 已经打到 `9001`。
