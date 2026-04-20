"""鉴权相关请求模型。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class LoginBody(BaseModel):
    """登录请求体。"""

    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    code: str | None = Field(default=None, description="验证码")
    uuid: str | None = Field(default=None, description="验证码 UUID")


class RegisterBody(BaseModel):
    """注册请求体。"""

    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    code: str | None = Field(default=None, description="验证码")
    uuid: str | None = Field(default=None, description="验证码 UUID")
