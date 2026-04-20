"""业务枚举定义。"""

from __future__ import annotations

from enum import StrEnum


class Angle(StrEnum):
    """穿搭图角度。"""

    FRONT = "front"
    SIDE = "side"
    BACK = "back"


class TaskStatus(StrEnum):
    """AI 任务状态。"""

    NONE = "none"
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Gender(StrEnum):
    """性别枚举。"""

    FEMALE = "FEMALE"
    MALE = "MALE"


class SkinColor(StrEnum):
    """肤色枚举。"""

    NATURAL_WHITE = "NATURAL_WHITE"
    LIGHT_WHEAT = "LIGHT_WHEAT"
    NATURAL_YELLOW = "NATURAL_YELLOW"
    WHEAT = "WHEAT"


class BodyType(StrEnum):
    """身材类型枚举。"""

    PEAR = "PEAR"
    APPLE = "APPLE"
    HOURGLASS = "HOURGLASS"
    RECTANGLE = "RECTANGLE"
    INVERTED_TRIANGLE = "INVERTED_TRIANGLE"
