# `imports_exports.factories` payload contracts

This file documents the payloads that the current factories actually accept or emit in this repo.
The goal is practical accuracy. If a field is listed here, the current code reads or writes it.

## Import Factories

## `ImportPropertyInstance`

Creates or updates a `Property`.

Required:
- one of `name` or `internal_name`

Optional:
- `type`
- `is_public_information`
- `add_to_filters`
- `has_image`
- `is_product_type`
- `translations`

Notes:
- if `type` is missing, it is auto-detected
- `translations` is a list of `{language, name}`
- updatable scalar flags are `is_public_information`, `add_to_filters`, `has_image`

Example:

```json
{
  "name": "Color",
  "internal_name": "color",
  "type": "SELECT",
  "is_public_information": true,
  "add_to_filters": true,
  "has_image": false,
  "translations": [
    {"language": "en", "name": "Color"},
    {"language": "nl", "name": "Kleur"}
  ]
}
```

## `ImportPropertySelectValueInstance`

Creates or updates a `PropertySelectValue`.

Required:
- `value`
- one of `property` or `property_data`

Optional:
- `translations`

Notes:
- `property_data` is passed to `ImportPropertyInstance`
- `translations` is a list of `{language, value}`

Example:

```json
{
  "value": "Red",
  "property_data": {
    "name": "Color",
    "internal_name": "color",
    "type": "SELECT"
  },
  "translations": [
    {"language": "en", "value": "Red"},
    {"language": "nl", "value": "Rood"}
  ]
}
```

## `ImportProductPropertiesRuleInstance`

Creates or updates a `ProductPropertiesRule`.

Required:
- `value`

Optional:
- `require_ean_code`
- `items`

`items` entries are handled by `ImportProductPropertiesRuleItemInstance` and accept:
- one of `property` or `property_data`
- one of `rule` or `rule_data`
- optional `type`
- optional `sort_order`

Rule item `type` values:
- `REQUIRED_IN_CONFIGURATOR`
- `OPTIONAL_IN_CONFIGURATOR`
- `REQUIRED`
- `OPTIONAL`

Example:

```json
{
  "value": "T-Shirt",
  "require_ean_code": true,
  "items": [
    {
      "property_data": {
        "name": "Color",
        "internal_name": "color",
        "type": "SELECT"
      },
      "type": "REQUIRED_IN_CONFIGURATOR",
      "sort_order": 1
    }
  ]
}
```

## `ImportProductPropertyInstance`

Creates or updates a `ProductProperty`.

Required:
- `value`
- one of `property` or `property_data`
- one of `product` or `product_data`

Optional:
- `value_is_id`
- `translations`

Current reverse value rules used by the code:
- `INT` -> integer
- `FLOAT` -> float
- `BOOLEAN` -> boolean
- `DATE` / `DATETIME` -> parsed with `dateutil`
- `TEXT` -> stored in `value_text`
- `DESCRIPTION` -> stored in `value_description`
- `SELECT`:
  - `value_is_id=true` -> treat `value` as select value ID
  - otherwise resolve by translated value
- `MULTISELECT`:
  - `value_is_id=true` -> treat `value` as a list of IDs
  - otherwise resolve each entry by translated value

Export compatibility target:

```json
{
  "property": {
    "name": "Color",
    "internal_name": "color",
    "type": "SELECT"
  },
  "value": "Red",
  "values": [
    {"value": "Red"}
  ],
  "requirement": "OPTIONAL"
}
```

When exporting IDs instead of translated values:

```json
{
  "property": {
    "name": "Color",
    "internal_name": "color",
    "type": "SELECT"
  },
  "value": 12,
  "values": [
    {"value": 12}
  ]
}
```

## `ImportProductInstance`

Creates or updates a `Product`.

Required:
- no hard required keys if an existing `instance` is provided
- for normal creation the practical minimum is `name` or `sku`
- if `type` is supplied it must be one of `SIMPLE`, `CONFIGURABLE`, `BUNDLE`, `ALIAS`

