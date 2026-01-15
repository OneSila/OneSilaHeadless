# Marketplace Sync Signals

This document defines the signal model and guard logic for marketplace async syncs
(Amazon, Ebay, Shein, Temu, Mirakl, Bol, and future marketplace integrations).
Direct website integrations (Magento, Shopify, WooCommerce) remain live, but should
reuse the same guard logic to avoid unnecessary updates.

## Goals
- Only create a sync signal when a change is relevant to the current sales channel
  view and will produce a real remote update.
- Dedupe signals for the same target product and view.
- Upgrade to a product/full sync when multiple change types stack up.

## Model Shape (Conceptual)
- `remote_product`: required, points to the product being synced.
- `view`: nullable; `AmazonSalesChannelView` for Amazon, null for channels that do
  not use views (e.g., Shein).
- `signal_type`: one of `product`, `content`, `price`, `images`, `property`.
- `status`: `pending`, `done`, `failed`.
- `reason`: short text or enum describing the trigger.
- `last_seen_at`: timestamp for dedupe refresh.

### Dedupe Constraint
Use a unique constraint on `(remote_product, view, signal_type)` and ensure that
`NULL` view values are treated as equal:

- PostgreSQL: `UniqueConstraint(..., nulls_distinct=False)`
- If the database does not support this, normalize null views to a sentinel value.

## View Resolution
Some changes are view-specific, others are channel-wide. Determine the view scope
before creating signals:

- Content: map the content language to a view (e.g., `AmazonRemoteLanguage`).
- Price: map the currency to a view (e.g., `AmazonRemoteCurrency`).
- Text/description properties with a language should also map to a view.
- Images, product identity changes, and property assignments do not carry a view.
  For these, create a signal per view for the sales channel (or use `None` when
  the integration does not have views).

## Flow A: Signal Type Resolution
1. **Hard gate**: if `remote_product.successfully_created` is False, STOP.
2. Determine `view` (e.g., `AmazonSalesChannelView`) or `None`. If the change is
   viewless, create one signal per view for the sales channel.
3. Determine `target_remote_product`:
   - If `remote_product.is_variation` and change type is `content`, `images`,
     `property`, or `product`, target the parent remote product.
   - If change type is `price`, target the variation itself.
4. Determine `signal_type`:
   - `content` for content changes.
   - `images` for image changes.
   - `property` for property changes on simple products assigned individually.
   - `price` for price changes.
   - `product` for identity/availability changes (active, EAN, SKU, identifiers).
5. Apply dedupe/upgrade rules (Flow C).

## Flow B: Protection Checks
Only create a signal when the change will affect the **effective** values for the
current channel view.

### Content
- If the content is tied to a different sales channel/view, STOP.
- If the change is on default content:
  - If a channel-specific override exists and is non-empty, STOP.
  - Otherwise compare effective content before/after; if unchanged, STOP.
- If the change is on channel-specific content:
  - If it is not the current sales channel/view, STOP.
  - Compare effective content before/after; if unchanged, STOP.

### Images
- If `ImageProductAssociation.sales_channel` is not the current view, STOP.
- If `ImageProductAssociation.sales_channel` is None (default):
  - If any override images exist for the current view, STOP.
  - Otherwise continue.
- If it is for the current view, continue.
- Compare the effective image set hash before/after; if unchanged, STOP.

### Properties
Properties require integration-specific mapping logic and category usage checks.
These checks should be implemented via a configurable class per integration.

- Guard 1: property is mapped for the current view (integration-specific check).
- Guard 2: property is used in the current category (integration-specific check).
- Guard 3: property is relevant to the current ProductPropertiesRule for the view.
- Guard 4: if property is select-type or multi-select, the option value is mapped.
- If any guard fails, STOP.
- If variation: target the parent remote product.
- If simple assigned individually: create a `property` signal (do not full sync).

### Price
- Compute the effective price using channel rules (currency, rounding, discounts).
- Compare effective price before/after; if unchanged, STOP.
- Target the variation (do not escalate to parent).

### Product/Full
Use for fields that change identity or availability (active, EAN, SKU, identifiers).
If the product is a variation, target the parent.

## Flow C: Dedupe and Upgrade Rules
1. Look for an existing signal on `(target_remote_product, view, signal_type)`.
2. If found, refresh `last_seen_at` and `reason`; STOP.
3. If a different signal type exists for the same target and view, upgrade it to
   `product` and update the reason; STOP.
4. Otherwise create a new signal.

## Notes
- Signals are only for marketplace integrations. Live channels can reuse the
  protection checks to avoid unnecessary pushes.
- If a sync is required while `successfully_created` is False, it must be
  initiated explicitly (do not create signals in that state).
