# eBay Push Strategy

Use this guide when implementing product export flows for the eBay integration. Payload examples follow eBay REST documentation, while the Python wrapper exposes every field in `snake_case`.

## Core endpoints

| Purpose | Wrapper method | Notes |
| --- | --- | --- |
| Create/replace single inventory item | `sell_inventory_create_or_replace_inventory_item(body, content_type, content_language)` | Send the complete item document (title, subtitle, description, aspects, media, internal properties, dimensions, etc.). |
| Create offer | `sell_inventory_create_offer(body, content_language, content_type)` | Builds the marketplace-specific offer. |
| Publish offer | `sell_inventory_publish_offer(offer_id)` | Activates the offer; `offer_id` equals the `SalesChannelViewAssign.remote_id`. |
| Bulk create/replace inventory items | `sell_inventory_bulk_create_or_replace_inventory_item(body, content_language, content_type)` | Use for variations (max batch size 25). |
| Bulk create offers | `sell_inventory_bulk_create_offer(body, content_language, content_type)` | Submit offers for multiple variations in one request. |
| Create/replace inventory item group | `sell_inventory_create_or_replace_inventory_item_group(body, content_language, content_type, inventory_item_group_key)` | Defines configurable parent (group key is parent SKU). |
| Publish offers by group | `sell_inventory_publish_offer_by_inventory_item_group(body, content_type)` | Publishes every offer linked to a parent SKU. |
| Delete single item | `sell_inventory_delete_inventory_item(sku)` | Run when the last marketplace is removed. |
| Delete configurable parent | `sell_inventory_delete_inventory_item_group(inventory_item_group_key)` | Use after clearing all variations. |
| Delete offer | `sell_inventory_delete_offer(offer_id)` | Remove a single marketplace listing. |
| Withdraw offers by group | `sell_inventory_withdraw_offer_by_inventory_item_group(body, content_type)` | Deactivate listings for configurable parents. |
| Update price/quantity | `sell_inventory_bulk_update_price_quantity(body, content_language, content_type)` | Supports price updates (quantity optional). |
| Update offer metadata | `sell_inventory_update_offer(offer_id, body, content_language, content_type)` | Required when refreshing `listing_description` or other offer-only fields. |
| Marketing price markdowns | `sell_marketing_create_item_price_markdown_promotion`, `sell_marketing_update_item_price_markdown_promotion`, `sell_marketing_delete_item_price_markdown_promotion` | Manage discounts per offer. |

## Payload construction

### Inventory item payload

The item document must include the following sections:

* `sku`: product SKU (variation SKU for configurable children).
* `product`:
  * `title`, `subtitle`, `description` (respect 80-char title limit).
  * `aspects`: send current `EbayProperty` selections.
  * `image_urls`: full list of media URLs.
  * `brand`, `upc`, `mpn`, `isbn`, `epid`, `ean`, `locale`, etc. sourced from internal property defaults or related models.
* `package_weight_and_size`: include `weight.value`, `weight.unit`, `dimensions.length`, `dimensions.width`, `dimensions.height`, `package_type`, `shipping_irregular`.
* `availability.ship_to_location_availability.quantity`: required by eBay, even if we ignore locally.

### Offer payload

* `sku`: the same SKU used for the inventory item.
* `marketplace_id`: map from `SalesChannelView.remote_id`.
* `format`: always "FIXED_PRICE".
* `listing_policies`: include `fulfillment_policy_id`, `payment_policy_id`, `return_policy_id` (plus optional `eBay_plus_if_eligible` when supported).
* `listing_description`: marketplace override; fall back to item description when empty.
* `listing_duration`: default to "GTC" for new offers.
* `merchant_location_key`: marketplace location key.
* `pricing_summary`: supply `price.value` and `price.currency`; optionally include `original_retail_price` as RRP.
* `tax.apply_tax` and `tax.vat_percentage`: mirror VAT configuration.

### Inventory item group payload (configurable parent)

```
{
  "title": "Parent title",
  "description": "Parent description",
  "aspects": { "brand": ["Nike"], "gender": ["men"] },
  "image_urls": ["https://..."],
  "variant_skus": ["sku_1", "sku_2", ...],
  "varies_by": {
    "aspectsImageVariesBy": ["Color"],
    "specifications": [
      {"name": "Color", "values": ["Green", "Blue", "Red"]}
    ]
  }
}
```

`inventory_item_group_key` equals the parent SKU.

## Export scenarios

### Single product / single variation

1. Call `sell_inventory_create_or_replace_inventory_item` with the item payload.
2. Call `sell_inventory_create_offer` with the offer payload.
3. Call `sell_inventory_publish_offer` using the resulting `offer_id`.
4. Surface any API validation errors to the user interface.

### Configurable product

1. Batch all variation payloads and send `sell_inventory_bulk_create_or_replace_inventory_item` (≤25 per call).
2. Build the offer payloads and call `sell_inventory_bulk_create_offer`.
3. Create/replace the parent with `sell_inventory_create_or_replace_inventory_item_group`, passing the parent SKU.
4. Publish with `sell_inventory_publish_offer_by_inventory_item_group`.
5. Capture and expose errors from any step to the user.

## Update operations

* **Product content**: Re-send `sell_inventory_create_or_replace_inventory_item` for the SKU and refresh `sell_inventory_update_offer` when marketplace descriptions change.
* **Aspects/properties**: Same as content—replace the full inventory item document.
* **Pricing**: Use `sell_inventory_bulk_update_price_quantity`; omit `ship_to_location_availability` if quantity is unchanged.
* **Images**: Always send the complete image list through `sell_inventory_create_or_replace_inventory_item`.
* **Discounts**: Use the marketing promotion endpoints to create/update/delete markdowns.

## Deletion flow

* Removing a single marketplace: call `sell_inventory_delete_offer` (or `sell_inventory_withdraw_offer_by_inventory_item_group` for configurables).
* Removing the last marketplace or deleting a product: delete the inventory item via `sell_inventory_delete_inventory_item`. For configurables also call `sell_inventory_delete_inventory_item_group` once all offers are gone.

Ensure we respect the wrapper’s snake_case naming when assembling payload dictionaries.

