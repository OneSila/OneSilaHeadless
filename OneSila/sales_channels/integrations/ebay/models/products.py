from sales_channels.models.products import (
    RemoteProduct, RemotePrice, RemoteProductContent,
    RemoteImageProductAssociation, RemoteEanCode,
)


class EbayProduct(RemoteProduct):
    """eBay product model."""
    pass


class EbayMediaThroughProduct(RemoteImageProductAssociation):
    """eBay media through product model."""
    pass


class EbayPrice(RemotePrice):
    """eBay price model."""
    pass


class EbayProductContent(RemoteProductContent):
    """eBay product content model."""
    pass


class EbayEanCode(RemoteEanCode):
    """eBay EAN code model."""
    pass
