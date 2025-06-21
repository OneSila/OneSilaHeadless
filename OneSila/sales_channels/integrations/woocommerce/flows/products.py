from sales_channels.integrations.woocommerce.factories.products import WooCommerceProductCreateFactory


def create_woocommerce_product_flow(sales_channel_assign):
    """
    Create the woocommerce product and assign it to the sales channel.
    """
    product = sales_channel_assign.product
    sc = sales_channel_assign.sales_channel

    fac = WooCommerceProductCreateFactory(sales_channel=sc, local_instance=product)
    fac.run()
