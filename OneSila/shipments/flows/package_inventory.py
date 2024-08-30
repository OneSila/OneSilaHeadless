from shipments.factories import PackageItemInventoryMoveFactory


def packageitem_inventory_move_flow(*, package, quantity_received, movement_from):
    f = PackageItemInventoryMoveFactory(package=package, quantity_received=quantity_received, movement_from=movement_from)
    f.run()
