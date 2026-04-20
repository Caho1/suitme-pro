"""总路由注册模块。"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import ai_test
from app.api.routes import auth
from app.api.routes import category
from app.api.routes import common
from app.api.routes import customer
from app.api.routes import matching
from app.api.routes import oss_file
from app.api.routes import outfit
from app.api.routes import product
from app.api.routes import sys_menu
from app.api.routes import sys_role
from app.api.routes import sys_user
from app.api.routes import tag


api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(ai_test.router)
api_router.include_router(customer.router)
api_router.include_router(matching.router)
api_router.include_router(outfit.router)
api_router.include_router(product.router)
api_router.include_router(tag.router)
api_router.include_router(category.router)
api_router.include_router(common.router)
api_router.include_router(oss_file.router)
api_router.include_router(sys_user.router)
api_router.include_router(sys_role.router)
api_router.include_router(sys_menu.router)