Optional top-level fields read by the factory:
- `name`
- `sku`
- `type`
- `active`
- `vat_rate`
- `use_vat_rate_name`
- `ean_code`
- `allow_backorder`
- `alias_parent_product`
- `alias_parent_sku`
- `product_type`
- `properties`
- `translations`
- `images`
- `documents`
- `prices`
- `sales_pricelist_items`
- `variations`
- `bundle_variations`
- `alias_variations`
- `configurator_select_values`
- `skip_rule_item_sync`

Nested payloads the factory supports:
- `translations` -> `ImportProductTranslationInstance`
- `images` -> `ImportImageInstance`
- `documents` -> `ImportDocumentInstance`
- `prices` -> `ImportSalesPriceInstance`
- `sales_pricelist_items` -> `ImportSalesPriceListItemInstance`
- `properties` -> `ImportProductPropertyInstance`
- `variations` -> `ImportConfigurableVariationInstance`
- `bundle_variations` -> `ImportBundleVariationInstance`
- `alias_variations` -> `ImportAliasVariationInstance`
- `configurator_select_values` -> used by `ImportConfiguratorVariationsInstance`

Example:

```json
{
  "name": "Plain T-Shirt",
  "sku": "plain-ts",
  "type": "SIMPLE",
  "active": true,
  "vat_rate": 19,
  "ean_code": "1234567890123",
  "allow_backorder": false,
  "product_type": "T-Shirt",
  "translations": [
    {
      "language": "en",
      "name": "Plain T-Shirt",
      "subtitle": "Soft cotton basic",
      "sales_channel": null,
      "short_description": "Very nice T-Shirt",
      "description": "Long description",
      "url_key": "plain-t-shirt",
      "bullet_points": [
        "100% cotton"
      ]
    }
  ],
  "properties": [
    {
      "property_data": {
        "name": "Color",
        "internal_name": "color",
        "type": "SELECT"
      },
      "value": "Red"
    }
  ],
  "images": [
    {
      "image_url": "https://example.com/image.jpg",
      "type": "PACK",
      "title": "Front",
      "description": "Front image",
      "is_main_image": true,
      "sort_order": 10
    }
  ],
  "documents": [
    {
      "document_url": "https://example.com/manual.pdf",
      "title": "Manual",
      "description": "Product manual",
      "document_type": "MANUAL",
      "document_language": "en",
      "sort_order": 10
    }
  ],
  "prices": [
    {
      "price": 49.99,
      "rrp": 59.99,
      "currency": "EUR"
    }
  ]
}
```

## `ImportProductTranslationInstance`

Creates or updates a `ProductTranslation`.

Required:
- `name`
- one of `product` or `product_data`

Optional:
- `subtitle`
- `short_description`
- `description`
- `url_key`
- `language`
- `bullet_points`
- `sales_channel`

Example:

```json
{
  "language": "en",
  "name": "Export Product",
  "subtitle": "Small subtitle",
  "short_description": "Short text",
  "description": "Long text",
  "url_key": "export-product",
  "bullet_points": ["Point one", "Point two"],
  "product_data": {"sku": "EXPORT-001"}
}
```

## `ImportImageInstance`

Creates or links an `Image` and optionally assigns it to a product.

Required:
- one of `image_url` or `image_content`

Optional:
- `type`
- `title`
- `description`
- `product_data`
- `is_main_image`
- `sort_order`

Notes:
- `image_content` takes priority over `image_url`
- `image_url` must be HTTPS
- `type` defaults to `Image.PACK_SHOT`

## `ImportDocumentInstance`

Creates or links a document/file and optionally assigns it to a product.

Required:
- `document_url`

Optional:
- `title`
- `description`
- `document_type`
- `document_language`
- `product_data`
- `sort_order`

Notes:
- only HTTPS URLs are allowed
- file type is inferred from the URL extension
- image-like documents are also marked as document images

## Variation imports

### `ImportConfigurableVariationInstance`

Required:
- one of `config_product` or `config_product_data`
- one of `variation_product` or `variation_data`

Payload shape:

```json
{
  "variation_data": {
    "sku": "variant-red-l",
    "name": "Red / L"
  }
}
```

