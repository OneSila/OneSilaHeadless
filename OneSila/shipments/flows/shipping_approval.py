from shipments.factories import PreApproveShippingFactory


def pre_approve_shipping_flow(order):
    f = PreApproveShippingFactory(order)
    f.run()
