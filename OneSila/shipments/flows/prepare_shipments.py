from shipments.factories import PrepareShipmentsFactory


def prepare_shipments_flow(order):
    f = PrepareShipmentsFactory(order)
    f.run()


def remove_inventory_after_shipping_flow(shipment):
    f = RemoveInventoryAfterShippingFactory(shipment)
    f.run()
