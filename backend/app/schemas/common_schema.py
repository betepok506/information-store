from enum import Enum

__all__ = ["IOrderEnum"]


class IOrderEnum(str, Enum):
    ascendent = "ascendent"
    descendent = "descendent"
