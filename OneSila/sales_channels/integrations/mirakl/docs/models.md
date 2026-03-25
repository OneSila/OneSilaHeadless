# Mirakl Models

This document describes the current planned model structure for the Mirakl integration.

It is a working fingerprint, not a frozen spec. Some parts are still uncertain and are intentionally documented as such so we can adjust them later without losing the reasoning.

## Current Mirakl Mental Model

Our current understanding is:

- One Mirakl API credential can access one or more seller shops.
- `shop_id` selects which Mirakl shop the API acts as.
- In OneSila, we currently plan to model `1 Mirakl shop = 1 MiraklSalesChannel`.
- Mirakl channels are different from Mirakl shops.
- Mirakl channels fit best as `MiraklSalesChannelView`.
- Mirakl is marketplace-like in structure:
  - categories / hierarchies
  - attributes
  - values lists
  - catalog products
  - pricing / stock / product imports
- Mirakl does not appear to be centered around a classic record-by-record product create API.
- Product creation/import appears to be feed/import based.
- For now, we intentionally ignore a dedicated `MiraklOffer` model.
- For now, pricing transparency and async processing are planned through `MiraklProductPrice` and `MiraklImport`.

## Main Identity Models

### `MiraklSalesChannel`

Main identity for a Mirakl integration in OneSila.

Current plan:

- `1 Mirakl shop = 1 MiraklSalesChannel`

Expected fields:

- `hostname`
- `shop_id`
- `api_key`
- optional `raw_data` / `metadata` JSON field

Primary APIs:

- `A01`
- `A21`
- `PC01`

Notes:

- `shop_id` belongs here, not on the view. even if there will be one account with multiple shops the shops will be created as separate integration
- Even if the API key only has one default shop, we still want to store `shop_id` explicitly so behavior stays deterministic.
- We do not currently plan first-class fields for:
  - remote shop name
  - default currency
  - offers count
  - last synced at
- If needed, those can live in JSON.

### `MiraklSalesChannelView`

Represents a Mirakl channel under one Mirakl shop.

Expected fields:

- `sales_channel`
- `code`
- `label`
- `description`

Primary APIs:

- `CH11`

Notes:

- We currently expect pricing and some product behavior to be channel-aware, so this should exist from the start.

## Reference / Platform Models

### `MiraklLanguage`

Represents an activated Mirakl locale/language.

Expected fields:

- `sales_channel`
- `code`
- `label`
- `is_default`

Primary APIs:

- `L01`

### `MiraklCurrency`

Represents an activated Mirakl currency.

Expected fields:

- `sales_channel`
- `code`
- `label`
- `is_default` (from currency_iso_code A01)

Primary APIs:

- `CUR01`

Notes:

- Default currency can be derived or stored in JSON on the sales channel if needed.

### `MiraklInternalProperty`

Represents Mirakl internal/operator property definitions.

Expected fields:

- `sales_channel`
- `code`
- `label`
- `name`
- `description`
- `entity`
- `type`
- `required`
- `editable`
- `accepted_values`
- `regex`
- `is_condition`

Primary APIs:

- `AF01`
- `OF61`

Notes:

- This is the Mirakl equivalent of the internal-property layer used by Amazon and eBay.
- It is not currently treated as part of the main product schema.
- It may still be mapped to local properties and used in listing / publishing rules.
- Condition should live in this layer as well.
- This should likely mirror the eBay structure: one internal property plus a separate option model when the field is enumerated.

### `MiraklInternalPropertyOption`

Represents an allowed option for a Mirakl internal property.

Expected fields:

- `internal_property`
- `sales_channel`
- optional `local_instance`
- `value`
- `label`
- optional `description`
- `sort_order`
- `is_active`

Primary APIs:

- `AF01`
- `OF61`

Notes:

