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
