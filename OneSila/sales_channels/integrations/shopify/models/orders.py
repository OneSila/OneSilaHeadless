from sales_channels.models.orders import RemoteOrder, RemoteOrderItem


class ShopifyOrder(RemoteOrder):
    """
    Shopify-specific model for remote orders, inheriting from the general RemoteOrder.
    """
    pass


class ShopifyOrderItem(RemoteOrderItem):
    """
    Shopify-specific model for remote order items, inheriting from the general RemoteOrderItem.
    """