- This should follow the same basic role as `EbayInternalPropertyOption`.
- Use this when Mirakl internal properties expose a controlled set of allowed values.
- `is_condition` belongs on `MiraklInternalProperty`, not on the option rows.

### `MiraklDocumentType`

Placeholder model for Mirakl document types.

Expected fields:

- `sales_channel`
- `code`
- `label`
- `description`

Primary APIs:

- `DO01`

Notes:

- Current understanding is that Mirakl documents are mainly shop / order oriented.
- We should still create the type model now, even if implementation is minimal.

## Taxonomy / Property Models

### `MiraklCategory`

Represents a Mirakl hierarchy/category node.

Expected fields:

- `sales_channel`
- `code`
- `label`
- `parent_code`
- `parent`
- `level`
- `is_leaf`
- translated labels if needed

Primary APIs:

- `H11`

Notes:

- This is the default category-tree model, similar to `EbayCategory` and `SheinCategory`.
- Even if Mirakl docs use hierarchy-oriented wording, our model naming should stay aligned with the other marketplace integrations.
- We may still use product-type language elsewhere when talking about property applicability, but the main taxonomy node should be `MiraklCategory`.

### `MiraklProperty`

Represents a Mirakl attribute definition.

Expected fields:

- `sales_channel`
- `code`
- `label`
- `description`
- `type`
- `required`
- `variant`
- `requirement_level`
- `default_value`
- `value_list`
- raw `validations`
- raw `transformations`

Primary APIs:

- `PM11`

Notes:

- We do not currently want to duplicate the same property per channel.
- The property itself should be unique at the sales-channel / shop level unless real data proves otherwise.

### `MiraklProductTypeItem`

Link model between `MiraklCategory` and `MiraklProperty`.

Expected fields:

- `category`
- `property`
- optional raw role / usage fields
- optional required / variant overrides if Mirakl behaves that way

Primary APIs:

- `PM11`

Notes:

- This follows the same conceptual pattern as other marketplace integrations.

### `MiraklPropertyApplicability`

Tracks channel availability for a property without duplicating mappings.

Expected fields:

- `property`
- `view`

Primary APIs:

- `PM11.channels`

Notes:

- Current plan is to avoid mapping the same Mirakl property multiple times just because it is available in several Mirakl channels.
- This model may be replaced by a direct many-to-many implementation depending on final querying needs.

### `MiraklPropertySelectValue`

Represents a selectable value for a Mirakl property.

Expected fields:

- `property`
- `code`
- `label`
- optional `value_list_code`
- optional `value_list_label`
- translated labels if needed

Primary APIs:

- `VL11`
- possibly inline `PM11.values`

Notes:

- This should follow the same naming pattern as the other marketplace integrations and be called `MiraklPropertySelectValue`.
- If Mirakl value lists need to be preserved structurally, keep their identifiers as fields on the select value or in raw JSON first.
- We do not currently plan a separate `MiraklValueList` model.

## Remote Product Models

### `MiraklProduct`

Represents a Mirakl remote catalog product / reference product.

Expected fields:

- `sales_channel`
- remote identifier fields
- product references
- sku / title / brand where available
- raw payload snapshot

Primary APIs:

- `P31`
- `P41` planned / uncertain for create / import flow

Notes:

- This is the remote catalog identity we match or publish against.
- The exact unique identity is still uncertain because Mirakl product references can be structured in several ways.

### `MiraklProductCategory`

Polymorphic assignment between a local product and a Mirakl product type.

Expected fields:

- shared remote-category assignment fields
- `remote_category` -> `MiraklCategory`

Notes:

- This is part of the standard integration structure and should exist even if first usage is simple.

### `MiraklProductContent`

Represents remote content synced for a product.

Expected fields:

- product/content shared integration fields
- title / description style fields as needed

Notes:

- Exact payload ownership is still uncertain because Mirakl publishing is import-driven.
- Still worth defining early for parity with the rest of the integrations.

### `MiraklProductPrice`

