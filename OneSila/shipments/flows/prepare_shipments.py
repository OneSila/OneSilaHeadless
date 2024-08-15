from shipments.factories import PrepareShipmentsFactory


def prepare_shipments_flow(order):
    f = PrepareShipmentsFactory(order)
    f.run()
