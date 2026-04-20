# 路由清单（骨架版）

这份清单是当前 FastAPI 骨架的**单一事实来源**。

| # | 模块 | 方法 | 路径 | 鉴权 | 说明 |
| ---: | --- | --- | --- | --- | --- |
| 1 | auth | POST | `/login` | anonymous | 登录；返回 {code,msg,token}。 |
| 2 | auth | POST | `/register` | anonymous | 注册；成功后初始化默认服装分类。 |
| 3 | auth | GET | `/captchaImage` | anonymous | 兼容端点；当前规划固定返回 captchaEnabled=false。 |
| 4 | auth | GET | `/getInfo` | login | 返回 user/roles/permissions 等。 |
| 5 | auth | POST | `/logout` | login | 建议保留兼容端点；纯 JWT 模式下可直接返回成功。 |
| 6 | ai_test | POST | `/api/test/generateDigitalImage` | anonymous | 匿名测试外部数字形象接口。 |
| 7 | ai_test | POST | `/api/test/generateOutfitImg` | anonymous | 匿名测试外部穿搭生图接口。 |
| 8 | ai_test | GET | `/api/test/getTaskStatus/{taskId}` | anonymous | 匿名测试外部任务查询接口。 |
| 9 | customer | POST | `/customer/add` | login | 新增顾客并发起数字形象任务。 |
| 10 | customer | GET | `/customer/get` | login | 查询顾客详情。 |
| 11 | customer | GET | `/customer/getDigitalImg` | login | 查询顾客数字形象，必要时主动轮询外部任务。 |
| 12 | customer | POST | `/customer/page` | login | MyBatis-Plus 风格分页。 |
| 13 | customer | POST | `/customer/delete` | login | 逻辑删除顾客。 |
| 14 | customer | POST | `/customer/update` | login | 局部更新顾客。 |
| 15 | matching | POST | `/matching/addOrUpdate` | login | 新增或修改搭配。 |
| 16 | matching | POST | `/matching/list` | login | 查询搭配列表。 |
| 17 | matching | POST | `/matching/delete` | login | 删除搭配。 |
| 18 | matching | POST | `/matching/tag/addOrUpdate` | login | 新增或修改搭配标签。 |
| 19 | matching | POST | `/matching/tag/list` | login | 查询搭配标签列表。 |
| 20 | matching | POST | `/matching/tag/delete` | login | 删除搭配标签。 |
| 21 | outfit | POST | `/outfit/generateOutfitImg` | login | 创建穿搭生图任务。 |
| 22 | outfit | POST | `/outfit/getOutfitImg` | login | 聚合获取穿搭图，并必要时更新任务状态。 |
| 23 | outfit | GET | `/outfit/getTaskStatus/{taskId}` | login | 透传外部任务查询。 |
| 24 | outfit | POST | `/outfit/taskPage` | login | 穿搭任务分页。 |
| 25 | product | POST | `/md/product/add` | login | 新增单品。 |
| 26 | product | POST | `/md/product/update` | login | 更新单品。 |
| 27 | product | POST | `/md/product/delete` | login | 删除单品。 |
| 28 | product | POST | `/md/product/updateDisplayFlag` | login | 更新单品展示开关。 |
| 29 | product | POST | `/md/product/page` | login | 单品分页。 |
| 30 | product | POST | `/md/productColor/add` | login | 新增颜色 SKU。 |
| 31 | product | POST | `/md/productColor/delete` | login | 删除颜色 SKU。 |
| 32 | tag | POST | `/md/tag/add` | login | 新增标签。 |
| 33 | tag | POST | `/md/tag/delete` | login | 删除标签。 |
| 34 | tag | POST | `/md/tag/update` | login | 更新标签。 |
| 35 | tag | GET | `/md/tag/list` | login | 标签列表。 |
| 36 | tag | POST | `/md/tag/updateOrders` | login | 批量调整标签顺序。 |
| 37 | category | POST | `/md/categoryTag/add` | login | 新增服装分类节点。 |
| 38 | category | POST | `/md/categoryTag/update` | login | 更新服装分类节点。 |
| 39 | category | POST | `/md/categoryTag/delete` | login | 删除服装分类节点。 |
| 40 | category | POST | `/md/categoryTag/list` | login | 服装分类树。 |
| 41 | common | GET | `/common/download` | login | 通用下载接口。 |
| 42 | common | POST | `/common/upload` | login | 本地磁盘上传接口。 |
| 43 | common | GET | `/common/uploads` | login | 访问本地上传资源。 |
| 44 | common | GET | `/common/download/resource` | login | 下载本地资源文件。 |
| 45 | oss_file | POST | `/oss/file/upload` | login | 上传单个文件到 OSS。 |
| 46 | oss_file | POST | `/oss/file/batchUpload` | login | 批量上传文件到 OSS。 |
| 47 | oss_file | GET | `/oss/file/download/{fileId}` | login | 按 fileId 下载 OSS 文件。 |
| 48 | oss_file | GET | `/oss/file/checkConnection` | login | 检查 OSS 连通性。 |
| 49 | sys_user | GET | `/system/user/profile` | login | 获取个人资料。 |
| 50 | sys_user | PUT | `/system/user/profile` | login | 更新个人资料。 |
| 51 | sys_user | PUT | `/system/user/profile/updatePwd` | login | 修改个人密码。 |
| 52 | sys_user | POST | `/system/user/profile/avatar` | login | 上传个人头像。 |
| 53 | sys_user | GET | `/system/user/list` | login | 分页查询用户。 |
| 54 | sys_user | GET | `/system/user/{userId}` | login | 查询用户详情。 |
| 55 | sys_user | POST | `/system/user` | login | 新增用户。 |
| 56 | sys_user | PUT | `/system/user` | login | 修改用户。 |
| 57 | sys_user | DELETE | `/system/user/{userIds}` | login | 批量删除用户。 |
| 58 | sys_user | PUT | `/system/user/changeStatus` | login | 启停用户。 |
| 59 | sys_user | PUT | `/system/user/resetPwd` | login | 重置密码。 |
| 60 | sys_user | GET | `/system/user/authRole/{userId}` | login | 查询用户可分配角色。 |
| 61 | sys_user | PUT | `/system/user/authRole` | login | 批量给用户授权角色。 |
| 62 | sys_user | POST | `/system/user/export` | login | 导出用户 Excel。 |
| 63 | sys_role | GET | `/system/role/authUser/allocatedList` | login | 已分配用户列表。 |
| 64 | sys_role | GET | `/system/role/authUser/unallocatedList` | login | 未分配用户列表。 |
| 65 | sys_role | PUT | `/system/role/authUser/cancel` | login | 取消单个用户角色。 |
| 66 | sys_role | PUT | `/system/role/authUser/cancelAll` | login | 批量取消用户角色。 |
| 67 | sys_role | PUT | `/system/role/authUser/selectAll` | login | 批量授权用户到角色。 |
| 68 | sys_role | GET | `/system/role/list` | login | 分页查询角色。 |
| 69 | sys_role | GET | `/system/role/{roleId}` | login | 查询角色详情。 |
| 70 | sys_role | POST | `/system/role` | login | 新增角色。 |
| 71 | sys_role | PUT | `/system/role` | login | 修改角色。 |
| 72 | sys_role | PUT | `/system/role/changeStatus` | login | 启停角色。 |
| 73 | sys_role | DELETE | `/system/role/{roleIds}` | login | 批量删除角色。 |
| 74 | sys_role | POST | `/system/role/export` | login | 导出角色 Excel。 |
| 75 | sys_menu | GET | `/system/menu/list` | login | 查询菜单列表。 |
| 76 | sys_menu | GET | `/system/menu/treeselect` | login | 菜单树下拉。 |
| 77 | sys_menu | GET | `/system/menu/roleMenuTreeselect/{roleId}` | login | 角色菜单树。 |
| 78 | sys_menu | GET | `/system/menu/{menuId}` | login | 查询菜单详情。 |
| 79 | sys_menu | POST | `/system/menu` | login | 新增菜单。 |
| 80 | sys_menu | PUT | `/system/menu` | login | 修改菜单。 |
| 81 | sys_menu | DELETE | `/system/menu/{menuId}` | login | 删除菜单。 |
