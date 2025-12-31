# Agent Guidelines for `sales_channels/integrations`

## Scope
These rules cover all integration apps under `sales_channels/integrations/`.

## Integration Delivery Order
1. Handle authentication first (OAuth or API credential storage).
2. Build **pull** factories before push flows so downstream syncs have dependable local data.
3. Confirm core infrastructure: `SalesChannel`, `SalesChannelView`, assignments, and shared test mixins must exist.
4. Import attributes, media, and other dependencies.
5. Implement product factories once upstream data is reliable.
6. Only then wire import factories or additional automation.

## Directory Structure & Scaffolding
- Each integration is a Django app created under this package. Use the `create_sales_channel_integration` command to scaffold and keep parity with existing channels.
- Required modules include `apps.py` (with a `ready()` importing receivers), `models.py`, `mixins.py`, `factories/`, `flows/`, `receivers.py`, `tasks.py`, `schema/` (types/input/ordering/filters, queries, mutations), and `tests/`.
- Maintain layered factories: shared base classes in `sales_channels/factories/`, integration-specific specialisations in the app’s `factories/` folder.

## App Registration
- Add new integrations to `INSTALLED_APPS` using their dotted path (e.g., `sales_channels.integrations.shopify`).
- Ensure `AppConfig` names follow the `sales_channels.integrations.<integration>` pattern and define a `ready()` method that imports receivers.

## Implementation Guidelines
- API mixins encapsulate session/auth setup. Keep them reusable for factories and flows.
- Mirror remote entities with models living inside the integration app. Keep fields lean but sufficient for sync.
- Factories should expose `.run()` orchestration, guard against missing prerequisites, and remain idempotent.
- Write smoke scripts/tests that exercise at least one successful `.run()` call per critical factory.
- When debugging, verify products are assigned to a `SalesChannelView`; missing assignments are a common silent failure.
- Do not use keyword-only `*` in method signatures (e.g., `def method(self, *)`); it breaks our runtime environment.

## Testing & Credentials
- Add fixtures or mocks so integration tests can run offline. Patch network calls at the module level (see root guidelines for `@patch(...)` usage).
- Store API credentials in environment variables—never hardcode secrets.
