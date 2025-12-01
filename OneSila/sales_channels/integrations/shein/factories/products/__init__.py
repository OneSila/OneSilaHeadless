"""Factories orchestrating Shein product create/update/delete flows."""

from .images import (
    SheinMediaProductThroughCreateFactory,
    SheinMediaProductThroughUpdateFactory,
    SheinMediaProductThroughDeleteFactory,
)
from .assigns import SheinSalesChannelAssignFactoryMixin
from .products import SheinProductCreateFactory, SheinProductUpdateFactory

__all__ = [
    "SheinMediaProductThroughCreateFactory",
    "SheinMediaProductThroughUpdateFactory",
    "SheinMediaProductThroughDeleteFactory",
    "SheinSalesChannelAssignFactoryMixin",
    "SheinProductCreateFactory",
    "SheinProductUpdateFactory",
]
