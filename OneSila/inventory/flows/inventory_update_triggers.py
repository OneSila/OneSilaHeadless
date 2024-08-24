def inventory_update_trigger_flow(inventory):
    from inventory.factories import InventoryUpdateTriggerFactory

    f = InventoryUpdateTriggerFactory(inventory)
    f.run()
