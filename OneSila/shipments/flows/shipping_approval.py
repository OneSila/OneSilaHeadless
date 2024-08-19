from shipments.factories import PreApproveShippingFactory
from orders.models import Order


def pre_approve_shipping_flow(order):
    f = PreApproveShippingFactory(order)
    f.run()


def inventory_change_trigger_flow(product):
    order_ids = product.orderitem_set.\
        filter(order__status=Order.AWAIT_INVENTORY).\
        values('order_id')

    for order in Order.objects.filter(id__in=order_ids):
        pre_approve_shipping_flow(order)
