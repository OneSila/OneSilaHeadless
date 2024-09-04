from shipments.factories import PackageItemInventoryMoveFactory


def packageitem_inventory_move_flow(*, package, product, quantity_received, movement_from):
    f = PackageItemInventoryMoveFactory(package=package, product=product, quantity_received=quantity_received, movement_from=movement_from)
    f.run()
