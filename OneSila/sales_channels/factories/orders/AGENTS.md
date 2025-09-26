# Agent Guidelines for `sales_channels/factories/orders`

## Scope
Covers factories that pull remote orders/customers/items.

## Periodic Pull Model
- Use scheduled tasks (not signals) to import orders, customers, and order items from remote platforms.
- Link remote records to local `Order`, customer, and item models, populating minimal fields such as quantity, price, and `remote_sku`.
- Keep remote product creation out of scope; focus on syncing transactional data.

## Factory Expectations
- `RemoteOrderPullFactory` should validate incoming payloads, map addresses/customers, and ensure idempotent creation of order hierarchies.
- Tests must cover periodic execution and confirm that repeated pulls do not duplicate records.
