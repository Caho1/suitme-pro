"""日志配置模块。"""

from __future__ import annotations

import sys

from loguru import logger

from app.core.config import get_settings


def configure_logger() -> None:
    """初始化全局日志配置。"""
    settings = get_settings()
    logger.remove()
    logger.add(
        sys.stdout,
        level=settings.log_level.upper(),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
        enqueue=False,
        backtrace=False,
        diagnose=False,
    )
