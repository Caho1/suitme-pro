# SuitMe Java → Python/FastAPI 迁移 PRD

> 生成时间：2026-04-20
> 最后修订：2026-04-20（基于用户 8 条确认回复收紧）
> 状态：**APPROVED**，可进入 M0 实现
---
## 0. 一句话目标

把基于若依（Spring Boot 3.5.4）的 `suitme-java` 后端重写成一个 Python/FastAPI 服务，**所有对前端暴露的 HTTP 接口**（路径、方法、请求体、响应结构、HTTP 头、鉴权方式）**完全保持一致**，使前端可以**无需改动**把 baseUrl 从 Java 服务指向新的 Python 服务完成**热切换**；同时删掉若依自带的管理后台前端与无关模块，保留核心业务 + 最小用户/角色/菜单。

---

## 1. 需求速查表（office-hours 已确认）

| 项 | 决策 |
| --- | --- |
| 接口迁移范围 | **业务 + 完整系统管理（用户/角色/菜单三件套的 RuoYi 完整分配逻辑）**；丢弃 `/getRouters`、monitor、Quartz、代码生成、Swagger demo、dept/dict/config/post/notice/operlog/logininfor |
| 数据库 | **MySQL 5.7**，继续连现有库，沿用原表名、原字段、原结构；SQL 方言需兼容 5.7（不用 CTE / WINDOW 函数 / `JSON_TABLE`），后期再迁 PostgreSQL |
| ORM / 迁移工具 | **SQLAlchemy 2.x + Alembic**（用 `alembic stamp head` 将现有库 baseline；未来表结构变更走 autogenerate） |
| 鉴权 | **纯 JWT Bearer，不再依赖 Redis**（无 Redis 缓存、无会话续期、无服务端吊销；Token 过期即重新登录） |
| 密码哈希 | **`passlib[bcrypt]` rounds=10**，与 Java 端 BCryptPasswordEncoder(10) 兼容，老用户密码可直接登录 |
| 图形验证码 | 接口保留，但返回 `captchaEnabled=false`（前端自动跳过；`/login` 不校验 code/uuid） |
| `/getRouters` | **不迁移**（此接口是 RuoYi 后台菜单渲染用的，当前 C 端前端不消费） |
| `createBy/updateBy` | 继续写 `sys_user.user_name` 字符串，保持与 Java 已写入数据的字段值格式一致 |
| 文件上传 | `/common/upload` **保留写本地磁盘**（`ruoyi.profile` 路径，用环境变量覆盖）；`/oss/file/*` 仍然写 OSS。两套并存 |
| 日志 | 默认 `INFO`，通过环境变量 `LOG_LEVEL=DEBUG` 切换 |
| 种子数据 | 不需要，**直接连原 MySQL 5.7 生产库**，`admin` 等账号已经存在 |
| Excel | 保留 `export`（xlsx 导出），**不迁 `import/importTemplate`** |
| 注释 | **所有类、方法、函数**均带中文注释，目的是最大化可读性 |
| 兜底逻辑 | **尽可能简单**，不写多余的重试、降级、边界补全；边界靠明确的 HTTP 错误码暴露 |

---

## 2. 范围（Scope）

### 2.1 保留的接口（共 **约 72 个**，对前端契约 100% 保真）

#### A. 鉴权 / 用户身份（4）
| 方法 | 路径 | 鉴权 | 备注 |
| --- | --- | --- | --- |
| POST | `/login` | 匿名 | 返回 `{code,msg,token}`；不校验 `code/uuid` |
| POST | `/register` | 匿名 | 成功后自动初始化默认服装分类树 |
| GET | `/captchaImage` | 匿名 | 固定返回 `{code:200, captchaEnabled:false, uuid:"", img:""}`，保留端点仅为前端兼容 |
| GET | `/getInfo` | 登录 | 返回 `{code,msg,user,roles,permissions,isDefaultModifyPwd,isPasswordExpired}` |

