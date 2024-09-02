from shipments.factories import PackageItemInventoryMoveFactory


def packageitem_inventory_move_flow(packageitem):
    f = PackageItemInventoryMoveFactory(packageitem)
    f.run()
