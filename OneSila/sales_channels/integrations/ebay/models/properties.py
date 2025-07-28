from sales_channels.models.properties import (
    RemoteProperty, RemotePropertySelectValue, RemoteProductProperty,
)


class EbayProperty(RemoteProperty):
    """eBay attribute model."""
    pass


class EbayPropertySelectValue(RemotePropertySelectValue):
    """eBay attribute value model."""
    pass


class EbayProductProperty(RemoteProductProperty):
    """eBay product property model."""
    pass
