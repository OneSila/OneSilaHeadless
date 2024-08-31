def inventory_change_product_update_trigger_flow(inventory):
    from inventory.factories import InventoryChangeProductUpdateTriggerFactory

    f = InventoryChangeProductUpdateTriggerFactory(inventory)
    f.run()
