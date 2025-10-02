# eBay Import Strategy

This document captures how we mirror eBay Inventory API data into OneSila. Examples are taken from eBay's REST documentation but note that the Python wrapper exposes every field in `snake_case`.

## Source endpoints

* Inventory items: `sell_inventory_get_inventory_item`
* Inventory item groups (configurable parents): `sell_inventory_get_inventory_item_group`
* Offers per marketplace: `sell_inventory_get_offer`

Always hydrate the base inventory item first, then collect offers for each marketplace/view.

## Item-level mapping

| eBay inventory item field | Local destination | Notes |
| --- | --- | --- |
| `sku` | `Product.sku` | Primary identifier for the product/variation. |
| `availability.ship_to_location_availability.quantity` | _Ignored_ | Reserved for future structural work; currently dropped. |
| `condition` | `EbayInternalProperty` → `ProductProperty` | Persist under the internal defaults namespace so the value becomes a local property. |
| `product.title` | `ProductTranslation.name` | Limit to 80 characters to respect eBay constraints. |
| `product.subtitle` | `ProductTranslation.subtitle` | **New** field required on translation model. |
| `product.description` | `ProductTranslation.description` | Use marketplace or language specific translation. |
| `product.aspects` | `EbayProperty` + `EbayPropertySelectValue` → `ProductProperty` | Persist keyed aspects and selected values. |
| `product.image_urls` | `Image` + `MediaAssociation` | Download/register each media reference. |
| `product.upc`, `product.mpn`, `product.isbn`, `product.epid`, `product.brand`, `product.package_weight_and_size.*`, `package_weight_and_size.shipping_irregular` | `EBAY_INTERNAL_PROPERTY_DEFAULTS` | Create dedicated internal property keys for each attribute; map values straight into linked product properties. |
| `product.ean` | `EanCode` | Attach to the product’s EAN codes. |
| `product.locale` | Reverse-resolve `EbayLanguage` | Match the eBay locale to our language entity for translations. |
| `inventory_item_group_keys` / `group_ids` | Parent SKU linkage | Treat presence as configurable parent relationship and sync parent first. |

## Offer-level mapping

Each inventory item can expose multiple marketplace offers. Import every marketplace/view combination and attach them to `SalesChannelViewAssign` records.

| eBay offer field | Local destination | Notes |
| --- | --- | --- |
| `offer_id` | `SalesChannelViewAssign.remote_id` | Primary key for the offer. |
| `marketplace_id` | `SalesChannelView` | Create/retrieve the view for the marketplace. |
| `listing.listing_status` | Product assignment status | `ACTIVE` → active, `INACTIVE` → inactive. |
| `pricing_summary.price.value` | Offer price | Store in the view assignment. |
| `pricing_summary.price.currency` | `EbayCurrency` (per marketplace) | Resolve using marketplace metadata. |
| `pricing_summary.original_retail_price.value` | RRP | Optional reference price on the assignment. |
| `tax.apply_tax` / `tax.vat_percentage` | VAT linkage | Attach to VAT table; treat falsy values as “no tax”. |
| `listing_description` | Marketplace-specific override | Use when present instead of item description. |
| `listing.listing_id` | TBD storage | Capture for diagnostics (candidate field on `SalesChannelViewAssign`). |
| `listing_duration` | Default `GTC` on push | Imported for completeness. |
| `listing_policies.fulfillment_policy_id` / `payment_policy_id` / `return_policy_id` | Marketplace policy references | Persist on assignment so we can reuse on push. |
| `merchant_location_key` | Merchant location | Required for push operations. |
| `pricing_summary.pricing_visibility`, `quantity_limit_per_buyer`, `listing.listing_on_hold`, `listing.sold_quantity`, `charity`, `store_category_names`, `regulatory`, `shipping_cost_overrides`, `regional_*` | _Ignored_ | Currently unsupported. |

## Import flow

1. **Fetch inventory item** (`sell_inventory_get_inventory_item`).
2. **Create/update the product**:
   * Upsert base product and translation.
   * Ensure every internal property default exists and map values.
   * Register aspects as selectable properties.
   * Mirror media references.
3. **Detect configurable parents**:
   * If `group_ids` (or `inventory_item_group_keys`) exists, fetch parent via `sell_inventory_get_inventory_item_group` and create the configurable product shell before linking variations.
4. **Fetch offers per marketplace** (`sell_inventory_get_offer`).
5. **Create/update `SalesChannelViewAssign` records**:
   * Match view by `marketplace_id` and create when missing.
   * Store pricing, policy references, merchant location, and description overrides.
   * Track listing status to control local activation.

Record any API validation failures as user-facing errors so they surface in the UI.

