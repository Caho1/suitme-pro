"""统一响应包装模块。

为了尽量贴近若依 `AjaxResult` / `TableDataInfo` 的返回形状，这里统一用 dict 返回。
"""

from __future__ import annotations

from typing import Any


SUCCESS_CODE = 200
ERROR_CODE = 500
WARN_CODE = 601


def ajax_result(code: int = SUCCESS_CODE, msg: str = "操作成功", **kwargs: Any) -> dict[str, Any]:
    """构建松散结构的 AjaxResult。"""
    data: dict[str, Any] = {"code": code, "msg": msg}
    data.update(kwargs)
    return data



def success(data: Any = None, msg: str = "操作成功", **extra: Any) -> dict[str, Any]:
    """返回成功结果。"""
    payload = ajax_result(code=SUCCESS_CODE, msg=msg, **extra)
    if data is not None:
        payload["data"] = data
    return payload



def error(msg: str = "操作失败", code: int = ERROR_CODE, **extra: Any) -> dict[str, Any]:
    """返回错误结果。"""
    return ajax_result(code=code, msg=msg, **extra)



def warn(msg: str = "操作警告", **extra: Any) -> dict[str, Any]:
    """返回若依风格警告结果。"""
    return ajax_result(code=WARN_CODE, msg=msg, **extra)



def to_ajax(rows: int, success_msg: str = "操作成功", error_msg: str = "操作失败") -> dict[str, Any]:
    """把受影响行数转换为若依风格 AjaxResult。"""
    if rows > 0:
        return success(msg=success_msg)
    return error(msg=error_msg)



def table_data(rows: list[Any], total: int, msg: str = "查询成功") -> dict[str, Any]:
    """返回 PageHelper 风格的表格分页结构。"""
    return {"code": SUCCESS_CODE, "msg": msg, "total": total, "rows": rows}



def mp_page(records: list[Any], total: int, size: int, current: int, pages: int, msg: str = "操作成功") -> dict[str, Any]:
    """返回 MyBatis-Plus 风格的分页结构。"""
    return {
        "code": SUCCESS_CODE,
        "msg": msg,
        "data": {
            "records": records,
            "total": total,
            "size": size,
            "current": current,
            "pages": pages,
        },
    }



def captcha_disabled() -> dict[str, Any]:
    """返回固定关闭验证码的兼容结构。"""
    return ajax_result(code=SUCCESS_CODE, msg="操作成功", captchaEnabled=False, uuid="", img="")



def not_implemented(feature: str) -> dict[str, Any]:
    """返回统一的“骨架已创建”提示。"""
    return error(msg=f"接口骨架已创建，待迁移业务逻辑：{feature}", code=ERROR_CODE)