> **`/getRouters` 已从范围中剔除**。该接口是若依管理后台渲染动态菜单用的，C 端前端不消费。

#### B. SUITME 业务核心（16）
- `/customer/*`（6）：add / get / getDigitalImg / page / delete / update
- `/matching/*`（3）：addOrUpdate / list / delete
- `/matching/tag/*`（3）：addOrUpdate / list / delete
- `/outfit/*`（4）：generateOutfitImg / getOutfitImg / getTaskStatus/{taskId} / taskPage

#### C. 主数据（12）
- `/md/product/*`（5）：add / update / delete / updateDisplayFlag / page
- `/md/productColor/*`（2）：add / delete
- `/md/tag/*`（5）：add / delete / update / list / updateOrders

#### D. 服装分类树（4）
- `/md/categoryTag/*`：add / update / delete / list

#### E. 通用公共接口（4）
- `/common/download`、`/common/upload`、`/common/uploads`、`/common/download/resource`

#### F. OSS（4）
- `/oss/file/upload`、`/oss/file/batchUpload`、`/oss/file/download/{fileId}`、`/oss/file/checkConnection`

#### G. 外部 AI 连通性测试（3，匿名）
- `/api/test/generateDigitalImage`、`/api/test/generateOutfitImg`、`/api/test/getTaskStatus/{taskId}`

#### H. 系统管理 — 用户 / 角色 / 菜单的完整 RuoYi 分配逻辑（约 **34 个**）

