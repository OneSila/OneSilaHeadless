# Remote Inventory Integration Guide

## Signal Workflow

### 1. Updating Remote Inventory
- **Trigger**: Quantity updates in the `Inventory` model.
- **Signal**: `update_remote_inventory`

## Key Points
- **Dependencies**: Ensures that the `RemoteProduct` is in place for inventory updates.
- **Cascading Updates**: Inventory updates are automatically handled when a product's inventory changes.
- **Single Source of Truth**: Quantity is synced from the local `Inventory` model to the remote system.


# Remote Product Variations Integration Guide

## Signal Workflow

### 1. Adding a Remote Product Variation
- **Trigger**: `ConfigurableVariation` instance is created.
- **Signal**: `add_remote_product_variation`
- **Receiver**:
  - Uses `RemoteProductVariationUpdateFactory`.
  - Checks:
    - `RemoteProduct` exists for the parent.
    - Parent has `SalesChannelViewAssign`.
    - Variation exists in the sales channel with `SalesChannelViewAssign`.

### 2. Removing a Remote Product Variation
- **Trigger**: `ConfigurableVariation` instance is deleted.
- **Signal**: `remove_remote_product_variation`
- **Receiver**:
  - Uses existing delete logic for `RemoteProduct`.
  - Checks:
    - Ensures the variation removal doesn’t affect other configurations.

## Factories

### RemoteProductVariationUpdateFactory
- **Purpose**: Adds variations to the parent product in the remote system.
- **Checks**:
  - `RemoteProduct` for parent and variation.
  - Required assignments in `SalesChannelViewAssign`.

### RemoteProductVariationDeleteFactory
We will ose the RemoteProductDeleteFactory
- **Purpose**: Deletes variations via the standard product deletion factory.
