from shipments.factories import PrepareShipmentsFactory, ShipmentCompletedFactory


def prepare_shipments_flow(order):
    f = PrepareShipmentsFactory(order)
    f.run()


def shipment_completed_flow(shipment):
    f = ShipmentCompletedFactory(shipment)
    f.run()
