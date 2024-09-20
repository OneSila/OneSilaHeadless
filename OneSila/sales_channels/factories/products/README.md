# Remote Product Content Integration Guide

## Signal Workflow

### 1. Updating Remote Product Content
- **Trigger**: A `ProductTranslation` is created, updated, or deleted.
- **Signal**: `update_remote_product_content`

## Key Points
- **Dependencies**: Ensures related `RemoteProduct` exists before updating content.
- **Usage**: This signal is used to synchronize product content with remote systems.

# Remote Product Variations Integration Guide

## Signal Workflow

### 1. Adding a Remote Product Variation
- **Trigger**: `ConfigurableVariation` instance is created.
- **Signal**: `add_remote_product_variation`
- **Receiver**:
  - Uses `RemoteProductVariationAddFactory`.
  - Checks:
    - `RemoteProduct` exists for the parent.
    - Parent has `SalesChannelViewAssign`.
    - Variation exists in the sales channel with `SalesChannelViewAssign`.

### 2. Removing a Remote Product Variation
- **Trigger**: `ConfigurableVariation` instance is deleted.
- **Signal**: `remove_remote_product_variation`
- **Receiver**:
  - Uses existing delete logic for `RemoteProduct`.

 Remote Product Synchronization Integration Guide

## Signal Workflow

### 1. Synchronizing Remote Products

- **Trigger**: A `Product` instance is created, updated, or significant changes occur (e.g., stock, price, or property updates).
- **Signal**: `sync_remote_product`
- **Receiver**:
  - Uses `RemoteProductSyncFactory`.
  - Checks:
    - The product passes preflight checks (e.g., inspector status is not red).
    - Required dependencies exist (e.g., product properties, images).
  - Actions:
    - Synchronizes the product with the remote system.
    - Handles creation, updating, or deletion as needed.
    - Manages related data such as properties, images, translations, and variations.

## Key Points

- **Dependencies**: Ensures the local `Product` and associated data are valid before synchronization.
- **Usage**: Keeps remote products in sync with local product data across various sales channels.
- **Extensibility**:
  - The `RemoteProductSyncFactory` is designed to be subclassed for different integrations.
  - Custom logic can be added by overriding methods in the factory.

---

# Remote Product Deletion Integration Guide

## Signal Workflow

### 1. Deleting a Remote Product

- **Trigger**: A `Product` instance is deleted or marked as not for sale.
- **Signal**: `delete_remote_product`
- **Receiver**:
  - Uses `RemoteProductDeleteFactory`.
  - Checks:
    - `RemoteProduct` exists for the local product.
  - Actions:
    - Deletes the product from the remote system.
    - Cleans up associated remote data (e.g., variations, images).

## Key Points

- **Dependencies**: Ensures that the product is no longer needed on the remote system.
- **Usage**: Removes products from remote systems when they are no longer available locally.

# Remote Configurator Update Integration Guide

## Task Workflow

### 1. Updating Configurators for Rule Changes
- **Trigger**: A `ProductPropertiesRule` is updated (e.g., new required or optional properties).
- **Task**: Updates all relevant `RemoteProducts` configurators to reflect the rule changes.

### 2. Updating Configurators for Variation Changes
- **Trigger**: A variation (`ConfigurableVariation`) is added or removed.
- **Task**: Updates the configurators for all parent products of the variation.

### 3. Updating Configurators for Property Updates
- **Trigger**: A `ProductProperty` marked as `OPTIONAL_IN_CONFIGURATOR` is updated.
- **Task**: Updates the configurators for the parent products

By updates it will try to update only if is needed and if is this will resync the config product.