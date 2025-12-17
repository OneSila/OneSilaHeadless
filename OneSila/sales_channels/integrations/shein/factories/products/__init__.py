"""Factories orchestrating Shein product create/update/delete flows."""

from .images import (
    SheinMediaProductThroughCreateFactory,
    SheinMediaProductThroughUpdateFactory,
    SheinMediaProductThroughDeleteFactory,
)
from .assigns import SheinSalesChannelAssignFactoryMixin
from .products import SheinProductCreateFactory, SheinProductUpdateFactory
from .products import SheinProductDeleteFactory
from .document_state import SheinProductDocumentStateFactory

__all__ = [
    "SheinMediaProductThroughCreateFactory",
    "SheinMediaProductThroughUpdateFactory",
    "SheinMediaProductThroughDeleteFactory",
    "SheinSalesChannelAssignFactoryMixin",
    "SheinProductCreateFactory",
    "SheinProductUpdateFactory",
    "SheinProductDeleteFactory",
    "SheinProductDocumentStateFactory",
]
