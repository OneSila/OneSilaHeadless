"""Factories managing Shein remote property definitions and mappings."""

from .properties import (
    SheinProductPropertyCreateFactory,
    SheinProductPropertyDeleteFactory,
    SheinProductPropertyUpdateFactory,
)

__all__ = [
    "SheinProductPropertyCreateFactory",
    "SheinProductPropertyUpdateFactory",
    "SheinProductPropertyDeleteFactory",
]