**H.1 `/system/user/*`（11）**
| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/system/user/list` | 分页查询用户 |
| GET | `/system/user/{userId}` | 查询用户详情（含 postIds/roleIds/roles/posts） |
| POST | `/system/user` | 新增用户 |
| PUT | `/system/user` | 修改用户 |
| DELETE | `/system/user/{userIds}` | 批量删除 |
| PUT | `/system/user/changeStatus` | 启停用户 |
| PUT | `/system/user/resetPwd` | 重置密码 |
| GET | `/system/user/authRole/{userId}` | **分角色** — 查询用户可分配的角色（返回 `{user, roles}`） |
| PUT | `/system/user/authRole` | **分角色** — 把多个角色绑定到用户 |
| POST | `/system/user/export` | **Excel 导出**用户列表（.xlsx，用 `openpyxl`） |

**H.2 `/system/user/profile/*`（4）**
| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/system/user/profile` | 查看个人资料（含 `roleGroup`、`postGroup`） |
| PUT | `/system/user/profile` | 修改个人资料 |
| PUT | `/system/user/profile/updatePwd` | 修改密码 |
| POST | `/system/user/profile/avatar` | 修改头像 |

**H.3 `/system/role/*`（12）**
| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/system/role/list` | 分页查询角色 |
| GET | `/system/role/{roleId}` | 查询角色详情（含 menuIds） |
| POST | `/system/role` | 新增角色（同时落 `sys_role_menu`） |
| PUT | `/system/role` | 修改角色（重建 `sys_role_menu`） |
| PUT | `/system/role/changeStatus` | 启停角色 |
| DELETE | `/system/role/{roleIds}` | 批量删除 |
| GET | `/system/role/authUser/allocatedList` | **分配用户** — 已分配用户列表 |
| GET | `/system/role/authUser/unallocatedList` | **分配用户** — 未分配用户列表 |
| PUT | `/system/role/authUser/cancel` | **分配用户** — 取消单个用户的角色 |
| PUT | `/system/role/authUser/cancelAll` | **分配用户** — 批量取消 |
| PUT | `/system/role/authUser/selectAll` | **分配用户** — 批量授权 |
| POST | `/system/role/export` | Excel 导出角色列表 |

> `/system/role/dataScope` 与 `/system/role/deptTree/{roleId}` **不迁移**（依赖 dept 树，已被剔除）。

**H.4 `/system/menu/*`（7）**
| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/system/menu/list` | 查询菜单 |
| GET | `/system/menu/{menuId}` | 查询菜单详情 |
| GET | `/system/menu/treeselect` | 菜单树下拉选择 |
| GET | `/system/menu/roleMenuTreeselect/{roleId}` | **分菜单** — 返回 `{checkedKeys, menus}` |
| POST | `/system/menu` | 新增菜单 |
| PUT | `/system/menu` | 修改菜单 |
| DELETE | `/system/menu/{menuId}` | 删除菜单 |

> **合计 ≈ 72 个**：A=4 + B=16 + C=12 + D=4 + E=4 + F=4 + G=3 + H=34 = **81**（上一版算少了，最终以代码为准）。`AjaxResult` 响应仍然是"基于 HashMap、可携带任意额外 key"的松散结构，由 FastAPI 层用 `dict` 而非严格 Pydantic 响应模型实现保真。

### 2.2 删除的部分（不迁移）

- `ruoyi-ui`：整个若依前端模块**直接删除**
- `/getRouters`：若依后台菜单渲染专用，不迁移
- 所有 `/monitor/*`：cache / server / logininfor / operlog / online / job / jobLog
- 所有 `/tool/gen/*`：代码生成器
- 所有 `/test/user/*`：Swagger demo
- `/system/dept/*`、`/system/dict/*`、`/system/config/*`、`/system/post/*`、`/system/notice/*`
- `/system/role/dataScope`、`/system/role/deptTree/*`（依赖 dept 树）
- `/system/user/importData`、`/system/user/importTemplate`（导入不迁，只保留导出）
- Quartz 定时任务：不需要
- MyBatis-Plus、PageHelper、Spring Security、JWT-Redis、Kaptcha：统一替换为 Python 生态等价物
- 阿里云 OSS 的**管理面**（Bucket 创建等）保持不动；保留上传/下载/metadata 写库

---

## 3. 技术选型

| 层 | Java 现状 | Python 新栈 |
| --- | --- | --- |
| Web 框架 | Spring Boot 3.5.4 | **FastAPI** + Uvicorn（Gunicorn+Uvicorn workers 生产） |
| 异步 | 同步 Servlet | FastAPI 原生 async；OkHttp → **httpx.AsyncClient** |
| ORM | MyBatis-Plus | **SQLAlchemy 2.x**（async 或同步二选一，推荐同步+线程池，更贴近现状、逻辑简单） |
| 迁移工具 | 手写 SQL | **Alembic** |
| 数据库 | MySQL 5.7 | **MySQL 5.7（保持）** → 将来 PG；SQL 只用 5.7 支持的语法：禁用 CTE（`WITH`）、Window 函数、`JSON_TABLE`、`CHECK` 约束等 8.0 特性 |
| DB 驱动 | `mysql-connector-j` | **`PyMySQL`**（纯 Python、5.7 兼容性好） |
| JWT | `jjwt` | **`python-jose[cryptography]`** |
| 密码 | `BCryptPasswordEncoder(10)` | **`passlib[bcrypt]` rounds=10**（与老密码哈希兼容） |
| Excel 导出 | EasyExcel / POI | **`openpyxl`** |
| 配置 | `application.yml` | **`pydantic-settings`** 读 `.env` + `config.yaml` |
| 日志 | Logback | **`loguru`**（中文输出友好） |
| HTTP 客户端（调 AI） | OkHttp | **`httpx`** |
| OSS SDK | `aliyun-sdk-oss` (Java) | **`oss2`**（阿里云官方 Python SDK） |
| 校验/序列化 | Hibernate Validator + Jackson | **Pydantic v2** |
| 文件上传 | Spring MultipartFile | FastAPI `UploadFile` |
| 验证码 | Kaptcha | **保留端点但返回 captchaEnabled=false**（不真正生成） |
| 依赖管理 | Maven | **`uv`** 或 `poetry`（推荐 `uv`，新且快） |
| 测试 | JUnit | **`pytest` + `httpx`** |

---

## 4. 目标项目结构

```
suitme-python/
├── pyproject.toml
├── .env                      # 数据库、OSS、AI baseUrl、JWT secret 等敏感配置
├── config.yaml               # 非敏感配置（端口、日志级别等）
├── alembic/
│   ├── env.py
│   └── versions/             # 迁移脚本
├── app/
│   ├── main.py               # FastAPI 入口 + 路由装配 + 中间件
│   ├── core/
│   │   ├── config.py         # pydantic-settings
│   │   ├── database.py       # SQLAlchemy engine / Session
│   │   ├── security.py       # JWT 签发/解析 + 密码哈希
│   │   ├── deps.py           # FastAPI 依赖：get_db / get_current_user / require_perm
│   │   ├── response.py       # AjaxResult / TableDataInfo 等通用响应包装
│   │   ├── exceptions.py     # 全局异常 & AjaxResult 转换
│   │   └── logger.py         # loguru 配置
│   ├── api/
│   │   ├── login.py          # /login /register /captchaImage /getInfo
│   │   ├── ai_test.py        # /api/test/*
│   │   ├── customer.py       # /customer/*
│   │   ├── matching.py       # /matching/* /matching/tag/*
│   │   ├── outfit.py         # /outfit/*
│   │   ├── product.py        # /md/product/* /md/productColor/*
│   │   ├── tag.py            # /md/tag/*
│   │   ├── category.py       # /md/categoryTag/*
│   │   ├── common.py         # /common/*
│   │   ├── oss_file.py       # /oss/file/*
│   │   ├── sys_user.py       # /system/user/* /system/user/profile/*
│   │   ├── sys_role.py       # /system/role/*
│   │   └── sys_menu.py       # /system/menu/*
│   ├── models/               # SQLAlchemy ORM（对应原表名、原字段）
│   │   ├── base.py           # MyBaseEntity → PyBaseModel（create_time/by, update_time/by, del_flag）
│   │   ├── customer.py       # Customer
│   │   ├── matching.py       # Matching, MatchingSku, MatchingTag
│   │   ├── ai.py             # AiJoin, AiOutfit, AiTask
│   │   ├── product.py        # Product, ProductColor
│   │   ├── tag.py            # Tag
│   │   ├── oss_file.py       # OssFile
│   │   ├── clothing_category.py
│   │   └── sys.py            # SysUser, SysRole, SysMenu, SysUserRole, SysRoleMenu
│   ├── schemas/              # Pydantic 入参/出参（DTO/VO）
│   │   └── …与 models 平行
│   ├── services/             # 业务逻辑（对应 *ServiceImpl.java）
│   │   ├── ai_client.py      # 对接 Python 生图服务（httpx）
│   │   ├── customer_service.py
│   │   ├── matching_service.py
│   │   ├── outfit_service.py
│   │   ├── product_service.py
│   │   ├── tag_service.py
│   │   ├── category_service.py
│   │   ├── oss_service.py    # oss2 封装
│   │   ├── common_service.py # 文件上传下载
│   │   └── sys/*             # sys_user_service, sys_role_service, sys_menu_service
│   └── constants/
│       ├── enums.py          # Angle/TaskStatus/Gender/SkinColor/BodyType（与 Java 端枚举 1:1）
│       └── defaults.py       # 默认服装分类树、默认角色
└── tests/
    ├── test_contracts.py     # 契约测试：对比 Java 与 Python 对同一请求的响应
    └── test_biz.py
```

---

## 5. 数据模型（与现有 MySQL 1:1）

保留并建立 ORM 模型的表（`t_*` 业务表 + 若干 `sys_*`）：

**业务表**
- `t_customer`、`t_matching`、`t_matching_sku`、`t_matching_tag`
- `ai_join`、`ai_outfit`、`ai_task`
- `md_product`、`md_product_color`、`md_tag`
- `clothing_category`、`oss_file`

**系统表（最小保留）**
- `sys_user`、`sys_role`、`sys_menu`、`sys_user_role`、`sys_role_menu`

**不建立 ORM 模型的表**（表留在库里，但代码不访问）
- `sys_dept`、`sys_dict_type`、`sys_dict_data`、`sys_config`、`sys_post`、`sys_user_post`、`sys_role_dept`、`sys_notice`、`sys_oper_log`、`sys_logininfor`、`qrtz_*`、`gen_*`

**`BaseEntity` / `MyBaseEntity` 的映射**
- `create_time`、`create_by`、`update_time`、`update_by`、`del_flag` 做成 mixin `PyBaseModel`
- 自动填充：在 SQLAlchemy 的 `before_insert` / `before_update` 事件中根据当前登录用户填充 `create_by / update_by`
- `del_flag` 软删：默认 0，删除时置 1；所有业务查询自动带 `del_flag=0`

**Alembic 基线（MySQL 5.7 场景）**

1. 直接连**现有生产库**，ORM 模型按当前表结构 1:1 编写
2. `alembic init` → `alembic revision --autogenerate -m "baseline"`（生成建表脚本用于环境重建参考）
3. 生产库 `alembic stamp head`：标记已执行，**不跑**建表脚本
4. 未来表结构变更均用 `alembic revision --autogenerate`
5. ORM DDL 生成时注意：
   - 字符集用 `utf8mb4` + `utf8mb4_general_ci`（与若依现有库一致）
   - `TEXT` / `LONGTEXT` 不要用 `DEFAULT ''`（5.7 禁止带 default 的 TEXT）
   - 不使用 5.7 不支持的 `CHECK` 约束、`JSON_TABLE`、`WITH`（CTE）、窗口函数
   - 时间字段继续用 `DATETIME`（不是 `TIMESTAMP`）以保留若依现有的时区行为

---

## 6. 外部集成（契约 100% 保真）

### 6.1 Python 生图服务（最关键，用户已确认 3 个接口）

本服务作为**调用方**，向 Python 生图后端请求：

| 用途 | 方法 | 路径 | 请求体 | 响应 |
| --- | --- | --- | --- | --- |
| AI 数字形象 | POST | `{baseUrl}/models/default` | `CustomerApiReq { userId, pictureUrl, bodyProfile, size }` | `ApiResp<AiImgData>` |
| AI 穿搭生图 | POST | `{baseUrl}/models/outfit` | `OutfitApiReq { userId, taskId, angle, outfitImages, size }` | `ApiResp<AiImgData>` |
| AI 任务查询 | GET | `{baseUrl}/tasks/{taskId}` | - | `ApiResp<TaskData>` |

- `baseUrl` 由 `.env` 注入：`SUITME_AI_BASE_URL=http://127.0.0.1:8000`
- 可选 Bearer：`SUITME_AI_AUTH_TOKEN=...`
- 超时：连接 60s / 读 60s / 整体 300s（对齐 Java 端 OkHttp 配置）
- 字段命名：请求/响应 JSON 字段命名与 Java 侧保持**完全一致**（通过 Pydantic `alias` 保证）

### 6.2 阿里云 OSS

- 使用 **`oss2`** 官方 SDK
- 凭证、endpoint、bucket、url 从 `.env` 读取（**注意：现有 `application.yml` 中的 keyId/keySecret 已泄漏在代码库中，新项目必须使用新凭证并放到 `.env`，禁止入库**）
- 上传逻辑：生成 key → 上传 → 将元数据写 `oss_file` 表，返回访问 URL

### 6.3 本地磁盘上传（`/common/upload`）

- 保留 Java 现状：`/common/upload`、`/common/uploads` 仍然写**本地磁盘**
- 路径通过环境变量 `SUITME_UPLOAD_PROFILE` 注入（对应原 `ruoyi.profile`），Linux 容器建议挂载一个 PV 目录到容器内
- `/common/download`、`/common/download/resource` 从该目录读取
- 返回的 `url` 字段保持与 Java 完全一致（通常是 `/profile/upload/<yyyyMMdd>/<uuid>.<ext>` 形式），前端兼容无感知

---

## 7. 鉴权与会话

**决策：纯 JWT Bearer，无 Redis**

- `/login` 成功后：服务端用 HS256 签发 JWT，Payload 含 `userId`、`userName`、`roles`、`iat`、`exp`（默认 30 分钟）
- 响应体兼容若依：`{code:200, msg:"操作成功", token:"<jwt>"}`
- 请求端：`Authorization: Bearer <jwt>`
- 过期行为：过期返回 `401 {code:401, msg:"认证失败"}`，**无服务端续期**；前端重新登录即可
- 权限校验：JWT 里带 `permissions: string[]`；FastAPI 依赖 `require_perm("system:user:add")` 做细粒度校验（仅 `/system/*` 用）
- 业务接口（`/customer`、`/matching` 等）**只要求登录**，不做按钮级权限（与 Java 现状一致）
- 匿名名单（不校验 Token）：`/login`、`/register`、`/captchaImage`、`/api/test/*`、`/v3/api-docs`、`/docs`、`/redoc`

**删除的机制**
- 不再维护 `login_user:{uuid}` 的 Redis 缓存
- 不再做滑动续期
- 不再做服务端主动踢人（`/monitor/online/{tokenId}` 已移除）

---

## 8. 响应契约保真要求（硬要求）

前端已经基于若依 `AjaxResult` 写死期望，**Python 层必须严格按下列规则输出**：

1. **所有业务接口**统一返回 `AjaxResult`，形状：
   ```json
   { "code": 200, "msg": "操作成功", "data": <any> }
   ```
   `AjaxResult` 继承自 `HashMap`，允许任意额外 key（如 `captchaEnabled`、`uuid`、`img`、`url`、`fileName`、`roleGroup`、`postGroup` 等），Python 端用 `dict` 直接返回，不用严格 Pydantic 响应模型。

2. **分页接口**返回 `TableDataInfo`：
   ```json
   { "code": 200, "msg": "查询成功", "total": 0, "rows": [] }
   ```

3. **MyBatis-Plus 的 `IPage`** 形式（`/customer/page`、`/md/product/page`、`/outfit/taskPage`）返回：
   ```json
   { "code":200, "msg":"操作成功", "data":{ "records":[], "total":0, "size":10, "current":1, "pages":1 } }
   ```

4. **枚举值**（Angle/TaskStatus/Gender/SkinColor/BodyType）使用字符串值与 Java 完全一致：`front/side/back`、`none/submitted/processing/completed/failed`、`FEMALE/MALE` 等。

5. **时间格式**统一 `yyyy-MM-dd HH:mm:ss`（与 Jackson 默认一致），通过 Pydantic 的 `json_encoders` 配置。

6. **字段命名**：与 Java 保持 `camelCase`（Python 内部可 `snake_case`，对外用 Pydantic `alias`）。

7. **错误结构**：全局异常处理器把任何异常转成 `{code:500, msg:"<错误信息>"}` 的 200 响应（与若依一致，大多数业务错误走 code 而非 HTTP 状态码）；认证失败返回 `{code:401}`。

---

## 9. 前提假设（需用户确认，任何否决都会改变方案）

1. **前端只依赖 HTTP 契约**，不依赖任何 Spring / 若依特有 HTTP 头（如 `X-RateLimit-*`、`x-ratelimit-*`、Spring Session Cookie）。前端调用链里没有隐藏依赖。
2. **连的数据库与 Java 服务是同一个 MySQL 实例**，迁移期间可以并行（双跑）也可以切换（停 Java 起 Python）。新项目不会修改表结构，只增不删。
3. **现有生产数据中存在的 `createBy/updateBy` 字段值**（保存的是登录用户名）允许 Python 服务继续以相同字符串格式写入。
4. **阿里云 OSS 的 Bucket、endpoint 域名保持不变**，因此已写入 `oss_file` 表的 URL 无需回写。
5. **`/captchaImage` 端点返回 `captchaEnabled=false` 后，前端会自动跳过验证码校验**（若依前端默认行为）。如果前端硬编码了验证码必填，需要前端同步改动。
6. **Python 生图服务的 3 个接口契约是稳定的**，不会因为后端语言从 Java 切到 Python 而改变；Java 端 `CustomerApiReq / OutfitApiReq / TaskData` 的字段就是 Python 服务的真实协议。
7. **最终部署环境**有 Python 3.11+ 与 **MySQL 5.7** 可用（现有生产库版本）。

---

## 10. 候选方案对比（Phase 4）

### 方案 A：整包切换，按模块并行重写（推荐）

- 先搭好骨架（Config、DB、Auth、通用响应、异常）
- 按模块串行交付：鉴权 → 用户/角色/菜单 → 主数据 → 顾客 → 穿搭 → OSS → 通用下载
- 每模块写一个契约测试用例：拿 Java 服务的响应示例，断言 Python 返回的 JSON **结构和关键字段值一致**
- 切换方式：前端 baseUrl 切换即可

**优点**：路径最直接；每个模块完成后可立即联调；最少的临时脚手架
**缺点**：切换日必须一次性全部就绪；回滚只能改 baseUrl
**完成度 Completeness：9/10**

### 方案 B：Sidecar 并存，按接口逐步切流

- Python 服务起在不同端口（如 `:8001`）
- Java 服务保留不动，前端用 Nginx/网关按路径转发：`/customer/*` → Python，其余 → Java
- 一个接口一个接口切，前端侧零感知

**优点**：灰度切换，风险最小
**缺点**：需要额外部署网关；两套服务同时写同一个 DB，要注意 `createBy` 等字段格式；整体节奏慢
**完成度 Completeness：8/10**

### 方案 C：在 Java 项目里嵌入 Python Sidecar，只重写 AI 相关部分

- 只把 `/api/test/*` 和 `/outfit/*` 迁过去

**优点**：量最小
**缺点**：完全不符合用户"整个项目迁到 Python"的目标。**不推荐**
**完成度 Completeness：3/10**

### 推荐：**方案 A**
理由：用户明确要"热切换"，前端不改动 baseUrl 以外任何东西；整包一次切换是最简单的契约保真验证手段，也最符合"逻辑尽可能简单"的诉求。

---

## 11. 开发里程碑（建议粒度，可按需拆）

> 按照方案 A，预计 CC+gstack 下 2~5 个工作日能完成，人工 2~3 周。

| 阶段 | 产出 |
| --- | --- |
| M0：基础设施 | pyproject、FastAPI 骨架、Config、DB 连接、Alembic baseline、logger、通用响应 `AjaxResult/TableDataInfo`、全局异常、JWT 签发/校验、FastAPI 依赖 `get_current_user` |
| M1：鉴权域 | `/login` `/register` `/captchaImage` `/getInfo` + SysUser/SysRole/SysMenu 模型与 Service；JWT 签发/校验；`permissions` 装配 |
| M2：主数据 | `md_product`、`md_product_color`、`md_tag`、`clothing_category` 相关接口 |
| M3：顾客与 AI 数字形象 | `/customer/*` + `ai_client.generate_digital_image` |
| M4：穿搭与生图 | `/matching/*`、`/matching/tag/*`、`/outfit/*` + `ai_client.generate_outfit` / `get_task_status` |
| M5：OSS + 本地文件 | `/oss/file/*`（oss2）、`/common/*`（本地磁盘） |
| M6：系统管理完整逻辑 | `/system/user/*`（含 authRole、export）、`/system/role/*`（含 authUser 五件套、export、changeStatus）、`/system/menu/*`（含 roleMenuTreeselect）、`/system/user/profile/*` |
| M7：契约测试 + 联调 | 对照 Java 服务的每个接口抓响应，做 Python 侧快照比对；前端联调 |
| M8：切换 | 前端 baseUrl 指向 Python；删除 `ruoyi-*` 源码 |

---

## 12. 用户确认回复（已固化到本 PRD）

本次 office-hours 的 8 条回复，已经吸收进第 1~11 节。这里留一个签收记录。

| # | 问题 | 用户回复 | 固化位置 |
| --- | --- | --- | --- |
| 1 | 要不要 `/system/user/authRole` + `/system/menu/roleMenuTreeselect`？ | **要，按现在 Java 项目的分角色 + 分菜单逻辑来** | §2.1 H.1 / H.3 / H.4 |
| 2 | Excel import/export 要不要？ | **只保留 export**，不要 import / importTemplate | §2.1 H.1 / §2.2 |
| 3 | `/getRouters` 要不要？ | **不要**（若依后台专用，C 端不消费） | §2.1 A 说明行 / §2.2 |
| 4 | `createBy / updateBy` 继续写 user_name 字符串？ | **OK** | §1 速查表 / §5 事件填充 |
| 5 | bcrypt rounds=10 以兼容老密码？ | **OK** | §1 / §3 技术选型 |
| 6 | `/common/upload` 改写 OSS？ | **否，先保留本地磁盘**；`/oss/file/*` 单独写 OSS，两套并存 | §1 / §6.3 |
| 7 | 日志默认 info？ | **OK**（`LOG_LEVEL=DEBUG` 可切换） | §1 / §3 |
| 8 | Python 侧要不要种子管理员？ | **不需要，直接连原 MySQL 5.7 库**，注意 SQL 语法兼容 5.7 | §1 / §3 / §5 |

---

## 13. 风险与注意事项

- **`AjaxResult` 是 HashMap**：很多接口随手 `put("extraKey", value)`，必须逐个接口核对 Java 源码，不能只看返回值签名
- **`ai_task`、`ai_join`、`ai_outfit` 的状态机**：`none/submitted/processing/completed/failed` 切换时机与 Java 端 `OutfitServiceImpl` 完全一致，尤其是"未完成任务主动轮询外部 `/tasks/{taskId}` 并回写状态"这段，是生图前端 UI 的核心心跳
- **默认服装分类树初始化**：`/register` 成功后调用，内容见 `doc/suitme-api-system-analysis.md § 3.1`。Python 侧放 `constants/defaults.py`
- **OSS 凭证泄漏**：现有 `application.yml` 的 `keyId/keySecret` 已进入 git 历史，建议立刻在阿里云控制台轮换，新密钥只放 `.env`
- **MyBatis-Plus `@TableField(fill=...)`** 的自动填充 → 用 SQLAlchemy 的 `event.listens_for(Session, "before_flush")` 实现，保持透明
- **PageHelper 的分页协议** vs **MyBatis-Plus Page** 同时存在于同一个项目，Python 端用两种返回包装（`TableDataInfo` 和"裸 Page 放进 data"）对齐
- **MySQL 5.7 兼容性**：现有生产库为 5.7，ORM / Alembic 生成的 DDL 需避开 8.0 独有特性（CTE / 窗口函数 / JSON_TABLE / CHECK），业务 SQL 同样
- **本地上传路径**：`/common/upload` 写本地磁盘，容器部署时必须挂载持久卷到 `SUITME_UPLOAD_PROFILE`，否则重启丢文件
- **老用户密码兼容**：bcrypt rounds 必须设为 **10**，与若依 Java 端 `BCryptPasswordEncoder(10)` 一致，`passlib.hash.bcrypt` 默认 rounds=12 会让老密码无法验证

---

> 本 PRD 状态：**APPROVED**。下一步进入 M0（基础设施），产出 FastAPI 骨架 + Config + DB 连接 + Alembic baseline + JWT + 通用响应 + 全局异常。
