# Integration Implementation Playbook

This guide documents the end-to-end workflow for adding or extending sales-channel integrations inside `sales_channels/integrations/`. It encodes the pattern we already use for Shopify, Magento 2, WooCommerce, Amazon, and eBay so new work stays predictable. Whenever the steps differ for marketplaces (Amazon, eBay) versus direct storefronts (Shopify, Magento 2, WooCommerce) the difference is called out explicitly.

## Naming and layout expectations

```
sales_channels/
└── integrations/
    ├── <integration>/
    │   ├── apps.py                # AppConfig + ready()
    │   ├── models/
    │   │   ├── sales_channels.py  # Remote sales channel + views + credentials
    │   │   ├── products.py        # Remote product mirrors
    │   │   ├── properties.py      # Remote attribute/property definitions
    │   │   ├── ...
    │   ├── factories/
    │   │   ├── sales_channels/    # Auth, metadata pulls, schema imports
    │   │   ├── products/          # Push factories + helpers
    │   │   ├── properties/
    │   │   ├── prices/
    │   │   ├── imports/
    │   │   └── ...
    │   ├── flows/                 # Task orchestration helpers
    │   ├── schema/
    │   │   ├── types/
    │   │   ├── queries.py
    │   │   └── mutations.py
    │   ├── receivers.py           # Signal wiring
    │   ├── tasks.py               # Huey entry-points
    │   └── tests/
    │       ├── tests_factories/
    │       ├── tests_flows/
    │       └── tests_schemas/
    └── ...
```

Guiding principles:
- Follow the "always kwargs" convention for callables (`def run(self, *, view) -> None` etc.).
- Keep modules below ~500 lines; break out domains (`models/products.py`, `factories/products/images.py`, ...) before they grow unwieldy.
- Never create Django migrations here unless the ticket explicitly says so.
- Guard secrets via environment variables and make OAuth/token exchange flows idempotent.
- Pull data before pushing: build import/pull factories first, then push flows, and only then automate with live signals.

## Phase map

| Phase | Goal | Marketplace (Amazon, eBay) | Direct storefront (Shopify, Magento 2, WooCommerce) |
|-------|------|----------------------------|-----------------------------------------------------|
| 0 | Pre-flight research and scaffolding | Required | Required |
| 1 | App skeleton and registration | Required | Required |
| 2 | Authentication & credential storage | Required | Required |
| 3 | Immediate metadata pulls (currencies/stores/languages/views) | Required | Required |
| 4 | Property mapping & shared references | Required | Required |
| 5 | Schema/category import | Required | Skip (unless storefront exposes a taxonomy you need) |
| 6 | Product pull/import pipeline | Required | Required |
| 7 | Product push (create/update/delete) factories | Required | Required |
| 8 | Live product signalling (initial) | Required | Required |
| 9 | Extended live coverage (properties, prices, media, inventory, orders) | Required | Required |
| 10 | Testing, observability, and operational hooks | Required | Required |

## Phase details

### Phase 0 – Pre-flight research and scaffolding
Applicable: Marketplace ✅ | Direct storefront ✅
1. Read vendor docs and define the integration type (marketplace vs storefront). Capture auth type, rate limits, pagination, and supported resources in the ticket.
2. Identify the local models you will mirror (products, properties, prices, stock, orders). Confirm which existing shared factories (`sales_channels/factories/...`) you can reuse.
3. Document environment variables you will require (API keys, OAuth client IDs, endpoints). Do **not** check secrets into the repo.
4. Decide which tests must exist on day one (factory happy path, validation failure, schema import). Plan to add them alongside the code.

### Phase 1 – App skeleton and registration
Applicable: Marketplace ✅ | Direct storefront ✅
1. Scaffold the app: `python manage.py create_sales_channel_integration <integration_name>`.
   - If the command is unavailable, run `python manage.py startapp <integration_name> sales_channels/integrations/<integration_name>` and add empty `models/__init__.py`, `factories/__init__.py`, etc.
2. Register the app in settings (usually `OneSila/settings/base.py`): add `'sales_channels.integrations.<integration_name>'` to `INSTALLED_APPS`.
3. Update `apps.py`:
   - Define `<IntegrationName>Config` with `default_auto_field` and `name = 'sales_channels.integrations.<integration_name>'`.
   - Implement `ready()` to import `sales_channels.integrations.<integration_name>.receivers`.
