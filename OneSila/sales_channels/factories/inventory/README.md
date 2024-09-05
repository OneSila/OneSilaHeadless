# Remote Inventory Integration Guide

## Signal Workflow

### 1. Updating Remote Inventory
- **Trigger**: Quantity updates in the `Inventory` model.
- **Signal**: `update_remote_inventory`

## Key Points
- **Dependencies**: Ensures that the `RemoteProduct` is in place for inventory updates.
- **Cascading Updates**: Inventory updates are automatically handled when a product's inventory changes.
- **Single Source of Truth**: Quantity is synced from the local `Inventory` model to the remote system.

