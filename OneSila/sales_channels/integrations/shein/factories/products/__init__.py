"""Factories orchestrating Shein product create/update/delete flows."""

from .images import (
    SheinMediaProductThroughCreateFactory,
    SheinMediaProductThroughUpdateFactory,
    SheinMediaProductThroughDeleteFactory,
)
from .documents import (
    SheinRemoteDocumentCreateFactory,
    SheinRemoteDocumentUpdateFactory,
    SheinRemoteDocumentDeleteFactory,
    SheinDocumentThroughProductCreateFactory,
    SheinDocumentThroughProductUpdateFactory,
    SheinDocumentThroughProductDeleteFactory,
)
from .assigns import SheinSalesChannelAssignFactoryMixin
from .products import SheinProductCreateFactory, SheinProductUpdateFactory
from .products import SheinProductDeleteFactory
from .document_state import SheinProductDocumentStateFactory
from .shelf import SheinProductShelfUpdateFactory

__all__ = [
    "SheinMediaProductThroughCreateFactory",
    "SheinMediaProductThroughUpdateFactory",
    "SheinMediaProductThroughDeleteFactory",
    "SheinRemoteDocumentCreateFactory",
    "SheinRemoteDocumentUpdateFactory",
    "SheinRemoteDocumentDeleteFactory",
    "SheinDocumentThroughProductCreateFactory",
    "SheinDocumentThroughProductUpdateFactory",
    "SheinDocumentThroughProductDeleteFactory",
    "SheinSalesChannelAssignFactoryMixin",
    "SheinProductCreateFactory",
    "SheinProductUpdateFactory",
    "SheinProductDeleteFactory",
    "SheinProductDocumentStateFactory",
    "SheinProductShelfUpdateFactory",
]