4. Create empty module placeholders to keep file sizes in check:
   - `models/{sales_channels, products, properties, prices, inventory, orders}.py` as needed.
   - `factories/{sales_channels, products, properties, prices, imports}/__init__.py` plus per-domain modules (e.g., `factories/products/products.py`).
   - `schema/__init__.py` exporting `queries` and `mutations` for the root schema loader.
   - `tests/tests_factories/__init__.py` etc. so pytest collects the suites.
5. Wire GraphQL loader: update `sales_channels/schema.py` (or the app-specific aggregator) to import the new integration schema modules using lazy imports to avoid circular dependencies.

### Phase 2 – Authentication & credential storage
Applicable: Marketplace ✅ | Direct storefront ✅
1. Model credentials in `models/sales_channels.py`:
   - Extend `RemoteSalesChannel` (or relevant base) with fields for API keys, OAuth tokens, refresh tokens, state, region, and connection errors.
   - Add related models for installations (`SalesChannelView`, remote account metadata, etc.).
2. Implement API mixin(s) in `factories/mixins.py` to centralise session setup (headers, endpoints, throttling). Ensure the mixin raises clear errors when credentials are missing or expired.
3. Build OAuth factories when required:
   - `factories/sales_channels/oauth.py` should hold `Get<Integration>RedirectUrlFactory` and `Validate<Integration>AuthFactory`. Follow existing patterns (Shopify and Amazon) for storing tokens and dispatching `refresh_website_pull_models` once credentials are valid.
   - Capture non-OAuth credential validation in `factories/sales_channels/credentials.py` if the vendor relies on static API keys.
4. Expose GraphQL mutations:
   - Define Strawberry inputs in `schema/types/input.py` (e.g., `<Integration>SalesChannelInput`, `<Integration>ValidateAuthInput`).
   - Add mutations in `schema/mutations.py`: `get_<integration>_redirect_url`, `validate_<integration>_auth`, `update_<integration>_sales_channel`, etc. Use decorator-based validation and `get_multi_tenant_company()` like Shopify does.
   - For OAuth flows that need a follow-up mutation to finish setup, create it now so frontends can call it immediately after the redirect.
5. Add credential tests:
   - Under `tests/tests_factories/test_sales_channel_oauth.py` assert that invalid credentials raise the expected error and that a successful run stores tokens and enqueues metadata refresh.
   - Mock HTTP calls with `@patch` at the module level to keep tests isolated.

### Phase 3 – Immediate metadata pulls (currencies, stores, remote languages, views)
Applicable: Marketplace ✅ | Direct storefront ✅
1. Model remote metadata:
   - Add models in `models/sales_channels.py` (or dedicated modules) for currencies, store views, languages, and marketplaces. Example: `AmazonRemoteLanguage`, `ShopifySalesChannelView`.
2. Create pull factories in `factories/sales_channels/`:
   - `views.py` for storefront storefronts, `marketplaces.py` for Amazon/eBay, `currencies.py`, `languages.py`.
   - Ensure each factory accepts `*, sales_channel` and uses the API mixin to iterate over remote resources. Use `select_related`/`prefetch_related` when reading local relations.
3. Connect the factories to post-auth signals:
   - In `receivers.py`, listen to `sales_channels.signals.refresh_website_pull_models` and `sales_channel_created`. On trigger, call the factories so metadata lands as soon as auth succeeds.
   - Only run pulls when credentials are present (check `access_token`, `refresh_token`, or API key field).
4. Build tests in `tests/tests_factories/test_sales_channel_metadata.py` that cover the three primary pulls (views/stores, currencies, languages). Use fixture JSON to simulate vendor responses.

### Phase 4 – Property mapping & shared references
Applicable: Marketplace ✅ | Direct storefront ✅
1. Mirror remote properties in `models/properties.py` (property definition, select values, product-type linkage). Include fields for local mappings (`local_instance`, `translated_remote_name`, etc.).
2. Implement pull factories under `factories/properties/`:
   - `definitions.py` (pull remote attributes), `select_values.py` (pull option lists), `rules.py` (build mapping aids). For marketplaces, also include rule generation factories (see Amazon’s `factories/sync/`).
