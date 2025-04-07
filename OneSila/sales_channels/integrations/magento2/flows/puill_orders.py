def pull_magento_orders_flow():
    from ..factories.orders import MagentoOrderPullFactory
    from ..models.sales_channels import MagentoSalesChannel

    for sales_channel in MagentoSalesChannel.objects.filter(active=True, import_orders=True).iterator():
        fac = MagentoOrderPullFactory(sales_channel=sales_channel)
        fac.run()