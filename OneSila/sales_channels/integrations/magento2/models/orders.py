from sales_channels.models.orders import RemoteOrder, RemoteCustomer, RemoteOrderItem


class MagentoOrder(RemoteOrder):
    """
    Magento-specific model for remote orders, inheriting from the general RemoteOrder.
    """
    pass


class MagentoOrderItem(RemoteOrderItem):
    """
    Magento-specific model for remote order items, inheriting from the general RemoteOrderItem.
    """
    pass