3. Add mapping aids:
   - Provide factories in `factories/properties/mapping.py` (or reuse shared ones) that populate `ProductPropertiesRuleItem` or equivalent bridging models.
4. Expose GraphQL management surface:
   - Extend `schema/types/types.py` and `schema/queries.py` so UI can list remote properties and select values.
   - Provide partial update mutations for linking local properties (see Amazon’s `ProductTypeProperty` patterns).
5. Tests:
   - Add factory tests covering translation, mapping toggles, and select value syncing.
   - Validate that repeated runs are idempotent and do not duplicate records.

### Phase 5 – Schema / category import (marketplaces only)
Applicable: Marketplace ✅ | Direct storefront ❌ (skip unless the storefront publishes a taxonomy you rely on)
1. Create schema models (`models/recommended_browse_nodes.py`, `models/product_types.py`) representing remote categories, browse nodes, or product type hierarchies.
2. Write import processors:
   - Place orchestrators in `factories/imports/schema_imports.py` and item processors in `factories/recommended_browse_nodes/`.
   - Break long-running steps into asynchronous tasks (see Amazon’s `AmazonSchemaImportProcessor`).
3. Update `tasks.py` with Huey tasks to run schema imports. Use `LOW_PRIORITY` queues for nightly refreshes and `CRUCIAL_PRIORITY` when the user triggers imports manually.
4. Provide management entry-points:
   - Add GraphQL mutation or admin action to request a schema import.
   - Ensure status updates land in `imports_exports` tables so progress can be tracked.
5. Tests:
   - Unit-test processors with fixture payloads.
   - Add integration-level tests validating that imports create expected nodes and queue dependent tasks (e.g., rule builders).

### Phase 6 – Product pull / import pipeline
Applicable: Marketplace ✅ | Direct storefront ✅
1. Define product mirror models in `models/products.py` (remote ID, SKU, status, marketplace assignments, timestamps). Include helper methods for state checks.
2. Implement importer factories:
   - `factories/imports/products_imports.py` should orchestrate pagination, chunking, and fan-out to item factories (`AmazonProductItemFactory`, `ShopifyProductImportFactory`, etc.).
   - Provide per-view refresh factories (`factories/imports/product_import.py`) for ad-hoc imports of a single product or catalog slice.
3. Queue imports:
   - Add Huey tasks in `tasks.py` that call the factories (`*_product_import_task`). Use `add_task_to_queue` with integration-specific flows for correct fan-out.
   - For marketplaces with multiple marketplaces per sales channel, iterate views before queuing tasks.
4. Tests:
   - Cover import processors (happy path, pagination, deduplication).
   - Assert that local products are created/updated correctly and that configurable/variation products associate as expected.

### Phase 7 – Product push factories (create/update/delete)
Applicable: Marketplace ✅ | Direct storefront ✅
1. Build base product sync factory in `factories/products/products.py` extending `RemoteProductSyncFactory`. Wire up mixins, image/property/price sub-factories, and remote model classes.
2. Implement create/update/delete factories:
   - `RemoteProductCreateFactory`, `RemoteProductUpdateFactory`, `RemoteProductDeleteFactory` specialisations that assemble payloads, perform preflight checks (GTIN/EAN validation, existing remote ID checks), and parse responses.
   - Add helper modules for media (`factories/products/images.py`), descriptions (`factories/products/content.py`), variations, and price updates (`factories/prices/<integration>_price.py`).
3. Ensure factories enforce idempotency and switch to sync when appropriate (e.g., raise `SwitchedToSyncException` when a listing already exists).
4. Hook into central flows:
   - For marketplaces, implement view-aware task runners in `flows/tasks_runner.py` (see Amazon) to fan out by marketplace and remote product.
   - For storefronts, reuse `sales_channels.flows.default` helpers.
5. Tests:
   - Add unit tests for each factory, mocking the API client to verify payload construction, error handling, and sync/create switching.
   - Cover media and property sub-factories separately to keep assertions focused.

### Phase 8 – Live product signalling (initial rollout)
Applicable: Marketplace ✅ | Direct storefront ✅
1. Update `receivers.py` to listen for the minimal product signals first:
   - `create_remote_product` on `SalesChannelViewAssign` to queue a create task when a product is assigned to a view.
   - `update_remote_product` on `products.Product` for updates.
   - `delete_remote_product` for removals (both from assignments and hard deletes).
