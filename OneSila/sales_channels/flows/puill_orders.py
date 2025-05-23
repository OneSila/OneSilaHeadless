
def pull_generic_orders_flow(sales_channel_class, factory):

    for sales_channel in sales_channel_class.objects.filter(active=True, import_orders=True).iterator():
        fac = factory(sales_channel=sales_channel)
        fac.run()
