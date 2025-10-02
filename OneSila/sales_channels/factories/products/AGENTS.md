# Agent Guidelines for `sales_channels/factories/products`

## Scope
Applies to remote product factories, including content, variations, sync, deletion, and configurator updates.

## Content Synchronisation
- When `ProductTranslation` objects change, use the `update_remote_product_content` signal to push updates. Ensure the related `RemoteProduct` exists before invoking factories.

## Variation Handling
- On `ConfigurableVariation` creation, trigger `add_remote_product_variation` and ensure parent products have `SalesChannelViewAssign` links. Handle deletion with `remove_remote_product_variation` using the standard delete flow.

## Product Sync Lifecycle
- `RemoteProductSyncFactory` mediates create/update logic. Gate execution behind inspector preflight checks and verify required assets (properties, media) are ready.
- Make the factory subclass-friendly so integrations can override behaviour without duplicating logic.

## Deletion
- Use `delete_remote_product` when products are removed or marked not for sale. Clean up remote dependencies such as variations and images.

## Configurator Tasks
- Maintain asynchronous tasks that update configurators when rules, variations, or property metadata change. Ensure they avoid redundant remote calls by checking whether updates are actually required.
