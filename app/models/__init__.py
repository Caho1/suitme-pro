
"""ORM 模型导出。"""

from app.models.ai import AiJoin, AiOutfit, AiTask
from app.models.base import Base
from app.models.category import ClothingCategory
from app.models.customer import Customer
from app.models.matching import Matching, MatchingSku, MatchingTag
from app.models.oss_file import OssFile
from app.models.product import Product, ProductColor
from app.models.sys import SysMenu, SysRole, SysRoleMenu, SysUser, SysUserRole
from app.models.tag import Tag

__all__ = [
    'Base',
    'AiJoin',
    'AiOutfit',
    'AiTask',
    'ClothingCategory',
    'Customer',
    'Matching',
    'MatchingSku',
    'MatchingTag',
    'OssFile',
    'Product',
    'ProductColor',
    'SysMenu',
    'SysRole',
    'SysRoleMenu',
    'SysUser',
    'SysUserRole',
    'Tag',
]