### `ImportConfiguratorVariationsInstance`

Required:
- one of `config_product` or `config_product_data`
- one of `rule` or `rule_data`
- one of `select_values` or `values`

`values` entries look like:

```json
{
  "property_data": {"name": "Color", "type": "SELECT"},
  "value": "Red"
}
```

### `ImportBundleVariationInstance`

Required:
- one of `bundle_product` or `bundle_product_data`
- one of `variation_product` or `variation_data`
- `quantity` or `qty`

### `ImportAliasVariationInstance`

Required:
- one of `parent_product` or `parent_product_data`
- one of `alias_product` or `variation_data`

Optional:
- `alias_copy_images`
- `alias_copy_product_properties`
- `alias_copy_content`

`variation_data.type` is forced to `ALIAS`.

## Sales price imports

## `ImportEanCodeInstance`

Creates or updates an `EanCode`.

Required:
- `ean_code`
- one of `product`, `product_sku`, or `product_data.sku`

Optional:
- `internal`
- `already_used`

Notes:
- if the product cannot be resolved by SKU, the importer skips the row without creating an EAN code

### `ImportSalesPriceInstance`

Required:
- one of `rrp` or `price`
- `currency`
- one of `product` or `product_data`

Notes:
- if only one of `rrp` or `price` is provided, the factory normalizes it
- `currency` must be a supported ISO code

### `ImportSalesPriceListInstance`

Required:
- `name`
- `currency`

Optional:
- `start_date`
- `end_date`
- `vat_included`
- `auto_update_prices`
- `auto_add_products`
- `price_change_pcnt`
- `discount_pcnt`
- `notes`
- `sales_pricelist_items`

### `ImportSalesPriceListItemInstance`

Required:
- one of `salespricelist` or `salespricelist_data`
- one of `product` or `product_data`

Optional:
- `price_auto`
- `discount_auto`
- `price_override`
- `discount_override`
- `disable_auto_update`

Example:

```json
{
  "salespricelist_data": {
    "name": "Wholesale EUR",
    "currency": "EUR"
  },
  "product_data": {
    "sku": "EXPORT-001"
  },
  "price_override": 39.99
}
```

## Export Factories

## General export rules

- Export `raw_data` should stay import-compatible whenever possible.
- Export kind uses `property_select_values`. Do not split this into separate `property_values` and `select_values`.
- Media exports are split by kind: `images`, `documents`, and `videos`.
- If export `columns` is empty or omitted, exporters emit all supported columns.
- Export `parameters` carries behavior flags and filters such as `flat`, `active_only`, `sales_channel`, `ids`, or nested config like `product_properties: {add_value_ids: true}`.
- Export processing sets `total_records` from `queryset.count()`, iterates top-level rows with `.iterator()`, and updates `percentage` in 10% steps while building `raw_data`.
- Output `type` controls transport only:
  - `json_feed` serves stored `raw_data`
  - `json` writes a file from `raw_data`
  - `csv` and `excel` currently generate `raw_data` first and then raise not implemented during file generation

## `products`

Supported columns:
- `name`
- `sku`
- `type`
- `active`
- `vat_rate`
- `ean_code`
- `allow_backorder`
- `product_type`
- `translations`
- `sales_channels`
- `properties`
- `images`
- `documents`
- `prices`
- `sales_pricelist_items`
- `variations`
- `bundle_variations`
- `alias_variations`
- `configurator_select_values`
- `configurable_products_skus`
- `bundle_products_skus`
- `alias_products_skus`

Important parameters:
- `language`
- `sales_channel`
- `active` or `active_only`
- `ids`, `product_ids`, or `products_ids`
- `flat`
- nested `product_properties.add_value_ids`

Notes:
- `translations` contain all product translations, both default and sales-channel-specific
- each translation emits `sales_channel` as the sales channel ID, or `null` for default translations
- translation payload includes `name`, `subtitle`, `short_description`, `description`, `url_key`, and `bullet_points` when present
- `sales_channels` emits assigned channels as `{id, hostname, type, subtype}`
- `sales_channel` filtering includes products directly assigned by `SalesChannelViewAssign` and variations inherited from assigned parent products
- `configurable_products_skus`, `bundle_products_skus`, and `alias_products_skus` are only emitted when `flat=true`

