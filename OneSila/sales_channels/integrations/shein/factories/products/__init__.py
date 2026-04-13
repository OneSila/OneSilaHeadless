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
from .assigns import (
    SheinSalesChannelAssignFactoryMixin,
    SheinSalesChannelViewAssignUpdateFactory,
)
from .products import SheinProductCreateFactory, SheinProductUpdateFactory
from .products import SheinProductDeleteFactory
from .document_state import SheinProductDocumentStateFactory
from .external_documents import SheinProductExternalDocumentsFactory
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
    "SheinSalesChannelViewAssignUpdateFactory",
    "SheinProductCreateFactory",
    "SheinProductUpdateFactory",
    "SheinProductDeleteFactory",
    "SheinProductDocumentStateFactory",
    "SheinProductExternalDocumentsFactory",
    "SheinProductShelfUpdateFactory",
]
