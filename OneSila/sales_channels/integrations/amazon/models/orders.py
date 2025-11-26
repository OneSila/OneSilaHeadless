from sales_channels.models.orders import RemoteOrder, RemoteOrderItem


class AmazonOrder(RemoteOrder):
    """Amazon specific remote order."""
    pass


class AmazonOrderItem(RemoteOrderItem):
    """Amazon specific remote order item."""
    pass