2. Route signals through flows (marketplaces use custom `run_*_amazon_sales_channel_task_flow`; storefronts reuse `run_generic_sales_channel_task_flow`).
3. Keep logging verbose while the integration is young. Add helper loggers (`_log_<integration>_product_signal`) to surface silent failures.
4. Document in the ticket that only product signals are live initially; other domains remain manual until Phase 9.

### Phase 9 – Extended live coverage (properties, prices, media, inventory, orders)
Applicable: Marketplace ✅ | Direct storefront ✅
1. Gradually enable additional signals once product sync is stable:
   - Properties: `create_remote_product_property`, `update_remote_product_property`, `delete_remote_product_property`.
   - Prices and inventory: `update_remote_price`, `update_remote_inventory` (if available).
   - Media: `create_remote_image_association`, `update_remote_image_association`, `delete_remote_image`, etc.
   - Orders: build dedicated receivers for order webhooks or polling flows before enabling live pushes.
2. Each new signal should point at specialised factories (`factories/properties/...`, `factories/prices/...`, `factories/inventory/...`). For marketplaces, ensure factories accept a `view` so they can scope to the correct marketplace.
3. Update tests to include the new signal wiring. Use decorator-based patching to assert the right task is enqueued without touching external services.
4. When extending live coverage, revisit `apps.py` and ensure all receivers are imported under `ready()`.

### Phase 10 – Testing, observability, and operations
Applicable: Marketplace ✅ | Direct storefront ✅
1. Add targeted tests for every new factory or mutation. Run them with `python manage.py test <path.to.test> --settings OneSila.settings.agent`.
2. Provide smoke scripts (`tests/helpers.py` or management commands) that call factory `.run()` with fixture data for manual QA.
3. Instrument logging:
   - Use structured logging around API calls, including remote identifiers and request IDs.
   - Surface validation issues on the remote model (e.g., store Amazon validation errors on `AmazonProduct.validation_errors`).
4. Update AGENTS or developer docs if the integration introduces new conventions.
5. Document follow-up tasks in the PR description (e.g., enable price signals after round-trip validation).

## Platform templates

Use these templates to double-check coverage per integration. Replace `<integration>` with the concrete directory name.

### Shopify
1. `models/sales_channels.py`: ensure access token, API version, install state, and store hostname fields exist.
2. `factories/mixins.py`: implement `GetShopifyApiMixin` wrapping the Shopify Python SDK session.
3. `factories/sales_channels/oauth.py`: redirect URL + token exchange (already present; extend when new scopes are required).
4. `schema/types/{input,types}.py` and `schema/mutations.py`: expose mutations `get_shopify_redirect_url` and `validate_shopify_auth` (extend for any new metadata pulls).
5. `factories/sales_channels/views.py`: pull shop locales, currencies, and primary store info right after auth.
6. `factories/properties/`: ensure tag handling and metafield mappings exist before pushing products.
7. `factories/imports/products_imports.py`: reuse GraphQL/bulk REST endpoints to import existing catalog items.
8. `factories/products/products.py` plus `prices.py`, `images.py`: confirm payload aligns with Shopify REST Admin API.
9. `receivers.py`: product create/update/delete + property, price, media signals wired through `sales_channels.flows.default` helpers.
10. Tests: `tests/tests_factories/test_products.py`, `test_sales_channel_oauth.py`, and `tests/tests_flows/test_task_runners.py` validating task fan-out.

### Magento 2
1. `models/sales_channels.py`: capture host URL, integration token, website/store view relations.
2. `factories/mixins.py`: `GetMagentoApiMixin` handles REST session (token + base URL) and retries.
3. `factories/sales_channels/credentials.py`: validate tokens and pull store views, websites, and currencies immediately after auth.
4. `factories/properties/`: pull attribute sets, attributes, and option lists; wire GraphQL queries for property management.
5. `factories/imports/products_imports.py`: import catalog via REST search API, storing configurable/variant relationships.
6. `factories/products/products.py`: create/update via REST `products` endpoint, including media gallery sync and inventory extensions.
7. `factories/inventory/`: manage stock items and reservations.
8. `factories/orders/`: optional but recommended before enabling order sync.
9. `receivers.py`: start with product signals, then extend to properties/prices/inventory once verified.
10. Tests: cover attribute pulls, product create/update payloads, and inventory adjustments.