Represents the effective remote price layer for a product.

Expected fields:

- shared remote-price fields
- `product`
- optional `view` if channel-specific pricing becomes necessary
- current price / discount-related fields if needed

Primary APIs:

- pricing behavior likely tied to `PRI01`
- possibly current-state enrichment from product / offer endpoints

Notes:

- Current assumption is `1 product -> 1 MiraklProductPrice`.
- This may change if Mirakl pricing turns out to be channel-specific in a way that needs separate rows.
- For now we use this model instead of introducing `MiraklOffer`.

### `MiraklProductEanCode`

Represents EAN / identifier data for a Mirakl product.

Expected fields:

- `product`
- `type`
- `value`

Primary APIs:

- `P31`

Notes:

- This is important because Mirakl product lookup is reference-driven.

## Import / Transparency Models

### `MiraklImport`

Represents Mirakl async import tracking.

Expected fields:

- `sales_channel`
- `type`
- `remote_import_id`
- `status`
- `source_file_name`
- `has_error_report`
- `has_transformed_file`
- `created_at`
- `updated_at`
- `ended_at`
- raw response / summary payload
- optional links to affected product / view / object

Primary APIs:

- `P51`
- `P42`
- `OF04`
- `OF02`
- `STO02`
- `PRI02`

Type candidates:

- `product`
- `offer`
- `pricing`

Notes:

- We want this visible in the frontend for transparency.
- This is similar to logs, but more structured around Mirakl async processing.
- This will likely be important very early because many Mirakl flows return tracking IDs instead of immediate final results.
- We do not currently care about a dedicated `stock` import type because OneSila is acting as a PIM, not an ERP.
- `offer` and `pricing` may end up collapsing into one import type if Mirakl commercial behavior does not require them to stay separate.

## Documents

Current understanding:

- Mirakl documents appear to be mainly:
  - shop documents
  - order documents
- We do not currently see product documents as a main phase-1 concern.

Current plan:

- create placeholder document-related models only where needed
- avoid building full document workflows in the first implementation slice

Potential future models:

- `MiraklShopDocument`
- `MiraklOrderDocument`

These are not phase-1 priorities.

## Uncertain Areas

These are still intentionally unresolved.

### Product import `P41`

We currently have conflicting local documentation:

- the local `README.md` documents `P41`
- the local `api_schema.json` does not expose the `POST /api/products/imports` operation

So:

- we should not depend on product import for first delivery
- we should keep `MiraklProduct` in the model plan
- we should treat product creation / import as a later confirmed workflow

### Offer model

Current decision:

- ignore `MiraklOffer` for now

Reason:

- current thinking is that `MiraklImport(type=pricing)` and `MiraklProductPrice` may be enough for the first implementation shape
- we may later discover that Mirakl offer behavior deserves a dedicated model similar to `EbayOffer`

This remains open and should not be considered final.

### Property scoping

Current assumption:

- properties live once per `MiraklSalesChannel`
- channel-specific usability is tracked separately

This should prevent duplicate mappings, but we need real payload validation before freezing it.

### Product identity

We still need to determine which combination is safest as the stable remote identifier:

- Mirakl product reference
- product reference type
- seller sku
- import-level identifiers
- or a combination

## Phase-1 Working Set

If we start small, the first important models are:

- `MiraklSalesChannel`
- `MiraklSalesChannelView`
- `MiraklLanguage`
- `MiraklCurrency`
- `MiraklInternalProperty`
- `MiraklInternalPropertyOption`
- `MiraklDocumentType`
- `MiraklCategory`
- `MiraklProperty`
- `MiraklProductTypeItem`
- `MiraklPropertyApplicability`
- `MiraklPropertySelectValue`
- `MiraklProduct`
- `MiraklProductCategory`
- `MiraklProductContent`
- `MiraklProductPrice`
- `MiraklProductEanCode`
- `MiraklImport`