Example:

```json
{
  "sku": "plain-ts",
  "translations": [
    {
      "language": "en",
      "name": "Plain T-Shirt",
      "subtitle": "Soft cotton basic",
      "sales_channel": null,
      "bullet_points": ["100% cotton"]
    },
    {
      "language": "en",
      "name": "Plain T-Shirt Amazon",
      "sales_channel": 12
    }
  ],
  "sales_channels": [
    {
      "id": 12,
      "hostname": "https://amazon.example.com",
      "type": "amazon",
      "subtype": null
    }
  ]
}
```

## `product_properties`

Supported columns:
- `product_data`
- `product_sku`
- `properties`

Important parameters:
- `product` or `product_ids`
- `ids`
- `sales_channel`
- `add_translations`
- `values_are_ids`
- `add_value_ids`
- nested `product_properties.add_value_ids`

Notes:
- each entry in `properties` emits `property`, `value`, `values`, and optional `requirement`
- `value` is the singular import-friendly representation
- `values` is the list form used for select and multiselect compatibility

## `properties`

Supported columns:
- `id`
- `name`
- `internal_name`
- `type`
- `is_public_information`
- `add_to_filters`
- `has_image`
- `is_product_type`
- `translations`
- `property_select_values`

Important parameters:
- `ids`
- nested `property_select_values.add_value_ids`

## `property_select_values`

Supported columns:
- `id`
- `value`
- `property_data`
- `translations`

Important parameters:
- `ids`
- `property`
- `add_value_ids` or `values_are_ids`

Notes:
- this is the only select-value export kind

## `rules`

Supported columns:
- `value`
- `require_ean_code`
- `items`

Important parameters:
- `ids`
- `sales_channel`

## `images`

Supported columns:
- `image_url`
- `type`
- `title`
- `description`
- `product_data`
- `product_sku`
- `sort_order`
- `is_main_image`

Important parameters:
- `ids`
- `product`
- `sales_channel`
- `add_product_sku`
- `add_title`
- `add_description`

## `documents`

Supported columns:
- `document_url`
- `type`
- `title`
- `description`
- `product_data`
- `product_sku`
- `sort_order`
- `document_type`
- `document_language`
- `thumbnail_image`
- `is_document_image`

Important parameters:
- `ids`
- `product`
- `sales_channel`
- `add_product_sku`
- `add_title`
- `add_description`

## `videos`

Supported columns:
- `video_url`
- `type`
- `title`
- `description`
- `product_data`
- `product_sku`
- `sort_order`

Important parameters:
- `ids`
- `product`
- `sales_channel`
- `add_product_sku`
- `add_title`
- `add_description`

## `sales_prices`

Supported columns:
- `rrp`
- `price`
- `currency`
- `product_data`
- `product_sku`

Important parameters:
- `ids`
- `product`
- `add_product_sku`

## `price_lists`

Supported columns:
- `name`
- `start_date`
- `end_date`
- `currency`
- `vat_included`
- `auto_update_prices`
- `auto_add_products`
- `price_change_pcnt`
- `discount_pcnt`
- `notes`
- `sales_pricelist_items`

Important parameters:
- `ids`

## `price_list_prices`

Supported columns:
- `price_auto`
- `discount_auto`
- `price_override`
- `discount_override`
- `product_data`
- `product_sku`
- `salespricelist_data`
- `salespricelist_name`

Important parameters:
- `ids`
- `product`
- `salespricelist`
- `add_product_sku`

## `ean_codes`

Supported columns:
- `ean_code`
- `product_sku`

Important parameters:
- `ids`
- `product`
- `add_product_sku`

Notes:
- the payload is intentionally simple so it can be fed directly into `ImportEanCodeInstance`

Example:

```json
{
  "ean_code": "1234567890123",
  "product_sku": "EXPORT-001"
}
```