### WooCommerce
1. `models/sales_channels.py`: store store URL, consumer key/secret, and version.
2. `factories/mixins.py`: wrap the WooCommerce REST client with signature generation.
3. `factories/sales_channels/credentials.py`: verify credentials, fetch store currencies, languages (if available via plugins), and shipping zones.
4. `factories/properties/`: map product attributes and terms.
5. `factories/imports/products_imports.py`: import simple, variable, and variation products; handle batch pagination.
6. `factories/products/products.py`: push payloads (WooCommerce batches create/update/delete) plus media uploads.
7. `factories/prices/` and `inventory/`: manage sale price windows, stock status, and multi-warehouse plugins when applicable.
8. `receivers.py`: enable product signals first; expand to attributes/prices when stable.
9. Add support for webhooks (optional) via `flows/` to listen for remote changes.
10. Tests: Verify credential validation, attribute imports, product pushes, and webhook handlers.

### Amazon (marketplace)
1. `models/sales_channels.py`: store refresh/access tokens, marketplace IDs, and Seller Central state.
2. `factories/sales_channels/oauth.py`: implement redirect + token exchange; persist `connection_error` on failure.
3. `factories/sales_channels/{views,languages,currencies}.py`: pull marketplaces, remote languages, and currencies immediately after auth.
4. `factories/properties/`: sync Amazon product types, properties, select values, and auto-mapping helpers.
5. `factories/imports/schema_imports.py`: import full product type schema; queue rule creation (`AmazonProductTypeRuleFactory`).
6. `factories/recommended_browse_nodes/`: manage browse node sync and translations.
7. `factories/imports/products_imports.py`: process SP-API listings into local remotes; handle configurable relationships and GTIN exemptions.
8. `factories/products/products.py`: implement create/update/delete with validation-only and GTIN logic; wire media, price, and property sub-factories.
9. `flows/tasks_runner.py`: fan out tasks per marketplace + remote product.
10. `receivers.py`: start with product signals; later enable property, price, content, and variation signals. Ensure logging captures remote IDs and view context.
11. `tasks.py`: expose `amazon_import_db_task`, `amazon_product_import_item_task`, and helper tasks for rule creation and translations.
12. Tests: fixture-based coverage for schema imports, property auto-mapping, product factories (including validation-only mode), and task fan-out.

### eBay (marketplace)
1. `models/sales_channels.py`: capture OAuth credentials, marketplace/site codes, business policies, and category cache.
2. `factories/sales_channels/oauth.py`: handle PKCE/OAuth exchange and schedule token refresh.
3. `factories/sales_channels/{marketplaces,currencies,languages}.py`: fetch site-specific metadata and business policies post-auth.
4. `factories/properties/`: map Item Specifics, categories, and policy requirements.
5. `factories/imports/schema_imports.py`: seed category trees and aspects for targeted marketplaces.
6. `factories/imports/products_imports.py`: import active listings and maintain local representation (Item ID, SKU, policy links).
7. `factories/products/products.py`: orchestrate Inventory API or Trading API calls for create/update/delete, including offer + inventory item flows.
8. `factories/prices/` and `inventory/`: manage price revisions, quantity adjustments, and business policy linking.
9. `flows/tasks_runner.py`: queue tasks per marketplace/site, respecting concurrency limits.
10. `receivers.py`: begin with product signals; extend to policies and pricing once validated.
11. Tests: validate OAuth flow, category/aspect imports, listing create/update payloads, and task orchestration.

## Final checklist before opening a PR
- [ ] App scaffolded with AppConfig, receivers imported, and schema registered.
- [ ] Auth factories + GraphQL mutations implemented; tokens validated and stored securely.
- [ ] Post-auth metadata pulls (views, currencies, languages) running automatically.
- [ ] Property and schema imports (if marketplace) available and idempotent.
- [ ] Product import pipeline in place with tests.
- [ ] Product push factories and flows implemented; live signals enabled for products only.
- [ ] Additional signals planned (documented) or implemented with coverage.
- [ ] Tests added for every new factory/mutation/flow and executed via agent settings.
- [ ] Logging and error surfaces updated for supportability.

Keep this playbook current when you discover better patterns or vendor-specific caveats.
